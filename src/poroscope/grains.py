"""Grain size analysis module for PoroScope.

Provides watershed-based grain segmentation, calibrated measurements,
ASTM grain size number calculation, and summary statistics.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy import ndimage as ndi
from skimage import feature, measure, morphology, segmentation


@dataclass(frozen=True)
class GrainAnalysisResult:
    """Result of a complete grain analysis pipeline."""

    labels: np.ndarray
    measurements: pd.DataFrame
    summary: dict[str, Any]
    pixel_size: float
    unit: str


GRAIN_MEASUREMENT_COLUMNS = [
    "label",
    "area_px",
    "area_unit2",
    "equivalent_diameter_px",
    "equivalent_diameter_unit",
    "perimeter_px",
    "circularity",
    "major_axis_length_px",
    "minor_axis_length_px",
    "aspect_ratio",
    "centroid_x_px",
    "centroid_y_px",
    "bbox_min_row",
    "bbox_min_col",
    "bbox_max_row",
    "bbox_max_col",
    "touches_border",
]


def distance_transform_based_segmentation(
    binary: np.ndarray,
    min_distance: int = 5,
    compactness: float = 0.0,
) -> np.ndarray:
    """Segment touching objects using distance-transform watershed.

    Parameters
    ----------
    binary : np.ndarray
        Binary image where grains are True/positive.
    min_distance : int
        Minimum distance between peaks for marker detection.
    compactness : float
        Watershed compactness parameter (0=standard, higher=more compact).

    Returns
    -------
    np.ndarray
        Labeled image (0=background, 1..N=grains).
    """
    binary = np.asarray(binary, dtype=bool)
    if binary.ndim != 2:
        raise ValueError("Expected a 2D binary image.")

    # Distance transform
    distance = ndi.distance_transform_edt(binary)

    if distance.max() == 0:
        return np.zeros_like(binary, dtype=np.int32)

    # Find local maxima as markers
    # Scale min_distance based on image size
    local_maxi = feature.peak_local_max(
        distance,
        min_distance=min_distance,
        exclude_border=False,
        labels=binary,
    )

    if len(local_maxi) == 0:
        # Fallback: everything is one grain
        return measure.label(binary, connectivity=2)

    markers = np.zeros_like(binary, dtype=np.int32)
    markers[tuple(local_maxi.T)] = np.arange(1, len(local_maxi) + 1)

    # Watershed
    labels = segmentation.watershed(
        -distance,
        markers,
        mask=binary,
        compactness=compactness,
    )
    return labels


def segment_grains(
    grayscale: np.ndarray | None = None,
    binary: np.ndarray | None = None,
    min_distance: int = 5,
    compactness: float = 0.0,
) -> np.ndarray:
    """Segment individual grains from a grayscale or binary image.

    Parameters
    ----------
    grayscale : np.ndarray, optional
        Grayscale image. If provided, Otsu thresholding is applied first.
    binary : np.ndarray, optional
        Pre-thresholded binary image (grains=True/positive).
        Exactly one of grayscale or binary must be provided.
    min_distance : int
        Minimum distance between grain centers.
    compactness : float
        Watershed compactness.

    Returns
    -------
    np.ndarray
        Labeled image (0=background, 1..N=grains).
    """
    if grayscale is not None and binary is not None:
        raise ValueError("Provide either grayscale or binary, not both.")
    if grayscale is None and binary is None:
        raise ValueError("Provide either grayscale or binary.")

    if grayscale is not None:
        from .segmentation import threshold_image

        binary, _ = threshold_image(grayscale, method="otsu", pores="bright")

    return distance_transform_based_segmentation(
        np.asarray(binary, dtype=bool),
        min_distance=min_distance,
        compactness=compactness,
    )


def measure_grains(
    label_image: np.ndarray,
    pixel_size: float,
    unit: str,
    exclude_border: bool = True,
) -> pd.DataFrame:
    """Measure each labeled grain region.

    Parameters
    ----------
    label_image : np.ndarray
        Labeled image from segment_grains.
    pixel_size : float
        Physical size of one pixel in `unit`.
    unit : str
        Unit string (e.g. 'um', 'nm', 'mm').
    exclude_border : bool
        If True, exclude grains touching the image border.

    Returns
    -------
    pd.DataFrame
        Per-grain measurements with calibrated columns.
    """
    if pixel_size <= 0:
        raise ValueError("pixel_size must be positive.")

    labels = np.asarray(label_image)
    if labels.ndim != 2:
        raise ValueError("measure_grains expects a 2D label image.")

    rows: list[dict[str, Any]] = []
    height, width = labels.shape

    for region in measure.regionprops(labels):
        # Border exclusion
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
                "major_axis_length_px": major_axis,
                "minor_axis_length_px": minor_axis,
                "aspect_ratio": aspect_ratio,
                "centroid_x_px": float(centroid_col),
                "centroid_y_px": float(centroid_row),
                "bbox_min_row": int(min_row),
                "bbox_min_col": int(min_col),
                "bbox_max_row": int(max_row),
                "bbox_max_col": int(max_col),
                "touches_border": bool(touches_border),
            }
        )

    return pd.DataFrame(rows, columns=GRAIN_MEASUREMENT_COLUMNS)


def astm_grain_size_number(grains_per_mm2: float) -> float:
    """Calculate ASTM grain size number G from grains/mm².

    Formula: G = -2.9542 + 6.6459 * log10(N_A)

    Where N_A is the number of grains per mm².

    Parameters
    ----------
    grains_per_mm2 : float
        Number of grains per square millimeter.

    Returns
    -------
    float
        ASTM grain size number G.

    Raises
    ------
    ValueError
        If grains_per_mm2 <= 0.
    """
    if grains_per_mm2 <= 0:
        raise ValueError("grains_per_mm2 must be positive.")
    return -2.9542 + 6.6459 * math.log10(grains_per_mm2)


def summarize_grains(measurements: pd.DataFrame) -> dict[str, Any]:
    """Build summary statistics from grain measurements.

    Parameters
    ----------
    measurements : pd.DataFrame
        Output from measure_grains.

    Returns
    -------
    dict
        Summary statistics.
    """
    n_grains = len(measurements)

    if measurements.empty:
        return {
            "grain_count": 0,
            "mean_grain_diameter_unit": None,
            "median_grain_diameter_unit": None,
            "std_grain_diameter_unit": None,
            "min_grain_diameter_unit": None,
            "max_grain_diameter_unit": None,
            "mean_grain_area_unit2": None,
            "median_grain_area_unit2": None,
            "mean_circularity": None,
            "mean_aspect_ratio": None,
            "astm_grain_size_number": None,
        }

    diameter = measurements["equivalent_diameter_unit"]
    area = measurements["area_unit2"]
    area_px = measurements["area_px"]

    # Total analyzed area in mm² (from image area, excluding border-touching grains)
    # Use the grain area sum as effective analyzed area
    total_grain_area_mm2 = area.sum()
    # Grains per mm²
    grains_per_mm2 = n_grains / total_grain_area_mm2 if total_grain_area_mm2 > 0 else 0

    try:
        astm_g = astm_grain_size_number(grains_per_mm2) if grains_per_mm2 > 0 else None
    except (ValueError, ZeroDivisionError):
        astm_g = None

    return {
        "grain_count": n_grains,
        "mean_grain_diameter_unit": float(diameter.mean()),
        "median_grain_diameter_unit": float(diameter.median()),
        "std_grain_diameter_unit": float(diameter.std()),
        "min_grain_diameter_unit": float(diameter.min()),
        "max_grain_diameter_unit": float(diameter.max()),
        "mean_grain_area_unit2": float(area.mean()),
        "median_grain_area_unit2": float(area.median()),
        "mean_circularity": float(measurements["circularity"].mean()),
        "mean_aspect_ratio": float(measurements["aspect_ratio"].mean()),
        "astm_grain_size_number": astm_g,
    }


def analyze_grains(
    grayscale: np.ndarray | None = None,
    binary: np.ndarray | None = None,
    pixel_size: float = 1.0,
    unit: str = "px",
    min_distance: int = 5,
    exclude_border: bool = True,
) -> GrainAnalysisResult:
    """Run complete grain analysis pipeline.

    Parameters
    ----------
    grayscale : np.ndarray, optional
        Grayscale image.
    binary : np.ndarray, optional
        Binary image.
    pixel_size : float
        Physical pixel size.
    unit : str
        Unit of pixel_size.
    min_distance : int
        Min distance between grain centers.
    exclude_border : bool
        Exclude border-touching grains.

    Returns
    -------
    GrainAnalysisResult
        Labels, measurements, and summary.
    """
    labels = segment_grains(
        grayscale=grayscale, binary=binary, min_distance=min_distance
    )
    measurements = measure_grains(
        labels, pixel_size=pixel_size, unit=unit, exclude_border=exclude_border
    )
    summary = summarize_grains(measurements)
    return GrainAnalysisResult(
        labels=labels,
        measurements=measurements,
        summary=summary,
        pixel_size=pixel_size,
        unit=unit,
    )
