from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    database_url: str = os.environ.get(
        "DATABASE_URL",
        "postgresql://remas_main:test123@localhost:15432/remas_main_db"
    )
    host: str = os.environ.get("HOST", "0.0.0.0")
    port: int = os.environ.get("PORT", 8000)
