# API/app/settings.py
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    API_KEY: str = ""

    ALLOWED_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])

    EXCEL_MODE: str = "local"          # "local" ou "gsheets"
    GSHEET_ID: Optional[str] = None
    GSHEET_NAME: str = "quitus-students"
    GSHEET_CREATE: bool = False
    GCP_SA_JSON: Optional[str] = None

    MAX_UPLOAD_MB: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",    # pas de préfixe
        extra="ignore",   # ignore les clés inconnues
    )

settings = Settings()
