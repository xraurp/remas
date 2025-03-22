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
    # grafana config
    grafana_url: str = os.environ.get(
        'GRAFANA_URL',
        'http://localhost:3000/'
    )
    grafana_username: str = os.environ.get('GRAFANA_USERNAME', 'admin')
    grafana_password: str = os.environ.get('GRAFANA_PASSWORD', 'admin')
    # TODO - add grafana email configuration

    # grafana user system folder templates
    grafana_user_system_folder_templates: list[str] = [
        '${user_name}_task_alerts',  # for task specific alerts
        '${user_name}_general_alerts',  # for general alerts
        '${user_name}_tasks',  # for dasboards
    ]
    # grafana user folder templates
    grafana_user_folder_templates: list[str] = [
        '${user_name}_user_folder'  # for things that user creates manually
    ]
    # grafana default folders
    grafana_default_folders: list[str] = [
        'node_dashboards'
    ]

@lru_cache
def get_settings():
    return Settings()
