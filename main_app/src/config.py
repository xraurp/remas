from pydantic_settings import BaseSettings
import os
from functools import lru_cache

class Settings(BaseSettings):
    debug: bool = os.environ.get("DEBUG", False)

    # database
    database_url: str = os.environ.get(
        "DATABASE_URL",
        "postgresql://remas_main:test123@localhost:15432/remas_main_db"
    )
    host: str = os.environ.get("HOST", "0.0.0.0")
    port: int = os.environ.get("PORT", 8000)
    # token signing
    token_secret_key: str = os.environ.get('SECRET_KEY')
    token_signing_algorithm: str = os.environ.get('ALGORITHM', 'HS256')
    # access token expiration time
    token_access_expire_minutes: int = os.environ.get(
        'TOKEN_ACCESS_EXPIRE_MINUTES',
        30
    )
    # refresh token expiration time
    token_refresh_expire_minutes: int = os.environ.get(
        'TOKEN_REFRESH_EXPIRE_MINUTES',
        120
    )
    # task scheduling
    # Interval in which scheduler will query tasks in advance. Larger interval
    # will result in less accurate scheduling but will result in less load on
    # scheduler.
    task_scheduler_precision_seconds: int = os.environ.get(
        'TASK_SCHEDULER_PRECISION_SECONDS',
        60
    )
    task_scheduler_retry_limit_seconds: int = os.environ.get(
        'TASK_SCHEDULER_RETRY_LIMIT_SECONDS',
        120
    )
    # email config required for sending notificatoins
    # about starting and ending events
    smtp_host: str = os.environ.get('SMTP_HOST', 'localhost')
    smtp_port: int = os.environ.get('SMTP_PORT', 465)
    smtp_user: str | None = os.environ.get('SMTP_USER', '')
    smtp_password: str | None = os.environ.get('SMTP_PASSWORD', '')
    smtp_enabled: bool = os.environ.get('SMTP_ENABLED', False)
    smtp_from_address: str | None = os.environ.get('SMTP_FROM_ADDRESS', smtp_user)
    smtp_from_name: str = os.environ.get('SMTP_FROM_NAME', 'REMAS')
    smtp_starttls_enabled: bool = os.environ.get('SMTP_STARTTLS_ENABLED', False)
    # grafana config
    grafana_url: str = os.environ.get(
        'GRAFANA_URL',
        'http://localhost:3000/'
    )
    grafana_username: str = os.environ.get('GRAFANA_USERNAME', 'admin')
    grafana_password: str = os.environ.get('GRAFANA_PASSWORD', 'admin')
    # required to show correct redirect for frontend
    # if app is running in container, it uses diferent url - ussually docker
    # dns record that does not work outside container
    grafana_redirect_url: str = os.environ.get(
        'GRAFANA_REDIRECT_URL',
        grafana_url
    )

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
