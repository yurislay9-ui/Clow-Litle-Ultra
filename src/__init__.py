"""
Claw-Litle 1.0
__init__.py - Main package

Personal Agentic Operating System
100% LOCAL/OFFLINE - Optimized for Termux ARM64
"""

__version__ = "1.0.0"
__author__ = "Claw-Litle Team"
__description__ = "Claw-Litle 1.0 - Personal Agentic Operating System"

from .gateway import Gateway, SecurityConfig, Request, Response
from .hybrid_engine import HybridEngine, IntentResult
from .router import Router, RouterConfig, RouterResult

__all__ = [
    "__version__",
    "__author__",
    "__description__",
    "Gateway",
    "SecurityConfig", 
    "Request",
    "Response",
    "HybridEngine",
    "IntentResult",
    "Router",
    "RouterConfig",
    "RouterResult",
]