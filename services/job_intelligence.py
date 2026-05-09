"""
Job Intelligence Engine for the Job Application Copilot
Handles job scoring, filtering, and decision making
"""

import asyncio
import logging
from typing import Tuple, List
from pathlib import Path

from models.job import JobMetadata, JobScore
from models.config import AppConfig


class JobIntelligenceEngine:
    """Intelligent job matching and filtering engine"""

    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.resume_text = self._load_resume()

    def _load_resume(self) -> str:
        """Load resume text for matching"""
        resume_path = (
            self.config.storage.resume_dir / self.config.storage.default_resume
        )
        resume_txt_path = resume_path.with_suffix(".txt")

        if resume_txt_path.exists():
            try:
                with open(resume_txt_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                self.logger.warning(f"Failed to read resume text: {e}")
        else:
            self.logger.warning(f"Resume text not found: {resume_txt_path}")

        return ""

    async def score_job(self, job: JobMetadata) -> JobScore:
        """
        Score a job based on multiple factors
        Returns a JobScore with match score and reasoning
        """
        # Calculate keyword match score
        keyword_score = self._calculate_keyword_match(job)

        # If no resume, rely primarily on keywords
        if not self.resume_text:
            match_score = max(0.5, keyword_score)
            return JobScore(
                match_score=match_score,
                llm_score=0.0,
                keyword_score=keyword_score,
                reasons=[
                    f"Keyword match: {keyword_score:.2f}",
                    "No resume provided for LLM scoring",
                ],
            )

        # Calculate LLM match score (simulated for now)
        llm_score = await self._calculate_llm_match(job)

        # Weighted combination
        match_score = (llm_score * 0.7) + (keyword_score * 0.3)

        # Generate reasons
        reasons = [
            f"Overall match: {match_score:.2f}",
            f"LLM assessment: {llm_score:.2f}",
            f"Keyword match: {keyword_score:.2f}",
        ]

        return JobScore(
            match_score=match_score,
            llm_score=llm_score,
            keyword_score=keyword_score,
            reasons=reasons,
        )

    def should_apply(self, job: JobMetadata, score: JobScore) -> Tuple[bool, str]:
        """
        Determine if we should apply to this job
        Returns (should_apply: bool, reason: str)
        """
        # Check company blacklist
        if self._is_blacklisted_company(job.company):
            return False, f"Company blacklisted: {job.company}"

        # Check keyword blacklist
        blocked_reason = self._check_keyword_blacklist(job.description)
        if blocked_reason:
            return False, blocked_reason

        # Check minimum match score
        min_score = self.config.matching.min_match_score
        if score.match_score < min_score:
            return False, f"Low match score: {score.match_score:.2f} < {min_score:.2f}"

        # If we pass all filters, we should apply
        if score.match_score >= self.config.matching.preferred_match_score:
            return True, f"Excellent match: {score.match_score:.2f}"
        else:
            return True, f"Good match: {score.match_score:.2f}"

    def _calculate_keyword_match(self, job: JobMetadata) -> float:
        """Calculate keyword-based match score"""
        jd_lower = job.description.lower()
        title_lower = job.title.lower()
        resume_lower = self.resume_text.lower() if self.resume_text else ""

        # Required keywords
        required_hits = 0
        for kw in self.config.matching.required_keywords:
            kw_l = kw.lower()
            if kw_l in jd_lower or kw_l in title_lower:
                if not resume_lower or kw_l in resume_lower:
                    required_hits += 1

        required_total = max(1, len(self.config.matching.required_keywords))
        required_score = required_hits / required_total

        # Bonus keywords
        bonus_hits = 0
        for kw in self.config.matching.bonus_keywords:
            kw_l = kw.lower()
            if kw_l in jd_lower and resume_lower and kw_l in resume_lower:
                bonus_hits += 1

        bonus_total = max(1, len(self.config.matching.bonus_keywords))
        bonus_score = bonus_hits / bonus_total

        # Weighted combination
        final = (required_score * 0.7) + (bonus_score * 0.3)
        return max(0.0, min(1.0, final))

    async def _calculate_llm_match(self, job: JobMetadata) -> float:
        """Calculate LLM-based match score (simulated)"""
        # In a real implementation, this would call an LLM API
        # For now, we'll simulate with a slight variation of keyword matching
        keyword_score = self._calculate_keyword_match(job)

        # Add some randomness to simulate LLM nuance
        import random

        variation = random.uniform(-0.1, 0.1)
        llm_score = max(0.0, min(1.0, keyword_score + variation))

        # Simulate API delay
        await asyncio.sleep(0.1)

        return llm_score

    def _is_blacklisted_company(self, company: str) -> bool:
        """Check if company is blacklisted"""
        company_lower = company.lower()
        return any(
            blocked.lower() in company_lower
            for blocked in self.config.matching.company_blacklist
        )

    def _check_keyword_blacklist(self, job_description: str) -> str:
        """Check for blacklisted keywords in job description"""
        jd_lower = job_description.lower()

        for keyword in self.config.matching.keyword_blacklist:
            if keyword.lower() in jd_lower:
                return f"Blacklisted keyword: {keyword}"

        return ""
