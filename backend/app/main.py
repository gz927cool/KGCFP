"""FastAPI main application for KGCFP."""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

from app.api import routes
from app.graph.connection import init_driver, close_driver


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup: initialize Neo4j driver
    await init_driver()
    yield
    # Shutdown: close Neo4j driver
    await close_driver()


app = FastAPI(
    title="KGCFP Knowledge Graph API",
    description="API for Chinese Figure Painting Knowledge Graph",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes.router, prefix="/api", tags=["graph"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "KGCFP Knowledge Graph API", "version": "0.1.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
