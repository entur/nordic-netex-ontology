#!/usr/bin/env python3
"""Generate SHACL shapes from profile:cardinality (docs/adr/0002).

Reads the profile:ProfileMember entries of one profile layer, resolves each
profile:path against the vendored base by name, and writes a constraint
wherever the profile is stricter than the XSD: sh:minCount when the profile
requires what the XSD leaves optional, sh:maxCount when it allows fewer.
Where profile and XSD agree, nothing is written.

Path steps are matched by name, never by computing an IRI: first against
sh:name on the base's property shapes for the class and its ancestors, then,
for a substitution group member (AuthorityRef where the XSD declares
TransportOrganisationRef), through rdfs:subPropertyOf. A path ending in
X/@ref is a requirement on X. A nested path becomes a nested property shape
(sh:node), so it applies only where its parent is present.

Layer-agnostic: a downstream profile runs it on its own layer and passes the
layers it builds on with --context.

Usage:
  python scripts/generate-shapes.py           (writes netex-nordic-shapes.ttl)
  python scripts/generate-shapes.py --check   (exit 1 if the file is stale)
  python scripts/generate-shapes.py --layer L --namespace NS --prefix P
      --ontology IRI --out F [--context C ...]
"""
import argparse
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, PROV, RDF, RDFS

ROOT = Path(__file__).resolve().parent.parent
NETEX = Namespace("https://netex-cen.eu/ontology#")
PROFILE = Namespace("https://netex-cen.eu/profile#")
SH = Namespace("http://www.w3.org/ns/shacl#")
BASE_SHAPES = "https://netex-cen.eu/ontology/shacl#"
UNBOUNDED = float("inf")
GENERATOR = URIRef("https://github.com/entur/nordic-netex-ontology/blob/main/scripts/generate-shapes.py")


@dataclass
class Step:
    name: str          # XML name as written in the profile path
    path: URIRef       # property IRI to constrain
    base_shape: object  # the base property shape giving the XSD bounds
    next_class: object  # class for the next step, or None for a leaf
    # Reached through a substitution group: the base shape constrains the
    # head (transportTypeRef), not this member's own path (vehicleTypeRef).
    via_head: bool = False


@dataclass
class Node:
    name: str
    path: URIRef
    min: int = 0
    max: float = UNBOUNDED
    description: str | None = None
    children: dict = field(default_factory=dict)


class Base:
    """The vendored base, indexed for lookups by XML name."""

    def __init__(self, g: Graph):
        self.g = g
        self.props = defaultdict(list)
        for shape, cls in g.subject_objects(SH.targetClass):
            if str(shape).startswith(BASE_SHAPES):
                self.props[cls].extend(g.objects(shape, SH.property))
        self.by_label = defaultdict(list)
        for prop, label in g.subject_objects(RDFS.label):
            if (prop, RDF.type, OWL.ObjectProperty) in g or (prop, RDF.type, OWL.DatatypeProperty) in g:
                self.by_label[str(label)].append(prop)
        self._ancestors = {}

    def ancestors(self, cls):
        if cls not in self._ancestors:
            out, todo = [], [cls]
            while todo:
                c = todo.pop(0)
                if c in out:
                    continue
                out.append(c)
                todo += [p for p in self.g.objects(c, RDFS.subClassOf) if isinstance(p, URIRef)]
            self._ancestors[cls] = out
        return self._ancestors[cls]

    def shapes(self, cls):
        for c in self.ancestors(cls):
            yield from self.props.get(c, ())

    def supers(self, prop):
        out, todo = set(), [prop]
        while todo:
            p = todo.pop()
            if p not in out:
                out.add(p)
                todo += list(self.g.objects(p, RDFS.subPropertyOf))
        return out - {prop}

    def step(self, cls, name: str) -> Step | None:
        for ps in self.shapes(cls):
            if str(self.g.value(ps, SH.name)) == name:
                return Step(name, self.g.value(ps, SH.path), ps, self.g.value(ps, SH["class"]))
        # A substitution group member stands where the class declares its head.
        for prop in self.by_label.get(name, ()):
            heads = self.supers(prop)
            for ps in self.shapes(cls):
                if self.g.value(ps, SH.path) in heads:
                    member = NETEX[name]
                    nxt = member if (member, RDF.type, OWL.Class) in self.g else self.g.value(ps, SH["class"])
                    return Step(name, prop, ps, nxt, via_head=True)
        return None

    def bounds(self, base_shape) -> tuple[int, float]:
        lo, hi = self.g.value(base_shape, SH.minCount), self.g.value(base_shape, SH.maxCount)
        return (int(lo) if lo is not None else 0), (int(hi) if hi is not None else UNBOUNDED)


def parse_cardinality(card: str) -> tuple[int, float]:
    lo, hi = card.split("..")
    return int(lo), UNBOUNDED if hi == "n" else int(hi)


def fmt(lo, hi) -> str:
    return f"{lo}..{'n' if hi == UNBOUNDED else int(hi)}"


def local(iri) -> str:
    return str(iri).rsplit("#", 1)[-1]


def load(paths) -> Graph:
    g = Graph()
    for p in paths:
        g.parse(Path(p).as_posix(), format="turtle")
    return g


def build(args):
    base = Base(load(sorted((ROOT / "base").glob("*.ttl"))))
    layer = load([ROOT / args.layer])
    own_classes = set(layer.subjects(RDF.type, PROFILE.ProfileClass))

    trees = defaultdict(dict)  # target class -> {path: Node}
    report = Counter()
    unresolved, looser = [], []
    for member in layer.subjects(RDF.type, PROFILE.ProfileMember):
        pclass = layer.value(member, PROFILE.memberOf)
        if pclass not in own_classes:
            continue
        cls = layer.value(pclass, PROFILE.onClass)
        path = str(layer.value(member, PROFILE.path))
        card = str(layer.value(member, PROFILE.cardinality))
        steps = path.split("/")[1:]
        if len(steps) > 1 and steps[-1] == "@ref":
            steps = steps[:-1]  # X/@ref: the XSD requires @ref on every reference

        chain, cur = [], cls
        for name in steps:
            step = base.step(cur, name) if cur is not None else None
            if step is None:
                break
            chain.append(step)
            cur = step.next_class
        if len(chain) < len(steps):
            unresolved.append((path, steps[len(chain)]))
            report["unresolved"] += 1
            continue

        p_lo, p_hi = parse_cardinality(card)
        x_lo, x_hi = base.bounds(chain[-1].base_shape)
        # An exclusion (0..0) is never looser, even where the XSD requires at
        # least one item inside an optional container.
        if p_hi != 0 and (p_lo < x_lo or p_hi > x_hi):
            looser.append((path, card, fmt(x_lo, x_hi)))
        if chain[-1].via_head:
            # The base's bounds sit on the head's path, so in SHACL nothing
            # constrains the member's own path: state the profile in full.
            x_lo, x_hi = 0, UNBOUNDED
        new_lo = p_lo if p_lo > x_lo else 0
        new_hi = p_hi if p_hi < x_hi else UNBOUNDED
        if not new_lo and new_hi == UNBOUNDED:
            report["same as XSD"] += 1
            continue
        report["generated"] += 1

        level = trees[cls]
        for i, step in enumerate(chain):
            node = level.setdefault(step.path, Node(step.name, step.path))
            if i == len(chain) - 1:
                node.min = max(node.min, new_lo)
                node.max = min(node.max, new_hi)
                node.description = f"{path} is {card} in the profile; the XSD allows {fmt(x_lo, x_hi)}."
            level = node.children
    return trees, report, unresolved, looser


def node_id(*parts) -> str:
    return "g_" + "_".join(re.sub(r"[^A-Za-z0-9]", "", p) for p in parts)


def emit_node(g: Graph, parent, node: Node, ident: str):
    ps = BNode(ident)
    g.add((parent, SH.property, ps))
    g.add((ps, SH.path, node.path))
    g.add((ps, SH.name, Literal(node.name)))
    if node.min:
        g.add((ps, SH.minCount, Literal(node.min)))
    if node.max != UNBOUNDED:
        g.add((ps, SH.maxCount, Literal(int(node.max))))
    if node.description:
        g.add((ps, SH.description, Literal(node.description)))
    if node.children:
        inner = BNode(ident + "_node")
        g.add((ps, SH.node, inner))
        g.add((inner, RDF.type, SH.NodeShape))
        for child in sorted(node.children.values(), key=lambda n: n.name):
            emit_node(g, inner, child, node_id(ident, child.name))


def render(args, trees) -> str:
    ns = Namespace(args.namespace)
    g = Graph()
    g.bind("netex", NETEX)
    g.bind(args.prefix, ns)
    g.bind("sh", SH)
    g.bind("prov", PROV)
    onto = URIRef(args.ontology)
    g.add((onto, RDF.type, OWL.Ontology))
    g.add((onto, DCTERMS.title, Literal(f"{args.layer}: shapes generated from profile:cardinality")))
    g.add((onto, RDFS.comment, Literal(
        f"Generated by scripts/generate-shapes.py from the profile:cardinality of the "
        f"members in {args.layer}, where the profile is stricter than the XSD "
        f"(docs/adr/0002). Do not hand-edit; change the membership and regenerate.")))
    g.add((onto, PROV.wasAttributedTo, GENERATOR))
    for cls in sorted(trees, key=local):
        shape = ns[f"{local(cls)}_CardinalityShape"]
        g.add((shape, RDF.type, SH.NodeShape))
        g.add((shape, SH.targetClass, cls))
        g.add((shape, RDFS.label, Literal(f"{local(cls)}: generated from profile:cardinality")))
        for node in sorted(trees[cls].values(), key=lambda n: n.name):
            emit_node(g, shape, node, node_id(local(cls), node.name))
    return g.serialize(format="turtle")


def overlaps(args, trees):
    """Hand-written shapes in the layer that count a property the generated
    shapes already count, so the two cannot drift apart."""
    layer = load([ROOT / args.layer])
    for shape in layer.subjects(RDF.type, SH.NodeShape):
        cls = layer.value(shape, SH.targetClass)
        for ps in layer.objects(shape, SH.property):
            path = layer.value(ps, SH.path)
            counted = (ps, SH.minCount, None) in layer or (ps, SH.maxCount, None) in layer
            if counted and path in trees.get(cls, {}):
                yield cls, path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--layer", default="netex-nordic.ttl")
    parser.add_argument("--namespace", default="https://netex-cen.eu/nordic#")
    parser.add_argument("--prefix", default="nordic")
    parser.add_argument("--ontology", default="https://netex-cen.eu/profile/nordic/shapes")
    parser.add_argument("--out", default="netex-nordic-shapes.ttl")
    parser.add_argument("--check", action="store_true", help="exit 1 if the output file is stale")
    args = parser.parse_args()

    trees, report, unresolved, looser = build(args)
    text = render(args, trees)
    out = ROOT / args.out

    print(f"{args.layer}: {sum(report.values())} members, "
          f"{report['generated']} generated, {report['same as XSD']} same as XSD, "
          f"{report['unresolved']} unresolved")
    for path, name in sorted(unresolved):
        print(f"  unresolved: {path} (no '{name}' in the base)")
    for path, card, xsd in sorted(looser):
        print(f"  looser than XSD, XSD applies: {path} is {card}, XSD {xsd}")

    if args.check:
        failed = False
        current = out.read_text(encoding="utf-8") if out.exists() else ""
        if current != text:
            print(f"{args.out} is stale; run scripts/generate-shapes.py", file=sys.stderr)
            failed = True
        for cls, path in overlaps(args, trees):
            print(f"hand-written shape in {args.layer} constrains the count of {local(path)} "
                  f"on {local(cls)}, which is generated; state it as a member instead", file=sys.stderr)
            failed = True
        return 1 if failed else 0
    out.write_text(text, encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
