from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
import warnings

class Settings(BaseSettings):
    APP_ENV: str = "development"

    DB_HOST: str
    DB_PORT: int = 3306
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_DATABASE: str

    APP_NAME: str

    SQL_LOGGING: bool = True

    HF_HUB_DISABLE_PROGRESS_BARS: str
    TOKENIZERS_PARALLELISM: str

    QDRANT_URL: str
    QDRANT_API_KEY: Optional[str] = None

    QDRANT_COLLECTION_NAME: str
    QDRANT_VECTOR_SIZE: int
    QDRANT_DISTANCE: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()

if settings.HF_HUB_DISABLE_PROGRESS_BARS:
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = settings.HF_HUB_DISABLE_PROGRESS_BARS

if settings.TOKENIZERS_PARALLELISM:
    os.environ["TOKENIZERS_PARALLELISM"] = settings.TOKENIZERS_PARALLELISM

warnings.filterwarnings(
    "ignore",
    message=".*unauthenticated requests to the HF Hub.*",
)
