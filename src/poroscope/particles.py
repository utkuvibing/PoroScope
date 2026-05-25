"""Particle analysis module for PoroScope.

Provides particle detection, size distribution analysis,
shape factor computation, and statistical summaries.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from skimage import measure


@dataclass(frozen=True)
class ParticleAnalysisResult:
    """Result of a complete particle analysis."""

    labels: np.ndarray
    measurements: pd.DataFrame
    summary: dict[str, Any]
    size_distribution: dict[str, list[float]] | None
    pixel_size: float
    unit: str


PARTICLE_MEASUREMENT_COLUMNS = [
    "label",
    "area_px",
    "area_unit2",
    "equivalent_diameter_px",
    "equivalent_diameter_unit",
    "perimeter_px",
    "circularity",
    "convexity",
    "solidity",
    "major_axis_length_px",
    "minor_axis_length_px",
    "aspect_ratio",
    "eccentricity",
    "centroid_x_px",
    "centroid_y_px",
    "bbox_min_row",
    "bbox_min_col",
    "bbox_max_row",
    "bbox_max_col",
    "touches_border",
]


def segment_particles(
    binary: np.ndarray,
    min_size: int = 10,
) -> np.ndarray:
    """Label individual particles in a binary image.

    Parameters
    ----------
    binary : np.ndarray
        Binary image (particles = True/positive).
    min_size : int
        Minimum particle area in pixels (smaller objects removed).

    Returns
    -------
    np.ndarray
        Labeled image (0=background, 1..N=particles).
    """
    binary = np.asarray(binary, dtype=bool)
    if binary.ndim != 2:
        raise ValueError("segment_particles expects a 2D binary image.")

    # Label connected components
    labels = measure.label(binary, connectivity=2)

    # Remove small objects below min_size
    if min_size > 0:
        region_sizes = np.bincount(labels.ravel())
        small_labels = np.flatnonzero(region_sizes < min_size)
        small_labels = small_labels[small_labels != 0]  # exclude background
        if len(small_labels) > 0:
            mask = np.isin(labels, small_labels)
            labels = labels.copy()
            labels[mask] = 0

    # Renumber labels consecutively
    unique_labels = np.unique(labels)
    renumber = {old: new for new, old in enumerate(sorted(unique_labels))}
    renumbered = np.zeros_like(labels)
    for old, new in renumber.items():
        renumbered[labels == old] = new

    return renumbered


def measure_particles(
    label_image: np.ndarray,
    pixel_size: float,
    unit: str,
    exclude_border: bool = True,
) -> pd.DataFrame:
    """Measure each labeled particle region.

    Parameters
    ----------
    label_image : np.ndarray
        Labeled image from segment_particles.
    pixel_size : float
        Physical size of one pixel.
    unit : str
        Unit string.
    exclude_border : bool
        If True, exclude particles touching the image border.

    Returns
    -------
    pd.DataFrame
        Per-particle measurements with calibrated columns.
    """
    if pixel_size <= 0:
        raise ValueError("pixel_size must be positive.")

    labels = np.asarray(label_image)
    if labels.ndim != 2:
        raise ValueError("measure_particles expects a 2D label image.")

    rows: list[dict[str, Any]] = []
    height, width = labels.shape

    for region in measure.regionprops(labels):
        min_row, min_col, max_row, max_col = region.bbox
        touches_border = (
            min_row == 0 or min_col == 0 or max_row == height or max_col == width
        )
        if exclude_border and touches_border:
            continue

        area_px = float(region.area)
        perimeter_px = float(region.perimeter)
        minor_axis = float(region.axis_minor_length)
        major_axis = float(region.axis_major_length)
        circularity = (
            4.0 * math.pi * area_px / (perimeter_px**2)
            if perimeter_px > 0.0
            else math.nan
        )
        aspect_ratio = major_axis / minor_axis if minor_axis > 0.0 else math.nan
        eccentricity = float(region.eccentricity) if hasattr(region, "eccentricity") else math.nan

        # Convex hull measurements
        convex_area = float(region.area_convex) if hasattr(region, "area_convex") else area_px
        convexity = convex_area / area_px if area_px > 0 else math.nan
        solidity = float(region.solidity) if hasattr(region, "solidity") else math.nan

        centroid_row, centroid_col = region.centroid

        rows.append(
            {
                "label": int(region.label),
                "area_px": area_px,
                "area_unit2": area_px * pixel_size**2,
                "equivalent_diameter_px": float(region.equivalent_diameter_area),
                "equivalent_diameter_unit": float(region.equivalent_diameter_area)
                * pixel_size,
                "perimeter_px": perimeter_px,
                "circularity": circularity,
                "convexity": convexity,
                "solidity": solidity,
                "major_axis_length_px": major_axis,
                "minor_axis_length_px": minor_axis,
                "aspect_ratio": aspect_ratio,
                "eccentricity": eccentricity,
                "centroid_x_px": float(centroid_col),
                "centroid_y_px": float(centroid_row),
                "bbox_min_row": int(min_row),
                "bbox_min_col": int(min_col),
                "bbox_max_row": int(max_row),
                "bbox_max_col": int(max_col),
                "touches_border": bool(touches_border),
            }
        )

    return pd.DataFrame(rows, columns=PARTICLE_MEASUREMENT_COLUMNS)


def particle_size_distribution(
    measurements: pd.DataFrame,
    bins: int = 10,
    unit: str = "unit",
) -> dict[str, list[float]]:
    """Compute particle size distribution histogram.

    Parameters
    ----------
    measurements : pd.DataFrame
        Output from measure_particles.
    bins : int
        Number of histogram bins.
    unit : str
        Label for the unit axis.

    Returns
    -------
    dict
        Histogram with bin_edges, bin_counts, bin_centers.
    """
    if measurements.empty:
        return {
            "bin_edges": [],
            "bin_counts": [],
            "bin_centers": [],
        }

    diameters = measurements["equivalent_diameter_unit"].values
    counts, edges = np.histogram(diameters, bins=bins)
    centers = (edges[:-1] + edges[1:]) / 2.0

    return {
        "bin_edges": [float(e) for e in edges],
        "bin_counts": [int(c) for c in counts],
        "bin_centers": [float(c) for c in centers],
    }


def summarize_particles(measurements: pd.DataFrame) -> dict[str, Any]:
    """Build summary statistics from particle measurements.

    Parameters
    ----------
    measurements : pd.DataFrame
        Output from measure_particles.

    Returns
    -------
    dict
        Summary statistics.
    """
    if measurements.empty:
        return {
            "particle_count": 0,
            "mean_diameter_unit": None,
            "median_diameter_unit": None,
            "std_diameter_unit": None,
            "min_diameter_unit": None,
            "max_diameter_unit": None,
            "mean_area_unit2": None,
            "mean_circularity": None,
            "mean_aspect_ratio": None,
            "mean_convexity": None,
            "mean_eccentricity": None,
            "total_area_unit2": None,
        }

    diameter = measurements["equivalent_diameter_unit"]
    area = measurements["area_unit2"]

    return {
        "particle_count": len(measurements),
        "mean_diameter_unit": float(diameter.mean()),
        "median_diameter_unit": float(diameter.median()),
        "std_diameter_unit": float(diameter.std()),
        "min_diameter_unit": float(diameter.min()),
        "max_diameter_unit": float(diameter.max()),
        "mean_area_unit2": float(area.mean()),
        "mean_circularity": float(measurements["circularity"].mean()),
        "mean_aspect_ratio": float(measurements["aspect_ratio"].mean()),
        "mean_convexity": float(measurements["convexity"].mean()),
        "mean_eccentricity": float(measurements["eccentricity"].mean()),
        "total_area_unit2": float(area.sum()),
    }


def analyze_particles(
    binary: np.ndarray,
    pixel_size: float = 1.0,
    unit: str = "px",
    min_size: int = 10,
    exclude_border: bool = True,
    bins: int = 10,
) -> ParticleAnalysisResult:
    """Run complete particle analysis pipeline.

    Parameters
    ----------
    binary : np.ndarray
        Binary image (particles = True).
    pixel_size : float
        Physical pixel size.
    unit : str
        Unit of pixel_size.
    min_size : int
        Minimum particle area in pixels.
    exclude_border : bool
        Exclude border-touching particles.
    bins : int
        Number of histogram bins for size distribution.

    Returns
    -------
    ParticleAnalysisResult
        Labels, measurements, summary, and size distribution.
    """
    labels = segment_particles(binary, min_size=min_size)
    measurements = measure_particles(
        labels, pixel_size=pixel_size, unit=unit, exclude_border=exclude_border
    )
    summary = summarize_particles(measurements)
    size_dist = particle_size_distribution(measurements, bins=bins, unit=unit)

    return ParticleAnalysisResult(
        labels=labels,
        measurements=measurements,
        summary=summary,
        size_distribution=size_dist,
        pixel_size=pixel_size,
        unit=unit,
    )