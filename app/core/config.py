from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DB_URL: str = "postgresql://poc_user:poc123@localhost:5432/poc_llm_simple_py"
    ASYNC_DB_URL: str = "postgresql+asyncpg://poc_user:poc123@localhost:5432/poc_llm_simple_py"
    GROQ_API_KEY: str
    UPLOAD_DIR: str = "uploads"
    REDIS_URL: str = "redis://localhost:6379/0"


settings = Settings()
