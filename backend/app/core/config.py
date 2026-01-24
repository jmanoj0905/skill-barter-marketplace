from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Skill Barter Marketplace API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # CORS settings
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
