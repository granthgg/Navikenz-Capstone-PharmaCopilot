"""
Data Collectors Package for PharmaCopilot Report Generation
Provides collectors for different types of manufacturing data
"""

from .forecasting_collector import ForecastingCollector
from .classification_collector import ClassificationCollector
from .rl_collector import RLCollector

__all__ = [
    'ForecastingCollector',
    'ClassificationCollector', 
    'RLCollector'
]

__version__ = '1.0.0'
