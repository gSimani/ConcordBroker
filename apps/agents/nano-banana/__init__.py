"""
Nano Banana Design Agent Package
================================

AI-powered design generation using Google AI Studio (Gemini API).
"""

from .design_agent import (
    NanoBananaDesignAgent,
    DesignRequest,
    DesignResult,
    get_agent,
    generate_design,
    DESIGN_CONTEXT,
    GOOGLE_AI_CONFIG,
)

__all__ = [
    "NanoBananaDesignAgent",
    "DesignRequest",
    "DesignResult",
    "get_agent",
    "generate_design",
    "DESIGN_CONTEXT",
    "GOOGLE_AI_CONFIG",
]

__version__ = "1.0.0"
