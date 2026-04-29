# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.database import Base, engine

from app.routes import auth
from app.routes import jobs
from app.routes import questions
from app.routes import submissions
from app.routes import resume
from app.routes import candidate


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Hiring Platform API",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["Auth"]
)

app.include_router(
    jobs.router,
    prefix="/api/jobs",
    tags=["Jobs"]
)

app.include_router(
    questions.router,
    prefix="/api/questions",
    tags=["Questions"]
)

app.include_router(
    submissions.router,
    prefix="/api/submissions",
    tags=["Submissions"]
)

app.include_router(
    resume.router,
    prefix="/api/resume",
    tags=["Resume"]
)

app.include_router(
    candidate.router,
    prefix="/api/candidates",
    tags=["Candidates"]
)


@app.get("/")
def root():
    return {
        "message": "Hiring Platform API is running"
    }


@app.on_event("startup")
def startup_event():
    logger.info("Server started successfully")
