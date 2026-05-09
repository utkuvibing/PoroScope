"""PoroScope: calibrated porosity analysis for microscopy images."""

__version__ = "0.2.0"

from .config import AnalysisConfig, Crop
from .pipeline import AnalysisResult, analyze_image

__all__ = ["AnalysisConfig", "AnalysisResult", "Crop", "analyze_image"]
