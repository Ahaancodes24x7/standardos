# StandardOS evaluation datasets

```
cd aiml
uv run python -m eval.run all --verbose   # report for all splits → eval/results/latest.{md,json}
uv run pytest                             # includes the regression gate (tests/test_eval_gate.py)
```

The datasets and metrics are unchanged from the TypeScript engine, and the Python
port reproduces its report exactly (every metric identical on every split; see
`results/latest.md`). For whole-document results on tender-realistic
specifications see `../benchmark/README.md`.

## Datasets

| File | Task | Size | Metric |
| --- | --- | --- | --- |
| `requirements.json` | Requirement identification, classification, attribute extraction | 10 documents, 61 gold requirements | P/R/F1 (a match needs token Jaccard ≥ 0.6 or containment); accuracy and macro-F1 on matched pairs; attribute P/R/F1 (value within 1 % or exact text) |
| `retrieval.json` | Standard and clause retrieval for requirements **without** explicit citations | 65 queries | Standard R@1/3/5, MRR, nDCG@5 (graded relevance 2/1); clause R@1/3, MRR |
| `resolution.json` | Citation → corpus record and edition relation | 42 citations | Accuracy |
| `relations.json` | Relation type per referenced standard in a sentence | 50 sentences | Typed P/R/F1 |
| `reasoning.json` | End-to-end findings per specification | 11 specifications | P/R/F1 per detector group (conflict, gap, dependency, outdated, certification) |
| (corpus) | Graph construction: edges extracted from clause text vs. the curated graph | 40 curated edges | Typed precision; recall over text-supported edges |

## Splits — read this before quoting numbers

- **dev** — used while writing rules and setting weights.
- **test** — held out for the first full run. After that run, some fixes were
  made in response to its errors (relation cues, a domain-consistency penalty,
  certification via replacement standards), so **test is partly contaminated**.
- **heldout** — written after all tuning was finished and scored once, with no
  changes made in response. This is the least biased estimate, but it is small
  (2 documents, 15 queries, 12 sentences, 8 citations, 3 specifications). The
  first-run report is kept at `results/heldout-first-run.md`. Later edits did
  not change the held-out numbers.

## Known limitations

1. **The same authors wrote the system and the labels.** Gold data reflects one
   reading of the standards and of what a reviewer should be told. Independent
   annotation by procurement engineers is needed before any claim beyond
   "works on these examples".
2. **Synthetic documents.** The specifications are short, written for this
   evaluation, and cleaner than real tenders, which have tables, boilerplate,
   scanned annexures and inconsistent numbering.
3. **Seed corpus.** Retrieval is scored against the same 39-standard, 90-clause corpus the
   system indexes. Precision on a large corpus with many near-duplicate standards
   will be lower.
4. **Clause-level gold is coarse.** Several clauses may legitimately govern a
   query; those are all listed, but the list can still be incomplete.

## Annotation guidelines (for extending the datasets)

- **Requirement:** a sentence, list item or table row that obliges or specifies
  a property of the supply or work, whether technical or contractual. Not a
  requirement: headings, scope statements ("This specification covers…"),
  permissions ("may"), notes, boilerplate.
- **Category:** the dominant concern: performance, electrical, environmental,
  safety, material, dimensional, testing, certification, documentation,
  installation, quality (water/material quality limits), general.
- **Attributes:** use the parameter keys in `standardos_aiml/nlp/parameters.py`,
  with values in canonical units (V, A, W, VA, Hz, mm, mm², MPa, m³/h, mg/L, NTU,
  %, °C, kg/m³, rpm, dB). Record only parameters in that vocabulary.
- **Retrieval relevance:** 2 = the standard that governs the requirement;
  1 = a related standard a reviewer would accept as useful. List every clause
  that governs.
- **Reasoning gold:** what a qualified reviewer should be told. Do not list
  issues the corpus cannot know about, and do not copy system output.
- Add new items to a new split (e.g. `heldout2`) and score it once before
  changing any code.
