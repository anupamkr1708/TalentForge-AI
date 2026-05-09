"""
Configuration Models for the Job Application Copilot
Defines structured configuration models with validation
"""

from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class LinkedInConfig:
    """LinkedIn-specific configuration"""

    cookie_file: str = "linkedin_cookies.json"
    refreshed_cookie_file: str = "linkedin_cookies_refreshed.json"
    base_url: str = "https://www.linkedin.com"
    feed_url: str = "https://www.linkedin.com/feed/"
    jobs_url: str = "https://www.linkedin.com/jobs/search/"

    # Rate limiting
    max_applications_per_day: int = 10
    min_delay_between_apps: int = 90  # seconds
    max_delay_between_apps: int = 180  # seconds

    # Search parameters
    default_keywords: List[str] = field(
        default_factory=lambda: ["AI Engineer", "Machine Learning Engineer"]
    )
    remote_only: bool = True
    default_location: str = "India"
    date_posted: str = "r86400"  # Last 24 hours

    # Application settings
    easy_apply_only: bool = True
    skip_cover_letter: bool = False
    auto_submit_threshold: float = 0.75


@dataclass
class BrowserConfig:
    """Browser automation configuration"""

    headless: bool = False
    slow_mo: int = 100  # ms
    timeout: int = 60000  # ms

    # Anti-detection
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
    viewport: dict = field(default_factory=lambda: {"width": 1280, "height": 800})
    locale: str = "en-US"
    timezone_id: str = "Asia/Kolkata"

    args: List[str] = field(
        default_factory=lambda: [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ]
    )


@dataclass
class LLMConfig:
    """LLM API configuration"""

    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    openrouter_api_key: Optional[str] = None
    openrouter_model: str = "meta-llama/llama-3.1-70b-instruct"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    hf_api_key: Optional[str] = None
    hf_model: str = "meta-llama/Meta-Llama-3-8B-Instruct"
    hf_base_url: str = "https://api-inference.huggingface.co/models"

    temperature: float = 0.3
    max_tokens: int = 150
    top_p: float = 0.9


@dataclass
class MatchingConfig:
    """Job matching configuration"""

    min_match_score: float = 0.65
    preferred_match_score: float = 0.80

    required_keywords: List[str] = field(
        default_factory=lambda: ["python", "machine learning", "AI"]
    )
    bonus_keywords: List[str] = field(
        default_factory=lambda: ["pytorch", "tensorflow", "llm", "nlp"]
    )

    company_blacklist: List[str] = field(default_factory=list)
    keyword_blacklist: List[str] = field(
        default_factory=lambda: ["10+ years", "PhD required"]
    )


@dataclass
class StorageConfig:
    """Storage configuration"""

    data_dir: Path = Path("data")
    logs_dir: Path = Path("logs")
    resume_dir: Path = Path("resumes")

    application_log: str = "applications.json"
    application_csv: str = "applications.csv"
    database_file: str = "job_applications.db"
    error_log: str = "errors.log"

    default_resume: str = "resume.pdf"


@dataclass
class SafetyConfig:
    """Safety and human-in-the-loop configuration"""

    daily_application_limit: int = 10
    require_user_confirmation: bool = True
    confirmation_timeout: int = 300  # seconds
    rate_limit_pause: int = 120  # seconds when rate limited


@dataclass
class AppConfig:
    """Master configuration"""

    linkedin: LinkedInConfig = field(default_factory=LinkedInConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    matching: MatchingConfig = field(default_factory=MatchingConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)

    debug_mode: bool = False
    dry_run: bool = True
