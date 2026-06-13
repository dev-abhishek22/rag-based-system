from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"

    DB_HOST: str
    DB_PORT: int = 3306
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_DATABASE: str

    APP_NAME: str

    SQL_LOGGING: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()