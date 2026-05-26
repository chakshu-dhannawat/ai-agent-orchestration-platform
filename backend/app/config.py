from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agent_platform"
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_MODE: str = "polling"
    SECRET_KEY: str = "change-me-in-production"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()
