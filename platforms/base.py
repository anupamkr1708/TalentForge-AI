"""
Base classes for platform-specific implementations
Provides extensibility for adding new job platforms
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from models.job import JobMetadata


class JobPlatform(ABC):
    """Abstract base class for job platform implementations"""

    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the job platform"""
        pass

    @abstractmethod
    async def search_jobs(
        self, keywords: List[str], location: str = None, max_results: int = 50
    ) -> List[JobMetadata]:
        """Search for jobs on the platform"""
        pass

    @abstractmethod
    async def apply_to_job(self, job: JobMetadata) -> dict:
        """Apply to a job on the platform"""
        pass

    @abstractmethod
    def get_platform_name(self) -> str:
        """Get the name of the platform"""
        pass


class PlatformFactory:
    """Factory for creating platform instances"""

    _platforms = {}

    @classmethod
    def register_platform(cls, name: str, platform_class):
        """Register a new platform implementation"""
        cls._platforms[name] = platform_class

    @classmethod
    def create_platform(cls, name: str, **kwargs) -> Optional[JobPlatform]:
        """Create a platform instance by name"""
        platform_class = cls._platforms.get(name)
        if platform_class:
            return platform_class(**kwargs)
        return None

    @classmethod
    def get_available_platforms(cls) -> List[str]:
        """Get list of available platform names"""
        return list(cls._platforms.keys())
