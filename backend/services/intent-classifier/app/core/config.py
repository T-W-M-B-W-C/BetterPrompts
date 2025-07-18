"""Configuration settings for the Intent Classification Service."""

from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    APP_NAME: str = "Intent Classification Service"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    PORT: int = 8001
    
    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "betterprompts"
    POSTGRES_USER: str = "betterprompts"
    POSTGRES_PASSWORD: str = "changeme"
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL."""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    @property
    def REDIS_URL(self) -> str:
        """Construct Redis URL."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # RabbitMQ
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    
    @property
    def RABBITMQ_URL(self) -> str:
        """Construct RabbitMQ URL."""
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/"
    
    # ML Model
    MODEL_NAME: str = "microsoft/deberta-v3-base"
    MODEL_PATH: str = "/app/models"
    MODEL_VERSION: str = "v1"
    MODEL_MAX_LENGTH: int = 512
    MODEL_BATCH_SIZE: int = 32
    MODEL_DEVICE: str = "cpu"  # "cuda" for GPU
    
    # Cache
    CACHE_TTL: int = 3600  # 1 hour
    ENABLE_CACHING: bool = True
    
    # CORS
    CORS_ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    
    # Performance
    MAX_WORKERS: int = 4
    REQUEST_TIMEOUT: int = 30
    
    # Security
    JWT_SECRET: str = "your-secret-key-change-this"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24


# Create settings instance
settings = Settings()