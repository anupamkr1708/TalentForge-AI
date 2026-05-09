"""
Analytics & Monitoring Module for the Job Application Copilot
Tracks application metrics, success rates, and system health
"""

import logging
from typing import Dict, List
from datetime import datetime, timedelta
from collections import defaultdict

from models.job import JobStatus
from storage.database import JobDatabase
from models.config import AppConfig


class AnalyticsEngine:
    """Tracks and analyzes job application metrics"""

    def __init__(self, config: AppConfig, database: JobDatabase):
        self.config = config
        self.database = database
        self.logger = logging.getLogger(__name__)

    def get_application_statistics(self) -> Dict:
        """Get comprehensive application statistics"""
        try:
            stats = self.database.get_statistics()

            # Get all applications for detailed analysis
            all_applications = self.database.get_all_applications()

            # Calculate success rate
            total = len(all_applications)
            applied_count = len(
                [app for app in all_applications if app.status == JobStatus.APPLIED]
            )
            skipped_count = len(
                [app for app in all_applications if app.status == JobStatus.SKIPPED]
            )
            failed_count = len(
                [app for app in all_applications if app.status == JobStatus.FAILED]
            )

            success_rate = (applied_count / total * 100) if total > 0 else 0

            # Calculate match score distribution
            match_scores = [
                app.score.match_score for app in all_applications if app.score
            ]
            avg_match_score = (
                sum(match_scores) / len(match_scores) if match_scores else 0
            )

            # Calculate applications by company
            companies = defaultdict(int)
            for app in all_applications:
                companies[app.job_metadata.company] += 1

            # Top companies
            top_companies = sorted(companies.items(), key=lambda x: x[1], reverse=True)[
                :10
            ]

            return {
                "total_applications": total,
                "applied": applied_count,
                "skipped": skipped_count,
                "failed": failed_count,
                "success_rate": round(success_rate, 2),
                "average_match_score": round(avg_match_score, 2),
                "today_count": stats.get("today_count", 0),
                "status_distribution": stats.get("status_counts", {}),
                "top_companies": top_companies,
                "last_updated": datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.error(f"Failed to generate statistics: {e}")
            return {}

    def get_daily_trend(self, days: int = 7) -> Dict[str, int]:
        """Get application trend over the last N days"""
        try:
            all_applications = self.database.get_all_applications()

            # Group by date
            daily_counts = defaultdict(int)
            cutoff_date = datetime.now() - timedelta(days=days)

            for app in all_applications:
                if app.created_at >= cutoff_date:
                    date_key = app.created_at.date().isoformat()
                    daily_counts[date_key] += 1

            return dict(daily_counts)
        except Exception as e:
            self.logger.error(f"Failed to generate daily trend: {e}")
            return {}

    def get_match_score_distribution(self) -> Dict[str, int]:
        """Get distribution of match scores"""
        try:
            all_applications = self.database.get_all_applications()
            match_scores = [
                app.score.match_score for app in all_applications if app.score
            ]

            # Bucket scores into ranges
            distribution = {
                "0.0-0.2": 0,
                "0.2-0.4": 0,
                "0.4-0.6": 0,
                "0.6-0.8": 0,
                "0.8-1.0": 0,
            }

            for score in match_scores:
                if score < 0.2:
                    distribution["0.0-0.2"] += 1
                elif score < 0.4:
                    distribution["0.2-0.4"] += 1
                elif score < 0.6:
                    distribution["0.4-0.6"] += 1
                elif score < 0.8:
                    distribution["0.6-0.8"] += 1
                else:
                    distribution["0.8-1.0"] += 1

            return distribution
        except Exception as e:
            self.logger.error(f"Failed to generate match score distribution: {e}")
            return {}

    def get_failure_analysis(self) -> Dict[str, int]:
        """Analyze reasons for application failures"""
        try:
            failed_applications = self.database.get_applications_by_status(
                JobStatus.FAILED
            )

            # Count failure reasons
            failure_reasons = defaultdict(int)
            for app in failed_applications:
                reason = app.failed_reason or "Unknown"
                failure_reasons[reason] += 1

            return dict(failure_reasons)
        except Exception as e:
            self.logger.error(f"Failed to analyze failures: {e}")
            return {}

    def generate_report(self) -> str:
        """Generate a comprehensive analytics report"""
        stats = self.get_application_statistics()
        trend = self.get_daily_trend()
        distribution = self.get_match_score_distribution()
        failures = self.get_failure_analysis()

        report = []
        report.append("=" * 60)
        report.append("📊 JOB APPLICATION COPILOT - ANALYTICS REPORT")
        report.append("=" * 60)
        report.append("")

        # Summary statistics
        report.append("📈 SUMMARY STATISTICS")
        report.append("-" * 25)
        report.append(f"Total Applications: {stats.get('total_applications', 0)}")
        report.append(f"Applied: {stats.get('applied', 0)}")
        report.append(f"Skipped: {stats.get('skipped', 0)}")
        report.append(f"Failed: {stats.get('failed', 0)}")
        report.append(f"Success Rate: {stats.get('success_rate', 0)}%")
        report.append(f"Average Match Score: {stats.get('average_match_score', 0)}")
        report.append(f"Today's Applications: {stats.get('today_count', 0)}")
        report.append("")

        # Daily trend
        report.append("📅 DAILY TREND (Last 7 Days)")
        report.append("-" * 30)
        for date, count in sorted(trend.items()):
            report.append(f"{date}: {count} applications")
        report.append("")

        # Match score distribution
        report.append("🎯 MATCH SCORE DISTRIBUTION")
        report.append("-" * 28)
        for range_label, count in distribution.items():
            report.append(f"{range_label}: {count} jobs")
        report.append("")

        # Top companies
        report.append("🏢 TOP COMPANIES")
        report.append("-" * 15)
        for company, count in stats.get("top_companies", []):
            report.append(f"{company}: {count} applications")
        report.append("")

        # Failure analysis
        if failures:
            report.append("❌ FAILURE ANALYSIS")
            report.append("-" * 18)
            for reason, count in failures.items():
                report.append(f"{reason}: {count} failures")
            report.append("")

        report.append("=" * 60)
        report.append(
            "Report generated at: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        report.append("=" * 60)

        return "\n".join(report)
