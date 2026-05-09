"""
Setup script for the modern Job Application Copilot architecture
Initializes database and verifies configuration
"""

import os
import sys
import logging
from pathlib import Path

from models.config import AppConfig
from storage.database import JobDatabase
from services.config_manager import ConfigManager


def setup_modern_architecture():
    """Set up the modern architecture components"""
    print("🔧 Setting up Job Application Copilot - Modern Architecture")
    print("=" * 60)

    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        # 1. Initialize configuration
        print("1. Initializing configuration...")
        config_manager = ConfigManager()
        config = config_manager.get_config()
        print("   ✅ Configuration loaded successfully")

        # 2. Create required directories
        print("2. Creating directories...")
        directories = [
            config.storage.data_dir,
            config.storage.logs_dir,
            config.storage.resume_dir,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ Created {directory}")

        # 3. Initialize database
        print("3. Initializing database...")
        db_path = config.storage.data_dir / config.storage.database_file
        database = JobDatabase(str(db_path))
        print(f"   ✅ Database initialized at {db_path}")

        # 4. Verify resume exists
        print("4. Verifying resume...")
        resume_path = config.storage.resume_dir / config.storage.default_resume
        if resume_path.exists():
            print(f"   ✅ Resume found at {resume_path}")
        else:
            print(f"   ⚠️  Resume not found at {resume_path}")
            print("      Please add your resume as resume.pdf in the resumes directory")

        # 5. Verify API keys
        print("5. Verifying API configuration...")
        api_keys_present = []
        if config.llm.groq_api_key:
            api_keys_present.append("Groq")
        if config.llm.openrouter_api_key:
            api_keys_present.append("OpenRouter")
        if config.llm.hf_api_key:
            api_keys_present.append("HuggingFace")

        if api_keys_present:
            print(f"   ✅ API keys configured: {', '.join(api_keys_present)}")
        else:
            print("   ⚠️  No API keys found")
            print("      LLM features will be limited")

        # 6. Verify cookies
        print("6. Verifying cookies...")
        cookie_path = Path(config.linkedin.cookie_file)
        if cookie_path.exists():
            print(f"   ✅ Cookies found at {cookie_path}")
        else:
            print(f"   ❌ Cookies not found at {cookie_path}")
            print("      Please export LinkedIn cookies using Cookie-Editor extension")
            return False

        # 7. Print configuration summary
        print("\n7. Configuration Summary:")
        config_manager.print_config_summary()

        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Run a test: python main_modern.py --dry-run")
        print("2. Start dashboard: streamlit run dashboard/web_dashboard.py")
        print("3. Run in production: python main_modern.py")

        return True

    except Exception as e:
        logger.error(f"Setup failed: {e}")
        print(f"\n❌ Setup failed: {e}")
        return False


if __name__ == "__main__":
    success = setup_modern_architecture()
    sys.exit(0 if success else 1)
