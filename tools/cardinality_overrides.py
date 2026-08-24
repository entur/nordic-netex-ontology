"""Where does the Nordic profile OVERRIDE the standard's cardinality?

The base projects XSD occurs as owl:Restriction blocks on the *_VersionStructure
superclasses (owl:cardinality / owl:minCardinality / owl:maxCardinality +
owl:onProperty). The profile asserts sh:minCount / sh:maxCount on the same
(class, property) pairs. This compares the two and classifies each shape:

  REQUIRE      profile makes mandatory what the standard leaves optional
  EXCLUDE      profile forbids (sh:maxCount 0) what the standard allows
  RESTRICT-MAX profile caps multiplicity the standard leaves open (>1/unbounded)
  MATCH        profile restates the standard's cardinality (no override)
  CONFLICT     profile LOOSENS beyond the standard (invalid for a profile)
  BASE-SILENT  no cardinality restriction on the class chain for that property
"""
import glob
import os
from rdflib import Graph, RDF, RDFS, OWL, URIRef, BNode
from rdflib.namespace import Namespace

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NETEX = Namespace("https://netex-cen.eu/ontology#")
SH = Namespace("http://www.w3.org/ns/shacl#")
INF = float("inf")

overlay_files = sorted(
    os.path.basename(p) for p in glob.glob(os.path.join(HERE, "netex-*.ttl"))
)

base = Graph()
for f in sorted(glob.glob(os.path.join(HERE, "base", "*.ttl"))):
    base.parse(f, format="turtle")

overlays = Graph()
for f in overlay_files:
    overlays.parse(os.path.join(HERE, f), format="turtle")


def superclasses(cls):
    """cls plus all rdfs:subClassOf ancestors that are named classes."""
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


def base_cardinality(cls, prop):
    """(min, max) the base declares for prop on cls's chain; None if silent."""
    lo, hi, found = 0, INF, False
    for c in superclasses(cls):
        for r in base.objects(c, RDFS.subClassOf):
            if not isinstance(r, BNode):
                continue
            if (r, OWL.onProperty, prop) not in base:
                continue
            found = True
            for exact in base.objects(r, OWL.cardinality):
                lo = max(lo, int(exact)); hi = min(hi, int(exact))
            for mn in base.objects(r, OWL.minCardinality):
                lo = max(lo, int(mn))
            for mx in base.objects(r, OWL.maxCardinality):
                hi = min(hi, int(mx))
    return (lo, hi) if found else None


def classify(bmin, bmax, pmin, pmax):
    if pmin < bmin or pmax > bmax:
        return "CONFLICT"
    if pmax == 0 and bmax != 0:
        return "EXCLUDE"
    if pmin >= 1 and bmin == 0:
        return "REQUIRE"
    if pmax == 1 and bmax > 1:
        return "RESTRICT-MAX"
    if (pmin, pmax) == (bmin, bmax):
        return "MATCH"
    return "TIGHTEN"


def fmt(lo, hi):
    return f"{lo}..{'*' if hi == INF else hi}"


rows = []
for shape in overlays.subjects(RDF.type, SH.NodeShape):
    tclass = overlays.value(shape, SH.targetClass)
    if not isinstance(tclass, URIRef):
        continue
    for pshape in overlays.objects(shape, SH.property):
        prop = overlays.value(pshape, SH.path)
        if not isinstance(prop, URIRef):
            continue
        pmin = overlays.value(pshape, SH.minCount)
        pmax = overlays.value(pshape, SH.maxCount)
        pmin = int(pmin) if pmin is not None else 0
        pmax = int(pmax) if pmax is not None else INF
        bc = base_cardinality(tclass, prop)
        if bc is None:
            verdict, bstr = "BASE-SILENT", "(none)"
        else:
            verdict = classify(bc[0], bc[1], pmin, pmax)
            bstr = fmt(*bc)
        rows.append((verdict, str(tclass).replace(str(NETEX), ""),
                     str(prop).replace(str(NETEX), ""), bstr, fmt(pmin, pmax)))

order = ["CONFLICT", "REQUIRE", "EXCLUDE", "RESTRICT-MAX", "TIGHTEN", "BASE-SILENT", "MATCH"]
rows.sort(key=lambda r: (order.index(r[0]), r[1], r[2]))

from collections import Counter
counts = Counter(r[0] for r in rows)
print("SUMMARY:", ", ".join(f"{k}={counts[k]}" for k in order if counts[k]))
print(f"{'verdict':<13}{'class':<28}{'property':<34}{'base':>8}  {'profile'}")
for v, c, p, b, pr in rows:
    print(f"{v:<13}{c:<28}{p:<34}{b:>8}  {pr}")
