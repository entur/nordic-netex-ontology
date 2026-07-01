# Nordic NeTEx Ontology

Maskinlesbar ontologi for NeTEx-standarden og det nordiske NeTEx-profilet (Nordic Profile). Modellerer klasser, relasjoner, rammeverk (frames) og profilbegrensninger som RDF/OWL og SHACL i Turtle-format.

## Formål

Ontologien tjener to formål:

- **For mennesker:** En presis, navigerbar referanse for hvordan NeTEx-klasser, referanser og begrensninger henger sammen.
- **For maskiner:** Et grunnlag for automatisert validering (SHACL), dokumentasjonsgenerering og verktøyintegrasjon.

## Scope og avgrensning

Dette repoet inneholder kun den **felles nordiske grunnmuren** — det som er avtalt på tvers av NO, SE, FI og DK. Det er bevisst separert fra lands- og organisasjonsspesifikke lag:

```
netex.ttl               ← NeTEx basisskjema (hva standarden definerer)
netex-nordic.ttl        ← Nordic Profile (hva Norden er enige om)
```

Alt utover dette — governance-regler, tjeneste-subprofiler, dokumentasjonsstier, codespace-konvensjoner — hører hjemme i nedstrøms repoer som importerer dette grunnlaget via `owl:imports` eller som git-submodul.

**Designprinsipp:** Ethvert lag som bygger videre kan stramme inn (via SHACL), men dette repoet forblir stabilt og gjenbrukbart uavhengig av hvem som konsumerer det.

## Filer

| Fil | Innhold |
|-----|---------|
| `netex.ttl` | OWL-klasser og egenskaper for NeTEx XML-skjemaet: rammeklasser, referansemetadata, XSD-kardinalitet, elementrekkefølge, SIRI-koblinger og Transmodel-alignering. |
| `netex-nordic.ttl` | SHACL-shapes som uttrykker hva Nordic Profile tillater, krever og ekskluderer utover XSD. |

## Utvidelsesmodell

Nedstrøms lag kan importere og bygge videre uten å endre dette repoet:

```
netex.ttl                          ← Grunnvokabular (dette repoet)
└─ netex-nordic.ttl                ← Nordiske begrensninger (dette repoet)
   └─ <ditt-lag>.ttl               ← Organisasjon, tjeneste, land, …
      └─ …
```

Hvert lag kan:
- **Stramme inn** — Legge til strengere SHACL-shapes (`sh:minCount`, `sh:maxCount 0`)
- **Utvide** — Definere nye klasser, referanser eller domeneegenskaper
- **Koble** — Referere til URI-er herfra i egne shapes og regler

## SHACL-validering

SHACL-shapes i `netex-nordic.ttl` uttrykker profilbegrensninger som valideringsverktøy kan kjøre direkte:

| Constraint | SHACL-uttrykk | Eksempel |
|------------|---------------|----------|
| Ekskludert | `sh:maxCount 0` | ParentSiteRef brukes ikke i NP |
| Tillatt | `sh:maxCount 1` | TopographicPlaceRef valgfritt |
| Påkrevd | `sh:minCount 1; sh:maxCount 1` | RouteRef obligatorisk (XSD sier valgfritt) |
| Typesjekk | `sh:class` | RouteRef må peke på en Route |

Shape-navngivning: `profile:NP_{ClassName}Shape`.

## Innebygde koblinger

| Kobling | Mekanisme |
|---------|-----------|
| SIRI sanntid | `netex:referencedBySIRI` — hvilke klasser refereres av ET, SX, VM, FM |
| Transmodel | `skos:exactMatch` / `skos:closeMatch` — alignering mot Transmodel-konsepter |

## Teknologi

| Vokabular | Rolle |
|-----------|-------|
| RDF/OWL | Klasser og egenskaper |
| SHACL | Profilbegrensninger som validerbare shapes |
| SKOS | Definisjoner, notasjon og kryssvokabular-mapping |
| Turtle (.ttl) | Serialiseringsformat |

## Prefikser

| Prefiks | Navnerom |
|---------|----------|
| `netex:` | `https://netex-cen.eu/ontology#` |
| `profile:` | `https://netex-cen.eu/profile#` |
| `sh:` | `http://www.w3.org/ns/shacl#` |
| `siri:` | `https://siri-cen.eu/ontology#` |
| `tm-commons:` | `https://w3id.org/transmodel/commons#` |

## Verktøy

Ontologien kan konsumeres av ethvert standard RDF/SHACL-verktøy, f.eks.:

- **pySHACL** — Validering av NeTEx-data mot profil-shapes
- **Apache Jena** — SPARQL-spørringer
- **TopBraid / Protégé** — Visuell utforskning og redigering
- **Egne skript/agenter** — Importer `.ttl`-filene via `owl:imports` eller last direkte

## Videre lesning

- [Ontology Guide](https://github.com/entur/nordic-netex-documentation/blob/main/guides/Ontology/Ontology_Guide.md) — Fullstendig guide til ontologiens oppbygning
- [W3C RDF Primer](https://www.w3.org/TR/rdf11-primer/) — Introduksjon til RDF og Turtle-syntaks
- [W3C SHACL Specification](https://www.w3.org/TR/shacl/) — Shapes Constraint Language
- [Transmodel](https://www.transmodel-cen.eu/) — Den konseptuelle modellen bak NeTEx
