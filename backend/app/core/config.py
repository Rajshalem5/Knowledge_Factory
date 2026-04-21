from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/knowledge_factory"
    
    # Redis (optional)
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    
    # Judge0
    JUDGE0_API_URL: str = "https://judge0-ce.p.rapidapi.com"
    JUDGE0_API_KEY: str = ""
    JUDGE0_API_HOST: str = "judge0-ce.p.rapidapi.com"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Assessment
    ASSESSMENT_DURATION_MINUTES: int = 40
    PASS_THRESHOLD: float = 70.0
    
    # Scoring weights
    CODING_WEIGHT: float = 0.7
    MCQ_POINTS_PER_QUESTION: int = 3
    
    class Config:
        env_file = ".env"


settings = Settings()
