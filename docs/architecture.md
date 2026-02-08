# Architecture

## Overview

The system follows a linear pipeline: parse inputs → extract structured data →
compare → produce categorized findings → render report.

There is no feedback loop, no iterative rewriting, and no autonomous decision-making.
Each stage has a clear input, a clear output, and explicit validation between stages.

```
┌──────────┐    ┌──────────┐    ┌───────────┐    ┌──────────┐    ┌──────────┐
│  Resume   │    │    JD    │    │ Alignment │    │ Constraint│    │  Report  │
│  Parser   │───▶│  Parser  │───▶│  Engine   │───▶│  Checker  │───▶│ Renderer │
│           │    │          │    │           │    │           │    │          │
│ raw text  │    │ raw text │    │ compare   │    │ validate  │    │ format   │
│ → struct  │    │ → struct │    │ A vs B    │    │ findings  │    │ output   │
└──────────┘    └──────────┘    └───────────┘    └──────────┘    └──────────┘
```

---

## Directory Structure

```
backend/
  app/
    main.py              # Application entrypoint
    api/
      analyze.py         # API endpoint — accepts resume + JD, returns report
    core/
      resume_parser.py   # Extract structured data from resume text
      jd_parser.py       # Extract structured requirements from JD text
      alignment.py       # Core comparison — produces Category A/B findings
      constraints.py     # Hard constraint validation on all outputs
    models/
      schemas.py         # Pydantic models for all data structures
    services/
      llm.py             # Constrained LLM interaction layer
    utils/
      text.py            # Text cleaning and normalization
  tests/
    test_alignment.py    # Tests for core alignment logic
  requirements.txt
  README.md
docs/
  problem_statement.md   # Why this project exists
  design_principles.md   # Hard constraints and philosophy
  architecture.md        # This file
```

---

## Pipeline Stages

### Stage 1: Resume Parser (`core/resume_parser.py`)

**Input:** Raw resume text (plain text or extracted from PDF)
**Output:** Structured `Resume` model

Extracts:
- Contact info (name, email — not used for alignment, but for identification)
- Skills (explicit and inferred from experience descriptions)
- Work experience entries (company, role, duration, bullet points)
- Education entries
- Certifications

**Rules:**
- Only extract what is explicitly stated or directly implied
- Never infer skills that aren't supported by the text
- Preserve original phrasing in bullet points

### Stage 2: JD Parser (`core/jd_parser.py`)

**Input:** Raw job description text
**Output:** Structured `JobDescription` model

Extracts:
- Role title and level
- Required skills (hard requirements)
- Preferred skills (nice-to-haves)
- Experience requirements (years, domains)
- Education requirements
- Certification requirements
- Responsibility descriptions

**Rules:**
- Distinguish between "required" and "preferred" — this affects Category A vs B
- Preserve the JD's original language for citation in findings

### Stage 3: Alignment Engine (`core/alignment.py`)

**Input:** Structured `Resume` + structured `JobDescription`
**Output:** List of `Finding` objects, each tagged as Category A or Category B

For each JD requirement, the engine:
1. Searches the resume for matching or related experience
2. If found → evaluates whether the resume surfaces it effectively
3. If surfaced poorly → **Category A** finding (improvable by wording)
4. If not found at all → **Category B** finding (real gap)

**Rules:**
- Every finding must reference the specific JD requirement it relates to
- Every finding must reference the specific resume content (or absence) it evaluated
- The Category A/B classification must include a justification

### Stage 4: Constraint Checker (`core/constraints.py`)

**Input:** List of `Finding` objects
**Output:** Validated list of `Finding` objects (or rejection)

Validates that:
- No Category A finding suggests inventing experience
- No Category A finding introduces buzzwords not present in the original resume
- No finding lacks a JD requirement citation
- No finding lacks an explanation
- Category B findings do not include "workaround" suggestions

**Rules:**
- If a finding fails validation, it is removed with a logged warning — not silently patched
- This stage exists as a guardrail, not a fixer

### Stage 5: Report Renderer

**Input:** Validated findings
**Output:** Structured alignment report

Formats the findings into a readable report with:
- Summary (overall alignment strength, count of A vs B findings)
- Category A section with actionable, cited suggestions
- Category B section with honest gap descriptions
- No overall "score" that gamifies the result

---

## Data Flow Contracts

All data between stages is passed as typed Pydantic models defined in
`models/schemas.py`. No raw dicts, no untyped strings between stages.

Key models:
- `Resume` — structured resume data
- `JobDescription` — structured JD requirements
- `Finding` — a single alignment finding (Category A or B)
- `AlignmentReport` — the full output containing all findings

---

## LLM Usage (`services/llm.py`)

The LLM is used as a **structured extraction and comparison tool**, not as a
creative writer.

**Where LLM is used:**
- Parsing resume text into structured `Resume` model
- Parsing JD text into structured `JobDescription` model
- Comparing resume entries against JD requirements to classify findings

**How LLM is constrained:**
- All calls use structured output (JSON mode / function calling)
- Temperature is set to 0 for deterministic results
- Prompts include explicit hard constraints from `design_principles.md`
- All responses are validated against Pydantic schemas before use
- Failed validations are retried once, then rejected with an error

**Where LLM is NOT used:**
- Report formatting (deterministic template)
- Constraint checking (rule-based, no AI)
- Scoring or ranking (formula-based if implemented)

---

## Testing Strategy

Tests are organized around the core alignment logic:

- **Unit tests** for individual parsers (given known input, expect known structure)
- **Unit tests** for alignment engine (given known resume + JD, expect specific findings)
- **Constraint tests** that verify bad findings are caught and rejected
- **Integration tests** that run the full pipeline on sample inputs

Test fixtures use realistic but synthetic resume and JD pairs.

---

## What This Architecture Deliberately Avoids

| Pattern                     | Why it's excluded                                      |
| --------------------------- | ------------------------------------------------------ |
| Autonomous agents           | Unpredictable behavior, violates determinism principle  |
| Iterative self-correction   | Masks errors instead of surfacing them                  |
| Embedding-based similarity  | Black-box scoring, violates explainability principle    |
| Resume rewriting pipeline   | Out of scope — this tool provides feedback, not rewrites|
| Caching/storage of resumes  | Privacy concern, out of scope                          |
| Multi-JD comparison         | Scope discipline — one resume, one JD                  |
