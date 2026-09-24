# Annotation guidelines (findings)

Gold findings list what a qualified procurement reviewer should be told. These rules apply to every
dataset; a dataset annotated under an earlier convention is re-annotated (with a version bump, the old
gold archived in `_archive/`, and an entry in `results/CONTAMINATION.md`). Blind splits are never edited.

## Certification (conformity evidence) — per product standard

Every product standard the specification invokes needs its own route to conformity evidence: a BIS
Standard Mark / ISI mark requirement, type-test or routine-test certificates, or third-party inspection.

* Evidence covers a product when the evidence clause cites its standard, names the product, or names no
  product at all and is about equipment in general ("all equipment shall be ISI marked").
* Evidence for one product does not cover another ("type-test certificates of the panel" does not cover
  the cables).
* Laboratory testing of samples, sources or materials under test ("water samples shall be tested at a
  NABL laboratory") is not product-conformity evidence.
* One certification finding per document, listing the uncovered products.

Why: a reviewer checks each item on the bill of materials; an uncertified product is a real procurement
risk even when another product in the same tender is covered. (tenders_v1 v1.0 used a document-level
convention — any evidence clause silenced the finding — which contradicted realworld_v2.)

## Checklist items — per product standard

A checklist item of an applicable product standard (conductor size of a cable, rated current of an MCB,
IP rating of an enclosure) must be stated for that product. A value stated for a different product (the
size of the power cable) does not satisfy the item for another (the control cable).

## Dependencies — only for invoked standards

"A requires B, which is not addressed" is reported only when the specification cites A. A standard
reached only by retrieval imposes no dependency findings.

## Vague wording

"Suitable", "adequate", "reputed make", "as low as possible" without a measurable value are gaps.
"Of approved make" refers to the tender's list of approved makes and is not vague.
