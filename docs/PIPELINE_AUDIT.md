# StandardOS AI/ML pipeline — code-level audit and next-phase plan

Audit date 2026-09-24. Scope: `aiml/standardos_aiml/**` (engine), `aiml/eval/**`
(evaluation), `aiml/benchmark/**`, and the backend call sites in `backend/app/store.py`.
Every claim below was checked against the code or reproduced by running it. Where
something could not be established, it says **NOT VERIFIED**. No code was changed for
this audit.

---

## 0. Which version the numbers refer to

| Report | Pipeline | Corpus | Status |
| --- | --- | --- | --- |
| `aiml/eval/results/heldout-first-run.md` | `standardos-pipeline/1.0.0` (TypeScript) | `seed-10f612a6` | Frozen record of the single heldout scoring. **This is the source of the figures in the audit brief.** |
| `aiml/eval/results/latest.md` | `standardos-pipeline/2.1.0-py` (Python port) | `seed-6ada30cf` | Current engine |
| `aiml/benchmark/results/first-run.md`, `latest.md` | 2.0.0-py / 2.1.0-py | `seed-6ada30cf` | Six tender-realistic specifications (176 gold requirements, 25 gold findings, 50 queries) |

- **Heldout is unchanged between the frozen run and the current engine.** Every heldout
  row (identification, classification, attributes, retrieval ablation, resolution,
  relations, reasoning) is identical in both reports. The graph-construction metrics are
  identical too.
- **Only the all-split Phase 1 figures moved,** from fixes made on dev/test before heldout
  was written:

  | Metric (all splits) | Frozen first run (1.0.0) | Current (2.1.0-py) |
  | --- | --- | --- |
  | Identification F1 | 94.0% | 95.0% |
  | Classification accuracy / macro-F1 | 78.2% / 76.2% | 78.9% / 76.6% |
  | Attribute F1 | 93.7% | 96.3% |

- **q23 is not a current error.** It was a miss only under the first run's default "full"
  configuration, which included thesaurus expansion (§4.1).
- **Heldout is not perfectly pristine.** The retrieval default was changed from "full" to
  "bm25+rerank" *after* the heldout run. The justification cited all splits, including
  heldout. This is minor, but heldout retrieval now also partly informed a configuration
  choice.

**Sample sizes on heldout are very small:** 2 documents / 12 requirements, 15 queries, 8
citations, 12 sentences, 3 specifications / 8 gold findings. The 50% dependency recall is
**1 of 2**. One item moves heldout recall by 50 points, which is why every recommendation
below also cites the 176-requirement benchmark.

---

## A. Current architecture (as implemented)

- **No trained model anywhere.** Every detection, extraction, retrieval and reasoning step
  is deterministic Python: `re`, hand-built lexicons, a hand-written BM25, a linear
  re-ranker with hand-set weights, graph traversal and interval arithmetic. The only
  statistical scoring is BM25 term weighting. No ML library is imported by the engine or
  the backend (verified by grep: no `sklearn`, `torch`, `transformers`, `numpy`, `spacy`,
  `nltk`).
- **scikit-learn is installed but unused.** It is declared as the `ml` optional extra in
  `aiml/pyproject.toml` and imported by nothing.
- **Documentation error to correct.** The docstring in `aiml/standardos_aiml/nlp/classify.py`
  mentions `standardos_aiml.ml.classifier`, which **does not exist**. I wrote it during the
  port, and it is wrong.
- **One optional LLM call:** Claude (`REPAIR_MODEL = "claude-opus-5"`,
  `standardos_aiml/llm_repair.py`) rewords repair proposals only. It is off unless
  `STANDARDOS_LLM_REPAIR=on`, and every rewrite passes `reasoning/repair_validate.validate_rewrite`
  or is discarded. It is invoked from `backend/app/store.py::execute_run` via
  `polish_repairs`. It is **never used by eval or benchmark runs**, and there is **no
  evaluation of it**.
- **The runtime knowledge graph is the curated edge list** (`corpus.relationships`, from
  `standards/data/seed_corpus.json` or Postgres `standard_relationships`).
  `standards/relations.py::extract_relations` and `extract_corpus_relationships` are called
  **only from `eval/evaluate.py`**. So the relation-extraction metric (93.8%) and the
  graph-construction metrics (78.4% / 80.6%) measure components that are **not on the
  production path** (§5.B).
- **Requirement-to-standard linking** uses citation resolution plus retrieval
  (`standards/resolve.py`, `standards/retrieval.py`), not relation typing.

Orchestration is in `standardos_aiml/pipeline.py::run_pipeline`, in eight stages
(`reading` → `reporting`). Everything is in-process; mean latency is 3.8 ms per eval spec
and 50–120 ms per benchmark spec (TXT to DOCX).

## B. Model inventory

Libraries: pypdf 6.19.0, mammoth 1.12.2, Python `re`/`unicodedata`/`math`, and optionally
anthropic 1.8.0.

| Stage | Implementation (file :: function) | Algorithm / model | Library | Input → Output | Evaluation |
| --- | --- | --- | --- | --- | --- |
| Document parsing | `ingest/parse.py` :: `parse_document`, `_parse_pdf`, `_parse_docx`, `docx_html_to_text`, `decode_text` | Text-layer extraction; DOCX → HTML → lines, 2-column table rows → `Key: Value`; UTF-8, else cp1252 | pypdf 6.19.0, mammoth 1.12.2 | bytes/str → `ParsedDocument` (pages, text, warnings) | `tests/test_ingest_nlp.py` (parse tests); benchmark PDF/DOCX columns |
| Normalisation | `ingest/normalize.py` :: `normalize_characters`, `reflow_lines`, `strip_repeated_lines` | Character map + NFKC; line reflow heuristics; header/footer removal (lines repeated on ≥60% of pages, ≥3 pages) | stdlib | page text → cleaned text | `test_normalisation`, `test_reflow`, `test_strips_running_headers` |
| Section detection | `ingest/sections.py` :: `detect_sections`, `locate` | Regex (numbered, labelled, upper/title-case headings) | `re` | text → `Section[]`, labels | `test_sections` |
| Requirement identification | `nlp/requirements.py` :: `segment`, `identify`, `extract_requirements` | Rules: line/enumerator/sentence segmentation; deontic cues (`MANDATORY`, `RECOMMENDED`, `PERMITTED`), `ATTRIBUTE_LINE`, `CONFORMITY`, `BOILERPLATE` filter, "short fragment with value" rule | `re` | text + sections → `StructuredRequirement[]` | `eval/evaluate.py::evaluate_requirements` (identification P/R/F1; Jaccard ≥ 0.6 or containment) |
| Requirement classification | `nlp/classify.py` :: `classify_requirement` | **Weighted cue lexicon** (12 categories) + dimension/entity/parameter boosts; argmax; no cue → `general` | `re` | text + quantities + entities + attributes → category, scores | `evaluate_requirements` (accuracy, macro-F1 on matched pairs) |
| Quantity/unit extraction | `nlp/quantities.py` :: `extract_quantities`; `nlp/units.py` :: `lookup_unit`, `to_canonical` | Regex + canonical-unit table, comparators, ranges, tolerances | `re` | text → `Quantity[]` | unit tests; attribute F1 |
| Attribute extraction | `nlp/quantities.py` :: `infer_parameter`; `nlp/requirements.py` :: `build_attributes`; `nlp/entities.py` :: `extract_entities`, `extract_text_parameters` | Nearest cue phrase within 90 chars (preferring cues before the value) over the `nlp/parameters.py` vocabulary; entity regexes; per-dimension defaults | `re` | quantities + entities → `Attribute[]` | `evaluate_requirements::score_attributes` (value within 1%) |
| Product terms | `nlp/entities.py` :: `extract_product_terms` | Surface-form lexicon (`PRODUCT_TERMS`) | `re` | text → terms | none directly |
| Standard reference extraction | `nlp/entities.py` :: `extract_standard_references`, `canonical_designation` | Regex over IS/IS-IEC/IEC/ISO designation grammar | `re` | text → `StandardReference[]` | resolution eval; `test_designations` |
| Entity resolution | `standards/resolve.py` :: `StandardResolver.resolve` | Cascade: exact/alias key → IEC→IS/IEC adoption → drop section/part → only-part / Part 1 | stdlib | reference → `ResolvedReference` | `evaluate_resolution` (accuracy) |
| Edition resolution | same, edition block | Year compare against record; `prior_editions` lookup | stdlib | reference year → current/older/newer/unspecified | `evaluate_resolution` (editionAccuracy) |
| Standard retrieval | `standards/retrieval.py` :: `StandardsIndex.build_query`, `bm25`, `retrieve` | **Fielded BM25** (k1 = 1.2, b = 0.75; clause text 1.0, heading 1.5, title 1.2, keywords 1.5, scope 0.6, designation 2.0), top-40 → **linear re-ranker** (hand-set `RERANK_WEIGHTS`) → best clause per standard | hand-written | requirement → `RetrievalHit[]` | `evaluate_retrieval` (R@1/3/5, MRR, nDCG@5) × 4 ablations |
| Clause retrieval | same (`clause_id` of the best clause); `rank_clauses` for BM25-only ablations | Same scoring; clause = argmax per standard | hand-written | → clause id | `evaluate_retrieval` (clause R@1/3, MRR) |
| Query expansion | `standards/text.py` :: `synonyms_of` | Thesaurus groups at weight 0.5; **off by default** | stdlib | — | ablation rows |
| Relation extraction | `standards/relations.py` :: `extract_relations` | Cue-regex window before each reference; coordination inheritance | `re` | sentence → typed relations | `evaluate_relations` (typed P/R/F1). **Not on the runtime path.** |
| Graph construction | `standards/relations.py` :: `extract_corpus_relationships` | `extract_relations` over clause texts + resolution; confidence = relation × resolution | `re` | corpus → extracted edges | `evaluate_graph_construction`. **Eval only; the runtime graph is curated.** |
| Runtime graph | `standards/graph.py` :: `StandardsGraph` (`outgoing`, `incoming`, `latest_replacement`, `dependencies`), `build_analysis_graph` | Adjacency lists, BFS (depth ≤ 2) | stdlib | curated edges → traversals, evidence graph | `test_graph_traversal`; indirectly via reasoning |
| Applicability | `pipeline.py` (stage 5, `note`); `reasoning/context.py::strong_applicable` | Standard applies if cited, or top hit ≥ 0.35; "strong" if cited or ≥ 0.5 | stdlib | mappings → `Applicability` | indirect |
| Conflict detection | `reasoning/conflicts.py` :: `check_constraints`, `compare`, `constraint_conflict_findings`, `intra_document_conflicts`, `reference_edition_conflicts` | Interval arithmetic vs clause constraints (qualifier-aware); checked standards = cited + top hit ≥ 0.35 | stdlib | attributes × constraints → findings | `evaluate_reasoning` (conflict group) |
| Gap detection | `reasoning/gaps.py` :: `checklist_gaps`, `vague_requirement_findings` | Per-standard purchaser checklist vs **document-wide** attributes; `VAGUE` regex | stdlib | → findings | gap group |
| Dependency detection | `reasoning/dependencies.py` :: `dependency_gaps`, `_addressed_standards` | Traverse REQUIRES/TESTED_BY (product standards: TESTED_BY only; edge confidence ≥ 0.7); skip targets already "addressed" | stdlib | → findings | dependency group |
| Outdated detection | `reasoning/versions.py` :: `version_findings` | Status + edition + version events + supersession chain | stdlib | → findings | outdated group |
| Certification | `reasoning/certification.py` :: `certification_findings` | Product standards with a certification scheme and no conformity-evidence attribute → one finding | stdlib | → finding | certification group |
| Verification | `reasoning/verification.py` | Satisfied constraints; current citations | stdlib | → verified findings | not scored |
| Repair | `reasoning/repair.py` :: `generate_repairs`; optional `llm_repair.py::polish_repairs` + `repair_validate.py` | Templates; optional LLM copy-edit with a fact-preservation guard | stdlib; anthropic (optional) | findings → proposals | `test_rewrite_guard` only; **no quality evaluation** |
| Readiness | `pipeline.py::compute_readiness` | `round(clamp(100 × mapped/total − (8·high + 3·medium + 1·low)))` | stdlib | → score | none (heuristic) |

### Confidence and fallback behaviour (from code)

**Confidence scores**

| Stage | Confidence |
| --- | --- |
| Requirement | 0.95 mandatory with a value or reference; 0.85 mandatory; 0.8 attribute line; 0.75 recommended or conformity; 0.55 permissive with a value; 0.6 value fragment |
| Classification | 0.5 + 0.5 × (top − second) / top; 0.4 when there are no cues (→ `general`) |
| Retrieval | Re-ranker score ÷ 1.15 (the sum of the non-explicit weights), +0.6 if cited; × 0.5 if superseded; × 0.6 for a test-method standard on a non-test requirement; × 0.6 if out of product scope; clamped to [0, 1] |
| Resolution | 0.98 / 0.9 / 0.8 / 0.7 / 0.6 by match path; 0 if unresolved |
| Relations | 0.8 cue; 0.7 inherited or example; 0.6 bare or related |
| Findings | Conflicts 0.9 disjoint / 0.75 partial; internal 0.8; edition 0.9; gaps 0.75 / 0.7; vague 0.65; dependency min(0.85, edge); versions 0.85 × resolution; newer / amendment 0.6; certification 0.7 |

None of these are calibrated.

**Fallbacks**

- **Corpus:** Postgres, else the bundled seed (`backend/app/corpus.py`).
- **Unresolved citation:** `standard_id=None`.
- **Scanned PDF:** `ParseError("no_text_layer")`.
- **No parameter cue:** the per-dimension default parameter.
- **LLM rewrite rejected:** the template is kept.
- **Run crash:** the sweeper re-queues it (max 3 attempts).

## C. Data flow (types from `standardos_aiml/types.py`)

```
bytes|str ──parse──> ParsedDocument{format, parser, pages[], text, warnings}
text ──detect_sections──> Section[]{number, heading, level, span, page}
text,sections ──extract_requirements──> StructuredRequirement[]{text, span, section_label, modality,
        category, category_scores, quantities[Quantity{value,min,max,unit,dimension,comparator,tolerance}],
        references[StandardReference{designation, year}], entities[], attributes[Attribute{parameter, quantity|text}],
        terms[], vague, provenance}
requirements ──document_context_terms──> context terms (≤4)
references ──resolver.resolve──> ResolvedReference{standard_id, edition, replaced_by_id, provenance}
requirement ──index.retrieve──> RetrievalHit[]{standard_id, clause_id, score(BM25), confidence, explanation, provenance}
                                → RequirementMapping{basis: explicit_reference|retrieval|none}
mappings,resolved ──> Applicability{standard_id, confidence, explicit, requirement_ids}
ReasoningContext ──detectors──> ReasoningFinding[]{kind, rule, parameter, severity, standard_id, clause_id,
        evidence[Evidence], provenance} ──generate_repairs──> RepairProposal[]
all ──> AnalysisResult{…, graph: AnalysisGraph, readiness, timings_ms}
backend/app/store.py::_persist_result → Postgres; backend/app/view.py → DocumentAnalysis JSON (unchanged frontend contract)
```

## D. Error trace

Reproduced on 2.1.0-py. Format: INPUT → STAGE → FAILURE → ROOT CAUSE → POSSIBLE FIX.

### D.1 Retrieval

- **q17** (dev) "Transformer routine tests shall include winding resistance and impedance measurement."
  - **Stage:** re-ranker (`retrieval.py::retrieve`).
  - **Failure:** IS 1180 (0.566) outranks gold IS 2026 (0.565). BM25 alone has IS 2026 first by a wide margin (23.6 vs 7.9).
  - **Root cause:** the `clause_parameter` feature. IS 1180's checklist maps `test_method` to its `#tests` clause (+0.2). IS 2026 is `kind: specification`, not `test_method`, so it gets no `test_method` credit. BM25 contributes only 0.45 of the normalised score, so a 3× BM25 advantage is erased.
  - **Possible fix:** grant `test_method` parameter credit by clause role (a tests clause of any kind); or cap how much the parameter features can reverse a large BM25 margin.

- **q23** (dev; first run only) "Minimum cover to main reinforcement shall be 40 mm."
  - **Stage:** query expansion.
  - **Failure:** with the thesaurus, IS 1786 ranks first.
  - **Root cause:** expansion adds rebar/tmt/bar synonyms of "reinforcement" at weight 0.5, boosting the steel-bar standard.
  - **Status:** already resolved by the default being `expansion=False`.
  - **Possible fix:** keep the thesaurus off; if it is ever revived, expand only product nouns that the query lacks.

- **q29** (test) "Concrete cubes shall be tested for compressive strength at 28 days."
  - **Stage:** re-ranker.
  - **Failure:** IS 456 `#sampling` (0.826) beats IS 516 (Part 1/Sec 1) (0.806).
  - **Root cause:** both get the same `test_method` clause-parameter credit (IS 456's checklist puts `test_method` on `#sampling`), and BM25 slightly favours IS 456 ("28", "day", "cube"). The gold also grades IS 456 as acceptable (1), so the label is partly ambiguous.
  - **Possible fix:** same as q17. Prefer `kind == test_method` standards for requirements whose category is `testing`.

- **h15** (heldout) "The conductor of flexible cords shall be class 5 annealed copper."
  - **Stage:** re-ranker.
  - **Failure:** BM25 ranks gold IS 8130 first (19.76 vs 19.68); the re-ranker pushes it to third (0.391).
  - **Root cause:** `conductor_material` is a checklist item on the IS 694 and IS 1554 `#conductors` clauses (+0.2 clause and +0.1 standard credit). IS 8130 has no checklist or constraints, so it gets no parameter credit. No product term fires, because "cord" is not a `PRODUCT_TERMS` surface form for `cable`.
  - **Possible fix:** add "cord(s)" to the cable forms. Model "conductor specification" as a parameter IS 8130 governs (a corpus change, recorded in the corpus version). Apply the q17 cap.

### D.2 Relation extraction

- **y11** (heldout) "Water quality monitoring shall use the methods of IS 3025 (Part 10)."
  - **Stage:** `relations.py::extract_relations`.
  - **Failure:** REFERENCES (bare mention) instead of TESTED_BY.
  - **Root cause:** the TESTED_BY cue needs a test verb (`test…`, `measur…`, `analys…`, `sampl…`) or the literal "methods of test/sampling" before the connector. "use the methods of" matches neither, so it falls through to a bare mention.
  - **Possible fix:** add a "(use|using|follow) the methods of" → TESTED_BY cue. Low runtime impact, because this extractor is not on the production path.

### D.3 Reasoning

- **t1** (heldout) Panels "shall conform to IS/IEC 61439-2:2020"; the spec never cites Part 1. Gold: dependency on `is-iec-61439-1-2020`.
  - **Stage:** `reasoning/dependencies.py::dependency_gaps` → `_addressed_standards`.
  - **Failure:** no dependency finding.
  - **Trace:**
    - req-1 cites IS/IEC 61439-2, which is explicit and applies.
    - IS/IEC 61439-2 is `kind: specification`, so REQUIRES edges are considered. Edge `REQUIRES → is-iec-61439-1-2020` has confidence 0.95 ≥ 0.7.
    - But req-3..6 (busbar rating, short-time current, IP42, 45 °C) each **retrieve** IS/IEC 61439-1 as their top hit, at 0.656–0.722 (≥ 0.5).
    - `_addressed_standards` adds every top hit ≥ 0.5 to "addressed", so the dependency is suppressed.
    - (The same retrieval correctly powers the ambient-temperature conflict.)
  - **Root cause:** a design conflation. *"A requirement is about the subject matter of standard X"* (retrieval) is treated as *"the document invokes standard X"* (citation). For normative REQUIRES dependencies the purchaser must **cite** the part.
  - **Confirmed systematic:** benchmark `b1` misses the IS 7098 → IS 10810 TESTED_BY dependency the same way. The IR-test requirement retrieves IS 10810 at 0.896.
  - **Possible fix:** treat a dependency as addressed only by an explicit citation of the target or its replacement. For TESTED_BY, also accept a testing-category requirement mapped to the target. Evaluate on new data (§I). **Do not tune on t1.**

### D.4 Classification

12 errors across all splits (the brief lists 10 distinct confusion types; the full list includes the duplicates).

| # | Split / doc | Requirement | Gold → predicted | Cue scores | Root cause | Possible fix |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | dev rq-2 | "The treatment plant shall produce 2 MLD of potable water." | performance → quality | quality 1.5 | "potable" is a quality cue; "MLD" is not a flow unit, so the `flow` dimension boost never fires | Add MLD/KLD flow units; lower cue weight for the context word "potable" |
| 2 | dev rq-3 | "Curing shall be continued for at least 10 days." | installation → general | none | Lexicon gap (curing) | Add construction-execution cues |
| 3 | dev rq-3 | "Formwork shall be removed only after approval of the Engineer." | installation → general | none | Lexicon gap (formwork) | Same as #2 |
| 4 | dev rq-3 | "Slump of concrete: 75 mm to 100 mm" | performance → dimensional | dimensional 0.8 | The length-dimension boost alone decides; "slump" is not a cue | Add workability cues; stop dimension boosts deciding alone |
| 5 | test rq-5 | "Cables shall be 1.1 kV grade, XLPE insulated…" | electrical → material | material 3.6, electrical 2.5 | Material words (XLPE, PVC) outweigh a single voltage value; taxonomy overlap | Taxonomy rule plus a voltage boost when the subject is cable |
| 6 | test rq-5 | "The maximum conductor temperature shall be 90 °C…" | electrical → environmental | environmental 2.2, electrical 1 | The temperature boost assumes ambient conditions, but `conductor_temperature` is electrical | Boost by inferred parameter, not by dimension |
| 7 | test rq-5 | "Cable drums shall be marked with the manufacturer's name…" | documentation → electrical | electrical 1 | "Cable" is an electrical cue; "marked" is not a documentation cue | Add marking/labelling cues |
| 8 | test rq-6 | "Pumps shall be horizontal split casing type…" | performance → general | none | Lexicon gap; the label is arguably general | Label guideline |
| 9 | test rq-6 | "Noise level at 1 m distance shall not exceed 85 dB(A)." | environmental → dimensional | dimensional 0.8 | The "1 m" length boost wins; `noise_level` gives no boost | Parameter boost for `noise_level` |
| 10 | test rq-7 | "Treated water shall meet the following limits:" | quality → general | none | "Treated water" is not a cue, and the line is a list header | Include "treated water" in quality cues |
| 11 | test rq-8 | "The transformer tank shall be painted with epoxy paint." | material → electrical | electrical 1 | "Transformer" is an electrical cue; paint/epoxy are not material cues | Add coating/material cues |
| 12 | heldout rq-h1 | "Luminaires shall be LED type with a minimum efficacy of 110 lm/W." | performance → general | none | Lexicon gap (efficacy); lm/W is not a unit | Add efficacy cue and lm/W unit |

**Mechanism behind all 12:**

- **5 of 12 have no cue at all** (#2, #3, #8, #10, #12) and default to `general`.
- **4 of 12 are decided by a single dimension boost** or context word (#1, #4, #6, #9).
- **3 of 12 are taxonomy overlap** between a component noun and a property (#5, #7, #11).
- **None is a model-capacity failure;** there is no model.

---

## E. Bottleneck analysis (ranked by evidence)

### 1. Findings precision on realistic documents is limited by what the detectors are fed

- **Heldout findings precision is 100%, on 8 findings.**
- **On the benchmark, precision is 67.6%** (23 TP, 11 FP).

| FP cause | Count | Where |
| --- | --- | --- |
| Mis-scoped retrieval mapping used by a detector | 4 | Submersible motor (IS 9283 cited elsewhere) mapped to IS 325 → IS 325 checklist gap and IS 4029 dependency; starter panel mapped to IS/IEC 61439-2 → Part 1 dependency; transformer temperature mapped to IS/IEC 61439-1 at **0.391** → conflict |
| Extraction noise reaching reasoning | 2 | Heading "SECTION IV – 11 kV POWER CABLES" extracted as a requirement → duplicate conflict; bidder-eligibility sentence → vague finding |
| Over-broad vague lexicon | 2 | "suitable for star-delta starting"; "of approved make" (the latter is arguably a label question) |
| Document-wide checklist matching | 1 | A cable IR-test mention satisfies or triggers the IS/IEC 61439-1 `test_method` checklist item |
| Amendment reminder per citation | 1 | IS 456 cited twice → two reminders |
| Gold disagreement | 1 | b5 conductor size (noted in the benchmark README) |

**Root:** detectors trust any mapping ≥ 0.35, and check checklist items against the whole
document rather than the requirements that invoke the standard.

### 2. Dependency detection recall

Heldout 1/2; benchmark 3/4 recall with 60% precision. The t1 and b1 misses share one root
cause (D.3). The two benchmark false positives are the mis-scoping in bottleneck 1.

### 3. Requirement classification

Macro-F1 76.6% on all eval splits and 67.6% on the benchmark (accuracy 69.2%, n = 169 matched requirements).

- **Lexicon coverage gaps.** On the eval set, 5 of 12 errors have zero cues. On the
  benchmark, 23 requirements were predicted `general`, and 13 of those were wrong.
  `installation` F1 is 0%.
- **Boosts that override meaning.** Dimension-based boosts decide the category even when
  the parameter says otherwise (#4, #6, #9).
- **Taxonomy overlap.** electrical vs material is the top benchmark confusion (5), then
  safety → electrical (4). A cable spec line is legitimately both.
- **Class imbalance and tiny classes.** The eval set has 61 labels over 12 classes;
  `safety`, `certification`, `testing` and `dimensional` have 1–2 examples each.
  Macro-F1 on this set is dominated by single items.
- **Not a weak-model problem yet.** No learned model exists. With 61 + 176 labels, a
  supervised model would be trained and tested on too little data to beat a fixed lexicon
  reliably.

Classification affects retrieval (`category == "testing"` gates the test-method penalty),
dependency targeting and UI grouping. It does not affect conflict detection.

### 4. Retrieval — the re-ranker is a trade-off, not a clear win

| Configuration | Heldout std R@1 | Heldout clause R@1 | Benchmark std R@1 | Benchmark clause R@1 / R@3 |
| --- | --- | --- | --- | --- |
| bm25 | **100%** | 80.0% | **92%** | 80% / **96%** |
| bm25+thesaurus | 86.7% | 66.7% | 90% | 80% / 94% |
| bm25+rerank (default) | 93.3% | **93.3%** | 88% | **86%** / 92% |
| bm25+thesaurus+rerank | 93.3% | 93.3% | 88% | 86% / 92% |

- **BM25 alone is best at standard level** on both heldout and the benchmark. The
  re-ranker costs 1 heldout query (h15) and 2 benchmark queries at standard R@1.
- **The re-ranker is best at clause R@1** (+2 heldout queries, +3 benchmark queries), but
  loses at clause R@3 on the benchmark.
- **The thesaurus never helps.**
- **All three standard-level misses (q17, q29, h15) have the same mechanism:** the
  parameter-match features (+0.2 / +0.1) overturn a correct BM25 ranking in favour of a
  standard whose checklist happens to name the parameter.
- **Evaluation gap:** every retrieval ablation runs with `document_context=False`. The
  production default (`document_context=True`, including the "cited elsewhere" feature)
  is **not measured by any retrieval metric**.
- **Dense retrieval is not indicated.** In every miss, BM25 had the correct standard at
  rank 1–2. The failures are in re-ranking, not recall.

### 5. Relationship typing vs graph construction — why 93.8% and 78.4% diverge

The two metrics use different gold conventions and inputs:

- **The pairs are right; the types differ by convention.** Untyped pair precision is 97.3%.
- **6 of 8 extracted-edge false positives are REQUIRES where the curated graph says
  REFERENCES,** for "in accordance with IS/IEC 60529" / "conform to IS 12640". Each of
  those same pairs appears again as a false negative, so one convention mismatch costs
  both precision and recall.
  - The sentence gold (`relations.json`) labels "conform to X" as REQUIRES.
  - The curated graph deliberately types informative citations inside codes of practice
    and IP-code declarations as REFERENCES, so that dependency reasoning does not fire on
    them.
- **1 false positive is a genuine extractor error:** SUPERSEDES was inherited across a
  coordination in the IS/IEC 61439-2 scope clause (IS 8623).
- **1 is a bare mention against a curated RELATED_TO** (IS 10262 → IS 456).
- **4 of the 9 false negatives are RELATED_TO edges with no textual support** at all.
  Recall over all curated edges is capped at 31/40.
- **Consequence:** neither metric affects production findings today (§A). Graph quality
  matters only if extracted edges are ever merged into the runtime graph. Before that
  happens, the typing convention must be defined and both gold sets aligned to it.

### 6. Lower priority, with evidence

- **Identification** is strong (heldout 100%, benchmark F1 94.4%). Remaining errors are
  zone errors (instructions to bidders, a numbered all-caps heading containing "11 kV")
  and GTP lines without a unit value.
- **Attributes** are strong (96–97%).
- **Resolution** is 100% (n = 8 heldout, 42 total).
- **Document formats:** PDF costs 0.5 points of identification F1 and 2 points of findings
  F1 against TXT; DOCX equals TXT.

---

## F. Three-phase development plan

Order of work: **Phase 3.1 (dependency) → Phase 1.1–1.3 → Phase 2.1–2.3 → the rest.**
The brief ranks dependency first, and its fix is small and isolated. Everything is gated
by the evaluation protocol in §I.

### Phase 0 — prerequisite, no behaviour change (1–2 days)

- **P0.1 Versioned results.** `eval/run.py` and `benchmark/run.py` write
  `results/<pipeline-version>/<corpus-version>/` plus `latest`, and never overwrite
  `first-run.*` or `heldout-first-run.md`.
- **P0.2 Before/after comparison.** A diff script,
  `aiml/eval/compare.py <runA> <runB>`, prints the metric deltas and the per-item
  changes (fixed, broken) for every task.
- **P0.3 Uncertainty and a new blind split.**
  - Bootstrap 95% confidence intervals for every headline metric.
  - Write a **new blind split `heldout2`** as new files
    (`reasoning_heldout2.json`, `requirements_heldout2.json`, `retrieval_heldout2.json`),
    by someone other than the rule author if at all possible. Target ≥ 10 specifications,
    ≥ 20 dependency cases and ≥ 40 queries.
  - Existing heldout files are not touched.
- **P0.4 Retrieval eval in the production configuration.** Add a variant with
  `document_context=True`: whole-document queries from the benchmark specs, with gold
  mappings.
- **P0.5 Docstring fix.** Correct the false `ml.classifier` docstring in
  `nlp/classify.py`, and either remove the unused `ml` extra or mark it experimental.

### Phase 1 — extraction and classification hardening

| Task | Files | Change | Target (benchmark, TXT/PDF/DOCX) |
| --- | --- | --- | --- |
| 1.1 Document zoning | `ingest/sections.py`, `nlp/requirements.py` | Label NIT/ITB/commercial/BOQ zones from headings ("Instructions to bidders", "General conditions", "Bill of quantities", "Schedule of quantities") and exclude them from requirement identification; zone recorded in provenance | Identification precision 92.9% → ≥ 97% with no recall loss; vague false positives from boilerplate → 0 |
| 1.2 Heading detection | `ingest/sections.py::is_heading_text` | Accept all-caps "SECTION n – …" headings that contain unit tokens | No heading extracted as a requirement |
| 1.3 Lexicon and boost repair | `nlp/classify.py`, `nlp/units.py` | Cues for the D.4 gaps (curing, formwork, efficacy, marking, coating, slump; MLD and lm/W units); parameter-based boosts replace dimension-only boosts where a parameter is inferred; written tie-break rules for the electrical/material and safety/electrical overlaps (added to `eval/README.md` guidelines) | Benchmark macro-F1 67.6% → ≥ 75% with no dev/test regression; heldout2 classification reported |
| 1.4 Classifier ensemble (conditional) | new `nlp/classifier_model.py` | Only once ≥ 500 labelled requirements exist (benchmark + heldout2 + reviewer-confirmed categories): TF-IDF (word + char n-grams) + multinomial logistic regression, combined with lexicon scores; the lexicon stays the explanation and the fallback | Must beat the lexicon on a blind split by more than the CI width, or it is not shipped |
| 1.5 Provenance | `nlp/requirements.py` | Record the zone, and the rule that suppressed a candidate | UI can show why a line was skipped |

### Phase 2 — standards intelligence and graph quality

| Task | Files | Change | Target |
| --- | --- | --- | --- |
| 2.1 Re-ranker parameter-feature fix | `standards/retrieval.py` | (a) `test_method` credit by clause role/heading, not only `kind == test_method`; (b) prefer test-method standards for `testing` requirements; (c) limit parameter features to breaking near-ties in BM25 (e.g. only within 0.8·max), so a large BM25 margin is kept | Standard R@1 ≥ BM25-only on dev, test and benchmark; clause R@1 kept at re-ranker level; q17/q29/h15-type misses fixed without new misses |
| 2.2 Two-level ranking (if 2.1 is insufficient) | `standards/retrieval.py` | Rank standards by aggregated BM25 (+ product/context features); pick the clause within the standard with the re-ranker | Best of both ablation rows |
| 2.3 Mapping scope guard | `standards/retrieval.py`, `pipeline.py` | When the document cites a standard for the same product term, prefer it over uncited competitors (e.g. IS 9283 over IS 325 for "motor" in a submersible spec); record `scope_mismatch` when the requirement's product terms and the standard's scope disagree | Removes the IS 325 / IS 61439 mis-scoping false positives |
| 2.4 Product lexicon | `nlp/entities.py::PRODUCT_TERMS` | Add missing surface forms (cord/cords, starter, feeder pillar, luminaire); corpus-version bump if the corpus changes | Measured on the retrieval sets |
| 2.5 Relation typing convention | `eval/README.md`, `eval/datasets/relations.json` (new split only), `standards/relations.py` | Define REQUIRES vs REFERENCES (normative obligation of the *subject* vs informative pointer); fix the coordination-inheritance leak across "Superseded"; add the "methods of" TESTED_BY cue | Typed-edge precision/recall on the aligned gold; relation F1 on heldout2 |
| 2.6 Extracted edges into the runtime graph? | `standards/relations.py`, `backend/scripts/seed_standards.py` | **Decision, not code.** Keep the curated graph authoritative; extracted edges may be proposed for curation (method `extracted`, below `MIN_EDGE_CONFIDENCE`) but never raise findings until reviewed | — |
| 2.7 Keep the thesaurus off | — | Evidence in §E.4 | — |
| 2.8 Resolution | `standards/resolve.py` | No change; add heldout2 citations | Stays at 100% |

### Phase 3 — compliance reasoning

| Task | Files | Change | Target |
| --- | --- | --- | --- |
| **3.1 Dependency "addressed" semantics (first)** | `reasoning/dependencies.py::_addressed_standards`, `dependency_gaps`; `reasoning/context.py` (split `Applicability` into cited vs retrieved ids) | REQUIRES target addressed only by citation of the target or its replacement/predecessor; TESTED_BY target addressed by citation, or by a testing-category requirement *citing* it; retrieval-only matches no longer suppress | Dependency recall on dev + test + benchmark + heldout2 up, precision not below the current 60% (benchmark); report t1 as a known-contaminated item, not as evidence |
| 3.2 Confidence gate for detectors | `reasoning/conflicts.py::_candidate_standards`, `reasoning/gaps.py`, `reasoning/dependencies.py` | Retrieval-only mappings must pass ≥ 0.5 (not 0.35) and scope agreement (2.3) to trigger conflicts or checklist gaps; below that the mapping is shown but raises nothing | Benchmark conflict precision 80% → ≥ 95% at unchanged recall |
| 3.3 Scoped checklists | `reasoning/gaps.py::checklist_gaps`, `reasoning/context.py::document_attributes` | Check a standard's checklist against the requirements in its applicability set plus document-level context attributes (voltage, frequency, ambient); do not match unrelated requirements | Gap precision 33% → ≥ 60% |
| 3.4 Vague-language precision | `nlp/requirements.py::VAGUE` | Do not flag "suitable for <specific noun>"; add "as low as possible", "as high as possible" | Vague false positives and negatives on the benchmark |
| 3.5 Amendment de-duplication | `reasoning/versions.py` | One amendment reminder per standard per document, with all citing requirements as evidence | Removes the b3-type false positive |
| 3.6 Evidence grounding checks | `tests/` | Property tests: every finding's evidence spans resolve in document text (exists for requirement_text); every `standard_id` / `clause_id` exists; every repair number appears in the evidence | CI invariant |
| 3.7 Repair evaluation | new `eval/repairs.json` + `eval/evaluate.py::evaluate_repairs` | Gold "acceptable repair" judgements per finding; measure template acceptability; for the optional LLM, measure the `validate_rewrite` rejection rate and blinded preference before it is recommended for production | First repair metric in the project |
| 3.8 Human-review feedback loop | `backend/app/store.py`, new `backend/scripts/export_review_labels.py` | Export confirmed/dismissed findings and edited repairs from `audit_events` as labelled data (with the pipeline version) for 1.4, 3.2 thresholds and calibration | Data pipeline only; no automatic learning |
| 3.9 Calibration (later) | `pipeline.py` / detectors | Fit per-detector confidence → probability on reviewer labels (isotonic or Platt) once ≥ 200 reviewed findings exist | Calibrated confidence in the UI |

## G. Proposed target architecture (incremental)

```
parse ─► normalize ─► sections + ZONES ─► requirement identification (rules, zone-filtered)
     ─► classification: lexicon (+ optional linear model on TF-IDF once data exists)
     ─► attributes (unchanged)
     ─► resolution (unchanged)
     ─► retrieval: BM25 standard ranking ─► clause re-ranker (fixed features) ─► scope check
     ─► applicability {cited ids, retrieved ids, scope flags}
     ─► detectors gated by (cited | retrieved ≥ 0.5 ∧ in-scope)
     ─► dependency: citation-based "addressed"
     ─► findings ─► repairs (templates; optional guarded LLM, evaluated)
     ─► human review ─► audit_events ─► label export ─► offline evaluation / retraining
curated graph = runtime truth; extracted edges = curation proposals only
```

The frontend and API contracts are unchanged. New provenance fields (zone, scope flag,
cited vs retrieved) are optional additions in `backend/app/view.py`, `src/lib/contracts.ts`
and the jsonb provenance.

## H. Component recommendations

| Component | Verdict | Justification |
| --- | --- | --- |
| pypdf / mammoth parsing | **KEEP** | PDF within 0.5 points of identification F1 of TXT; DOCX equal. Table-aware PDF parsing only when multi-column tender tables appear in the data |
| Normalisation / reflow / header strip | **KEEP** | Benchmark PDF (wrapped lines, running headers) holds up |
| Section detection | **MODIFY** | Zoning (1.1) and heading fix (1.2) |
| Requirement identification (rules) | **MODIFY** | Errors are zone errors; an ML identifier is not justified (F1 94–100%) |
| Classification (lexicon) | **MODIFY now; ADD linear model later** | Errors are missing cues, boost overrides and taxonomy overlap. TF-IDF + logistic regression only when ≥ 500 labels exist and only if it beats the lexicon on a blind split. No transformer: the data is too small, and explanations are needed |
| Quantity / attribute extraction | **KEEP** | 96–97% F1 |
| Entity and edition resolution | **KEEP** | 100%; extend tests only |
| BM25 | **KEEP** | Best standard-level R@1 on heldout and the benchmark |
| Thesaurus expansion | **KEEP OFF** | Worse or equal on every split |
| Re-ranker | **MODIFY** | Wins clause R@1 but loses standard R@1; all standard misses trace to the parameter features |
| Dense embeddings / cross-encoder | **DO NOT ADD (now)** | Every miss has gold at BM25 rank 1–2; the corpus is 90 clauses. Revisit when a larger corpus shows paraphrase recall failures on heldout2 |
| Relation extractor | **MODIFY (low priority)** | Not on the runtime path; align the convention first |
| Curated graph + traversal | **KEEP** | Runtime source of truth |
| Conflict detector (interval logic) | **KEEP logic; MODIFY inputs** | All benchmark conflict false positives come from mappings, not arithmetic |
| Gap detector | **MODIFY** | Scope checklists; vague lexicon |
| Dependency detector | **MODIFY (first)** | Citation-based "addressed" |
| Version detector | **MODIFY (small)** | Amendment de-duplication |
| Certification detector | **KEEP** | 100% on heldout and the benchmark after the ISI-mark fix |
| Template repairs | **KEEP; ADD evaluation** | No repair metric exists |
| LLM repair wording (Claude `claude-opus-5`) | **KEEP optional, off** | No evaluation yet; enable only after 3.7 |
| Readiness score | **KEEP (heuristic)** | Label it as such; calibrate later |

**Replacement cards** for the components marked MODIFY or ADD:

- **Classifier**
  - CURRENT: weighted cue lexicon.
  - PROBLEM: benchmark macro-F1 67.6%; 5/12 eval errors have no cues; boosts override meaning.
  - PROPOSED: fix the lexicon and boosts first; later ensemble with TF-IDF + logistic regression.
  - WHY: errors are coverage and taxonomy, which cheap fixes address; linear models are explainable and trainable on hundreds of labels.
  - EXPECTED: ≥ 75% benchmark macro-F1 from lexicon repairs alone.
  - EVAL: dev/test/benchmark before and after, heldout2 once, per-class F1 with confidence intervals.
- **Re-ranker**
  - CURRENT: linear features with hand-set weights.
  - PROBLEM: overturns correct BM25 rankings (q17, q29, h15).
  - PROPOSED: role-based `test_method` credit and a near-tie gate.
  - WHY: the ablation shows BM25 is the better standard ranker.
  - EXPECTED: standard R@1 ≥ BM25 while keeping the clause R@1 gain.
  - EVAL: all 4 ablations + benchmark 50 + heldout2 + the document-context variant.
- **Dependency detector**
  - CURRENT: retrieval ≥ 0.5 counts as addressed.
  - PROBLEM: t1 and b1 misses.
  - PROPOSED: citation-based addressing.
  - WHY: normative parts must be cited in procurement.
  - EXPECTED: recall up, with precision held by 3.2.
  - EVAL: dependency P/R on dev, test, benchmark and heldout2; t1 reported separately as contaminated.

## I. Evaluation plan

1. **Freeze a new blind split** (P0.3) before any Phase 1–3 change, and score it **once** per phase release, never during development. Existing `heldout` is scored and reported but no longer used as a decision signal for dependency (t1 is now a known item).
2. **Every change** runs:
   - `eval.run all`
   - `benchmark.run` (TXT/PDF/DOCX)
   - both pytest suites
   - `compare.py` against the previous versioned run

   The PR must include the delta table and the per-item fixed/broken list.
3. **Metrics per change:**
   - identification P/R/F1
   - classification accuracy and macro-F1, plus per-class F1
   - attribute F1
   - standard and clause R@1/R@3/MRR/nDCG@5 for all ablations and the document-context variant
   - resolution / edition accuracy
   - relation typed F1
   - graph typed P/R (aligned convention)
   - findings P/R/F1 per detector group
   - benchmark findings per document
   - latency
   - bootstrap 95% confidence intervals
4. **Acceptance:** no regression beyond the confidence interval on any headline metric on dev/test/benchmark; a stated target met; the blind split reported with the result as-is.
5. **Versioning:** pipeline version bump per behavioural change (component versions in `version.py`); corpus version recorded; results stored under `results/<pipeline>/<corpus>/`. `first-run.*` and `heldout-first-run.md` are immutable.
6. **Contamination log:** `aiml/eval/CONTAMINATION.md` lists every dataset item that has been inspected while making a change (starting with t1, h15, y11, all dev/test, and benchmark b1–b6 via the ISI-mark fix).

---

## What exactly should we build next?

1. **Phase 0 infrastructure** (versioned results, `compare.py`, bootstrap confidence intervals, a new blind `heldout2` split written before any change):
   - `aiml/eval/run.py`
   - `aiml/benchmark/run.py`
   - new `aiml/eval/compare.py`
   - new `aiml/eval/datasets/*_heldout2.json`
   - new `aiml/eval/CONTAMINATION.md`
2. **Dependency fix** (Phase 3.1): make "addressed" citation-based:
   - `aiml/standardos_aiml/reasoning/dependencies.py` (`_addressed_standards`, `dependency_gaps`)
   - `aiml/standardos_aiml/reasoning/context.py` (cited vs retrieved in `Applicability`)
   - the applicability block in `aiml/standardos_aiml/pipeline.py`
3. **Detector input gating** (3.2 + 2.3), which removes most benchmark false positives:
   - `reasoning/conflicts.py::_candidate_standards`
   - `reasoning/gaps.py::checklist_gaps`
   - `standards/retrieval.py` (scope check / cited-standard preference)
4. **Then Phase 1:** zoning and headings (`ingest/sections.py`, `nlp/requirements.py`), and lexicon/boost repair (`nlp/classify.py`, `nlp/units.py`).
5. **Then Phase 2.1:** re-ranker features (`standards/retrieval.py`).


---

## Addendum (2026-09-24): pipeline 3.0.0 results

All fixes in this audit sit behind `PipelineConfig` flags. The `legacy-2.1` preset reproduces 2.1.0 exactly. Official runs are in `aiml/results/runs/20260924-0353*`, and paired-bootstrap comparisons are in `aiml/results/comparisons/`.

**Findings F1 (TXT), legacy-2.1 → v3:**

| Split | Role | Before | After |
| --- | --- | --- | --- |
| realworld_v2/dev | open | 73.0 | 96.3 |
| realworld_v2/test | blind | 49.6 | 67.7 |
| tenders_v1 | contaminated | 78.0 | 84.8 |
| component/heldout | blind | 93.3 | 100.0 |
| component/test | contaminated | 100.0 | 92.3 |

**Known trade-offs:**
- component/test s5: v3 flags the missing conductor size and material for the control cable. That is arguably correct, but the gold does not expect it.
- tenders_v1 certification (3 FP): v3 asks for conformity evidence per product. The tenders_v1 gold treats one document-level evidence clause as covering every product. The two conventions conflict, and the per-product check is the `certification_scope` flag.
- Blind realworld_v2/test findings precision is 53.8 against 100 on dev. The rules still overfit the dev paraphrases, and this is the largest open gap.

**Dependency DAG:** 33 nodes, 20 normative edges, acyclic, depth 1, no transitive-only obligations.
- `v3-dag` gives the same findings as `v3` on every split. On this corpus the DAG adds no detection power.
- It is kept for structure checks (cycles, supersession contraction), for the dependency view in the API and UI, and for change impact. Ancestors let a revision of IS 269 reach specifications that cite only IS 456.

**Requirement classifiers** (`aiml/results/classifiers/`): trained on open splits only and tested on wording the models never saw. Macro-F1:

| Test set | lexicon | tfidf-lr | embed-lr | hybrid-nn | gated |
| --- | --- | --- | --- | --- | --- |
| realworld_v2/test | 83.1 | 86.2 | 89.2 | 90.9 | 86.6 |
| tenders_v1 | 76.5 | 80.3 | 78.7 | 83.7 | 79.5 |
| component/test | 76.0 | 43.9 | 41.8 | 51.3 | 70.6 |
| component/heldout | 100 | 56.5 | 63.8 | 82.1 | 94.0 |

- On the two larger sets the hybrid network is best. On the small component sets (22 and 12 items) it is worse, and the lexicon wins there.
- The category does not change any finding: findings are identical across classifier presets.
- The default therefore stays `lexicon`: it is interpretable and needs no extra dependencies. `v3-gated` is the recommended opt-in.
