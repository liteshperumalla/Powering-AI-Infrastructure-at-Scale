"""
Base model infrastructure for dual-mode operation.

This module provides base classes and utilities for models that can operate
both with and without database connections.
"""

from .standalone_model import StandaloneModel
from .model_factory import ModelFactory, ModelMode
from .database_utils import DatabaseStatus

__all__ = [
    "StandaloneModel",
    "ModelFactory", 
    "ModelMode",
    "DatabaseStatus"
]