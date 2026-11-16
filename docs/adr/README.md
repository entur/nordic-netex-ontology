# Architecture decision records (ADR)

This folder holds the *system* decisions of the Nordic NeTEx Ontology: how the profile is represented in RDF, what is generated and from what, and what tooling may rely on. *Specification* decisions, the rules the Nordic Profile sets for NeTEx data, are made by the [Nordic Profile Change and Control Board](https://github.com/hfjelstad/nordic-profile-change-and-control) and recorded here only as `nordic:decision` provenance. [ADR 0001](0001-record-architecture-decisions.adoc) explains the split.

The layout follows [Kompass](https://github.com/entur/kompass/tree/main/docs/adr), [Gangleri](https://github.com/entur/gangleri/tree/main/docs/adr) and the CCB repository, so decisions across the repositories can be read and linked the same way.

## Index

| ADR | Status | Read it when |
|---|---|---|
| [0001-record-architecture-decisions.adoc](0001-record-architecture-decisions.adoc) | proposed | you are writing, amending or superseding an ADR, or are unsure whether something belongs here or in the CCB |
| [0002-generate-shacl-from-profile-cardinality.adoc](0002-generate-shacl-from-profile-cardinality.adoc) | proposed | you are changing a `profile:cardinality`, writing a SHACL shape by hand, or consuming the profile's shapes in a validator or rule tool |
| [0003-value-lists-and-severity-on-profile-members.adoc](0003-value-lists-and-severity-on-profile-members.adoc) | proposed | a profile allows fewer values than the XSD, or a requirement should be reported as a warning or information rather than an error |

## Is it an ADR?

Could the decision make a dataset valid or invalid, or change what a consumer may rely on in the data? Then it is a specification decision for the CCB. Otherwise, if it changes how the profile is modelled, generated, published or consumed, it is an ADR here.

## Conventions

- **File name:** `NNNN-short-slug.adoc`, sequential four-digit number. Numbers are never reused, not even for rejected proposals. Referred to as `ADR-NNNN` elsewhere.
- **Format:** AsciiDoc, as in Kompass, Gangleri and the CCB. Diagrams as plain text in `----` blocks.
- **Language:** English, like all documentation.
- **Status:** `Proposed`, `Accepted`, `Accepted and implemented`, `Rejected` or `Superseded by ADR NNNN`. Give the date and owner in the Status section.
- **Changes:** An accepted ADR is not rewritten. Small clarifications are added as a dated amendment (`[[amendment-YYYY-MM-DD]]`) at the end, and the Status section points to it. If the decision changes materially, write a new ADR and mark the old one as superseded.
- **Evidence:** Refer to files as `path/to/file.ttl:line` and to commits by short SHA. Refer to specification decisions by ID (`NP-0001`) and to change requests by repository and issue number.
- **Index:** Add every new ADR to the table above in the same PR.

## Template

```asciidoc
== NNNN. Title that states what was decided

Date: YYYY-MM-DD

== Status

Proposed. Owner: <team or person>.

== Context

The problem, the forces and constraints, and what holds today.

== Decision

What we will do, concrete enough that someone can check whether the repository follows it.

== Consequences

=== Positive

=== Negative

== Risks

== Alternatives

What was considered and why it was rejected.
```
