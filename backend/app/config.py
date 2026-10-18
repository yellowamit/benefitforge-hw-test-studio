import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env from project root or current working directory
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"postgresql://hw_admin:hw_secret@localhost:{os.getenv('HW_DB_PORT', '5432')}/benefitforge_sandbox"
    )

settings = Settings()

