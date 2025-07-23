"""Central settings for MadSpark with mock-first defaults."""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Settings:
    """Application settings with mock-first defaults."""
    
    # Mode settings
    mode: str = "mock"  # Default to mock for safety
    
    # API settings
    google_api_key: Optional[str] = None
    model_name: str = "gemini-2.0-flash-exp"
    
    # Performance settings
    max_concurrent_agents: int = 10
    request_timeout: int = 300
    
    # Cache settings
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 3600
    cache_enabled: bool = True
    
    # Safety settings
    require_explicit_api_mode: bool = True  # Must explicitly set mode=direct
    warn_on_api_usage: bool = True  # Warn when using real API
    
    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings from environment variables."""
        from . import get_mode, require_api_key
        
        mode = get_mode()
        
        # Only try to get API key if not in mock mode
        api_key = None
        if mode != "mock":
            try:
                api_key = require_api_key()
            except ValueError:
                # Fall back to mock mode if no API key
                mode = "mock"
        
        return cls(
            mode=mode,
            google_api_key=api_key,
            model_name=os.getenv("GOOGLE_GENAI_MODEL", cls.model_name),
            max_concurrent_agents=int(os.getenv("MAX_CONCURRENT_AGENTS", "10")),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "300")),
            redis_url=os.getenv("REDIS_URL", cls.redis_url),
            cache_ttl=int(os.getenv("CACHE_TTL", "3600")),
            cache_enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true"
        )
    
    def is_safe_for_ci(self) -> bool:
        """Check if settings are safe for CI/CD."""
        return self.mode == "mock" or self.google_api_key is None
    
    def validate(self) -> list[str]:
        """Validate settings and return any warnings."""
        warnings = []
        
        if self.mode == "direct" and not self.google_api_key:
            warnings.append("Direct mode set but no API key configured")
        
        if self.max_concurrent_agents > 50:
            warnings.append(f"Very high concurrent agents ({self.max_concurrent_agents}) may cause issues")
        
        if self.request_timeout > 600:
            warnings.append(f"Very long timeout ({self.request_timeout}s) may cause hanging")
        
        return warnings

# Global settings instance
settings = Settings.from_env()