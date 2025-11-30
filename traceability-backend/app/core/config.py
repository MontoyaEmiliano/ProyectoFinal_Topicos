from pydantic import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Traceability API"
    DATABASE_URL: str = "sqlite:///./trace.db"

    class Config:
        env_file = ".env"

settings = Settings()
