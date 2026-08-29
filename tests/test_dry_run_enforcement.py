"""
Focused regression tests for Issue #3:
"Enforce dry-run mode before application execution"

Scope of this file (intentionally narrow):
    1. When config.dry_run is True, the actual application-submission
       execution boundary (ApplyOrchestrator._submit_easy_apply_application,
       the method that performs the - currently simulated - Easy Apply
       submission) is never invoked.
    2. When dry_run prevents submission, the result is recorded as
       JobStatus.SKIPPED with a distinguishing skipped_reason, never as
       JobStatus.APPLIED.
    3. When config.dry_run is False, the existing execution path is
       preserved: the submission method is invoked exactly once, and a
       simulated success is still recorded as JobStatus.APPLIED.

Every test drives the real, unmocked ApplyOrchestrator.process_job() -
the same entry point JobApplicationController uses - so this proves the
invariant holds at the actual call boundary, not merely that a
configuration flag is set correctly.

Out of scope (see Issue #3 and the source-level audit for follow-up
work): real LinkedIn authentication/cookies, daily-cap wiring, rate
limiting, confirmation prompts, LLM scoring quality, and any pytest
infrastructure changes beyond what this file itself needs.

Isolation notes:
    JobDatabase and JobIntelligenceEngine are replaced with mocks, so
    these tests require no filesystem database, no resume file, no LLM
    API key, no network access, and no Playwright/browser. The only
    real production code under test is ApplyOrchestrator itself.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.config import AppConfig
from models.job import ApplyMethod, JobMetadata, JobScore, JobStatus
from services.apply_orchestrator import ApplyOrchestrator


def _make_job(job_id: str = "job-1") -> JobMetadata:
    """A minimal Easy Apply job, deterministic and free of any real data."""
    return JobMetadata(
        job_id=job_id,
        title="AI Engineer",
        company="Acme Corp",
        location="Remote",
        url="https://example.com/jobs/1",
        description="A sample job description.",
        is_easy_apply=True,
        apply_url=None,
    )


def _make_orchestrator(dry_run: bool) -> ApplyOrchestrator:
    """
    Build an ApplyOrchestrator with a real config (dry_run set explicitly)
    but fully mocked database and intelligence engine, so tests exercise
    only the orchestrator's own routing/gating logic.
    """
    config = AppConfig()
    config.dry_run = dry_run

    database = MagicMock()  # save_application is a no-op here, not asserted on

    intelligence_engine = MagicMock()
    intelligence_engine.score_job = AsyncMock(
        return_value=JobScore(
            match_score=0.9, llm_score=0.9, keyword_score=0.9
        )
    )
    intelligence_engine.should_apply.return_value = (True, "Strong match")

    return ApplyOrchestrator(config, database, intelligence_engine)


def _patched_to_simulate_submission_success():
    """
    The current (simulated) submission logic uses random.random() to
    decide success/failure. Patching it to a fixed value makes the
    non-dry-run assertion deterministic rather than an 80%-of-the-time
    flaky test.
    """
    return patch("random.random", return_value=0.99)


@pytest.mark.asyncio
async def test_dry_run_true_does_not_invoke_submission_method():
    """
    TEST 1 (acceptance criterion): dry_run=True must prevent the actual
    application execution method from being invoked.
    """
    orchestrator = _make_orchestrator(dry_run=True)
    orchestrator._submit_easy_apply_application = AsyncMock(
        wraps=orchestrator._submit_easy_apply_application
    )

    await orchestrator.process_job(_make_job())

    orchestrator._submit_easy_apply_application.assert_not_awaited()


@pytest.mark.asyncio
async def test_dry_run_true_records_skipped_not_applied():
    """
    TEST 2 (acceptance criterion): dry_run=True must produce an explicit
    simulated/skipped result, and must never report a real successful
    application (JobStatus.APPLIED).
    """
    orchestrator = _make_orchestrator(dry_run=True)

    application = await orchestrator.process_job(_make_job())

    assert application.status == JobStatus.SKIPPED
    assert application.status != JobStatus.APPLIED
    assert application.applied_at is None
    assert application.skipped_reason is not None
    assert "dry-run" in application.skipped_reason.lower()
    # The job was still routed as an Easy Apply candidate - only the
    # submission side effect was withheld, not the routing decision.
    assert application.apply_method == ApplyMethod.EASY_APPLY


@pytest.mark.asyncio
async def test_dry_run_false_preserves_existing_execution_path():
    """
    TEST 3 (acceptance criterion): dry_run=False must preserve the
    existing execution path - the submission method is still invoked,
    and its outcome (simulated success, in the current implementation)
    still results in JobStatus.APPLIED.
    """
    orchestrator = _make_orchestrator(dry_run=False)
    orchestrator._submit_easy_apply_application = AsyncMock(
        wraps=orchestrator._submit_easy_apply_application
    )

    with _patched_to_simulate_submission_success():
        application = await orchestrator.process_job(_make_job())

    orchestrator._submit_easy_apply_application.assert_awaited_once()
    assert application.status == JobStatus.APPLIED
    assert application.applied_at is not None
