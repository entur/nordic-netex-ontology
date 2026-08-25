# Nordic NeTEx Ontology

The **Nordic NeTEx Profile** as a machine-readable overlay on top of the
generated NeTEx base ontology. This repository holds the profile layer only —
SHACL constraints, element ordering, Nordic vocabulary, and cross-standard
alignment — layered on a vendored snapshot of the CEN-owned base (`base/`)
rather than re-deriving it.

## Purpose

- **For humans:** A precise, navigable reference for what the Nordic Profile
  allows, requires, and excludes beyond the NeTEx standard.
- **For machines:** A SHACL-validatable definition of the Nordic Profile that
  standard tooling can execute against real NeTEx data.

## Architecture

The NeTEx base vocabulary is **generated** — projected deterministically from
the official NeTEx XSD by the [netex-ontology-generator](#base-ontology-generated)
(intended to be CEN-owned). This repository builds the Nordic layer on top:

```
base/ (netex.ttl + modules + netex-shacl.ttl)  ← generated NeTEx base — vendored snapshot
└─ netex-nordic.ttl                ← Nordic Profile: SHACL constraints, ordering
   ├─ netex-nordic-vocab.ttl       ← Nordic vocabulary (nordic:)
   ├─ netex-nordic-model.ttl       ← curated frame containment & specialisation
   ├─ netex-transmodel-alignment.ttl ← NeTEx ⇄ Transmodel (skos)
   └─ netex-siri-bridge.ttl        ← NeTEx ⇄ SIRI real-time bridges
      └─ <your-layer>.ttl          ← Organisation, service, country, …
```

**Design principle:** The generated base stays a faithful, mechanical projection
of the standard. The Nordic layer only *tightens* (SHACL), *annotates*, and
*aligns* — it never renames or forks the base.

## Base ontology (generated)

The base is produced by `netex-ontology-generator`, which projects the NeTEx XSD
into RDF/OWL and splits it into per-module documents (`netex.ttl` root plus
`netex-core`, `netex-framework`, `netex-part1`…`part5`, `netex-service`,
`netex-siri`, `netex-gml`). Terms keep their NeTEx identity in the single
`netex:` namespace; only the documents are split.

A snapshot of this output is **vendored under `base/`** — the ten OWL modules
plus the generator's SHACL baseline (`netex-shacl.ttl`) — so the profile can be
validated with standard tooling without fetching anything external.

**Naming philosophy:** term names follow the NeTEx XSD (and the standard RDF
convention): **PascalCase classes** (`netex:StopPlace`) and **lowerCamelCase
properties** (`netex:parentSiteRef`). Transmodel governs *alignment*, not
naming — the mapping lives in `netex-transmodel-alignment.ttl` via
`skos:exactMatch` / `skos:closeMatch`, so NeTEx keeps its own identity.

> **Vendored base (living branch):** `base/` is a checked-in snapshot of the
> generated base, so the repository is self-contained and validatable today.
> **TODO:** once the generator is hosted (Entur/CEN), replace the manual
> snapshot with an automated ingest that refreshes `base/` from the published
> output.

## Files

| File | Contents |
|------|----------|
| `base/` | Vendored snapshot of the generated NeTEx base — ten OWL modules plus the `netex-shacl.ttl` SHACL baseline. Projected from the NeTEx XSD; not hand-edited. |
| `netex-nordic.ttl` | SHACL shapes for the Nordic Profile (allow / require / exclude), plus profile element ordering and navigational domain chains. |
| `netex-nordic-vocab.ttl` | Nordic-invented vocabulary in the `nordic:` namespace (profile meta-classes, data-confidence, ordering, domain chains, SIRI bridge property, structural predicates). |
| `netex-nordic-model.ttl` | Curated structural overlay: frame containment and functional specialisation semantics on the generated classes. |
| `netex-transmodel-alignment.ttl` | `skos:exactMatch` / `skos:closeMatch` alignment from generated NeTEx classes to Transmodel concepts. |
| `netex-siri-bridge.ttl` | Which generated NeTEx classes are referenced by SIRI services (ET, SX, VM, FM). |

## Extension model

Downstream layers import and build on top without modifying this repository:

Each layer can:
- **Tighten** — Add stricter SHACL shapes (`sh:minCount`, `sh:maxCount 0`)
- **Extend** — Define new classes or properties in its own namespace
- **Link** — Reference generated `netex:` URIs and `nordic:` terms in its own rules

## SHACL validation

SHACL shapes in `netex-nordic.ttl` target generated `netex:` classes and
constrain their generated (lowerCamelCase) properties directly:

| Constraint | SHACL expression | Example |
|------------|------------------|---------|
| Excluded | `sh:maxCount 0` | `netex:parentSiteRef` not used in NP |
| Allowed | `sh:maxCount 1` | `netex:topographicPlaceRef` optional |
| Required | `sh:minCount 1; sh:maxCount 1` | `netex:routeRef` mandatory (XSD says optional) |
| Type check | `sh:class` | `netex:routeRef` must point to a `netex:Route` |

Shape naming: `profile:NP_{ClassName}Shape`.

## Cross-standard links

| Link | Mechanism | File |
|------|-----------|------|
| SIRI real-time | `nordic:referencedBySIRI` — which classes ET, SX, VM, FM reference | `netex-siri-bridge.ttl` |
| Transmodel | `skos:exactMatch` / `skos:closeMatch` — conceptual alignment | `netex-transmodel-alignment.ttl` |

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
| `nordic:` | `https://netex-cen.eu/nordic#` |
| `profile:` | `https://netex-cen.eu/profile#` |
| `sh:` | `http://www.w3.org/ns/shacl#` |
| `siri:` | `https://siri-cen.eu/ontology#` |
| `tm-commons:` | `https://w3id.org/transmodel/commons#` |
| `tm-fac:` | `https://w3id.org/transmodel/facilities#` |
| `tm-journeys:` | `https://w3id.org/transmodel/journeys#` |
| `tm-org:` | `https://w3id.org/transmodel/organisations#` |

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
