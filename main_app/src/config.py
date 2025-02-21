from pydantic_settings import BaseSettings
import os
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str = os.environ.get(
        "DATABASE_URL",
        "postgresql://remas_main:test123@localhost:15432/remas_main_db"
    )
    host: str = os.environ.get("HOST", "0.0.0.0")
    port: int = os.environ.get("PORT", 8000)
    # token signing
    access_token_secret_key: str = os.environ.get('SECRET_KEY')
    access_token_signing_algorithm: str = os.environ.get('ALGORITHM', 'HS256')
    access_token_expire_minutes: int = 60

@lru_cache
def get_settings():
    return Settings()
