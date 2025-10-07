"""
Production API Service
Combines all API services into a single deployment
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

# Import all API modules
from production_autocomplete_api import app as autocomplete_app
from backup_management_api import app as backup_app
from mortgage_analytics_api import app as mortgage_app

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("Starting production API services...")
    yield
    print("Shutting down production API services...")

# Main application
app = FastAPI(
    title="ConcordBroker Production API",
    description="Combined API services for ConcordBroker",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://concordbroker.com",
        "https://www.concordbroker.com",
        "http://localhost:5173",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount sub-applications
app.mount("/autocomplete", autocomplete_app)
app.mount("/backup", backup_app)
app.mount("/mortgage", mortgage_app)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "ConcordBroker Production API",
        "version": "2.0.0",
        "endpoints": {
            "autocomplete": "/autocomplete",
            "backup": "/backup",
            "mortgage": "/mortgage"
        },
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "autocomplete": "active",
            "backup": "active",
            "mortgage": "active"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)