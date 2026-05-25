"""PoroScope: calibrated porosity analysis for microscopy images."""

__version__ = "0.2.0"

from .config import AnalysisConfig, Crop
from .grains import GrainAnalysisResult, analyze_grains, segment_grains, measure_grains
from .phases import PhaseAnalysisResult, analyze_phases, multi_otsu, measure_phase_fractions
from .pipeline import AnalysisResult, analyze_image

__all__ = [
    "AnalysisConfig",
    "AnalysisResult",
    "Crop",
    "GrainAnalysisResult",
    "PhaseAnalysisResult",
    "analyze_grains",
    "analyze_image",
    "analyze_phases",
    "measure_grains",
    "measure_phase_fractions",
    "multi_otsu",
    "segment_grains",
]
