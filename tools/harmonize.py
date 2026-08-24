"""Harmonize the Nordic overlays with the latest generated base.

Beyond "does the term exist" (see ground_against_base.py), this checks semantic
alignment of every SHACL property shape against the base:

  1. APPLICABILITY — is sh:path a property that the sh:targetClass actually
     carries? A class carries property P iff some owl:Restriction with
     owl:onProperty P sits on the class or any of its rdfs:subClassOf ancestors.
     A shape constraining a property the class does not have is dead weight.

  2. RANGE — if the shape asserts sh:class C, does it agree with the base's
     rdfs:range for that property? A stricter NP range is fine (subclass); a
     range that contradicts the base signals drift.

Nothing is mutated — this reports exactly what to reconcile in the Nordic files.
"""
import glob
import os
from rdflib import Graph, RDF, RDFS, OWL, URIRef, BNode
from rdflib.namespace import Namespace

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NETEX = Namespace("https://netex-cen.eu/ontology#")
SH = Namespace("http://www.w3.org/ns/shacl#")

overlay_files = sorted(
    os.path.basename(p) for p in glob.glob(os.path.join(HERE, "netex-*.ttl"))
)

base = Graph()
for f in sorted(glob.glob(os.path.join(HERE, "base", "*.ttl"))):
    base.parse(f, format="turtle")

overlays = Graph()
for f in overlay_files:
    overlays.parse(os.path.join(HERE, f), format="turtle")


def short(u):
    return str(u).replace(str(NETEX), "netex:") if isinstance(u, URIRef) else str(u)


def named_ancestors(cls):
    """Transitive closure of rdfs:subClassOf over NAMED classes, incl. cls."""
    seen, stack = set(), [cls]
    while stack:
        c = stack.pop()
        if c in seen:
            continue
        seen.add(c)
        for sup in base.objects(c, RDFS.subClassOf):
            if isinstance(sup, URIRef):
                stack.append(sup)
    return seen


def applicable_properties(cls):
    """Properties the class carries: owl:onProperty of restrictions on the
    class or any named ancestor (restriction supers are blank nodes)."""
    props = set()
    for anc in named_ancestors(cls):
        for sup in base.objects(anc, RDFS.subClassOf):
            if isinstance(sup, BNode) and (sup, RDF.type, OWL.Restriction) in base:
                for p in base.objects(sup, OWL.onProperty):
                    props.add(p)
    return props


# base rdfs:range per property (first named range)
base_range = {}
for p in set(base.subjects(RDF.type, OWL.ObjectProperty)) | set(base.subjects(RDF.type, OWL.DatatypeProperty)):
    for r in base.objects(p, RDFS.range):
        if isinstance(r, URIRef):
            base_range[p] = r
            break


def subclass_of(sub, sup):
    return sup in named_ancestors(sub)


not_applicable = []   # (shape, targetClass, path)
range_mismatch = []   # (shape, path, sh_class, base_range)
no_target = []        # shapes without a resolvable netex: targetClass
checked = 0

for shape in overlays.subjects(RDF.type, SH.NodeShape):
    targets = [t for t in overlays.objects(shape, SH.targetClass)
               if isinstance(t, URIRef) and str(t).startswith(str(NETEX))]
    if not targets:
        continue
    tcls = targets[0]
    if (tcls, RDF.type, OWL.Class) not in base:
        no_target.append((shape, tcls))
        continue
    carried = applicable_properties(tcls)
    for pshape in overlays.objects(shape, SH.property):
        paths = [p for p in overlays.objects(pshape, SH.path)
                 if isinstance(p, URIRef) and str(p).startswith(str(NETEX))]
        if not paths:
            continue
        path = paths[0]
        checked += 1
        if path not in carried:
            not_applicable.append((shape, tcls, path))
        for sc in overlays.objects(pshape, SH["class"]):
            if isinstance(sc, URIRef) and path in base_range:
                br = base_range[path]
                if sc != br and not subclass_of(sc, br) and not subclass_of(br, sc):
                    range_mismatch.append((shape, path, sc, br))

print(f"Checked {checked} property shapes across {len(overlay_files)} overlays "
      f"against base ({len(base)} triples).\n")

print(f"[1] NON-APPLICABLE sh:path — property not carried by target class ({len(not_applicable)}):")
for shape, tcls, path in not_applicable:
    print(f"    {short(shape)}  target {short(tcls)}  ->  {short(path)}")
if not not_applicable:
    print("    (none — every sh:path is carried by its target class)")

print(f"\n[2] RANGE MISMATCH — sh:class disagrees with base rdfs:range ({len(range_mismatch)}):")
for shape, path, sc, br in range_mismatch:
    print(f"    {short(shape)}  {short(path)}  sh:class {short(sc)}  vs base range {short(br)}")
if not range_mismatch:
    print("    (none — every sh:class is consistent with the base range)")

print(f"\n[3] SHAPES with unresolved target class ({len(no_target)}):")
for shape, tcls in no_target:
    print(f"    {short(shape)}  ->  {short(tcls)}")
if not no_target:
    print("    (none)")
