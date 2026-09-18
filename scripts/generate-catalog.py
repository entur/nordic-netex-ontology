#!/usr/bin/env python3
"""Generate catalog.ttl - a DCAT manifest of every RDF document in this repo.

Lets a human or LLM discover which graphs exist, their intent, provenance and
triple count from one file, without guessing from filenames. Self-maintaining:
title/description are harvested from each file's own owl:Ontology header
(dcterms:title/rdfs:label, rdfs:comment/dcterms:description).

Usage: python scripts/generate-catalog.py   (writes catalog.ttl in repo root)
"""
import subprocess
from datetime import date, datetime
from pathlib import Path

from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS, DCTERMS

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "catalog.ttl"

CATALOG_IRI = "https://netex-cen.eu/catalog"
CATALOG_TITLE = "Nordic NeTEx Ontology — catalog"
CATALOG_DESC = ("Manifest of every RDF document this repository composes: the "
                "vendored generated NeTEx base and the Nordic profile layer on "
                "top of it.")

# Root-level Nordic layer files, in reading order. keyword/provenance here
# take priority over the generic base/*.ttl handling below.
ROOT_FILES = [
    ("netex-nordic-vocab.ttl", "vocab", "maintained here"),
    ("netex-nordic-model.ttl", "model", "maintained here"),
    ("netex-nordic.ttl", "profile", "maintained here"),
    ("netex-nordic-baseline.ttl", "baseline",
     "seeded once from nordic-netex-documentation Table_*.md; now inherits from CCB decisions"),
    ("netex-siri-bridge.ttl", "bridge", "maintained here"),
    ("netex-transmodel-alignment.ttl", "mapping", "maintained here"),
]


def git_date(relpath: str) -> str:
    """Last commit date for the file (ISO). Falls back to filesystem mtime."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", relpath],
            cwd=ROOT, capture_output=True, text=True, timeout=15,
        ).stdout.strip()
        if out:
            return out
    except Exception:
        pass
    ts = (ROOT / relpath).stat().st_mtime
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def ontology_subject(g: Graph):
    for s in g.subjects(RDF.type, OWL.Ontology):
        if isinstance(s, URIRef):
            return s
    return None


def title_and_desc(path: Path, g: Graph, subject):
    title = desc = None
    if subject is not None:
        title = g.value(subject, DCTERMS.title) or g.value(subject, RDFS.label)
        desc = g.value(subject, RDFS.comment) or g.value(subject, DCTERMS.description)
    return str(title) if title else path.stem, str(desc) if desc else ""


def esc(s: str) -> str:
    """Collapse whitespace and escape for a single-line Turtle string."""
    s = " ".join(s.split())
    return s.replace("\\", "\\\\").replace('"', '\\"')


def build_entry(path: Path):
    rel = path.relative_to(ROOT).as_posix()
    g = Graph()
    g.parse(path.as_posix(), format="turtle")
    subject = ontology_subject(g)
    title, desc = title_and_desc(path, g, subject)
    if rel.startswith("base/"):
        keyword = "base"
        provenance = "vendored snapshot, generated from NeTEx_publication.xsd; not hand-edited"
    else:
        override = next((o for f, o, _ in ROOT_FILES if f == path.name), None)
        keyword = override or "root"
        provenance = next((p for f, _, p in ROOT_FILES if f == path.name), "maintained here")
    return {
        "iri": f"<{subject}>" if subject is not None else f"<https://netex-cen.eu/catalog/{path.stem}>",
        "title": title,
        "desc": desc,
        "keyword": keyword,
        "provenance": provenance,
        "triples": len(g),
        "modified": git_date(rel),
        "href": rel,
    }


def collect():
    entries = [build_entry(p) for p in sorted((ROOT / "base").glob("*.ttl"))]
    ordered_root = [f for f, _, _ in ROOT_FILES if (ROOT / f).is_file()]
    extra_root = sorted(
        p.name for p in ROOT.glob("*.ttl")
        if p.name not in ordered_root and p.name != "catalog.ttl"
    )
    for name in ordered_root + extra_root:
        entries.append(build_entry(ROOT / name))
    return entries


def render(entries) -> str:
    today = date.today().isoformat()
    L = [
        "@prefix dcat:    <http://www.w3.org/ns/dcat#> .",
        "@prefix dcterms: <http://purl.org/dc/terms/> .",
        "@prefix void:    <http://rdfs.org/ns/void#> .",
        "@prefix xsd:     <http://www.w3.org/2001/XMLSchema#> .",
        "",
        "# =============================================================================",
        "# GENERATED FILE - do not hand-edit.",
        "# Run: python scripts/generate-catalog.py",
        "#",
        "# DCAT manifest of every RDF document this repository is composed of.",
        "# Title/description are harvested from each file's own owl:Ontology header.",
        "#",
        "# Predicates:",
        "#   dcat:keyword       -> layer (base/vocab/model/profile/baseline/bridge/mapping)",
        "#   dcterms:provenance -> where the file's content originates",
        "#   void:triples       -> triple count at generation time",
        "# =============================================================================",
        "",
        f"<{CATALOG_IRI}> a dcat:Catalog ;",
        f'    dcterms:title "{esc(CATALOG_TITLE)}" ;',
        f'    dcterms:description "{esc(CATALOG_DESC)}" ;',
        f'    dcterms:modified "{today}"^^xsd:date ;',
        "    dcat:dataset",
        "        " + " ,\n        ".join(e["iri"] for e in entries) + " .",
        "",
    ]
    for e in entries:
        L.append(f'{e["iri"]} a dcat:Dataset ;')
        L.append(f'    dcterms:title "{esc(e["title"])}" ;')
        if e["desc"]:
            L.append(f'    dcterms:description "{esc(e["desc"])}" ;')
        L.append(f'    dcat:keyword "{esc(e["keyword"])}" ;')
        L.append(f'    dcterms:provenance "{esc(e["provenance"])}" ;')
        L.append(f'    void:triples {e["triples"]} ;')
        L.append(f'    dcterms:modified "{e["modified"]}"^^xsd:date ;')
        L.append("    dcat:distribution [ a dcat:Distribution ;")
        L.append(f'        dcat:downloadURL <{e["href"]}> ;')
        L.append('        dcterms:format "text/turtle" ] .')
        L.append("")
    return "\n".join(L) + "\n"


def main():
    entries = collect()
    OUT.write_text(render(entries), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} with {len(entries)} datasets.")


if __name__ == "__main__":
    main()
