from pydantic_settings import BaseSettings
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent.parent.parent.parent / ".env"

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    META_APP_ID: str
    META_APP_SECRET: str
    META_VERIFY_TOKEN: str
    META_API_KEY: str
    UPI_ID: str
    JWT_SECRET: str
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = str(ENV_FILE)

settings = Settings()
