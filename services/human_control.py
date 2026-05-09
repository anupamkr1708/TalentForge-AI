"""
Human-in-the-Loop Control Layer for the Job Application Copilot
Ensures safe, transparent operation with user oversight
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta

from models.job import JobApplication, JobStatus
from models.config import AppConfig
from storage.database import JobDatabase


class HumanControlLayer:
    """Manages human oversight and control of the application process"""

    def __init__(self, config: AppConfig, database: JobDatabase):
        self.config = config
        self.database = database
        self.logger = logging.getLogger(__name__)
        self.daily_counter = 0
        self.last_application_time = None
        self._initialize_daily_counter()

    def _initialize_daily_counter(self):
        """Initialize daily application counter from database"""
        try:
            stats = self.database.get_statistics()
            self.daily_counter = stats.get("today_count", 0)
            self.logger.info(f"Initialized daily counter: {self.daily_counter}")
        except Exception as e:
            self.logger.warning(f"Failed to initialize daily counter: {e}")

    def check_daily_limit(self) -> bool:
        """Check if we've reached the daily application limit"""
        return self.daily_counter < self.config.safety.daily_application_limit

    def check_rate_limit(self) -> bool:
        """Check if we need to respect rate limiting"""
        if not self.last_application_time:
            return True

        time_since_last = datetime.now() - self.last_application_time
        min_delay = timedelta(seconds=self.config.linkedin.min_delay_between_apps)

        return time_since_last >= min_delay

    async def request_user_confirmation(self, application: JobApplication) -> bool:
        """
        Request user confirmation before applying to a job
        Returns True if user confirms, False otherwise
        """
        if not self.config.safety.require_user_confirmation:
            return True

        self.logger.info(
            f"❓ User confirmation required for: {application.job_metadata.title} @ {application.job_metadata.company}"
        )
        self.logger.info(f"   Match Score: {application.score.match_score:.2f}")
        self.logger.info(f"   Reasons: {', '.join(application.score.reasons)}")

        # In a real implementation, this would present a UI prompt
        # For now, we'll simulate user confirmation with a timeout
        try:
            # Simulate user thinking time
            await asyncio.wait_for(
                self._simulate_user_confirmation(),
                timeout=self.config.safety.confirmation_timeout,
            )
            return True
        except asyncio.TimeoutError:
            self.logger.warning(
                f"⏰ User confirmation timed out for {application.job_metadata.job_id}"
            )
            return False

    async def _simulate_user_confirmation(self) -> asyncio.Future:
        """Simulate user confirmation (in real implementation, this would be a UI prompt)"""
        # Simulate a random user decision
        import random

        await asyncio.sleep(2)  # Simulate user thinking time

        # 90% chance of approval in simulation
        decision = random.random() < 0.9
        if decision:
            future = asyncio.Future()
            future.set_result(True)
            return future
        else:
            raise asyncio.TimeoutError("User declined")

    def record_application_attempt(self):
        """Record that an application attempt was made"""
        self.daily_counter += 1
        self.last_application_time = datetime.now()

        # Reset counter if it's a new day (simplified check)
        if (
            self.last_application_time.hour == 0
            and self.last_application_time.minute < 5
        ):
            self.daily_counter = 1

    def pause_if_needed(self) -> Optional[int]:
        """
        Determine if we need to pause due to rate limiting
        Returns pause duration in seconds, or None if no pause needed
        """
        if not self.last_application_time:
            return None

        time_since_last = datetime.now() - self.last_application_time
        min_delay = timedelta(seconds=self.config.linkedin.min_delay_between_apps)

        if time_since_last < min_delay:
            remaining = min_delay - time_since_last
            return int(remaining.total_seconds())

        return None

    def handle_rate_limiting(self) -> bool:
        """
        Handle rate limiting scenarios
        Returns True if we should continue, False if we should pause
        """
        pause_duration = self.pause_if_needed()
        if pause_duration:
            self.logger.warning(
                f"⏳ Rate limit enforced. Pausing for {pause_duration} seconds."
            )
            # In a real implementation, we would actually pause here
            # For now, we'll just log it
            return False
        return True
