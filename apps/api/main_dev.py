"""
ConcordBroker FastAPI Backend - Development Server
Simplified API for localhost development
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
from dotenv import load_dotenv

# Add the api directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Now import the properties router
from routers.properties import router as properties_router

# Load environment variables
load_dotenv()

app = FastAPI(
    title="ConcordBroker API",
    description="Real Estate Intelligence Platform - Address-Based Property Management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for localhost development
origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # Alternative React port
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(properties_router, tags=["properties"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ConcordBroker API - Development Server",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "properties": "/api/properties",
            "search": "/api/properties/search",
            "dashboard": "/api/properties/stats/overview"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "api": "running",
        "environment": "development"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)