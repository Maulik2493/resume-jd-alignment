from pydantic import BaseModel, Field
from typing import List, Literal, Optional


# ── Extraction Models: Resume ──────────────────────────────────────────────────

class ContactInfo(BaseModel):
    """Basic contact details extracted from resume header."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None


class Skill(BaseModel):
    """A single skill extracted from the resume."""
    name: str = Field(..., description="Skill name, preserving the resume's original phrasing")
    source: Literal["explicit", "inferred_from_experience"] = Field(
        ...,
        description=(
            "'explicit' if listed in a skills section; "
            "'inferred_from_experience' if derived from a work-experience bullet"
        ),
    )


class ExperienceEntry(BaseModel):
    """One position / role from the resume's work-experience section."""
    company: str
    title: str
    start_date: Optional[str] = Field(None, description="Normalized to YYYY-MM format, e.g. '2020-01'")
    end_date: Optional[str] = Field(None, description="Normalized to YYYY-MM format, or 'Present'")
    duration_months: Optional[int] = Field(None, description="Auto-calculated from dates — do not set manually")
    bullets: List[str] = Field(default_factory=list, description="Original bullet text, one string per bullet")
    technologies: List[str] = Field(
        default_factory=list,
        description="Technologies, tools, and frameworks used in this role, extracted from bullets",
    )


class EducationEntry(BaseModel):
    """One education credential from the resume."""
    institution: str
    degree: Optional[str] = None
    field: Optional[str] = None
    year: Optional[str] = None


class CertificationEntry(BaseModel):
    """One certification or license from the resume."""
    name: str
    issuer: Optional[str] = None
    year: Optional[str] = None


class ProjectEntry(BaseModel):
    """A project from a dedicated projects section (open-source, side projects, hackathons, etc.)."""
    name: str
    description: Optional[str] = Field(None, description="Brief project description, preserving original phrasing")
    technologies: List[str] = Field(
        default_factory=list,
        description="Technologies, tools, and frameworks used in the project",
    )
    url: Optional[str] = Field(None, description="Link to repo, demo, or write-up if mentioned")


class ParsedResume(BaseModel):
    """Structured extraction output for a resume. Produced by resume_parser, consumed by alignment engine."""
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    skills: List[Skill] = Field(default_factory=list)
    experience: List[ExperienceEntry] = Field(default_factory=list)
    projects: List[ProjectEntry] = Field(default_factory=list)
    education: List[EducationEntry] = Field(default_factory=list)
    certifications: List[CertificationEntry] = Field(default_factory=list)
    raw_text: str = Field("", description="Original resume text, kept for citation in findings")


# ── Extraction Models: Job Description ─────────────────────────────────────────

class JDRequirement(BaseModel):
    """A single requirement extracted from the job description.

    Uses a unified model: every JD ask is one of these, tagged by priority
    and category. This keeps the alignment engine simple (one list to iterate)
    and is easy to extend with new categories.
    """
    description: str = Field(..., description="Requirement text, preserving the JD's original language")
    priority: Literal["required", "preferred"] = Field(
        ..., description="MUST be exactly 'required' or 'preferred' — no other values"
    )
    category: Literal["skill", "experience", "education", "certification", "responsibility"] = Field(
        ..., description="What kind of requirement this is"
    )
    min_years: Optional[int] = Field(
        None,
        description="Minimum years of experience required, if explicitly stated (e.g. '5+ years' → 5)",
    )


class ParsedJobDescription(BaseModel):
    """Structured extraction output for a job description. Produced by jd_parser, consumed by alignment engine."""
    role_title: Optional[str] = None
    role_level: Optional[str] = Field(None, description="e.g. 'Senior', 'Staff', 'Entry-level'")
    requirements: List[JDRequirement] = Field(default_factory=list)
    raw_text: str = Field("", description="Original JD text, kept for citation in findings")


# ── API I/O Models ──────────────────────────────────────────────────────────────

class ResumeInput(BaseModel):
    text: str

class JDInput(BaseModel):
    text: str

class AnalyzeRequest(BaseModel):
    resume: ResumeInput
    jd: JDInput

class CategoryASuggestion(BaseModel):
    type: str  # A1, A2, A3
    original: str
    suggestion: str
    justification: str

class CategoryBFeedback(BaseModel):
    gap: str
    justification: str

class AnalyzeResponse(BaseModel):
    category_a: List[CategoryASuggestion]
    category_b: List[CategoryBFeedback]
