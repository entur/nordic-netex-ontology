# Nordic NeTEx Ontology

Machine-readable ontology for the NeTEx standard and the Nordic NeTEx Profile. Models classes, relationships, frames, and profile constraints as RDF/OWL and SHACL in Turtle format.

## Purpose

The ontology serves two purposes:

- **For humans:** A precise, navigable reference for how NeTEx classes, references, and constraints relate to each other.
- **For machines:** A foundation for automated validation (SHACL), documentation generation, and tooling integration.

## Scope

This repository contains only the **shared Nordic foundation** — what has been agreed upon across NO, SE, FI, and DK. It is deliberately separated from country- and organisation-specific layers:

```
netex.ttl               ← NeTEx base schema (what the standard defines)
netex-nordic.ttl        ← Nordic Profile (what the Nordics agree on)
```

Everything beyond this — governance rules, service sub-profiles, documentation paths, codespace conventions — belongs in downstream repositories that import this foundation via `owl:imports` or as a git submodule.

**Design principle:** Any layer built on top can tighten constraints (via SHACL), but this repository remains stable and reusable regardless of who consumes it.

## Files

| File | Contents |
|------|----------|
| `netex.ttl` | OWL classes and properties for the NeTEx XML schema: frame classes, reference metadata, XSD cardinality, element ordering, SIRI bridges, and Transmodel alignment. |
| `netex-nordic.ttl` | SHACL shapes expressing what the Nordic Profile allows, requires, and excludes beyond XSD. |

## Extension model

Downstream layers can import and build on top without modifying this repository:

```
netex.ttl                          ← Base vocabulary (this repo)
└─ netex-nordic.ttl                ← Nordic constraints (this repo)
   └─ <your-layer>.ttl             ← Organisation, service, country, …
      └─ …
```

Each layer can:
- **Tighten** — Add stricter SHACL shapes (`sh:minCount`, `sh:maxCount 0`)
- **Extend** — Define new classes, references, or domain properties
- **Link** — Reference URIs from this repo in your own shapes and rules

## SHACL validation

SHACL shapes in `netex-nordic.ttl` express profile constraints that validation tools can execute directly:

| Constraint | SHACL expression | Example |
|------------|------------------|---------|
| Excluded | `sh:maxCount 0` | ParentSiteRef not used in NP |
| Allowed | `sh:maxCount 1` | TopographicPlaceRef optional |
| Required | `sh:minCount 1; sh:maxCount 1` | RouteRef mandatory (XSD says optional) |
| Type check | `sh:class` | RouteRef must point to a Route |

Shape naming: `profile:NP_{ClassName}Shape`.

## Built-in links

| Link | Mechanism |
|------|-----------|
| SIRI real-time | `netex:referencedBySIRI` — which classes are referenced by ET, SX, VM, FM |
| Transmodel | `skos:exactMatch` / `skos:closeMatch` — alignment with Transmodel concepts |

## Technology

| Vocabulary | Role |
|------------|------|
| RDF/OWL | Classes and properties |
| SHACL | Profile constraints as validatable shapes |
| SKOS | Definitions, notation, and cross-vocabulary mapping |
| Turtle (.ttl) | Serialisation format |

## Prefixes

| Prefix | Namespace |
|--------|-----------|
| `netex:` | `https://netex-cen.eu/ontology#` |
| `profile:` | `https://netex-cen.eu/profile#` |
| `sh:` | `http://www.w3.org/ns/shacl#` |
| `siri:` | `https://siri-cen.eu/ontology#` |
| `tm-commons:` | `https://w3id.org/transmodel/commons#` |

## Tools

The ontology can be consumed by any standard RDF/SHACL tooling, e.g.:

- **pySHACL** — Validate NeTEx data against profile shapes
- **Apache Jena** — SPARQL queries
- **TopBraid / Protégé** — Visual exploration and editing
- **Custom scripts/agents** — Import the `.ttl` files via `owl:imports` or load directly

## Further reading

- [Ontology Guide](https://github.com/entur/nordic-netex-documentation/blob/main/guides/Ontology/Ontology_Guide.md) — Full guide to the ontology structure
- [W3C RDF Primer](https://www.w3.org/TR/rdf11-primer/) — Introduction to RDF and Turtle syntax
- [W3C SHACL Specification](https://www.w3.org/TR/shacl/) — Shapes Constraint Language
- [Transmodel](https://www.transmodel-cen.eu/) — The conceptual model behind NeTEx
