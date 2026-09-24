# StandardOS benchmark — tender-realistic specifications

```
cd aiml
uv run python -m benchmark.run      # → benchmark/results/latest.{md,json}
```

`eval/` measures each component on short, clean, author-written snippets. This
benchmark measures the whole pipeline on documents shaped like real Indian public
tenders, which is where precision problems actually appear.

## What is in it

| Doc | Modelled on | Lines | Gold requirements | Gold findings |
| --- | --- | --- | --- | --- |
| b1 | CPWD NIT — LT panel, ACB/MCCB/MCB/RCCB, XLPE cables, earthing | 82 | 40 | 5 |
| b2 | PHED Rajasthan / Jal Jeevan Mission — submersible pumpsets, flat cables, starters, water quality | 65 | 32 | 4 |
| b3 | TWAD Board — 500 KL RCC elevated reservoir, coastal (severe exposure) | 50 | 29 | 4 |
| b4 | DISCOM enquiry — 630 kVA transformers, 11 kV cables, LT ACBs | 50 | 26 | 5 |
| b5 | MJP — raw water pumping machinery (deliberately clean) | 56 | 29 | 0 |
| b6 | State PWD — internal electrification of a hostel | 38 | 20 | 7 |
| retrieval | 50 requirement sentences in tender phrasing, no citations | — | — | — |

Every document has what real tenders have and the `eval/` snippets do not: NIT header
fields, instructions to bidders (EMD, bid validity, eligibility), scope statements,
Guaranteed Technical Particulars as `Parameter: Value` blocks, pipe-separated BOQ
rows, notes, approved-make lists, multi-sentence clauses and repeated values across
sections. The planted issues are the ones reviewers actually find in tenders: IS 694
wires specified as "1100 V grade", 11 kV cables against IS 7098 (Part 1), withdrawn
IS 8828 / IS 13947 / IS 12269, the 1987 earthing code, and site temperatures above the
switchgear's normal service conditions. b5 has no planted issue, so every problem
finding on it is a false positive.

Each specification is scored three ways:

- **TXT**: the text as written.
- **PDF**: hard-wrapped at ~90 characters, 28 lines per page, with a running header and
  "Page n of N" footer (`render.py`). Ingestion has to re-flow broken sentences and strip
  the header and footer.
- **DOCX**: data sheets and BOQs as real Word tables, parsed through mammoth.

## Labelling rules

The same guidelines as `eval/README.md`, plus these for full tenders:

- **Not a requirement:** NIT header fields, instructions to bidders (EMD, bid validity,
  eligibility, rejection rules, "rates shall include taxes"), scope statements, BOQ rows,
  notes, a purchaser's reserved rights, and the approved-make list.
- **A requirement:** anything that obliges or specifies the supply or the work, including
  documentation, warranty, delivery, trial run and site/design conditions ("the site is at
  an altitude of less than 1000 m").
- **Findings:** what a qualified reviewer should be told *given what the corpus knows*.
  An amendment reminder is expected once per standard, not once per citation. Normative
  references of product standards and edges the corpus marks below 0.7 confidence are not
  expected. Standards not in the corpus (IS 3370, CPWD General Specifications) cannot
  produce findings.

## Protocol

1. The six documents, the gold requirements and findings, and the 50 retrieval queries were
   written first, after reading only the corpus contents, never the system's output on
   these texts.
2. A mechanical check confirmed that every gold requirement is a verbatim substring of its
   document and every referenced standard/clause id exists.
3. The benchmark was run once. That result is frozen in `results/first-run.md`.
4. The first run exposed one unambiguous defect: "ISI marked" / "ISI marking", the usual
   tender wording, was not recognised as conformity evidence (the TypeScript engine had the
   same defect). It was fixed in `nlp/entities.py` (component version 2.1.0), with a
   regression test; `eval/` metrics are unchanged. `results/latest.md` is the post-fix run.
   No other code, weight or label was changed after scoring.

## Known limitations

- **One author wrote the documents, the labels and (as a port) the system.** Independent
  annotation by procurement engineers is the next step before these numbers are quoted as
  anything more than an internal benchmark.
- **Label disagreement noticed after scoring (not changed):** in b5 the engine reports that
  the conductor size of the IS 7098 motor cables is unspecified. On reflection that is a fair
  finding, and the gold arguably should include it. It is scored as a false positive to keep
  the protocol intact.
- **Documents are realistic in structure but synthetic.** Real tenders also have scanned
  annexures, multi-column tables, Hindi text and hundreds of pages. OCR and multilingual
  input are not implemented.
- **Corpus scope.** Everything is judged against the 39-standard seed corpus.
  Standards outside it (IS 3370, IS 1255, …) are invisible to the engine.
- **Small counts.** 25 gold findings and 50 queries give wide confidence intervals: one
  finding moves findings recall by 4 points.
