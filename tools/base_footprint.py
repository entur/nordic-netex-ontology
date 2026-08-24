"""Which base modules does the Nordic layer actually touch?

Maps every netex: term the overlays reference (sh:path, sh:class,
sh:targetClass) to the base/*.ttl file that defines it, so we can see the real
footprint — i.e. how much of the generator output NP depends on.
"""
import glob
import os
from collections import defaultdict
from rdflib import Graph, RDF, URIRef
from rdflib.namespace import Namespace

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NETEX = Namespace("https://netex-cen.eu/ontology#")
SH = Namespace("http://www.w3.org/ns/shacl#")

overlay_files = sorted(
    os.path.basename(p) for p in glob.glob(os.path.join(HERE, "netex-*.ttl"))
)

# term -> defining file
term_file = {}
for f in sorted(glob.glob(os.path.join(HERE, "base", "*.ttl"))):
    g = Graph(); g.parse(f, format="turtle")
    for s in g.subjects(RDF.type, None):
        if isinstance(s, URIRef) and str(s).startswith(str(NETEX)):
            term_file.setdefault(s, os.path.basename(f))

overlays = Graph()
for f in overlay_files:
    overlays.parse(os.path.join(HERE, f), format="turtle")

referenced = set()
for pred in (SH.targetClass, SH["class"], SH.path):
    referenced |= {o for o in overlays.objects(None, pred)
                   if isinstance(o, URIRef) and str(o).startswith(str(NETEX))}

per_file = defaultdict(int)
for t in referenced:
    per_file[term_file.get(t, "<UNRESOLVED>")] += 1

total_terms_per_file = defaultdict(int)
for t, fn in term_file.items():
    total_terms_per_file[fn] += 1

print(f"NP references {len(referenced)} distinct netex: terms.\n")
print(f"{'module':<24}{'used by NP':>12}{'in module':>12}")
for fn in sorted(total_terms_per_file):
    print(f"{fn:<24}{per_file.get(fn, 0):>12}{total_terms_per_file[fn]:>12}")
touched = [fn for fn in total_terms_per_file if per_file.get(fn, 0) > 0]
print(f"\nModules touched: {len(touched)} of {len(total_terms_per_file)} -> {sorted(touched)}")
