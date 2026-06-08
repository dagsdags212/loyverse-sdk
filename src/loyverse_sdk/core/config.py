from dotenv import load_dotenv
from pydantic_settings import BaseSettings

from loyverse_sdk.core.paths import env_file, migrate_legacy_env

migrate_legacy_env()
load_dotenv(env_file())


class Config(BaseSettings):
    BASE_URL: str = "https://api.loyverse.com/v1.0"
    LOYVERSE_API_TOKEN: str = ""
    PAGE_LIMIT: int = 250
    TIMEZONE: str = "Asia/Manila"
    LOYVERSE_DB_PATH: str = "loyverse.db"


config = Config()
