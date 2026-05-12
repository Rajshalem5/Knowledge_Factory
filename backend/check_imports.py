"""Check which packages are installed."""
packages = ["fastapi", "uvicorn", "sqlalchemy", "aiosqlite", "pydantic", "pydantic_settings", "jose", "bcrypt", "httpx", "alembic"]
for p in packages:
    try:
        mod = __import__(p)
        v = getattr(mod, "__version__", "?")
        print(f"  ✓ {p} == {v}")
    except ImportError:
        print(f"  ✗ {p} NOT INSTALLED")
