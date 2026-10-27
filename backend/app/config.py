from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="COMINTERN_")

    database_url: str = f"sqlite:///{BASE_DIR / 'comintern.db'}"
    jwt_secret: str = "dev-only-secret-change-me-in-production-0000"
    jwt_expire_minutes: int = 60 * 24
    upload_dir: Path = BASE_DIR / "uploads"
    max_upload_mb: int = 25
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
