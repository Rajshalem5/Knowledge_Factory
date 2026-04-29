from pydantic_settings import BaseSettings #type: ignore


class Settings(BaseSettings):
    DATABASE_URL: str

    SUPABASE_URL: str
    SUPABASE_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()