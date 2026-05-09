"""
Database Storage Implementation for the Job Application Copilot
Implements SQLite storage for job applications with full lifecycle tracking
"""

import sqlite3
import json
import logging
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from models.job import JobApplication, JobMetadata, JobScore, JobStatus, ApplyMethod


class JobDatabase:
    """SQLite database for storing job applications and their status"""

    def __init__(self, db_path: str = "data/job_applications.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS job_applications (
                    job_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    url TEXT NOT NULL,
                    description TEXT,
                    is_easy_apply BOOLEAN,
                    apply_url TEXT,
                    status TEXT NOT NULL,
                    match_score REAL,
                    llm_score REAL,
                    keyword_score REAL,
                    score_reasons TEXT,
                    apply_method TEXT,
                    applied_at TEXT,
                    skipped_reason TEXT,
                    failed_reason TEXT,
                    steps_completed INTEGER DEFAULT 0,
                    user_confirmed BOOLEAN DEFAULT FALSE,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )

            # Create indexes for common queries
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_status ON job_applications(status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_company ON job_applications(company)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_created_at ON job_applications(created_at)"
            )

            conn.commit()

    def save_application(self, application: JobApplication) -> bool:
        """Save or update a job application in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO job_applications (
                        job_id, title, company, location, url, description, 
                        is_easy_apply, apply_url, status, match_score, llm_score,
                        keyword_score, score_reasons, apply_method, applied_at,
                        skipped_reason, failed_reason, steps_completed, user_confirmed,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        application.job_metadata.job_id,
                        application.job_metadata.title,
                        application.job_metadata.company,
                        application.job_metadata.location,
                        application.job_metadata.url,
                        application.job_metadata.description,
                        application.job_metadata.is_easy_apply,
                        application.job_metadata.apply_url,
                        application.status.value,
                        application.score.match_score if application.score else None,
                        application.score.llm_score if application.score else None,
                        application.score.keyword_score if application.score else None,
                        (
                            json.dumps(application.score.reasons)
                            if application.score
                            else None
                        ),
                        (
                            application.apply_method.value
                            if application.apply_method
                            else None
                        ),
                        (
                            application.applied_at.isoformat()
                            if application.applied_at
                            else None
                        ),
                        application.skipped_reason,
                        application.failed_reason,
                        application.steps_completed,
                        application.user_confirmed,
                        application.created_at.isoformat(),
                        application.updated_at.isoformat(),
                    ),
                )
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(
                f"Failed to save application {application.job_metadata.job_id}: {e}"
            )
            return False

    def get_application(self, job_id: str) -> Optional[JobApplication]:
        """Retrieve a job application by job ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM job_applications WHERE job_id = ?
                """,
                    (job_id,),
                )

                row = cursor.fetchone()
                if not row:
                    return None

                return self._row_to_application(row)
        except Exception as e:
            self.logger.error(f"Failed to retrieve application {job_id}: {e}")
            return None

    def get_applications_by_status(self, status: JobStatus) -> List[JobApplication]:
        """Retrieve all job applications with a specific status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM job_applications WHERE status = ?
                """,
                    (status.value,),
                )

                rows = cursor.fetchall()
                return [self._row_to_application(row) for row in rows]
        except Exception as e:
            self.logger.error(
                f"Failed to retrieve applications with status {status.value}: {e}"
            )
            return []

    def get_all_applications(self) -> List[JobApplication]:
        """Retrieve all job applications"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM job_applications ORDER BY created_at DESC"
                )
                rows = cursor.fetchall()
                return [self._row_to_application(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to retrieve all applications: {e}")
            return []

    def job_exists(self, job_id: str) -> bool:
        """Check if a job application already exists"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT 1 FROM job_applications WHERE job_id = ? LIMIT 1
                """,
                    (job_id,),
                )
                return cursor.fetchone() is not None
        except Exception as e:
            self.logger.error(f"Failed to check if job {job_id} exists: {e}")
            return False

    def update_application_status(
        self, job_id: str, status: JobStatus, updated_at: datetime = None
    ) -> bool:
        """Update the status of a job application"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE job_applications 
                    SET status = ?, updated_at = ?
                    WHERE job_id = ?
                """,
                    (status.value, (updated_at or datetime.now()).isoformat(), job_id),
                )
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to update status for job {job_id}: {e}")
            return False

    def get_statistics(self) -> dict:
        """Get application statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get counts by status
                cursor = conn.execute(
                    """
                    SELECT status, COUNT(*) as count 
                    FROM job_applications 
                    GROUP BY status
                """
                )
                status_counts = {row[0]: row[1] for row in cursor.fetchall()}

                # Get today's applications
                today = datetime.now().date().isoformat()
                cursor = conn.execute(
                    """
                    SELECT COUNT(*) 
                    FROM job_applications 
                    WHERE DATE(created_at) = DATE(?)
                """,
                    (today,),
                )
                today_count = cursor.fetchone()[0]

                # Get average match score
                cursor = conn.execute(
                    """
                    SELECT AVG(match_score) 
                    FROM job_applications 
                    WHERE match_score IS NOT NULL
                """
                )
                avg_match_score = cursor.fetchone()[0] or 0.0

                return {
                    "status_counts": status_counts,
                    "today_count": today_count,
                    "average_match_score": avg_match_score,
                }
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {}

    def _row_to_application(self, row: tuple) -> JobApplication:
        """Convert database row to JobApplication object"""
        # Unpack row data
        (
            job_id,
            title,
            company,
            location,
            url,
            description,
            is_easy_apply,
            apply_url,
            status,
            match_score,
            llm_score,
            keyword_score,
            score_reasons,
            apply_method,
            applied_at,
            skipped_reason,
            failed_reason,
            steps_completed,
            user_confirmed,
            created_at,
            updated_at,
        ) = row

        # Create metadata
        metadata = JobMetadata(
            job_id=job_id,
            title=title,
            company=company,
            location=location,
            url=url,
            description=description,
            is_easy_apply=bool(is_easy_apply),
            apply_url=apply_url,
        )

        # Create score if available
        score = None
        if match_score is not None:
            score = JobScore(
                match_score=match_score,
                llm_score=llm_score or 0.0,
                keyword_score=keyword_score or 0.0,
                reasons=json.loads(score_reasons) if score_reasons else [],
            )

        # Create application
        return JobApplication(
            job_metadata=metadata,
            status=JobStatus(status),
            score=score,
            apply_method=ApplyMethod(apply_method) if apply_method else None,
            applied_at=datetime.fromisoformat(applied_at) if applied_at else None,
            skipped_reason=skipped_reason,
            failed_reason=failed_reason,
            steps_completed=steps_completed,
            user_confirmed=bool(user_confirmed),
            created_at=datetime.fromisoformat(created_at),
            updated_at=datetime.fromisoformat(updated_at),
        )
