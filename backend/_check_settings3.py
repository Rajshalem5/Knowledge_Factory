"""Check settings loaded from .env"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

os.chdir(os.path.dirname(__file__))

from app.config import settings
print(f"CWD: {os.getcwd()}")
print(f"DATABASE_URL = '{settings.DATABASE_URL}'")
print(f"DEBUG = {settings.DEBUG}")
print(f"CORS_ORIGINS = '{settings.CORS_ORIGINS}'")
print(f"JWT_SECRET_KEY = '{settings.JWT_SECRET_KEY[:20]}...'")
