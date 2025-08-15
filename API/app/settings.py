from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    API_KEY: str = ""                       # si tu veux protéger l’API
    ALLOWED_ORIGINS: List[str] = ["*"]      # ajuste si besoin

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
