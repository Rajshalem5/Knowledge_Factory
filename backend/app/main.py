from fastapi import FastAPI
from app.core.database import Base, engine
from app.models import user
from app.routes import auth

app = FastAPI()


@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


app.include_router(auth.router, prefix="/api/auth")
