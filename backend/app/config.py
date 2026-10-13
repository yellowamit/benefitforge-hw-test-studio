import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://hw_admin:hw_secret@localhost:5432/benefitforge_sandbox"
    )

settings = Settings()
