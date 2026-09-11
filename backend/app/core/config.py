from typing import Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Healthcare AI Pre-consultation Platform"
    app_env: str = "development"
    database_url: str = "sqlite:///./health_ai.db"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "super-secret-key-change-in-production"
    cors_origins: Union[list[str], str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    
    # AI Provider Configuration
    ai_provider: str = "mock"  # Options: "mock", "openai", "gemini", "local", "ollama"
    openai_api_key: str = ""  # Set via OPENAI_API_KEY environment variable
    gemini_api_key: str = ""  # Set via GEMINI_API_KEY environment variable
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3"  # Options: "qwen3", "llama2", "mistral", etc.
    
    # File Upload Configuration
    log_level: str = "INFO"
    upload_dir: str = "uploads"
    max_upload_size_bytes: int = 25 * 1024 * 1024  # 25 MB

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, list[str]]) -> list[str]:
        if isinstance(v, str):
            if v.startswith("["):
                import json
                return json.loads(v)
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


settings = Settings()
