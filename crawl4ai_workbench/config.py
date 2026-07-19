from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from C4AI_* environment variables."""

    model_config = SettingsConfigDict(env_prefix="C4AI_", env_file=".env")

    host: str = "0.0.0.0"
    port: int = 8088
    output_dir: Path = Path("outputs")
    allow_private_networks: bool = False
    page_timeout_ms: int = 60_000


settings = Settings()
