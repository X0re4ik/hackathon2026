from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class Segment(BaseModel):
    type: Literal["individual", "sole_proprietor", "business", "unknown"] = "unknown"
    subtype: Optional[str] = None
    quote: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0, le=1)


class Source(BaseModel):
    origin: str
    modality: Literal["text", "audio", "video", "structured"] = "text"
    reference: str
    attributes: dict[str, Any] = Field(default_factory=dict)


class Respondent(BaseModel):
    role: Optional[str] = None
    traits: list[str] = Field(default_factory=list)
    customer_status: Optional[Literal["churned", "churning", "active", "new"]] = None
    quote: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0, le=1)


class Engagement(BaseModel):
    usage_frequency: Optional[Literal["daily", "weekly", "monthly", "rare", "unknown"]] = None
    product_knowledge: Optional[int] = Field(None, ge=0, le=3)
    usage_depth: Optional[int] = Field(None, ge=0, le=3)
    invested: Optional[bool] = None
    signals: list[str] = Field(default_factory=list)
    engagement_score: Optional[int] = Field(None, ge=0, le=10)
    confidence: Optional[float] = Field(None, ge=0, le=1)


class Job(BaseModel):
    id: str
    job: str
    quote: str


class Competitor(BaseModel):
    name: str
    relation: Optional[Literal["came_from", "uses_now", "considered", "returning_to"]] = None
    likes: list[str] = Field(default_factory=list)
    dislikes: list[str] = Field(default_factory=list)
    quote: Optional[str] = None


class Emotion(BaseModel):
    valence: Optional[int] = Field(None, ge=-2, le=2)
    intensity: Optional[int] = Field(None, ge=0, le=3)
    markers: list[Literal["frustration", "resignation", "enthusiasm", "anxiety", "sarcasm"]] = Field(default_factory=list)
    quote: Optional[str] = None


class Commentary(BaseModel):
    pain_nature: Optional[Literal["defect", "missing_feature", "expectation_mismatch", "ux_friction", "trust_breach"]] = None
    expectation_source: Optional[str] = None
    generalizability: Optional[str] = None
    alternative_explanations: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


class Pain(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    quote: str
    context: Optional[str] = None
    related_jobs: list[str] = Field(default_factory=list)
    spontaneous: Optional[bool] = None
    past_behavior: Optional[bool] = None
    workaround: Optional[str] = None
    frequency: Optional[Literal["daily", "weekly", "monthly", "rare", "unknown"]] = None
    trust_breach: Optional[bool] = None
    emotion: Optional[Emotion] = None
    commentary: Optional[Commentary] = None
    confidence: Optional[float] = Field(None, ge=0, le=1)


class SupportEpisode(BaseModel):
    issue: str
    outcome: str
    quote: Optional[str] = None


class SupportExperience(BaseModel):
    contacted: bool = False
    episodes: list[SupportEpisode] = Field(default_factory=list)
    overall: Optional[Literal["positive", "neutral", "negative"]] = None


class InterviewCommentary(BaseModel):
    who_and_expectations: Optional[str] = None
    expectations_vs_experience: Optional[str] = None
    churn_driver_hypotheses: list[str] = Field(default_factory=list)
    audience_fit_signals: Optional[str] = None
    evidence_quality: Optional[str] = None


class InterviewMeta(BaseModel):
    meta_id: str
    segment: Optional[Segment] = None
    source: Source
    respondent: Optional[Respondent] = None
    engagement: Optional[Engagement] = None
    jobs: list[Job] = Field(default_factory=list)
    competitors: list[Competitor] = Field(default_factory=list)
    pains: list[Pain]
    support_experience: Optional[SupportExperience] = None
    interview_commentary: Optional[InterviewCommentary] = None
    processed_at: Optional[datetime] = None
    agent_version: Optional[str] = None

    @model_validator(mode="after")
    def check_source(self):
        assert self.source.reference, "source.reference is required"
        return self

    @staticmethod
    def compute_meta_id(content: bytes) -> str:
        h = hashlib.sha256(content).hexdigest()[:8]
        return f"META-{h}"


class ValidationError(BaseModel):
    field: str
    message: str


class ValidationResult(BaseModel):
    valid: bool
    errors: list[ValidationError] = Field(default_factory=list)
