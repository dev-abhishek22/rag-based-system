from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    APP_ENV: str = "development"

    DB_HOST: str
    DB_PORT: int = 3306
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_DATABASE: str

    APP_NAME: str

    SQL_LOGGING: bool = True

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