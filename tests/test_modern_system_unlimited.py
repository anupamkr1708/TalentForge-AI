"""
Test script for the modern Job Application Copilot system
Tests the complete workflow with unlimited daily applications for testing
"""

import asyncio
import logging
from datetime import datetime

from models.job import JobMetadata
from controllers.job_controller import JobApplicationController
from services.config_manager import ConfigManager


# Mock platform that doesn't require browser automation
class MockPlatform:
    """Mock platform for testing without browser automation"""

    def __init__(self, config):
        self.config = config

    def get_platform_name(self):
        return "MockPlatform"

    async def authenticate(self):
        print("🔒 Mock authentication successful")
        return True

    async def search_jobs(self, keywords, location=None, max_results=50):
        print(f"🔍 Mock searching for jobs with keywords: {keywords}")

        # Create mock jobs
        mock_jobs = []
        for i, keyword in enumerate(keywords[:3]):  # Limit to 3 for demo
            job = JobMetadata(
                job_id=f"mock_{datetime.now().timestamp()}_{i}",
                title=f"{keyword} Specialist",
                company=f"Mock Company {i+1}",
                location=location or "Remote",
                url=f"https://mock-jobs.com/job/{i}",
                description=f"Exciting opportunity for a {keyword} specialist with experience in modern technologies.",
                is_easy_apply=True,
                apply_url=None,
            )
            mock_jobs.append(job)

        print(f" Found {len(mock_jobs)} mock jobs")
        return mock_jobs

    async def apply_to_job(self, job):
        print(f"🚀 Mock applying to {job.title} at {job.company}")
        # Simulate some processing time
        await asyncio.sleep(0.5)
        return {
            "success": True,
            "status": "applied",
            "message": f"Successfully applied to {job.title}",
        }

    async def cleanup(self):
        print("🧹 Mock platform cleanup complete")


# Patch the controller to use mock platform and unlimited applications
class TestJobController(JobApplicationController):
    """Test controller with unlimited daily applications"""

    def __init__(self, config_manager=None):
        super().__init__(config_manager)
        # Override daily limit for testing
        self.config.safety.daily_application_limit = 1000

    async def run_job_search_and_apply(self, keywords=None, max_jobs=50):
        """Override to bypass daily limit check for testing"""
        # Temporarily disable daily limit check
        original_check = self.human_control.check_daily_limit
        self.human_control.check_daily_limit = lambda: True

        try:
            return await super().run_job_search_and_apply(keywords, max_jobs)
        finally:
            # Restore original check
            self.human_control.check_daily_limit = original_check


# Test the complete workflow
async def test_complete_workflow():
    """Test the complete workflow with mock platform"""
    print("=" * 60)
    print("🤖 Job Application Copilot - Unlimited System Test")
    print("=" * 60)

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Initialize test controller
    config_manager = ConfigManager()
    controller = TestJobController(config_manager)

    # Replace real platform with mock
    controller.platform = MockPlatform(controller.config)

    # Print configuration
    controller.print_config_summary()

    # Test job search and apply
    print("\n🚀 Starting job search and apply process...")
    results = await controller.run_job_search_and_apply(
        keywords=["AI Engineer", "Machine Learning Engineer"], max_jobs=3
    )

    # Print results
    if results["success"]:
        print("\n Job search and apply completed successfully!")
        print(f"📊 Results: {results['results']}")

        # Show database stats
        stats = controller.database.get_statistics()
        print(f"\n🗄️  Database Statistics:")
        print(f"   Total Applications: {stats.get('total_applications', 0)}")
        print(f"   Applied: {stats.get('status_counts', {}).get('applied', 0)}")
        print(f"   Skipped: {stats.get('status_counts', {}).get('skipped', 0)}")
        print(f"   Failed: {stats.get('status_counts', {}).get('failed', 0)}")

        # Show recent applications
        recent_apps = controller.database.get_all_applications()[:5]
        print(f"\n📋 Recent Applications:")
        for app in recent_apps:
            score_info = f" (Score: {app.score.match_score:.2f})" if app.score else ""
            print(
                f"   • {app.job_metadata.title} at {app.job_metadata.company} - {app.status.value}{score_info}"
            )

        # Generate analytics report
        print(f"\n📈 Analytics Report Summary:")
        report = controller.generate_analytics_report()
        # Print just a portion of the report for brevity
        report_lines = report.split("\n")
        for line in report_lines[:15]:  # Show first 15 lines
            print(f"   {line}")
        if len(report_lines) > 15:
            print("   ... (report truncated for brevity)")

    else:
        print(f"\n Job search and apply failed: {results['error']}")

    print("\n" + "=" * 60)
    print("🏁 Unlimited System Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test_complete_workflow())
    except KeyboardInterrupt:
        print("\n Test interrupted by user")
    except Exception as e:
        print(f"\n Test failed with error: {e}")
        raise
