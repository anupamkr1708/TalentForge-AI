"""
Data migration script for Job Application Copilot
Migrates data from old JSON format to new SQLite database
"""

import json
import sys
from pathlib import Path
from datetime import datetime

from models.job import JobMetadata, JobApplication, JobStatus, JobScore
from storage.database import JobDatabase
from models.config import AppConfig


def migrate_json_to_sqlite():
    """Migrate data from JSON files to SQLite database"""
    print("🔄 Migrating data from JSON to SQLite database...")
    print("=" * 50)

    # Initialize configuration and database
    config = AppConfig()
    db_path = config.storage.data_dir / config.storage.database_file
    database = JobDatabase(str(db_path))

    # JSON files to migrate
    json_files = [
        config.storage.data_dir / config.storage.application_log,
    ]

    migrated_count = 0

    for json_file in json_files:
        if not json_file.exists():
            print(f"  JSON file not found: {json_file}")
            continue

        print(f" Processing {json_file.name}...")

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                print(f"  Invalid format in {json_file.name}, skipping...")
                continue

            for item in data:
                try:
                    # Create JobMetadata
                    job_metadata = JobMetadata(
                        job_id=item.get("job_id", ""),
                        title=item.get("job_title", "").split("\n")[
                            0
                        ],  # Take first line if multiple
                        company=item.get("company", ""),
                        location="Unknown",  # Not in old data
                        url=item.get("job_url", ""),
                        description="",  # Not in old data
                        is_easy_apply=False,  # Not in old data
                        apply_url=None,
                    )

                    # Create JobScore if match_score exists
                    score = None
                    if "match_score" in item:
                        score = JobScore(
                            match_score=float(item.get("match_score", 0.0)),
                            llm_score=0.0,  # Not in old data
                            keyword_score=float(
                                item.get("match_score", 0.0)
                            ),  # Approximate
                            reasons=(
                                [item.get("reason", "")] if item.get("reason") else []
                            ),
                        )

                    # Determine status
                    status_map = {
                        "submitted": JobStatus.APPLIED,
                        "skipped": JobStatus.SKIPPED,
                        "failed": JobStatus.FAILED,
                        "no_easy_apply": JobStatus.SKIPPED,
                        "pending": JobStatus.DISCOVERED,
                    }
                    status = status_map.get(
                        item.get("status", "skipped"), JobStatus.SKIPPED
                    )

                    # Create JobApplication
                    application = JobApplication(
                        job_metadata=job_metadata,
                        status=status,
                        score=score,
                        skipped_reason=(
                            item.get("reason") if status == JobStatus.SKIPPED else None
                        ),
                        failed_reason=(
                            item.get("reason") if status == JobStatus.FAILED else None
                        ),
                        steps_completed=item.get("steps_completed", 0),
                        created_at=datetime.fromisoformat(
                            item.get("applied_at", datetime.now().isoformat())
                        ),
                        updated_at=datetime.fromisoformat(
                            item.get("applied_at", datetime.now().isoformat())
                        ),
                    )

                    # Save to database
                    if database.save_application(application):
                        migrated_count += 1

                except Exception as e:
                    print(
                        f"  Failed to migrate item {item.get('job_id', 'unknown')}: {e}"
                    )
                    continue

            print(f" Processed {len(data)} items from {json_file.name}")

        except Exception as e:
            print(f" Failed to process {json_file.name}: {e}")
            continue

    print(
        f"\n🎉 Migration completed! {migrated_count} applications migrated to database."
    )
    print(f"🗄️  Database location: {db_path}")

    # Show database statistics
    try:
        stats = database.get_statistics()
        print(f" Database statistics:")
        print(f"   Total applications: {stats.get('total_applications', 0)}")
        print(f"   Applied: {stats.get('status_counts', {}).get('applied', 0)}")
        print(f"   Skipped: {stats.get('status_counts', {}).get('skipped', 0)}")
        print(f"   Failed: {stats.get('status_counts', {}).get('failed', 0)}")
    except Exception as e:
        print(f"  Could not retrieve database statistics: {e}")

    return migrated_count > 0


if __name__ == "__main__":
    success = migrate_json_to_sqlite()
    sys.exit(0 if success else 1)
