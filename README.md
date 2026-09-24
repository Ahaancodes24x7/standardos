# STANDARDOS

<div align="center">

### From Specifications to Certainty.

**AI-powered Standards & Procurement Intelligence**

[![Status](https://img.shields.io/badge/Status-Prototype-orange)]()
[![Stack](https://img.shields.io/badge/Stack-TanStack%20Start%20%7C%20FastAPI%20%7C%20Python%20%7C%20Postgres-black)]()
[![AI](https://img.shields.io/badge/AI-NLP%20%7C%20Semantic%20Search-purple)]()

</div>

---

## Table of Contents

- [Overview](#overview)
- [The Problem](#the-problem)
- [Our Solution](#our-solution)
- [How STANDARDOS Works](#how-standardos-works)
- [Core Features](#core-features)
- [What Makes STANDARDOS Different](#what-makes-standardos-different)
- [System Architecture](#system-architecture)
- [AI Pipeline](#ai-pipeline)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running the Project](#running-the-project)
- [Example Workflow](#example-workflow)
- [Use Cases](#use-cases)
- [Innovation](#innovation)
- [Data & Standards Governance](#data--standards-governance)
- [Human-in-the-Loop](#human-in-the-loop)
- [Roadmap](#roadmap)
- [Future Scope](#future-scope)
- [Contributing](#contributing)
- [Disclaimer](#disclaimer)
- [License](#license)
- [Team](#team)

---

# Overview

**STANDARDOS** is an AI-powered procurement specification intelligence platform designed to help organizations understand, map, audit, and improve technical procurement specifications against relevant Indian Standards.

Procurement documents often contain requirements that are not independent.

A single product specification can depend on:

- Product standards
- Test methods
- Safety standards
- Installation standards
- Terminology standards
- Normative references
- Certification requirements
- Amendments and newer versions

STANDARDOS transforms these relationships into a structured intelligence workflow.

Instead of treating standards as isolated documents, STANDARDOS models them as a connected system:

```text
Requirements
     ↓
Indian Standards
     ↓
Normative References
     ↓
Testing
     ↓
Certification
     ↓
Compliance
The Problem

Technical procurement specifications are often created and reviewed manually.

A procurement officer may need to:

Understand the product requirements.
Identify applicable Indian Standards.
Search through related standards.
Inspect normative references.
Verify amendments and versions.
Identify certification requirements.
Check whether important requirements are missing.
Review the specification for technical inconsistencies.

This process becomes increasingly difficult when specifications involve multiple technical domains and interconnected standards.

The hidden problem

A procurement specification may look like:

Product
├── Technical Parameters
├── Safety Requirements
├── Testing Requirements
├── Environmental Requirements
└── Certification

But underneath it can actually represent:

Requirement
      ↓
Product Standard
      ↓
Normative Reference
      ↓
Test Method
      ↓
Safety Standard
      ↓
Certification Requirement

Missing one relationship can result in an incomplete specification.

Our Solution

STANDARDOS acts as an intelligent layer between procurement specifications and standards knowledge.

                 PROCUREMENT SPECIFICATION
                           │
                           ↓
                  Requirement Extraction
                           │
                           ↓
                    Standards Discovery
                           │
                           ↓
                 Standards Dependency Graph
                           │
                           ↓
                  Compliance Reasoning
                           │
             ┌─────────────┼─────────────┐
             ↓             ↓             ↓
        Gap Detection  Conflict Check  Version Check
             │             │             │
             └─────────────┼─────────────┘
                           ↓
                  Specification Repair
                           │
                           ↓
                  Evidence-backed Output

STANDARDOS is designed to move beyond simple document retrieval.

It attempts to understand:

What does the specification require?
Which standards apply?
What other standards are connected to them?
What requirements may be missing?
Are there potential conflicts?
Are referenced standards current?
What should a reviewer investigate?
How STANDARDOS Works

STANDARDOS follows a multi-stage intelligence pipeline.

1. Understand

The system receives a procurement specification, technical description, or tender document.

Example:

Industrial motor

Rated Power: 15 kW
Voltage: 415 V
Frequency: 50 Hz
Protection: IP55
Industrial environment
Safety compliance required
2. Parse

The document is processed to identify:

Technical parameters
Requirements
Product attributes
Existing standards
Certification references
Testing requirements
3. Extract Requirements

Natural-language requirements are converted into structured representations.

Example:

"Motor shall operate at 415V ±10%"

        ↓

Parameter:
operating_voltage

Value:
415

Tolerance:
±10%

Unit:
V
4. Discover Standards

The extracted requirements are matched against the available standards knowledge base using semantic retrieval.

The system can consider:

Product terminology
Technical attributes
Application domain
Requirement semantics
Existing standard references
5. Build the Standards Graph

Relevant standards are represented as interconnected entities.

                    Product Standard
                           │
            ┌──────────────┼──────────────┐
            ↓              ↓              ↓
      Test Standard   Safety Standard   Terminology
            │              │
            ↓              ↓
      Test Evidence   Certification

This allows STANDARDOS to reason about relationships rather than treating every standard as an isolated search result.

6. Reason

The reasoning layer evaluates relationships between:

Requirements
Standards
Normative references
Tests
Certifications
Versions
Constraints
7. Audit

The system can identify areas requiring review.

Examples:

Potential Missing Requirement
Potential Standards Conflict
Potential Outdated Reference
Missing Supporting Test Reference
Certification Review Required
8. Repair

STANDARDOS can generate a structured recommendation for improving the specification.

Original Requirement
        ↓
Detected Issue
        ↓
Applicable Standard
        ↓
Supporting Reference
        ↓
Suggested Revision
        ↓
Reason / Evidence
Core Features
🔎 Semantic Standards Discovery

Find potentially relevant Indian Standards from natural-language procurement requirements.

Instead of requiring exact standard numbers or keywords, STANDARDOS uses semantic understanding to connect technical requirements with relevant standards.

🧩 Requirement Graph

Break complex specifications into atomic requirements.

Example:

Industrial Motor
│
├── Rated Power
├── Voltage
├── Frequency
├── Efficiency
├── Protection Rating
├── Temperature
├── Safety
└── Testing

Each requirement can then be mapped to relevant standards and references.

🕸️ Standards Dependency Graph

Model relationships between standards.

The graph can represent:

Standard
   │
   ├── references
   ├── tested-by
   ├── depends-on
   ├── supports
   ├── supersedes
   ├── amended-by
   └── requires

This enables deeper standards intelligence.

⚠️ Standards Collision Detection

Identify potential conflicts between procurement requirements and standards.

Example:

Tender Requirement
        │
        ↓
Operating Temperature: 120°C
        │
        ↓
Referenced Standard
        │
        ↓
Compatibility Check
        │
        ↓
Potential Conflict

The result is surfaced for human review.

🕳️ Missing Requirement Detection

STANDARDOS can identify potentially missing supporting elements.

Examples:

Test methods
Safety references
Installation requirements
Certification requirements
Normative references
Technical parameters
🔄 Version & Amendment Intelligence

Standards can change over time.

STANDARDOS is designed to track relationships such as:

Old Version
     ↓
Amendment
     ↓
Updated Version
     ↓
Affected Specification

This helps identify procurement documents that may require review.

🛠️ Specification Repair

Instead of only reporting an issue, STANDARDOS can generate a structured proposal for review.

Example:

Issue:
Missing supporting test requirement

Related Standard:
IS XXXXX

Suggested Action:
Add the relevant test reference to the specification.

Reason:
The requirement depends on the associated test methodology.
📋 Compliance Intelligence

STANDARDOS can organize information related to:

Applicable standards
Certification
Testing
Safety
Normative references
Version information

The objective is to make technical review more structured and traceable.

What Makes STANDARDOS Different?

STANDARDOS is intentionally designed not to be just another:

PDF
 ↓
Vector Database
 ↓
RAG
 ↓
Chatbot

A conventional standards assistant might work like:

Question
   ↓
Search
   ↓
Retrieve Documents
   ↓
LLM
   ↓
Answer

STANDARDOS introduces an additional reasoning layer:

Tender
  ↓
Requirement Graph
  ↓
Standards Graph
  ↓
Normative Dependencies
  ↓
Constraint Reasoning
  ↓
Gap Detection
  ↓
Conflict Detection
  ↓
Version Analysis
  ↓
Specification Repair
Core innovation

STANDARDOS treats a procurement specification as a dependency graph rather than a document.

The objective is to move from:

Search → Answer

toward:

Understand → Connect → Reason → Audit → Repair

System Architecture
┌─────────────────────────────────────────────┐
│              STANDARDOS FRONTEND             │
│           TanStack Start (React)            │
└──────────────────────┬──────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────┐
│                 API LAYER                    │
│      FastAPI (Python) + PostgreSQL          │
└──────────────────────┬──────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Requirement  │ │  Semantic    │ │ Standards    │
│ Extraction   │ │  Retrieval   │ │ Knowledge    │
│              │ │              │ │ Graph        │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────────────┼────────────────┘
                        ↓
              ┌──────────────────┐
              │ Reasoning Engine │
              │                  │
              │ Rules            │
              │ Constraints      │
              │ Relationships    │
              └────────┬─────────┘
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Gap          │ │ Conflict     │ │ Version      │
│ Detection    │ │ Detection    │ │ Intelligence │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────────────┼────────────────┘
                        ↓
              ┌──────────────────┐
              │ Specification    │
              │ Repair Engine    │
              └────────┬─────────┘
                       ↓
              ┌──────────────────┐
              │ Explainable      │
              │ Output           │
              └──────────────────┘
AI Pipeline
                 INPUT DOCUMENT
                       │
                       ↓
              Document Processing
                       │
                       ↓
            Requirement Extraction
                       │
                       ↓
             Semantic Representation
                       │
                       ↓
              Standards Retrieval
                       │
                       ↓
             Graph Construction
                       │
                       ↓
             Relationship Analysis
                       │
                       ↓
              Constraint Reasoning
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
        Gaps       Conflicts     Versions
          │            │            │
          └────────────┼────────────┘
                       ↓
                Human Review
                       │
                       ↓
             Specification Repair
Technology Stack

What this repository actually contains. The design rationale for each choice, and what is not built yet, are in [docs/INTELLIGENCE.md](docs/INTELLIGENCE.md).

| Layer | Technology |
| --- | --- |
| Frontend | TanStack Start (React 19, file-based routing, SSR), Tailwind CSS, Radix UI. `/api/*` is forwarded to FastAPI by a gateway route, so the browser uses a single origin. |
| Backend API | **FastAPI** (Python 3.12) in `backend/`: auth (signed HTTP-only session cookie, scrypt hashes), uploads, analysis runs, review/repair decisions, audit trail, standards search and graph, change impact |
| Database | **PostgreSQL** via SQLAlchemy 2 + psycopg 3; schema migrations with **Alembic** (documents, runs, requirements, standards graph, findings, evidence, repairs, audit trail) |
| Jobs | Postgres-backed run queue: FastAPI background task executes the run, atomic claim, stage heartbeat, cron sweeper re-queues stalled runs |
| AI/ML engine | **Python package `standardos_aiml`** in `aiml/`, no web or database dependencies |
| Document parsing | pypdf for PDF, mammoth for DOCX, UTF-8/Windows-1252 for TXT. OCR is not implemented. |
| NLP | Deterministic requirement identification, unit-normalised quantity parsing, entity and standard-reference extraction, lexicon classification |
| Retrieval | Fielded BM25 over standard clauses + interpretable feature re-ranker (in-memory) |
| Knowledge graph | Typed relationships in Postgres + in-memory traversal (supersession, REQUIRES, TESTED_BY, …) |
| Reasoning | Interval constraint checks, purchaser checklists, dependency/version/certification rules, evidence-grounded repair templates |
| LLM (optional) | Claude (`claude-opus-5`) for repair wording only, off by default, with every rewrite checked for changed facts |
| Tests / evaluation | pytest (engine unit tests, eval regression gate, API integration tests on Postgres); gold datasets in `aiml/eval/`; tender-realistic benchmark in `aiml/benchmark/` |

Project Structure

```text
aiml/                      AI/ML engine (Python)
  standardos_aiml/           ingest/ nlp/ standards/ reasoning/ pipeline.py llm_repair.py
  standardos_aiml/standards/data/seed_corpus.json   curated standards corpus (seed)
  eval/                      gold datasets, harness (python -m eval.run), results
  benchmark/                 6 tender-realistic specs + 50 queries, runner, results
  tests/                     unit tests + evaluation regression gate
backend/                   FastAPI service (Python)
  app/                       main.py, routers/, models.py, store.py (runs/persistence), view.py, corpus.py, security.py
  alembic/                   migrations (baseline = the previous Drizzle schema)
  scripts/seed_standards.py  load the standards corpus into Postgres
  tests/                     API integration tests against Postgres
src/                       Frontend (TanStack Start)
  routes/                    pages, plus routes/api/$.ts (gateway to FastAPI)
  services/                  analysis.ts, auth.ts — the only modules that call the API
  lib/                       api.ts (HTTP client), contracts.ts (API types), report.ts
  components/                UI
pyproject.toml             uv workspace (aiml + backend)
docs/INTELLIGENCE.md       Architecture, decisions, implemented vs. future work
```

Installation

Prerequisites: [uv](https://docs.astral.sh/uv/) (Python 3.12+), Bun 1.2+, Node.js 22+, PostgreSQL 14+.

```bash
uv sync --all-packages --all-extras   # Python: engine + API (+ dev tools) into .venv
bun install                           # Frontend
cp .env.example .env                  # set DATABASE_URL and SESSION_SECRET
bun run db:migrate                    # alembic upgrade head (adopts an existing Drizzle-created schema)
bun run db:seed                       # load the standards corpus
```

Environment Variables

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Postgres connection string (required for accounts and saved analyses) |
| `DATABASE_POOL_MAX` | Optional max connections per API process |
| `DB_MIGRATION_URL` | Optional direct connection for Alembic; **takes precedence over `DATABASE_URL` for migrations** |
| `SESSION_SECRET` | 32+ random characters to sign the session cookie (required) |
| `SESSION_COOKIE_SECURE` | `true` when served over HTTPS |
| `CRON_SECRET` | Bearer token for `GET /api/cron/analysis-sweeper` |
| `STANDARDOS_LLM_REPAIR` | `on` enables optional LLM wording of repairs (default off) |
| `ANTHROPIC_API_KEY` | Credentials for the above |
| `API_INTERNAL_URL` | Where the frontend gateway and SSR reach FastAPI (default `http://127.0.0.1:8000`) |
| `VITE_API_URL` | Optional: browser calls a separately hosted API directly (then set `CORS_ORIGINS`) |

Do not commit .env files or API keys.

Running the Project

```bash
bun run api:dev             # FastAPI on :8000 (docs at http://localhost:8000/api/docs)
bun run dev                 # frontend on :3000 (its /api/* is forwarded to FastAPI)
bun run test                # pytest: engine, eval gate, API integration (needs TEST_DATABASE_URL)
bun run eval                # versioned evaluation run (open splits) → aiml/results/runs/<id>/report.md
bun run build:vercel-api    # refresh deploy/vercel-api after changing backend/app or aiml/
bun run build && bun run preview
```

API integration tests run against a real Postgres named by `TEST_DATABASE_URL` and are skipped without it; never point it at a database you want to keep. Without a database the demo workspace ("Explore demo") still works: it runs the real pipeline and saves nothing.

Any procurement document can be analysed and kept in the workspace: technical specifications, tenders, bills of quantities, vendor datasheets, test and inspection reports, or a document type you name yourself.

**Deploying:** see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md). It uses two Vercel projects: the web app at the repository root and the API in `deploy/vercel-api`.

Current results (pipeline 3.1.0, preset `v3.1`; findings F1 on TXT; details in [aiml/results/INDEX.md](aiml/results/INDEX.md) and [docs/PIPELINE_AUDIT.md](docs/PIPELINE_AUDIT.md)):

| Dataset / split | Role | Findings F1 | Requirement ID F1 |
| --- | --- | --- | --- |
| realworld_v2 / test (18 tenders, unseen wording) | blind | 81.5 | 99.6 |
| realworld_v2 / dev2 (12 tenders, independent wording) | open | 98.4 | 100.0 |
| realworld_v2 / dev (12 tenders) | open | 96.3 | 99.9 |
| tenders_v1 (6 hand-written tenders, v1.1 gold) | contaminated | 100.0 | 98.0 |
| component / heldout | blind | 100.0 | 100.0 |

Example Workflow](#example-workflow)
- [Use Cases](#use-cases)
- [Innovation](#innovation)
- [Data & Standards Governance](#data--standards-governance)
- [Human-in-the-Loop](#human-in-the-loop)
- [Roadmap](#roadmap)
- [Future Scope](#future-scope)
- [Contributing](#contributing)
- [Disclaimer](#disclaimer)
- [License](#license)
- [Team](#team)

---

# Overview

**STANDARDOS** is an AI-powered procurement specification intelligence platform designed to help organizations understand, map, audit, and improve technical procurement specifications against relevant Indian Standards.

Procurement documents often contain requirements that are not independent.

A single product specification can depend on:

- Product standards
- Test methods
- Safety standards
- Installation standards
- Terminology standards
- Normative references
- Certification requirements
- Amendments and newer versions

STANDARDOS transforms these relationships into a structured intelligence workflow.

Instead of treating standards as isolated documents, STANDARDOS models them as a connected system:

```text
Requirements
     ↓
Indian Standards
     ↓
Normative References
     ↓
Testing
     ↓
Certification
     ↓
Compliance
The Problem

Technical procurement specifications are often created and reviewed manually.

A procurement officer may need to:

Understand the product requirements.
Identify applicable Indian Standards.
Search through related standards.
Inspect normative references.
Verify amendments and versions.
Identify certification requirements.
Check whether important requirements are missing.
Review the specification for technical inconsistencies.

This process becomes increasingly difficult when specifications involve multiple technical domains and interconnected standards.

The hidden problem

A procurement specification may look like:

Product
├── Technical Parameters
├── Safety Requirements
├── Testing Requirements
├── Environmental Requirements
└── Certification

But underneath it can actually represent:

Requirement
      ↓
Product Standard
      ↓
Normative Reference
      ↓
Test Method
      ↓
Safety Standard
      ↓
Certification Requirement

Missing one relationship can result in an incomplete specification.

Our Solution

STANDARDOS acts as an intelligent layer between procurement specifications and standards knowledge.

                 PROCUREMENT SPECIFICATION
                           │
                           ↓
                  Requirement Extraction
                           │
                           ↓
                    Standards Discovery
                           │
                           ↓
                 Standards Dependency Graph
                           │
                           ↓
                  Compliance Reasoning
                           │
             ┌─────────────┼─────────────┐
             ↓             ↓             ↓
        Gap Detection  Conflict Check  Version Check
             │             │             │
             └─────────────┼─────────────┘
                           ↓
                  Specification Repair
                           │
                           ↓
                  Evidence-backed Output

STANDARDOS is designed to move beyond simple document retrieval.

It attempts to understand:

What does the specification require?
Which standards apply?
What other standards are connected to them?
What requirements may be missing?
Are there potential conflicts?
Are referenced standards current?
What should a reviewer investigate?
How STANDARDOS Works

STANDARDOS follows a multi-stage intelligence pipeline.

1. Understand

The system receives a procurement specification, technical description, or tender document.

Example:

Industrial motor

Rated Power: 15 kW
Voltage: 415 V
Frequency: 50 Hz
Protection: IP55
Industrial environment
Safety compliance required
2. Parse

The document is processed to identify:

Technical parameters
Requirements
Product attributes
Existing standards
Certification references
Testing requirements
3. Extract Requirements

Natural-language requirements are converted into structured representations.

Example:

"Motor shall operate at 415V ±10%"

        ↓

Parameter:
operating_voltage

Value:
415

Tolerance:
±10%

Unit:
V
4. Discover Standards

The extracted requirements are matched against the available standards knowledge base using semantic retrieval.

The system can consider:

Product terminology
Technical attributes
Application domain
Requirement semantics
Existing standard references
5. Build the Standards Graph

Relevant standards are represented as interconnected entities.

                    Product Standard
                           │
            ┌──────────────┼──────────────┐
            ↓              ↓              ↓
      Test Standard   Safety Standard   Terminology
            │              │
            ↓              ↓
      Test Evidence   Certification

This allows STANDARDOS to reason about relationships rather than treating every standard as an isolated search result.

6. Reason

The reasoning layer evaluates relationships between:

Requirements
Standards
Normative references
Tests
Certifications
Versions
Constraints
7. Audit

The system can identify areas requiring review.

Examples:

Potential Missing Requirement
Potential Standards Conflict
Potential Outdated Reference
Missing Supporting Test Reference
Certification Review Required
8. Repair

STANDARDOS can generate a structured recommendation for improving the specification.

Original Requirement
        ↓
Detected Issue
        ↓
Applicable Standard
        ↓
Supporting Reference
        ↓
Suggested Revision
        ↓
Reason / Evidence
Core Features
🔎 Semantic Standards Discovery

Find potentially relevant Indian Standards from natural-language procurement requirements.

Instead of requiring exact standard numbers or keywords, STANDARDOS uses semantic understanding to connect technical requirements with relevant standards.

🧩 Requirement Graph

Break complex specifications into atomic requirements.

Example:

Industrial Motor
│
├── Rated Power
├── Voltage
├── Frequency
├── Efficiency
├── Protection Rating
├── Temperature
├── Safety
└── Testing

Each requirement can then be mapped to relevant standards and references.

🕸️ Standards Dependency Graph

Model relationships between standards.

The graph can represent:

Standard
   │
   ├── references
   ├── tested-by
   ├── depends-on
   ├── supports
   ├── supersedes
   ├── amended-by
   └── requires

This enables deeper standards intelligence.

⚠️ Standards Collision Detection

Identify potential conflicts between procurement requirements and standards.

Example:

Tender Requirement
        │
        ↓
Operating Temperature: 120°C
        │
        ↓
Referenced Standard
        │
        ↓
Compatibility Check
        │
        ↓
Potential Conflict

The result is surfaced for human review.

🕳️ Missing Requirement Detection

STANDARDOS can identify potentially missing supporting elements.

Examples:

Test methods
Safety references
Installation requirements
Certification requirements
Normative references
Technical parameters
🔄 Version & Amendment Intelligence

Standards can change over time.

STANDARDOS is designed to track relationships such as:

Old Version
     ↓
Amendment
     ↓
Updated Version
     ↓
Affected Specification

This helps identify procurement documents that may require review.

🛠️ Specification Repair

Instead of only reporting an issue, STANDARDOS can generate a structured proposal for review.

Example:

Issue:
Missing supporting test requirement

Related Standard:
IS XXXXX

Suggested Action:
Add the relevant test reference to the specification.

Reason:
The requirement depends on the associated test methodology.
📋 Compliance Intelligence

STANDARDOS can organize information related to:

Applicable standards
Certification
Testing
Safety
Normative references
Version information

The objective is to make technical review more structured and traceable.

What Makes STANDARDOS Different?

STANDARDOS is intentionally designed not to be just another:

PDF
 ↓
Vector Database
 ↓
RAG
 ↓
Chatbot

A conventional standards assistant might work like:

Question
   ↓
Search
   ↓
Retrieve Documents
   ↓
LLM
   ↓
Answer

STANDARDOS introduces an additional reasoning layer:

Tender
  ↓
Requirement Graph
  ↓
Standards Graph
  ↓
Normative Dependencies
  ↓
Constraint Reasoning
  ↓
Gap Detection
  ↓
Conflict Detection
  ↓
Version Analysis
  ↓
Specification Repair
Core innovation

STANDARDOS treats a procurement specification as a dependency graph rather than a document.

The objective is to move from:

Search → Answer

toward:

Understand → Connect → Reason → Audit → Repair

System Architecture
┌─────────────────────────────────────────────┐
│              STANDARDOS FRONTEND             │
│           TanStack Start (React)            │
└──────────────────────┬──────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────┐
│                 API LAYER                    │
│      FastAPI (Python) + PostgreSQL          │
└──────────────────────┬──────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Requirement  │ │  Semantic    │ │ Standards    │
│ Extraction   │ │  Retrieval   │ │ Knowledge    │
│              │ │              │ │ Graph        │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────────────┼────────────────┘
                        ↓
              ┌──────────────────┐
              │ Reasoning Engine │
              │                  │
              │ Rules            │
              │ Constraints      │
              │ Relationships    │
              └────────┬─────────┘
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Gap          │ │ Conflict     │ │ Version      │
│ Detection    │ │ Detection    │ │ Intelligence │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────────────┼────────────────┘
                        ↓
              ┌──────────────────┐
              │ Specification    │
              │ Repair Engine    │
              └────────┬─────────┘
                       ↓
              ┌──────────────────┐
              │ Explainable      │
              │ Output           │
              └──────────────────┘
AI Pipeline
                 INPUT DOCUMENT
                       │
                       ↓
              Document Processing
                       │
                       ↓
            Requirement Extraction
                       │
                       ↓
             Semantic Representation
                       │
                       ↓
              Standards Retrieval
                       │
                       ↓
             Graph Construction
                       │
                       ↓
             Relationship Analysis
                       │
                       ↓
              Constraint Reasoning
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
        Gaps       Conflicts     Versions
          │            │            │
          └────────────┼────────────┘
                       ↓
                Human Review
                       │
                       ↓
             Specification Repair
Technology Stack

What this repository actually contains. The design rationale for each choice, and what is not built yet, are in [docs/INTELLIGENCE.md](docs/INTELLIGENCE.md).

| Layer | Technology |
| --- | --- |
| Frontend | TanStack Start (React 19, file-based routing, SSR), Tailwind CSS, Radix UI. `/api/*` is forwarded to FastAPI by a gateway route, so the browser uses a single origin. |
| Backend API | **FastAPI** (Python 3.12) in `backend/`: auth (signed HTTP-only session cookie, scrypt hashes), uploads, analysis runs, review/repair decisions, audit trail, standards search and graph, change impact |
| Database | **PostgreSQL** via SQLAlchemy 2 + psycopg 3; schema migrations with **Alembic** (documents, runs, requirements, standards graph, findings, evidence, repairs, audit trail) |
| Jobs | Postgres-backed run queue: FastAPI background task executes the run, atomic claim, stage heartbeat, cron sweeper re-queues stalled runs |
| AI/ML engine | **Python package `standardos_aiml`** in `aiml/`, no web or database dependencies |
| Document parsing | pypdf for PDF, mammoth for DOCX, UTF-8/Windows-1252 for TXT. OCR is not implemented. |
| NLP | Deterministic requirement identification, unit-normalised quantity parsing, entity and standard-reference extraction, lexicon classification |
| Retrieval | Fielded BM25 over standard clauses + interpretable feature re-ranker (in-memory) |
| Knowledge graph | Typed relationships in Postgres + in-memory traversal (supersession, REQUIRES, TESTED_BY, …) |
| Reasoning | Interval constraint checks, purchaser checklists, dependency/version/certification rules, evidence-grounded repair templates |
| LLM (optional) | Claude (`claude-opus-5`) for repair wording only, off by default, with every rewrite checked for changed facts |
| Tests / evaluation | pytest (engine unit tests, eval regression gate, API integration tests on Postgres); gold datasets in `aiml/eval/`; tender-realistic benchmark in `aiml/benchmark/` |

Project Structure

```text
aiml/                      AI/ML engine (Python)
  standardos_aiml/           ingest/ nlp/ standards/ reasoning/ pipeline.py llm_repair.py
  standardos_aiml/standards/data/seed_corpus.json   curated standards corpus (seed)
  eval/                      gold datasets, harness (python -m eval.run), results
  benchmark/                 6 tender-realistic specs + 50 queries, runner, results
  tests/                     unit tests + evaluation regression gate
backend/                   FastAPI service (Python)
  app/                       main.py, routers/, models.py, store.py (runs/persistence), view.py, corpus.py, security.py
  alembic/                   migrations (baseline = the previous Drizzle schema)
  scripts/seed_standards.py  load the standards corpus into Postgres
  tests/                     API integration tests against Postgres
src/                       Frontend (TanStack Start)
  routes/                    pages, plus routes/api/$.ts (gateway to FastAPI)
  services/                  analysis.ts, auth.ts — the only modules that call the API
  lib/                       api.ts (HTTP client), contracts.ts (API types), report.ts
  components/                UI
pyproject.toml             uv workspace (aiml + backend)
docs/INTELLIGENCE.md       Architecture, decisions, implemented vs. future work
```

Installation

Prerequisites: [uv](https://docs.astral.sh/uv/) (Python 3.12+), Bun 1.2+, Node.js 22+, PostgreSQL 14+.

```bash
uv sync --all-packages --all-extras   # Python: engine + API (+ dev tools) into .venv
bun install                           # Frontend
cp .env.example .env                  # set DATABASE_URL and SESSION_SECRET
bun run db:migrate                    # alembic upgrade head (adopts an existing Drizzle-created schema)
bun run db:seed                       # load the standards corpus
```

Environment Variables

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Postgres connection string (required for accounts and saved analyses) |
| `DATABASE_POOL_MAX` | Optional max connections per API process |
| `DB_MIGRATION_URL` | Optional direct connection for Alembic; **takes precedence over `DATABASE_URL` for migrations** |
| `SESSION_SECRET` | 32+ random characters to sign the session cookie (required) |
| `SESSION_COOKIE_SECURE` | `true` when served over HTTPS |
| `CRON_SECRET` | Bearer token for `GET /api/cron/analysis-sweeper` |
| `STANDARDOS_LLM_REPAIR` | `on` enables optional LLM wording of repairs (default off) |
| `ANTHROPIC_API_KEY` | Credentials for the above |
| `API_INTERNAL_URL` | Where the frontend gateway and SSR reach FastAPI (default `http://127.0.0.1:8000`) |
| `VITE_API_URL` | Optional: browser calls a separately hosted API directly (then set `CORS_ORIGINS`) |

Do not commit .env files or API keys.

Running the Project

```bash
bun run api:dev             # FastAPI on :8000 (docs at http://localhost:8000/api/docs)
bun run dev                 # frontend on :3000 (its /api/* is forwarded to FastAPI)
bun run test                # pytest: engine, eval gate, API integration (needs TEST_DATABASE_URL)
bun run eval                # component evaluation → aiml/eval/results/latest.md
bun run benchmark           # tender-realistic benchmark → aiml/benchmark/results/latest.md
bun run build && bun run preview
```

API integration tests run against a real Postgres named by `TEST_DATABASE_URL` and are skipped without it; never point it at a database you want to keep. Without a database the demo workspace ("Explore demo") still works: it runs the real pipeline over bundled synthetic sample specifications and saves nothing.

Current results (details and caveats in the linked reports):

| Measure | Result |
| --- | --- |
| Component eval (held-out split) | identical to the TypeScript engine it replaces: requirement F1 100%, standard R@1 93.3%, reasoning F1 93.3% ([aiml/eval/results/latest.md](aiml/eval/results/latest.md)) |
| Benchmark, 6 tender-realistic specs (TXT) | requirement identification F1 94.4%, attribute F1 96.3%, classification accuracy 69.2%, compliance findings P/R 67.6% / 92.0% ([aiml/benchmark/results/latest.md](aiml/benchmark/results/latest.md)) |
| Benchmark retrieval, 50 queries | standard R@1 88.0%, R@3 98.0%; clause R@1 86.0% |

Example Workflow

A typical STANDARDOS workflow looks like this:

1. Upload Tender
       ↓
2. Extract Requirements
       ↓
3. Identify Product / Domain
       ↓
4. Retrieve Relevant Standards
       ↓
5. Build Standards Relationships
       ↓
6. Check Normative References
       ↓
7. Detect Missing Requirements
       ↓
8. Detect Potential Conflicts
       ↓
9. Check Version Information
       ↓
10. Generate Review Recommendations
       ↓
11. Review & Approve
Example
Input
Procurement of a 15 kW industrial motor.

Voltage: 415 V
Frequency: 50 Hz
Protection: IP55
Industrial environment
Safety compliance required.
STANDARDOS analysis
Requirements Detected
────────────────────────────
✓ Rated Power
✓ Voltage
✓ Frequency
✓ Protection Rating
✓ Environment
✓ Safety

Standards
────────────────────────────
✓ Relevant product standards
✓ Supporting safety standards
✓ Potential testing references

Audit
────────────────────────────
⚠ Potential missing test reference
⚠ Certification review required
⚠ Version verification required

The actual recommendations depend on the standards data available to the system.

Use Cases
Government Procurement

STANDARDOS can assist procurement teams with:

Tender preparation
Technical specification review
Standards discovery
Compliance analysis
Specification auditing
Public Sector Enterprises

Potential applications include:

Engineering procurement
Technical documentation
Vendor qualification
Compliance workflows
Specification management
Private Enterprises

Potential use cases include:

Procurement
Quality assurance
Regulatory compliance
Engineering
Product documentation
Manufacturers

STANDARDOS can potentially help manufacturers understand:

Applicable standards
Certification requirements
Testing requirements
Tender specifications
Compliance dependencies
Procurement Consultants

Consultants can use the platform for:

Tender preparation
Specification analysis
Standards mapping
Compliance review
Innovation

STANDARDOS combines several capabilities into one workflow.

Capability	Purpose
Requirement Graph	Converts specifications into structured requirements
Semantic Discovery	Finds relevant standards
Standards Graph	Connects related standards
Normative Reasoning	Traverses supporting references
Gap Detection	Identifies potentially missing requirements
Collision Engine	Identifies potential conflicts
Version Intelligence	Tracks standard-version relationships
Specification Repair	Generates structured review proposals
Change Impact	Identifies potentially affected specifications
Evidence Layer	Makes recommendations traceable
Why a Graph?

Standards are inherently relational.

A single standard can:

Reference another standard
Depend on a test method
Require a safety standard
Define terminology
Be amended
Be superseded
Affect certification
Influence procurement specifications

A flat document search system can retrieve documents.

A graph allows the system to model relationships between them.

               STANDARD A
              /     |     \
             /      |      \
            ↓       ↓       ↓
        TEST B   SAFETY C   TERM D
            │
            ↓
        EVIDENCE

This relationship layer is central to the STANDARDOS architecture.

Explainability

Procurement-related recommendations require traceability.

STANDARDOS aims to connect every recommendation to its underlying reasoning path.

Requirement
     ↓
Matched Standard
     ↓
Relationship
     ↓
Supporting Evidence
     ↓
Recommendation

Instead of producing only:

"Use Standard X."

the system should provide context such as:

Requirement:
Operating condition

Related Standard:
Standard X

Relationship:
Applicable product requirement

Supporting Reference:
Standard Y

Action:
Review / include supporting requirement
Human-in-the-Loop

STANDARDOS is designed as a decision-support system.

It does not replace:

Procurement officers
Engineers
Standards experts
Certification authorities
Compliance professionals

AI-generated recommendations should be reviewed by qualified personnel before being used in real procurement or regulatory workflows.

Data & Standards Governance

Standards content may be subject to:

Copyright
Licensing restrictions
Access restrictions
Institutional policies

STANDARDOS should distinguish between:

Public Metadata
      +
Licensed Standards Content
      +
User-provided Documents
      +
Derived Representations
      +
Organizational Data

Production deployment should use standards content through legally permitted access mechanisms.

The project does not assume that copyrighted standards can be freely scraped, reproduced, or redistributed.

Security Considerations

Procurement documents may contain sensitive technical and commercial information.

A production implementation should consider:

Authentication
Role-based access control
Encryption
Secure API communication
Document access controls
Audit logs
Data retention policies
Secure secret management
Tenant isolation

API keys and credentials must never be committed to the repository.

Performance Considerations

STANDARDOS is designed to minimize unnecessary computational requirements.

The architecture separates:

Retrieval

Finding potentially relevant standards.

Reasoning

Evaluating relationships and constraints.

Generation

Producing explanations and specification recommendations.

This allows computationally expensive language models to be used selectively rather than for every operation.

Scalability

The architecture can be expanded from a prototype into a larger standards intelligence platform.

Potential scaling path:

Prototype
   ↓
Standards Knowledge Base
   ↓
Standards Dependency Graph
   ↓
Multi-domain Intelligence
   ↓
Enterprise Workspaces
   ↓
Procurement Platform Integration
   ↓
Standards Change Monitoring
Roadmap
Phase 1 — Prototype
 Product concept
 Landing page
 Procurement specification workflow
 Initial AI architecture
 Expanded standards corpus
 Advanced standards graph
Phase 2 — Standards Intelligence
 Normative reference graph
 Version tracking
 Amendment detection
 Certification mapping
 Test-method relationships
 Multilingual requirement processing
Phase 3 — Procurement Intelligence
 Specification completeness analysis
 Advanced constraint reasoning
 Conflict detection
 Automated specification repair
 Procurement template auditing
 Change-impact analysis
Phase 4 — Enterprise
 Organization workspaces
 Role-based access control
 Audit trails
 Standards update monitoring
 API access
 Enterprise integrations
 Licensed standards integration
Future Scope

Potential future capabilities include:

🌐 Multilingual Standards Intelligence

Support technical requirements expressed in multiple Indian languages.

📡 Standards Change Monitoring

Continuously monitor standards metadata and identify potentially affected procurement templates.

🧠 Learning from Human Review

Use reviewer feedback to improve:

Requirement extraction
Standards ranking
Relationship confidence
Recommendation quality
🔗 Procurement Platform Integration

Expose STANDARDOS through APIs that can integrate with existing procurement systems.

🏢 Organization-Specific Knowledge

Organizations could maintain private:

Procurement templates
Approved standards
Internal policies
Vendor requirements
Historical specifications
Research Direction

STANDARDOS opens several research directions around:

Standards knowledge graphs
Retrieval-augmented generation
Technical requirement extraction
Graph-based reasoning
Constraint-aware NLP
Explainable AI
Document intelligence
Compliance automation
Change-impact analysis

A particularly important research direction is the combination of:

LLM
 +
Semantic Retrieval
 +
Knowledge Graph
 +
Constraint Reasoning

rather than relying exclusively on generative models.

Limitations

The current prototype has several limitations.

Standards Coverage

The quality of recommendations depends on the available standards corpus and metadata.

Source Availability

Some standards may require licensed or restricted access.

Technical Validation

AI-generated recommendations require expert review.

Version Accuracy

Version and amendment information is only as accurate as the underlying source.

Domain Coverage

Initial implementations may focus on selected procurement domains rather than all industries.

Contributing

Contributions are welcome.

Development Workflow

Create a feature branch:

git checkout -b feature/your-feature

Make your changes.

Stage them:

git add .

Commit:

git commit -m "feat: describe your change"

Push:

git push origin feature/your-feature

Then open a Pull Request.

Commit Convention

Recommended commit prefixes:

feat:     New feature
fix:      Bug fix
docs:     Documentation
refactor: Code restructuring
test:     Tests
chore:    Maintenance
perf:     Performance improvement

Example:

git commit -m "feat: add standards dependency graph"
Disclaimer

STANDARDOS is an AI-powered technical decision-support prototype.

Information and recommendations generated by the system should be reviewed by qualified professionals before being used for:

Procurement
Engineering decisions
Certification
Regulatory compliance
Legal decisions
Safety-critical applications

STANDARDOS does not itself certify products, establish legal compliance, or replace official standards authorities.

License

This project is currently under development.

License information will be added as the project moves toward its public/research release.

Team
STANDARDOS
From Specifications to Certainty.

An AI-powered standards and procurement intelligence platform.

Core Philosophy

Traditional procurement intelligence asks:

"Which document contains the answer?"

STANDARDOS asks:

"How are these requirements, standards, tests, certifications, and dependencies connected?"

The goal is to transform standards from static documents into structured intelligence.

DOCUMENTS
    ↓
REQUIREMENTS
    ↓
RELATIONSHIPS
    ↓
REASONING
    ↓
AUDIT
    ↓
ACTION
<div align="center">
STANDARDOS
From Specifications to Certainty.

AI-powered Standards & Procurement Intelligence

</div>
