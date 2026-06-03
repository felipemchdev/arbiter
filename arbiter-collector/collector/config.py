from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    collector_interval: int = 30
    airflow_url: str = "http://localhost:8080"
    airflow_user: str = "admin"
    airflow_pass: str = "admin"
    arbiter_api: str = "http://localhost:8000"
    arbiter_key: str = "arb_x"


settings = Settings()