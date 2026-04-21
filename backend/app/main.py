from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import assessment, code_execution
from .core.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Knowledge Factory - Round 2 Assessment API",
    description="AI-powered coding assessment platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(assessment.router)
app.include_router(code_execution.router)


@app.get("/")
async def root():
    return {
        "message": "Knowledge Factory Assessment API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
