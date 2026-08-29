"""
Focused regression tests for Issue #2:
"Allow clean checkout without LinkedIn cookies"

Scope of this file (intentionally narrow):
    1. ConfigManager can initialize when the LinkedIn cookie file is absent.
    2. No ValueError is raised solely because the cookie file is missing.
    3. The default LinkedIn cookie path matches the documented repository
       layout: cookies/linkedin_cookies.json
    4. The missing-cookie condition is reported as a warning (not an error),
       and the pre-existing missing-resume / missing-API-key warnings are
       unaffected by this change.

Out of scope (see the source-level audit and Issue #2 for follow-up work):
    - Real cookie loading/injection into Playwright
    - Authentication validity/expiration handling
    - dry_run enforcement, rate limiting, daily-cap wiring
    - General pytest/test-infrastructure overhaul

Isolation notes:
    Every test runs with the working directory pointed at an empty
    tmp_path, and with the environment variables ConfigManager reads
    explicitly cleared. This ensures the tests never depend on whatever
    .env, cookies/, or resumes/ happen to exist on the developer's
    machine, and never require network access, Playwright, a real
    LinkedIn account, or a real LLM API key.
"""

import logging

import pytest

from models.config import AppConfig, LinkedInConfig
from services.config_manager import ConfigManager


# Environment variables read by ConfigManager._override_with_env.
_ENV_VARS_READ_BY_CONFIG_MANAGER = [
    "GROQ_API_KEY",
    "OPENROUTER_API_KEY",
    "HF_API_KEY",
    "DEBUG",
    "DRY_RUN",
    "DAILY_APPLICATION_LIMIT",
    "REQUIRE_USER_CONFIRMATION",
]


@pytest.fixture
def isolated_clean_checkout(tmp_path, monkeypatch):
    """
    Simulate a clean checkout: an empty working directory with no .env,
    no cookies/, no resumes/, and no relevant environment variables set.
    """
    monkeypatch.chdir(tmp_path)

    for variable in _ENV_VARS_READ_BY_CONFIG_MANAGER:
        monkeypatch.delenv(variable, raising=False)

    return tmp_path


def test_default_linkedin_cookie_path_matches_documented_layout():
    """
    Verify the default LinkedIn cookie path matches the documented layout.
    """
    expected_path = "cookies/linkedin_cookies.json"

    assert LinkedInConfig().cookie_file == expected_path
    assert AppConfig().linkedin.cookie_file == expected_path


def test_config_manager_initializes_without_cookie_file(
    isolated_clean_checkout,
):
    """
    Verify ConfigManager initializes when the LinkedIn cookie file is absent.
    """
    cookie_path = (
        isolated_clean_checkout
        / "cookies"
        / "linkedin_cookies.json"
    )

    assert not cookie_path.exists()

    manager = ConfigManager(
        config_path=str(isolated_clean_checkout / ".env")
    )

    assert (
        manager.get_config().linkedin.cookie_file
        == "cookies/linkedin_cookies.json"
    )


def test_missing_cookie_emits_warning_not_error(
    isolated_clean_checkout,
    caplog,
):
    """
    Verify a missing cookie is logged as a warning rather than an error,
    while the existing resume and API-key warnings remain unchanged.
    """
    config_path = isolated_clean_checkout / ".env"

    with caplog.at_level(
        logging.WARNING,
        logger="services.config_manager",
    ):
        ConfigManager(config_path=str(config_path))

    warning_messages = [
        record.getMessage()
        for record in caplog.records
        if record.levelno == logging.WARNING
    ]

    error_messages = [
        record.getMessage()
        for record in caplog.records
        if record.levelno == logging.ERROR
    ]

    assert any(
        "cookies/linkedin_cookies.json" in message
        and "LinkedIn authentication is not configured" in message
        for message in warning_messages
    )

    assert any(
        "Resume not found" in message
        for message in warning_messages
    )

    assert any(
        "GROQ_API_KEY not found" in message
        for message in warning_messages
    )

    assert error_messages == []
