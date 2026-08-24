"""Ground the Nordic overlays against the local generated NeTEx base.

Loads base/*.ttl + the Nordic overlay files into one graph, then reports every
netex: term the overlays reference (sh:path, sh:class, sh:targetClass, rdf:type,
domain/range chains) that the base does NOT define. That list is exactly what
must change in the Nordic files (typos, moved/renamed classes, absent terms).
"""
import glob
import os
from rdflib import Graph, RDF, RDFS, OWL, URIRef
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

# Terms the base actually defines (has any rdf:type statement as subject).
defined = {s for s in base.subjects(RDF.type, None) if isinstance(s, URIRef)}
base_classes = {s for s in base.subjects(RDF.type, OWL.Class) if isinstance(s, URIRef)}
base_classes |= {s for s in base.subjects(RDF.type, RDFS.Class) if isinstance(s, URIRef)}
base_props = set()
for t in (OWL.ObjectProperty, OWL.DatatypeProperty, RDF.Property, OWL.AnnotationProperty):
    base_props |= {s for s in base.subjects(RDF.type, t) if isinstance(s, URIRef)}

overlays = Graph()
for f in overlay_files:
    p = os.path.join(HERE, f)
    if os.path.exists(p):
        overlays.parse(p, format="turtle")


def netex_terms(nodes):
    return {n for n in nodes if isinstance(n, URIRef) and str(n).startswith(str(NETEX))}


# Classes the overlays point at (SHACL targets + type checks).
referenced_classes = netex_terms(
    set(overlays.objects(None, SH.targetClass))
    | set(overlays.objects(None, SH["class"]))
)
# Properties the overlays constrain (sh:path) or declare domain/range on.
referenced_props = netex_terms(set(overlays.objects(None, SH.path)))

missing_classes = sorted(referenced_classes - defined, key=str)
missing_props = sorted(referenced_props - defined, key=str)

# Also: netex: subjects the overlays add statements about that base doesn't define.
overlay_subjects = netex_terms(set(overlays.subjects(None, None)))
extended_subjects = sorted(overlay_subjects - defined, key=str)


def short(u):
    return str(u).replace(str(NETEX), "netex:")


print(f"BASE: {len(base)} triples, {len(base_classes)} classes, {len(base_props)} properties")
print(f"OVERLAYS: {len(overlays)} triples across {len(overlay_files)} files")
print(f"  referenced netex: classes = {len(referenced_classes)}")
print(f"  referenced netex: properties (sh:path) = {len(referenced_props)}")
print()
print(f"MISSING CLASSES ({len(missing_classes)}) — sh:targetClass/sh:class not in base:")
for u in missing_classes:
    print("  -", short(u))
print()
print(f"MISSING PROPERTIES ({len(missing_props)}) — sh:path not in base:")
for u in missing_props:
    print("  -", short(u))
print()
print(f"OVERLAY netex: SUBJECTS not defined in base ({len(extended_subjects)}):")
for u in extended_subjects:
    print("  -", short(u))
