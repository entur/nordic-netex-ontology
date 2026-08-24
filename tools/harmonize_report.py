"""How do ALL Nordic overlays harmonize with the (regenerated) base?

For every overlay file, collect each netex: IRI used in subject OR object
position and check it resolves to a term defined in base/*.ttl. Covers the
non-SHACL files (transmodel-alignment skos maps, siri-bridge nordic:referencedBySIRI,
nordic-model nordic:contains chains) that the cardinality tool does not see.
"""
import glob
import os
from rdflib import Graph, RDF, URIRef
from rdflib.namespace import Namespace

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NETEX = Namespace("https://netex-cen.eu/ontology#")

overlay_files = sorted(
    os.path.basename(p) for p in glob.glob(os.path.join(HERE, "netex-*.ttl"))
)

base = Graph()
for f in sorted(glob.glob(os.path.join(HERE, "base", "*.ttl"))):
    base.parse(f, format="turtle")
defined = {s for s in base.subjects(RDF.type, None) if isinstance(s, URIRef)}


def is_netex(n):
    return isinstance(n, URIRef) and str(n).startswith(str(NETEX))


print(f"BASE defines {len(defined)} netex: terms\n")
grand_missing = 0
for f in overlay_files:
    g = Graph(); g.parse(os.path.join(HERE, f), format="turtle")
    subj = {s for s in g.subjects() if is_netex(s)}
    obj = {o for s, p, o in g if is_netex(o)}
    refs = subj | obj
    missing = sorted(r for r in refs if r not in defined)
    grand_missing += len(missing)
    status = "OK" if not missing else f"{len(missing)} MISSING"
    print(f"{f:<34} refs={len(refs):>3} (subj={len(subj)}, obj={len(obj)})  -> {status}")
    for m in missing:
        print("     - MISSING:", str(m).replace(str(NETEX), "netex:"))

print(f"\nTOTAL unresolved netex: references across all overlays: {grand_missing}")
