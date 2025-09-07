"""
A/B Testing and Experimentation Framework.

This package provides comprehensive A/B testing capabilities including:
- Experiment design and configuration
- User segmentation and traffic splitting
- Statistical analysis and significance testing
- Performance monitoring and metrics collection
- Automated experiment lifecycle management
"""

from .framework import (
    ABTestingFramework, ExperimentManager, Experiment, 
    ExperimentConfig, ExperimentStatus, ExperimentVariant, VariantType
)

__all__ = [
    'ABTestingFramework',
    'ExperimentManager', 
    'Experiment',
    'ExperimentConfig',
    'ExperimentStatus',
    'ExperimentVariant',
    'VariantType'
]