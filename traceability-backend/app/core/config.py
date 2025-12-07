from pydantic import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Traceability API"
    DATABASE_URL: str = "sqlite:///./trace.db"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"

settings = Settings()