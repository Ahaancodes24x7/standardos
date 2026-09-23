# StandardOS intelligence layer — design, status and evaluation

This document describes the backend and AI/ML implementation of roadmap
Phases 1–3: what was built, why each technology was chosen, what is **not**
built yet, and how the system is evaluated. Current metrics are in
[`aiml/eval/results/latest.md`](../aiml/eval/results/latest.md) (components) and
[`aiml/benchmark/results/latest.md`](../aiml/benchmark/results/latest.md) (whole tender-realistic
specifications). Dataset construction and caveats are in [`aiml/eval/README.md`](../aiml/eval/README.md)
and [`aiml/benchmark/README.md`](../aiml/benchmark/README.md).

> StandardOS is decision support. It proposes findings and repairs with evidence.
> A person reviews them and the system records the decision. It never declares
> a specification compliant.

---

## 1. Constraints that shaped the design

| Constraint | Consequence |
| --- | --- |
| **No licensed standards text.** The README's governance section rules out scraping or redistributing BIS content. | The corpus is curated *metadata* (designation, edition, status, supersession, typed relationships) plus short **paraphrased** clause summaries and machine-readable limits. Every record is marked `verified: false`. |
| **Small corpus.** Tens of standards now, low thousands of clauses at most in the foreseeable future. | Retrieval and graph queries run in memory. There is no vector database and no graph database. |
| **Numbers decide compliance.** A 120 °C requirement against a 40 °C limit, or M20 against a minimum of M30. | Extraction of values, units and ranges is deterministic and unit-normalised. Language models are not trusted with numbers. |
| **Every conclusion must be traceable.** | Each derived object carries `Provenance` (component, version, method, confidence, signals). Each finding carries `Evidence` (requirement span, clause, graph path, interval check, version record). |
| **Stack.** TanStack Start frontend; Python for AI/ML; Postgres. | The engine is a Python package (`aiml/standardos_aiml`) with no web or database imports. A FastAPI service (`backend/`) owns persistence, auth and jobs; the frontend reaches it through a same-origin `/api` gateway route. Jobs are queued in Postgres. |
| **No labelled training data.** | Rules and lexicons are transparent and testable, and are measured on a small gold set. Learned components are future work, gated on data (§6). |

**Migration note (v2.0).** The engine, API and schema were first built in TypeScript
(TanStack Start server functions + Drizzle). They were ported to Python (engine) and
FastAPI + SQLAlchemy + Alembic (API) with the same database schema, JSON contract and
behaviour: on every eval dataset the Python engine reproduces the TypeScript report
exactly, and a field-by-field diff over 24 documents and all retrieval/resolution/relation
cases differed only in the order of two exactly-tied clauses at ranks 4–8 (floating-point
noise in `log`). Password hashes use the same scrypt format, so existing accounts keep working.

---

## 2. Pipeline

```
PDF / DOCX / TXT / pasted text
  └─ ingest/parse        pypdf · mammoth · UTF-8/Windows-1252 decoding
  └─ ingest/normalize    NFKC, symbol folding, dehyphenation, line reflow, header/footer removal
  └─ ingest/sections     numbered clauses, labelled/uppercase headings
  └─ nlp/requirements    segmentation → deontic/attribute-line identification
  └─ nlp/classify        weighted cue lexicon + entity/dimension evidence
  └─ nlp/quantities      numbers, units → canonical, ranges, tolerances, comparators
  └─ nlp/entities        IS/IEC designations, IP codes, concrete/steel grades, IE class, materials
  = StructuredRequirement[]                                    (Phase 1)
  └─ standards/resolve   citation → corpus record, edition = current|older|newer|unspecified
  └─ standards/retrieval fielded BM25 over clauses → feature re-ranker
  └─ standards/graph     supersession chains, REQUIRES/TESTED_BY dependencies, evidence graph
  = RequirementMapping[] + AnalysisGraph                       (Phase 2)
  └─ reasoning/conflicts     interval checks vs clause limits; internal consistency; edition conflicts
  └─ reasoning/gaps          purchaser-checklist gaps; vague/unmeasurable requirements
  └─ reasoning/dependencies  A REQUIRES/TESTED_BY B not addressed
  └─ reasoning/versions      superseded standard, superseded edition, newer edition, amendments
  └─ reasoning/certification conformity evidence for product standards
  └─ reasoning/verification  positive evidence: limits satisfied, current references
  └─ reasoning/repair        evidence-grounded templates (+ optional guarded LLM wording)
  = ReasoningFinding[] + RepairProposal[] + readiness          (Phase 3)
```

The engine (`aiml/standardos_aiml/**`) is pure Python with no database, network or
framework imports. The server, the evaluation harness and the tests all run the
same code. A typical specification takes 2–5 ms end to end, excluding PDF parsing.

### 2.1 Technology decisions

| Decision | Chosen | Alternatives considered and why not (for now) |
| --- | --- | --- |
| PDF parsing | **pypdf** (pure Python, BSD) | PyMuPDF extracts layout better but is AGPL; Poppler or Tika need native binaries or a JVM. |
| DOCX parsing | **mammoth** (semantic HTML → lines; two-column tables → `Parameter: Value`) | Raw-text extraction loses table structure, and procurement data sheets are mostly tables. |
| OCR | **Not implemented.** Scanned PDFs are detected (fewer than 40 chars/page) and rejected with a clear message. | tesseract.js adds seconds per page and about 20 MB of language data per function, and its error rate on numbers would silently corrupt constraint checks. Future: a separate OCR worker whose output is flagged low-confidence. |
| Requirement identification | **Rules** for deontic modality ("shall", "must", "should"), attribute lines ("Voltage: 415 V"), conformity statements, and short value fragments | No labelled corpus to train on. Rules are auditable, and each extraction records the cue that fired. An LLM extractor would be slower, cost money per page, and still need this validation. |
| Classification | **Weighted cue lexicon** + dimension/entity evidence; confidence from the margin between the top two scores | Same data constraint. This is the weakest component (§5); a trained classifier is the first learned model to add once reviewer labels exist. |
| Values and units | **Deterministic parser** with a canonical-unit table (kV→V, sq mm→mm², N/mm²→MPa, lps→m³/h, °F→°C) and interval semantics | Constraint checks must be exact and explainable. |
| Retrieval | **Fielded BM25** over clause documents (clause text, heading, standard title, keywords, scope, designation) + **feature re-ranker** | Dense embeddings (hosted or local ONNX) add latency, cold-start cost and model hosting, and with 90 clauses across 39 standards the technical vocabulary is highly lexical. The ablation (§5) shows BM25 is already strong. Adopt embeddings only if paraphrase recall falls as the corpus grows. |
| Query expansion | Domain thesaurus implemented but **off by default** | It lowered R@1 on every split (dev −4 pts, held-out −13 pts). Kept as an option for experiments. |
| Re-ranker | Linear combination of six interpretable features (normalised BM25, clause-parameter match, standard-parameter match, product-in-scope, document-context product, standard cited elsewhere in the document) plus penalties (superseded, test-method for non-test requirements, out-of-domain) | A cross-encoder needs a model server and training pairs. The linear model's features appear in each hit's provenance as the "why this was recommended" text. |
| Entity resolution | Designation canonicalisation → exact/alias → IEC→IS/IEC adoption → family fallback (drop section/part, or add Part 1 when a citation omits the part); edition comparison against prior-edition records | — |
| Relationship extraction | Cue-phrase rules over the text window before each reference (conformity → REQUIRES, test/analyse/verify → TESTED_BY, replace/covered by → SUPERSEDES, amendment → AMENDED_BY, see also → RELATED_TO), with coordination inheritance | Used both to build graph edges from clause text and to link requirement text to standards. |
| Graph storage | **Postgres tables** (`standard_relationships`, typed edges with clause, confidence and method) + in-memory adjacency lists | Neo4j or another graph DB is another service to run, and every query here is a bounded traversal (depth ≤ 3) from a few seeds. |
| Reasoning | **Interval arithmetic** over canonical units, qualifier-aware constraints (e.g. IS 456 limits by exposure condition), purchaser checklists, graph traversal | Logic solvers or LLM reasoning add opacity without adding capability at this scale. |
| LLM | **Claude (`claude-opus-5`), optional, repair wording only**, off by default (`STANDARDOS_LLM_REPAIR=on`). Structured JSON output; each rewrite passes `validateRewrite()` (all numbers, designations and placeholders preserved, nothing added) or the template is kept. | Wording is the one place where language quality matters more than determinism. No detection depends on the LLM. |
| Jobs | **Postgres-backed runs** with atomic claim (`queued → running`), stage heartbeat, and a cron sweeper that re-queues stalled runs (max 3 attempts) | Redis/BullMQ would add a broker; serverless functions can't host long-lived workers. |
| Tests | **pytest** (engine, eval gate, API integration against Postgres); headless-browser walk-through for the UI | — |

---

## 3. Data model (Postgres, `backend/app/models.py`, migrations in `backend/alembic/`)

| Table | Contents |
| --- | --- |
| `documents` | Owner, name, format, SHA-256, original bytes (for reproducible re-runs) |
| `analysis_runs` | Status, stage, attempts, heartbeat, pipeline version, corpus version and source, LLM model, parser, extracted text, warnings, readiness + formula inputs, applicable standards, evidence graph, per-stage timings |
| `requirements` | Text, span, page, section label, modality, category + scores, attributes, quantities, references, entities, terms, vagueness, provenance |
| `requirement_standard_links` | Ranked requirement → standard/clause hits with score, confidence, basis, explanation, provenance |
| `standards`, `standard_clauses` | Corpus records, paraphrased clauses, machine-readable constraints, purchaser checklists, source/verification |
| `standard_relationships` | Typed edges (REFERENCES, REQUIRES, TESTED_BY, SUPERSEDES, AMENDED_BY, RELATED_TO, SUPPORTS) with clause, confidence, method |
| `standard_version_events`, `standard_prior_editions`, `corpus_versions` | Amendments, revisions, supersessions (dates only where verified), earlier editions, active corpus version |
| `findings`, `evidence` | Finding with rule, parameter, reason, action, provenance and review state; ordered evidence items with spans and graph-edge ids |
| `repairs` | Proposal, provenance, decision (pending/accepted/rejected/edited), final text, decided by/at |
| `audit_events` | Append-only log: upload, queue, run success/failure, review decisions and repair decisions, with before/after state |

---

## 4. API (FastAPI, `backend/app/routers/`; OpenAPI docs at `/api/docs`)

| Area | Endpoint | Notes |
| --- | --- | --- |
| Accounts | `GET /api/auth/me`, `POST /api/auth/signup`, `/signin`, `/signout`, `PATCH /api/auth/profile`, `POST /api/auth/password`, `/password-reset/request`, `/password-reset/confirm` | Signed HTTP-only session cookie |
| Ingestion | `POST /api/analyses` (multipart: file or text) | Validates type and size, stores the original, queues a run and executes it as a background task |
| Orchestration | `GET /api/runs/{id}`, `POST /api/runs/{id}/execute`, `POST /api/documents/{id}/reanalyze`, `GET /api/cron/analysis-sweeper` | The client polls stage progress (1–8); execution claims runs atomically |
| Results | `GET /api/documents` (`?summary=true`), `GET /api/documents/{id}` | Return the frontend contract in `src/lib/contracts.ts` |
| Findings / gaps / conflicts | `GET /api/findings?kind=&severity=&reviewStatus=&documentId=` | `kind=missing` is the gap API; `kind=conflicting` the conflict API |
| Evidence | `GET /api/findings/{id}` | Finding with evidence and provenance |
| Human review | `POST /api/findings/{id}/review`, `POST /api/repairs/{id}/decision` | Every decision is written to `audit_events` |
| Audit / report | `GET /api/documents/{id}/audit`, `GET /api/documents/{id}/report` | Markdown report with evidence, provenance and decisions |
| Standards | `GET /api/standards`, `GET /api/standards/{id}`, `POST /api/standards/search`, `GET /api/standards/{id}/graph`, `GET /api/corpus/status` | Public |
| Change impact | `GET /api/change-impact?scope=workspace|sample` | Version events → affected analysed documents |
| Demo | `GET /api/samples`, `POST /api/analyze/stateless` | Real pipeline, nothing persisted (demo mode has no account) |
| Health | `GET /api/health` | Pipeline and corpus versions, corpus source |

The frontend contract keeps the original `Finding`, `Requirement`, `Repair`,
`ProcurementDocument`, `Standard` and `SearchResult` shapes. New fields
(evidence, provenance, review state, counts, graph paths) are optional additions.

---

## 5. Evaluation summary

Run `bun run eval` (`cd aiml && uv run python -m eval.run all --verbose`). The regression gate is
`aiml/tests/test_eval_gate.py`. Datasets are small and author-labelled; read `aiml/eval/README.md`
before quoting any number. Whole-document results on six tender-realistic specifications
(TXT, PDF and DOCX) are in `aiml/benchmark/results/latest.md` (`bun run benchmark`).

Held-out split (written after tuning, scored once):

| Task | Metric | Held-out |
| --- | --- | --- |
| Requirement identification | F1 | 1.00 (2 docs, 12 requirements) |
| Requirement classification | accuracy | 0.92 |
| Attribute extraction | F1 | 1.00 |
| Standard retrieval (default) | R@1 / R@3 / MRR | 0.93 / 1.00 / 0.96 (15 queries) |
| Clause retrieval (default) | R@1 / R@3 | 0.93 / 1.00 |
| Entity resolution | accuracy (id / edition) | 1.00 / 1.00 (8 cases) |
| Relationship extraction | typed F1 | 0.94 (12 sentences) |
| Compliance reasoning | P / R | 1.00 / 0.88 (3 specs, 8 gold findings) |

Across all splits, the weakest component is **requirement classification**
(~79% accuracy, macro-F1 ~0.77). Graph construction from clause text reaches
78% typed-edge precision and 81% recall against the text-supported curated edges.

**Ablation findings:**
- BM25 alone is a strong baseline for standard-level R@1 on isolated queries.
- The thesaurus hurts on every split.
- The re-ranker's gains show at clause level (held-out clause R@1 0.80 → 0.93) and in document-level features (context product, cited-elsewhere) that single-query evaluation does not exercise.

### 5.1 Verification beyond the metrics

- `uv run pytest aiml/tests`: unit and pipeline tests for parsing (generated PDF and DOCX fixtures, scanned-PDF rejection, encodings), NLP, resolution, retrieval, relations, graph, reasoning, the LLM-rewrite guard, provenance and evidence invariants, plus the evaluation regression gate.
- `TEST_DATABASE_URL=… uv run pytest backend/tests`: API and persistence against a real PostgreSQL 16 (Alembic migration, corpus import/load, sign-up/sign-in/password reset, upload → background run → reload, idempotent run execution, review/repair decisions in the audit trail, compliance report, owner isolation, PDF/DOCX success and scanned-PDF failure, re-runs, demo endpoints, sweeper).
- A browser walk-through (headless Edge) against the dev server covered sign-up → paste specification → staged progress → results → evidence dialog → confirm finding → accept repair → documents, compliance, change impact, standards and search, plus the demo workspace. It surfaced and fixed a pre-existing routing bug: `/analyze/$id` and `/documents/$id` were nested under parent pages without an `<Outlet/>`, so result and detail pages never rendered. The parents are now index routes.

---

## 6. Implemented vs. future

**Implemented (Phases 1–3):** everything in §2–§4. That includes persistent
documents, runs, requirements, mappings, findings, evidence, repairs and audit;
the standards database with typed relationships, versions and graph queries; conflict,
gap, dependency, version and certification reasoning; evidence-grounded repairs;
human review; the compliance report; change impact; and the evaluation harness with ablations.

**Not implemented — future or research work:**

| Item | Status / trigger |
| --- | --- |
| OCR for scanned PDFs | Detected and rejected today. Needs a worker outside the request path and confidence propagation to extracted numbers. |
| Licensed standards content | The corpus is unverified seed metadata. An import path exists (`import_corpus`, `bun run db:seed` / `backend/scripts/seed_standards.py`); an in-app upload/admin workflow does not. |
| Dense / hybrid retrieval | Revisit when the corpus exceeds a few thousand clauses or paraphrase recall on a larger eval set drops. |
| Learned classifier / extractor | Needs reviewer-labelled data. Review decisions are already recorded in `audit_events`, which is where the labels would come from. |
| Learning from review (ranking, relationship confidence) | Not implemented; decisions are stored but not fed back. |
| Hindi / multilingual processing | Not implemented; the search page says so when Hindi is selected. |
| QCO (mandatory certification) tracking | Not modelled; certification findings ask the purchaser to confirm. |
| Standards change monitoring | Change impact is computed from recorded version events; nothing polls BIS for new ones. |
| Object storage for uploads | Originals are stored in Postgres `bytea` (≤ 20 MB). Move to object storage at scale. |
| Upload size on Vercel | The app accepts 20 MB, but Vercel Functions cap request bodies at about 4.5 MB. Larger files need direct-to-storage upload. |
| Per-page / table-aware PDF structure | Text order follows pdf.js; complex multi-column tables may interleave. |

---

## 7. Confidence semantics

| Object | Confidence |
| --- | --- |
| Requirement | Rule strength: 0.95 mandatory with a value or reference, 0.85 mandatory, 0.8 attribute line, 0.75 recommended or conformity line, 0.6 value fragment, 0.55 permissive with a value |
| Classification | 0.5 + 0.5 × (top − second) / top over cue scores |
| Resolution | 0.98 exact/alias, 0.9 IEC→IS/IEC, 0.8 unique part, 0.7 section dropped, 0.6 part dropped or Part 1 assumed |
| Retrieval hit | Re-ranker score normalised to [0, 1] (explicit citation adds 0.6 before clamping) |
| Findings | Detector-specific: 0.9 disjoint interval, 0.75 partial, 0.7–0.85 gap/dependency/version (dependency ≤ edge confidence) |

These scores are **not calibrated probabilities**. Calibrating them against
reviewer decisions is future work.

Readiness = `round(clamp(100 × mapped/total − (8·high + 3·medium + 1·low open findings), 0, 100))`,
a triage heuristic, stored with its inputs on each run.
