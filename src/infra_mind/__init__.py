"""
Infra Mind - AI-powered infrastructure advisory platform.

A sophisticated multi-agent system that provides comprehensive AI infrastructure
recommendations, compliance guidance, and strategic roadmaps for enterprises.
"""

__version__ = "0.1.0"
__author__ = "Infra Mind Team"
__email__ = "team@inframind.ai"

# Core imports for easy access
from .core.config import settings
from .core.database import init_database
from .core.logging import setup_logging

__all__ = [
    "settings",
    "init_database", 
    "setup_logging",
]