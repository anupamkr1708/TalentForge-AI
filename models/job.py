"""
Job Data Models for the Job Application Copilot
Defines the core data structures used throughout the application
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class JobStatus(Enum):
    """Job processing status lifecycle"""

    DISCOVERED = "discovered"
    SCORED = "scored"
    QUEUED = "queued"
    APPLIED = "applied"
    SKIPPED = "skipped"
    FAILED = "failed"


class ApplyMethod(Enum):
    """Method used to apply to a job"""

    EASY_APPLY = "easy_apply"
    EXTERNAL = "external"
    MANUAL_REVIEW = "manual_review"


@dataclass
class JobMetadata:
    """Core job metadata extracted from job boards"""

    job_id: str
    title: str
    company: str
    location: str
    url: str
    description: str
    is_easy_apply: bool
    apply_url: Optional[str] = None
    posted_date: Optional[datetime] = None
    salary: Optional[str] = None
    experience_level: Optional[str] = None


@dataclass
class JobScore:
    """Job scoring information"""

    match_score: float  # 0.0 to 1.0
    llm_score: float  # 0.0 to 1.0
    keyword_score: float  # 0.0 to 1.0
    reasons: List[str] = field(default_factory=list)


@dataclass
class JobApplication:
    """Complete job application record"""

    job_metadata: JobMetadata
    status: JobStatus
    score: Optional[JobScore] = None
    apply_method: Optional[ApplyMethod] = None
    applied_at: Optional[datetime] = None
    skipped_reason: Optional[str] = None
    failed_reason: Optional[str] = None
    steps_completed: int = 0
    user_confirmed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
