"""
Modern Main Entry Point for the Job Application Copilot
Uses the new Controller → Service → Storage architecture
"""

import asyncio
import argparse
import logging

from controllers.job_controller import JobApplicationController
from services.config_manager import ConfigManager


async def main():
    """Main entry point"""
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Job Application Copilot")
    parser.add_argument("--keywords", nargs="+", help="Job search keywords")
    parser.add_argument(
        "--max-jobs", type=int, default=50, help="Maximum number of jobs to process"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (no actual applications)",
    )
    parser.add_argument(
        "--dashboard", action="store_true", help="Start the web dashboard"
    )

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # If dashboard mode, start dashboard
    if args.dashboard:
        print("Starting web dashboard...")
        print("Run: streamlit run dashboard/web_dashboard.py")
        return

    # Initialize controller
    config_manager = ConfigManager()

    # Set dry run mode if specified
    if args.dry_run:
        config = config_manager.get_config()
        config.dry_run = True
        config_manager.update_config(config)

    controller = JobApplicationController(config_manager)

    # Print configuration
    controller.print_config_summary()

    # Run job search and apply
    results = await controller.run_job_search_and_apply(
        keywords=args.keywords, max_jobs=args.max_jobs
    )

    # Print results
    if results["success"]:
        print("\n Job search and apply completed successfully!")
        print(f"Processed: {results['results']['total_processed']} jobs")
        print(f"Applied: {results['results']['applied']} jobs")
        print(f"Skipped: {results['results']['skipped']} jobs")
        print(f"Failed: {results['results']['failed']} jobs")

        if results["results"]["daily_limit_reached"]:
            print("  Daily application limit reached")
    else:
        print(f"\n Job search and apply failed: {results['error']}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n Job Application Copilot stopped by user")
    except Exception as e:
        print(f"\n Fatal error: {e}")
        raise
