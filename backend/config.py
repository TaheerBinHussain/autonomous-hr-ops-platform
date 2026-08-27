from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://n8n:n8npassword@localhost:5432/n8n"
    redis_url: str = "redis://localhost:6379"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    slack_bot_token: str = ""
    minio_url: str = "http://localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    qdrant_url: str = "http://localhost:6333"

    class Config:
        env_file = ".env"


settings = Settings()
