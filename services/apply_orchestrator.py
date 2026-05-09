"""
Apply Orchestration Service for the Job Application Copilot
Routes jobs to appropriate application pipelines based on job type
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime

from models.job import JobApplication, JobMetadata, JobStatus, ApplyMethod
from models.config import AppConfig
from services.job_intelligence import JobIntelligenceEngine
from storage.database import JobDatabase


class ApplyOrchestrator:
    """Orchestrates job applications across different pipelines"""

    def __init__(
        self,
        config: AppConfig,
        database: JobDatabase,
        intelligence_engine: JobIntelligenceEngine,
    ):
        self.config = config
        self.database = database
        self.intelligence_engine = intelligence_engine
        self.logger = logging.getLogger(__name__)

    async def process_job(self, job: JobMetadata) -> JobApplication:
        """
        Process a job through the application pipeline
        Returns a JobApplication with final status
        """
        # Create initial application record
        application = JobApplication(job_metadata=job, status=JobStatus.DISCOVERED)

        # Save initial state
        self.database.save_application(application)

        try:
            # Score the job
            application.status = JobStatus.SCORED
            application.score = await self.intelligence_engine.score_job(job)
            application.updated_at = datetime.now()
            self.database.save_application(application)

            # Determine if we should apply
            should_apply, reason = self.intelligence_engine.should_apply(
                job, application.score
            )

            if not should_apply:
                application.status = JobStatus.SKIPPED
                application.skipped_reason = reason
                application.updated_at = datetime.now()
                self.database.save_application(application)
                self.logger.info(f"⏭️  Skipped {job.title} @ {job.company}: {reason}")
                return application

            # Determine apply method
            apply_method = self._determine_apply_method(job)
            application.apply_method = apply_method
            application.status = JobStatus.QUEUED
            application.updated_at = datetime.now()
            self.database.save_application(application)

            # Route to appropriate pipeline
            if apply_method == ApplyMethod.EASY_APPLY:
                application = await self._process_easy_apply(application)
            elif apply_method == ApplyMethod.EXTERNAL:
                application = await self._process_external_apply(application)
            else:
                application = await self._process_manual_review(application)

            # Save final state
            application.updated_at = datetime.now()
            self.database.save_application(application)

            return application

        except Exception as e:
            self.logger.error(f"❌ Failed to process job {job.job_id}: {e}")
            application.status = JobStatus.FAILED
            application.failed_reason = str(e)
            application.updated_at = datetime.now()
            self.database.save_application(application)
            return application

    def _determine_apply_method(self, job: JobMetadata) -> ApplyMethod:
        """Determine the appropriate apply method for a job"""
        if job.is_easy_apply:
            return ApplyMethod.EASY_APPLY
        elif job.apply_url:
            return ApplyMethod.EXTERNAL
        else:
            return ApplyMethod.MANUAL_REVIEW

    async def _process_easy_apply(self, application: JobApplication) -> JobApplication:
        """Process job through Easy Apply pipeline"""
        self.logger.info(
            f"🚀 Processing Easy Apply for {application.job_metadata.title} @ {application.job_metadata.company}"
        )

        # In a real implementation, this would integrate with the browser automation
        # For now, we'll simulate the process

        # Simulate form filling and submission
        await asyncio.sleep(1)  # Simulate processing time

        # Simulate success or failure
        import random

        if random.random() > 0.2:  # 80% success rate
            application.status = JobStatus.APPLIED
            application.applied_at = datetime.now()
            application.steps_completed = 5  # Simulate steps completed
            self.logger.info(
                f"✅ Applied to {application.job_metadata.title} @ {application.job_metadata.company}"
            )
        else:
            application.status = JobStatus.FAILED
            application.failed_reason = "Form submission failed"
            self.logger.error(
                f"❌ Failed to apply to {application.job_metadata.title} @ {application.job_metadata.company}"
            )

        return application

    async def _process_external_apply(
        self, application: JobApplication
    ) -> JobApplication:
        """Process job through external apply pipeline"""
        self.logger.info(
            f"🔗 Processing external apply for {application.job_metadata.title} @ {application.job_metadata.company}"
        )

        # In a real implementation, this would open the external URL
        # For now, we'll simulate the process

        await asyncio.sleep(0.5)  # Simulate processing time

        # Mark as requiring manual review
        application.status = JobStatus.QUEUED  # Queued for manual review
        application.apply_method = ApplyMethod.MANUAL_REVIEW
        self.logger.info(
            f"📋 Added {application.job_metadata.title} @ {application.job_metadata.company} to manual review queue"
        )

        return application

    async def _process_manual_review(
        self, application: JobApplication
    ) -> JobApplication:
        """Process job through manual review pipeline"""
        self.logger.info(
            f"📋 Queuing {application.job_metadata.title} @ {application.job_metadata.company} for manual review"
        )

        # In a real implementation, this would notify the user
        # For now, we'll just mark it as queued for manual review

        application.status = JobStatus.QUEUED
        self.logger.info(
            f"📋 Queued {application.job_metadata.title} @ {application.job_metadata.company} for manual review"
        )

        return application
