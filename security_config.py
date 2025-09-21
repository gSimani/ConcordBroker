"""
Security Configuration for Railway Deployment
Implements rate limiting, CORS, and security headers
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response
import time
import os

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Prometheus metrics
request_count = Counter('app_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('app_request_duration_seconds', 'Request duration', ['method', 'endpoint'])

def setup_security(app: FastAPI):
    """
    Configure all security middleware for the FastAPI app
    """

    # CORS Configuration
    origins = [
        "https://www.concordbroker.com",
        "https://concordbroker.com",
        "https://concordbroker.vercel.app",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002"
    ]

    # Add environment-specific origins
    if custom_origin := os.environ.get("ALLOWED_ORIGIN"):
        origins.append(custom_origin)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count", "X-Page-Count"]
    )

    # Trusted Host Middleware (prevents host header attacks)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.concordbroker.com", "*.railway.app", "localhost"]
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)

        # Track metrics
        process_time = time.time() - start_time
        request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(process_time)

        request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self' https: data: 'unsafe-inline'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Process-Time"] = str(process_time)

        return response

    return app

def add_api_routes(app: FastAPI):
    """
    Add monitoring and health check routes
    """

    @app.get("/health")
    @limiter.exempt
    async def health_check():
        """Health check endpoint (rate limit exempt)"""
        return {
            "status": "healthy",
            "service": "concordbroker-api",
            "deployment": "railway"
        }

    @app.get("/metrics")
    @limiter.exempt
    async def metrics():
        """Prometheus metrics endpoint (rate limit exempt)"""
        return Response(generate_latest(), media_type="text/plain")

    @app.get("/api/v1/properties")
    @limiter.limit("100/minute")
    async def get_properties(request: Request):
        """Example protected endpoint with rate limiting"""
        # This would be replaced with actual property logic
        return {"message": "Properties endpoint", "limit": "100/minute"}

    @app.get("/api/v1/search")
    @limiter.limit("50/minute")
    async def search(request: Request, q: str = ""):
        """Search endpoint with stricter rate limiting"""
        # This would be replaced with actual search logic
        return {"query": q, "limit": "50/minute"}

    return app

# Configuration for different environments
SECURITY_CONFIG = {
    "development": {
        "rate_limit": "1000/hour",
        "strict_mode": False,
        "debug_headers": True
    },
    "staging": {
        "rate_limit": "500/hour",
        "strict_mode": True,
        "debug_headers": True
    },
    "production": {
        "rate_limit": "200/hour",
        "strict_mode": True,
        "debug_headers": False
    }
}

def get_environment() -> str:
    """Get current environment from ENV variable"""
    return os.environ.get("RAILWAY_ENVIRONMENT", "development")

def get_security_config() -> dict:
    """Get security configuration for current environment"""
    env = get_environment()
    return SECURITY_CONFIG.get(env, SECURITY_CONFIG["development"])