"""PoroScope: calibrated porosity analysis for microscopy images."""

__version__ = "0.2.0"

from .config import AnalysisConfig, Crop
from .grains import GrainAnalysisResult, analyze_grains, segment_grains, measure_grains
from .particles import ParticleAnalysisResult, analyze_particles, measure_particles, segment_particles
from .phases import PhaseAnalysisResult, analyze_phases, multi_otsu, measure_phase_fractions
from .pipeline import AnalysisResult, analyze_image

__all__ = [
    "AnalysisConfig",
    "AnalysisResult",
    "Crop",
    "GrainAnalysisResult",
    "ParticleAnalysisResult",
    "PhaseAnalysisResult",
    "analyze_grains",
    "analyze_image",
    "analyze_particles",
    "analyze_phases",
    "measure_grains",
    "measure_particles",
    "measure_phase_fractions",
    "multi_otsu",
    "segment_grains",
    "segment_particles",
]
