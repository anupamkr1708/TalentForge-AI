"""
Config & Policy Engine for the Job Application Copilot
Centralizes configuration management and policy enforcement
"""

import os
import logging
from pathlib import Path
from typing import Optional

from models.config import AppConfig
from dotenv import load_dotenv


class ConfigManager:
    """Manages application configuration and policy enforcement"""

    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path or ".env"
        self.config = self._load_config()

    def _load_config(self) -> AppConfig:
        """Load configuration from environment variables and defaults"""
        # Load .env file
        load_dotenv(self.config_path)

        # Create base config
        config = AppConfig()

        # Override with environment variables
        self._override_with_env(config)

        # Validate configuration
        self._validate_config(config)

        return config

    def _override_with_env(self, config: AppConfig):
        """Override configuration with environment variables"""
        # LLM Configuration
        config.llm.groq_api_key = os.getenv("GROQ_API_KEY") or config.llm.groq_api_key
        config.llm.openrouter_api_key = (
            os.getenv("OPENROUTER_API_KEY") or config.llm.openrouter_api_key
        )
        config.llm.hf_api_key = os.getenv("HF_API_KEY") or config.llm.hf_api_key

        # Debug mode
        config.debug_mode = os.getenv("DEBUG", "false").lower() == "true"

        # Dry run mode
        config.dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

        # Safety configuration
        daily_limit = os.getenv("DAILY_APPLICATION_LIMIT")
        if daily_limit:
            config.safety.daily_application_limit = int(daily_limit)

        require_confirmation = os.getenv("REQUIRE_USER_CONFIRMATION")
        if require_confirmation:
            config.safety.require_user_confirmation = (
                require_confirmation.lower() == "true"
            )

    def _validate_config(self, config: AppConfig):
        """Validate configuration and log warnings/errors"""
        errors = []
        warnings = []

        # Check for required API keys
        if not config.llm.groq_api_key:
            warnings.append(
                "GROQ_API_KEY not found in environment - LLM features will be limited"
            )

        # Check for resume
        resume_path = config.storage.resume_dir / config.storage.default_resume
        if not resume_path.exists():
            warnings.append(
                f"Resume not found at {resume_path} - matching accuracy will be reduced"
            )

        # Check for cookies
        cookie_path = Path(config.linkedin.cookie_file)
        if not cookie_path.exists():
            errors.append(
                f"Cookie file not found at {cookie_path} - authentication will fail"
            )

        # Log warnings
        for warning in warnings:
            self.logger.warning(f"⚠️  Configuration Warning: {warning}")

        # Log errors
        for error in errors:
            self.logger.error(f"❌ Configuration Error: {error}")

        # If there are critical errors, raise exception
        if errors:
            raise ValueError(
                "Critical configuration errors found. Please fix before continuing."
            )

    def get_config(self) -> AppConfig:
        """Get the current configuration"""
        return self.config

    def update_config(self, new_config: AppConfig):
        """Update the configuration"""
        self.config = new_config
        self._validate_config(self.config)

    def save_config_to_env(self, env_path: Optional[str] = None):
        """Save current configuration to .env file"""
        env_path = env_path or self.config_path
        env_lines = []

        # Save API keys if they exist
        if self.config.llm.groq_api_key:
            env_lines.append(f"GROQ_API_KEY={self.config.llm.groq_api_key}")

        if self.config.llm.openrouter_api_key:
            env_lines.append(f"OPENROUTER_API_KEY={self.config.llm.openrouter_api_key}")

        if self.config.llm.hf_api_key:
            env_lines.append(f"HF_API_KEY={self.config.llm.hf_api_key}")

        # Save boolean values
        env_lines.append(f"DEBUG={'true' if self.config.debug_mode else 'false'}")
        env_lines.append(f"DRY_RUN={'true' if self.config.dry_run else 'false'}")
        env_lines.append(
            f"REQUIRE_USER_CONFIRMATION={'true' if self.config.safety.require_user_confirmation else 'false'}"
        )

        # Save numeric values
        env_lines.append(
            f"DAILY_APPLICATION_LIMIT={self.config.safety.daily_application_limit}"
        )

        # Write to file
        try:
            with open(env_path, "w") as f:
                f.write("\n".join(env_lines))
            self.logger.info(f"Configuration saved to {env_path}")
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")

    def print_config_summary(self):
        """Print a summary of the current configuration"""
        config = self.config

        print("=" * 60)
        print("🤖 Job Application Copilot - Configuration Summary")
        print("=" * 60)
        print(f"Daily Application Limit: {config.safety.daily_application_limit}")
        print(f"Minimum Match Score: {config.matching.min_match_score * 100}%")
        print(f"LLM Providers: {'Groq' if config.llm.groq_api_key else 'None'}")
        print(f"Easy Apply Only: {config.linkedin.easy_apply_only}")
        print(f"Dry Run Mode: {config.dry_run}")
        print(f"Debug Mode: {config.debug_mode}")
        print(f"User Confirmation Required: {config.safety.require_user_confirmation}")
        print("=" * 60)
