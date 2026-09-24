# StandardOS evaluation — standardos-pipeline/1.0.0

Corpus `seed-10f612a6` · generated 2026-09-23T06:53:47.001Z

Splits: **dev** was used while developing rules and weights. **test** was held out for the first run, but some fixes were then made after inspecting its errors, so it is partly contaminated (see eval/README.md). **heldout** was written after all tuning and scored once without further changes; treat it as the uncontaminated estimate, keeping in mind it is small.

## Phase 1 — requirement extraction

| Split | Identification P / R / F1 | Classification acc. / macro-F1 | Attribute P / R / F1 |
| --- | --- | --- | --- |
| dev (4 docs) | 100.0% / 77.8% / 87.5% | 81.0% / 70.5% | 100.0% / 82.4% / 90.3% |
| test (4 docs) | 95.7% / 100.0% / 97.8% | 68.2% / 56.3% | 94.1% / 94.1% / 94.1% |
| heldout (2 docs) | 100.0% / 100.0% / 100.0% | 91.7% / 85.0% | 100.0% / 100.0% / 100.0% |
| all (10 docs) | 98.2% / 90.2% / 94.0% | 78.2% / 76.2% | 97.4% / 90.2% / 93.7% |

## Phase 2 — standard and clause retrieval (ablation)

| Split | Configuration | Std R@1 | Std R@3 | Std MRR | nDCG@5 | Clause R@1 | Clause R@3 | Clause MRR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dev (25) | bm25 | 100.0% | 100.0% | 1.000 | 0.976 | 88.0% | 100.0% | 0.940 |
| dev (25) | bm25+thesaurus | 96.0% | 100.0% | 0.980 | 0.965 | 84.0% | 100.0% | 0.913 |
| dev (25) | bm25+rerank | 92.0% | 100.0% | 0.960 | 0.950 | 88.0% | 92.0% | 0.900 |
| dev (25) | full (bm25+thesaurus+rerank) | 92.0% | 100.0% | 0.960 | 0.950 | 88.0% | 92.0% | 0.900 |
| test (25) | bm25 | 92.0% | 100.0% | 0.960 | 0.977 | 96.0% | 100.0% | 0.980 |
| test (25) | bm25+thesaurus | 92.0% | 100.0% | 0.960 | 0.977 | 92.0% | 100.0% | 0.960 |
| test (25) | bm25+rerank | 96.0% | 100.0% | 0.980 | 0.971 | 100.0% | 100.0% | 1.000 |
| test (25) | full (bm25+thesaurus+rerank) | 96.0% | 100.0% | 0.980 | 0.971 | 100.0% | 100.0% | 1.000 |
| heldout (15) | bm25 | 100.0% | 100.0% | 1.000 | 0.995 | 80.0% | 86.7% | 0.863 |
| heldout (15) | bm25+thesaurus | 86.7% | 100.0% | 0.933 | 0.964 | 66.7% | 93.3% | 0.817 |
| heldout (15) | bm25+rerank | 93.3% | 100.0% | 0.956 | 0.971 | 93.3% | 100.0% | 0.956 |
| heldout (15) | full (bm25+thesaurus+rerank) | 93.3% | 100.0% | 0.956 | 0.967 | 93.3% | 100.0% | 0.956 |

## Phase 2 — entity resolution, relationship extraction, graph construction

| Split | Resolution accuracy | Edition accuracy | Relation P / R / F1 |
| --- | --- | --- | --- |
| dev | 100.0% (17) | 100.0% | 100.0% / 100.0% / 100.0% (20 sentences) |
| test | 100.0% (17) | 100.0% | 100.0% / 100.0% / 100.0% (18 sentences) |
| heldout | 100.0% (8) | 100.0% | 93.8% / 93.8% / 93.8% (12 sentences) |
| all | 100.0% (42) | 100.0% | 98.5% / 98.5% / 98.5% (50 sentences) |

Graph construction from clause text: 37 edges extracted; 31 of 40 curated edges are stated in clause text.

| Metric | Value |
| --- | --- |
| Typed-edge precision | 78.4% |
| Typed-edge recall (text-supported curated edges) | 80.6% |
| Untyped pair precision | 97.3% |
| Recall over all curated edges | 72.5% |

## Phase 3 — compliance reasoning

| Split | Detector | Precision | Recall | F1 | TP/FP/FN |
| --- | --- | --- | --- | --- | --- |
| dev | overall (4 specs) | 100.0% | 100.0% | 100.0% | 9/0/0 |
| dev | conflict | 100.0% | 100.0% | 100.0% | 3/0/0 |
| dev | gap | 100.0% | 100.0% | 100.0% | 0/0/0 |
| dev | dependency | 100.0% | 100.0% | 100.0% | 2/0/0 |
| dev | outdated | 100.0% | 100.0% | 100.0% | 3/0/0 |
| dev | certification | 100.0% | 100.0% | 100.0% | 1/0/0 |
| test | overall (4 specs) | 100.0% | 100.0% | 100.0% | 12/0/0 |
| test | conflict | 100.0% | 100.0% | 100.0% | 4/0/0 |
| test | gap | 100.0% | 100.0% | 100.0% | 2/0/0 |
| test | dependency | 100.0% | 100.0% | 100.0% | 1/0/0 |
| test | outdated | 100.0% | 100.0% | 100.0% | 3/0/0 |
| test | certification | 100.0% | 100.0% | 100.0% | 2/0/0 |
| heldout | overall (3 specs) | 100.0% | 87.5% | 93.3% | 7/0/1 |
| heldout | conflict | 100.0% | 100.0% | 100.0% | 2/0/0 |
| heldout | gap | 100.0% | 100.0% | 100.0% | 2/0/0 |
| heldout | dependency | 100.0% | 50.0% | 66.7% | 1/0/1 |
| heldout | outdated | 100.0% | 100.0% | 100.0% | 1/0/0 |
| heldout | certification | 100.0% | 100.0% | 100.0% | 1/0/0 |

Mean end-to-end pipeline latency per specification: 2.5 ms (in-process, seed corpus).

## Error listing

### Retrieval misses (full configuration)

- q17: expected is-2026-1-2011, got is-1180-1-2014, is-2026-1-2011, is-4029-2010
- q23: expected is-456-2000, got is-1786-2008, is-456-2000, is-2062-2011
- q29: expected is-516-1-1-2021, got is-456-2000, is-516-1-1-2021, is-516-1959
- h15: expected is-8130-2013, got is-694-2010, is-1554-1-1988, is-8130-2013

### Relation errors

- y11: predicted REFERENCES IS 3025 (Part 10); gold TESTED_BY IS 3025 (Part 10)

### Extracted edges not in curated graph

- REQUIRES is-iec-61439-1-2020 → is-iec-60529-2001 (conformity cue "in accordance with")
- SUPERSEDES is-iec-61439-2-2020 → is-8623-1-1993 (supersession cue "Superseded" (coordinated reference))
- REQUIRES is-732-2019 → is-12640-1-2016 (conformity cue "conform to")
- REQUIRES is-732-2019 → is-694-2010 (conformity cue "conforming to")
- REQUIRES is-732-2019 → is-1554-1-1988 (conformity cue "conforming to" (coordinated reference))
- REQUIRES is-732-2019 → is-iec-60898-1-2002 (conformity cue "conform to")
- REQUIRES is-325-1996 → is-iec-60529-2001 (conformity cue "in accordance with")
- REFERENCES is-10262-2019 → is-456-2000 (bare mention)

### Reasoning errors

- t1: missed dependency is-iec-61439-1-2020

### Classification errors (gold → predicted)

- performance → quality
- installation → general
- installation → general
- performance → dimensional
- electrical → material
- electrical → environmental
- documentation → electrical
- performance → general
- environmental → dimensional
- quality → general
- material → electrical
- performance → general

