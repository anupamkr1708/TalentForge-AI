"""
Main Controller for the Job Application Copilot
Orchestrates all components in the Controller → Service → Storage architecture
"""

import asyncio
import logging
from typing import List

from models.job import JobMetadata, JobStatus
from models.config import AppConfig
from services.config_manager import ConfigManager
from services.job_intelligence import JobIntelligenceEngine
from services.apply_orchestrator import ApplyOrchestrator
from services.human_control import HumanControlLayer
from services.analytics import AnalyticsEngine
from storage.database import JobDatabase

# from platforms.linkedin import LinkedInPlatform # Disabled for testing
from platforms.base import PlatformFactory
from platforms.linkedin import LinkedInPlatform


class JobApplicationController:
    """Main controller that orchestrates the job application process"""

    def __init__(self, config_manager: ConfigManager = None):
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.get_config()

        # Initialize components
        self.database = JobDatabase(
            str(self.config.storage.data_dir / self.config.storage.database_file)
        )
        self.intelligence_engine = JobIntelligenceEngine(self.config)
        self.apply_orchestrator = ApplyOrchestrator(
            self.config, self.database, self.intelligence_engine
        )
        self.human_control = HumanControlLayer(self.config, self.database)
        self.analytics_engine = AnalyticsEngine(self.config, self.database)

        # Initialize platform (disabled for testing)
        self.platform = LinkedInPlatform(self.config)

        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Register platform (disabled for testing)
        # PlatformFactory.register_platform("linkedin", LinkedInPlatform)

    async def run_job_search_and_apply(
        self, keywords: List[str] = None, max_jobs: int = 50
    ) -> dict:
        """
        Main execution flow: search jobs, score them, and apply where appropriate
        """
        if keywords is None:
            keywords = self.config.linkedin.default_keywords

        self.logger.info(f"🚀 Starting job search for: {', '.join(keywords)}")
        
        if not self.platform:
            raise RuntimeError("Job platform not initialized")

        # Authenticate with platform
        self.logger.info("🔐 Authenticating with job platform...")
        if not await self.platform.authenticate():
            self.logger.error("❌ Failed to authenticate with job platform")
            return {"success": False, "error": "Authentication failed"}

        try:
            # Search for jobs
            self.logger.info("🔍 Searching for jobs...")
            jobs = await self.platform.search_jobs(
                keywords=keywords,
                location=self.config.linkedin.default_location,
                max_results=max_jobs,
            )

            self.logger.info(f"✅ Found {len(jobs)} jobs")

            # Process each job
            results = {
                "total_processed": 0,
                "applied": 0,
                "skipped": 0,
                "failed": 0,
                "daily_limit_reached": False,
            }

            for i, job in enumerate(jobs, 1):
                self.logger.info(
                    f"\n[{i}/{len(jobs)}] Processing: {job.title} @ {job.company}"
                )

                # Check daily limit
                if not self.human_control.check_daily_limit():
                    self.logger.warning("🚫 Daily application limit reached")
                    results["daily_limit_reached"] = True
                    break

                # Check if job already exists in database
                if self.database.job_exists(job.job_id):
                    self.logger.info("⏭️  Job already processed, skipping")
                    continue

                # Process job through orchestrator
                application = await self.apply_orchestrator.process_job(job)

                # Update results
                results["total_processed"] += 1
                if application.status == JobStatus.APPLIED:
                    results["applied"] += 1
                elif application.status == JobStatus.SKIPPED:
                    results["skipped"] += 1
                elif application.status == JobStatus.FAILED:
                    results["failed"] += 1

                # Handle rate limiting
                if not self.human_control.handle_rate_limiting():
                    # In a real implementation, we would pause here
                    pass

                # Brief delay between jobs
                await asyncio.sleep(0.5)

            # Generate final report
            report = self.analytics_engine.generate_report()
            self.logger.info("\n" + report)

            return {"success": True, "results": results, "report": report}

        except Exception as e:
            self.logger.error(f"❌ Job search and apply failed: {e}")
            return {"success": False, "error": str(e)}

        finally:
            # Clean up
            await self.platform.cleanup()

    def get_statistics(self) -> dict:
        """Get current application statistics"""
        return self.analytics_engine.get_application_statistics()

    def generate_analytics_report(self) -> str:
        """Generate a full analytics report"""
        return self.analytics_engine.generate_report()

    def print_config_summary(self):
        """Print configuration summary"""
        self.config_manager.print_config_summary()


# Example usage function
async def main():
    """Example of how to use the controller"""
    # Initialize controller
    controller = JobApplicationController()

    # Print configuration
    controller.print_config_summary()

    # Run job search and apply
    results = await controller.run_job_search_and_apply(
        keywords=["AI Engineer", "Machine Learning Engineer"], max_jobs=10
    )

    # Print results
    if results["success"]:
        print("\n✅ Job search and apply completed successfully!")
        print(f"Processed: {results['results']['total_processed']} jobs")
        print(f"Applied: {results['results']['applied']} jobs")
        print(f"Skipped: {results['results']['skipped']} jobs")
        print(f"Failed: {results['results']['failed']} jobs")
    else:
        print(f"\n❌ Job search and apply failed: {results['error']}")


if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run example
    asyncio.run(main())
