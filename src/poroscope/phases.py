"""Phase fraction analysis module for PoroScope.

Provides multi-class Otsu thresholding for N-phase microstructure
analysis, phase fraction quantification, and summary statistics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from skimage import filters


@dataclass(frozen=True)
class PhaseAnalysisResult:
    """Result of a complete phase analysis."""

    labels: np.ndarray
    measurements: pd.DataFrame
    summary: dict[str, Any]
    thresholds: list[float]
    pixel_size: float
    unit: str


def multi_otsu(
    grayscale: np.ndarray, n_classes: int = 3
) -> tuple[np.ndarray, list[float]]:
    """Segment a grayscale image into N phases using multi-Otsu thresholding.

    Parameters
    ----------
    grayscale : np.ndarray
        2D grayscale input image.
    n_classes : int
        Number of phases/classes (2-5). Default is 3.

    Returns
    -------
    labels : np.ndarray
        Integer label image (0=background/darkest, n_classes-1=brightest).
    thresholds : list[float]
        Threshold values between classes (length = n_classes - 1).
    """
    image = np.asarray(grayscale, dtype=np.float64)
    if image.ndim != 2:
        raise ValueError("multi_otsu expects a 2D grayscale image.")
    if not 2 <= n_classes <= 5:
        raise ValueError("n_classes must be between 2 and 5.")

    thresholds = filters.threshold_multiotsu(image, classes=n_classes)
    thresholds_list = [float(t) for t in thresholds]

    # Digitize: assign each pixel to a class based on thresholds
    labels = np.digitize(image, bins=thresholds_list).astype(np.int32)

    return labels, thresholds_list


def measure_phase_fractions(
    labels: np.ndarray,
    pixel_size: float,
    unit: str,
) -> pd.DataFrame:
    """Compute area fraction for each phase.

    Parameters
    ----------
    labels : np.ndarray
        Labeled image from multi_otsu.
    pixel_size : float
        Physical size of one pixel.
    unit : str
        Unit string.

    Returns
    -------
    pd.DataFrame
        Phase-level measurements with columns:
        phase, pixel_count, area_unit2, area_fraction, area_fraction_percent.
    """
    if pixel_size <= 0:
        raise ValueError("pixel_size must be positive.")

    labels = np.asarray(labels)
    total_pixels = labels.size
    phases_present = np.unique(labels)

    rows: list[dict[str, Any]] = []
    for phase in sorted(phases_present):
        pixel_count = int(np.count_nonzero(labels == phase))
        area_fraction = pixel_count / total_pixels
        rows.append(
            {
                "phase": int(phase),
                "pixel_count": pixel_count,
                "area_unit2": pixel_count * pixel_size**2,
                "area_fraction": float(area_fraction),
                "area_fraction_percent": float(area_fraction * 100.0),
            }
        )

    return pd.DataFrame(rows)


def summarize_phases(measurements: pd.DataFrame) -> dict[str, Any]:
    """Build summary from phase fraction measurements.

    Parameters
    ----------
    measurements : pd.DataFrame
        Output from measure_phase_fractions.

    Returns
    -------
    dict
        Summary with n_phases, dominant_phase, phase_fractions.
    """
    if measurements.empty:
        return {
            "n_phases": 0,
            "dominant_phase_index": None,
            "dominant_phase_fraction": None,
            "phase_fractions": {},
        }

    n_phases = len(measurements)
    dominant = measurements.loc[measurements["area_fraction"].idxmax()]

    phase_fractions = {
        int(row["phase"]): float(row["area_fraction"])
        for _, row in measurements.iterrows()
    }

    return {
        "n_phases": n_phases,
        "dominant_phase_index": int(dominant["phase"]),
        "dominant_phase_fraction": float(dominant["area_fraction"]),
        "phase_fractions": phase_fractions,
    }


def analyze_phases(
    grayscale: np.ndarray,
    n_classes: int = 3,
    pixel_size: float = 1.0,
    unit: str = "px",
) -> PhaseAnalysisResult:
    """Run complete multi-phase analysis pipeline.

    Parameters
    ----------
    grayscale : np.ndarray
        2D grayscale image.
    n_classes : int
        Number of phases to segment.
    pixel_size : float
        Physical pixel size.
    unit : str
        Unit of pixel_size.

    Returns
    -------
    PhaseAnalysisResult
        Labels, measurements, and summary.
    """
    labels, thresholds = multi_otsu(grayscale, n_classes=n_classes)
    measurements = measure_phase_fractions(labels, pixel_size=pixel_size, unit=unit)
    summary = summarize_phases(measurements)
    return PhaseAnalysisResult(
        labels=labels,
        measurements=measurements,
        summary=summary,
        thresholds=thresholds,
        pixel_size=pixel_size,
        unit=unit,
    )
