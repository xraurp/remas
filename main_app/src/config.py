from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://remas_main:test123@localhost:15432/remas_main_db"
    host: str = "0.0.0.0"
    port: int = 8000
