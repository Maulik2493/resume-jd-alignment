# Design Principles

These are the hard constraints that govern every decision in this project —
from architecture to prompts to output formatting. If a feature or implementation
violates any of these, it must not ship.

---

## 1. Honesty Over Helpfulness

The system must never produce output that makes a candidate look better than they
are. If the choice is between "more helpful but slightly dishonest" and "less
helpful but truthful," truthfulness wins every time.

**Concrete rules:**

- Never invent experience the candidate doesn't have
- Never inflate scope, scale, or impact of existing experience
- Never inject buzzwords or clichés to fill gaps
- Never rewrite the entire resume — suggest targeted improvements only
- Always separate Category A (fixable by wording) from Category B (real gaps)

---

## 2. Clarity Over Cleverness

Code should be readable by someone unfamiliar with the project. Output should be
understandable by someone unfamiliar with alignment tools.

**In code:**

- Prefer explicit variable names over abbreviations
- Prefer simple functions over complex abstractions
- Prefer flat structures over deep nesting
- No "clever" one-liners that sacrifice readability

**In output:**

- Every suggestion must state *what* to change and *why*
- No vague advice like "make it more impactful"
- No jargon without definition

---

## 3. Explicit Logic Over Magic

Every decision the system makes must be traceable. There should be no hidden
heuristics, no unexplained scoring, and no black-box transformations.

**Concrete rules:**

- If the system says a skill is missing, it must cite the JD requirement
- If the system suggests a rewording, it must explain what it improves
- Scoring (if any) must have a documented, deterministic formula
- Prompt engineering must be version-controlled and reviewable

---

## 4. Deterministic Reasoning Over Free-Form AI Output

LLM usage must be structured and constrained. The system uses AI as a tool for
extraction and comparison — not as a creative writer.

**Concrete rules:**

- LLM calls must use structured output (JSON schemas, not free text)
- Prompts must include explicit constraints and examples
- Temperature should be set to 0 or near-0 for consistency
- All LLM outputs must be validated against expected schemas before use
- If an LLM response violates constraints, it must be rejected — not patched

---

## 5. Explainability Is Not Optional

Every piece of output must carry its reasoning. The user should never have to ask
"why did it say that?"

**For Category A findings:**

- What JD requirement does this relate to?
- Where in the resume is the relevant experience?
- What specifically should change?
- Why does this count as a truthful improvement?

**For Category B findings:**

- What JD requirement is unmet?
- What was searched for in the resume?
- Why can't this be addressed through rewording?

---

## 6. Preserve the Candidate's Voice

The system provides *feedback*, not *rewrites*. When it suggests improvements,
they should feel like the candidate's own words — not a template.

**Concrete rules:**

- Suggestions should match the tone and style of the original resume
- Never replace domain-specific terminology with generic alternatives
- Never homogenize formatting or structure without reason
- The candidate's original phrasing is the starting point, not a draft to be replaced

---

## 7. Scope Discipline

This project does one thing well: compare one resume against one JD and produce
honest, categorized alignment feedback.

**Out of scope (by design) as of now:**

- Batch processing of multiple JDs
- Resume storage or candidate databases
- ATS score prediction or optimization
- Cover letter generation
- Interview preparation
- Job search or matching
