"""
Main entry point for ConcordBroker API - Railway Deployment
This file serves as the entry point for Railway deployment with optimizations
"""

import os
import sys

# Add the apps/api directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

# Import optimization modules if available
try:
    from cache_config import cache_decorator, check_cache_health
    from security_config import setup_security, add_api_routes
    OPTIMIZATIONS_AVAILABLE = True
except ImportError:
    OPTIMIZATIONS_AVAILABLE = False
    print("INFO: Running without advanced optimizations")

# Import and run the actual API
try:
    # Try to import the ultimate autocomplete API first
    from ultimate_autocomplete_api import app
    print("SUCCESS: Loaded ultimate_autocomplete_api")
except ImportError:
    try:
        # Fallback to property_live_api
        from property_live_api import app
        print("SUCCESS: Loaded property_live_api")
    except ImportError:
        # Create a minimal working API if others fail
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware

        app = FastAPI(
            title="ConcordBroker API",
            description="Real Estate Property Search API",
            version="1.0.0"
        )

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.get("/")
        def read_root():
            return {
                "message": "ConcordBroker API is running on Railway!",
                "status": "operational",
                "endpoints": {
                    "health": "/health",
                    "docs": "/docs",
                    "api": "/api"
                }
            }

        @app.get("/health")
        def health_check():
            health_status = {
                "status": "healthy",
                "service": "ConcordBroker API",
                "deployment": "Railway"
            }

            # Add cache health if available
            if OPTIMIZATIONS_AVAILABLE:
                try:
                    health_status["cache"] = check_cache_health()
                except:
                    pass

            return health_status

        @app.get("/api")
        def api_info():
            return {
                "name": "ConcordBroker API",
                "version": "1.0.0",
                "description": "Property search and autocomplete API",
                "optimizations": OPTIMIZATIONS_AVAILABLE
            }

        print("WARNING: Using minimal fallback API")

# Apply security optimizations if available
if OPTIMIZATIONS_AVAILABLE:
    try:
        app = setup_security(app)
        app = add_api_routes(app)
        print("SUCCESS: Security and monitoring configured")
    except Exception as e:
        print(f"WARNING: Could not apply all optimizations: {e}")

# Run the server if this file is executed directly
if __name__ == "__main__":
    import uvicorn

    # Get port from environment variable (Railway provides this)
    port = int(os.environ.get("PORT", 8000))

    print(f"STARTING: ConcordBroker API on port {port}")
    print(f"OPTIMIZATIONS: {'Enabled' if OPTIMIZATIONS_AVAILABLE else 'Disabled'}")

    # Check if we should use Gunicorn (production) or Uvicorn (development)
    if os.environ.get("RAILWAY_ENVIRONMENT") == "production":
        # In production, Gunicorn will handle this via railway.json
        print("INFO: Production mode - Gunicorn will handle server startup")
    else:
        # Development mode - run with Uvicorn directly
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=True,
            reload=False  # Set to True for development
        )