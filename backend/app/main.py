from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.routes import auth
from app.routes import resume 
from app.routes import candidate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)


app = FastAPI(title="Hiring Platform API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  #  restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(resume.router, prefix="/api/resume", tags=["Resume"])  # 🔥 NEW


app.include_router(candidate.router, prefix="/api/candidates", tags=["Candidates"])


@app.get("/")
def root():
    return {"message": "API is running"}

@app.on_event("startup")
def startup_event():
    logger.info(" Server started successfully")