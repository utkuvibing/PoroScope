"""Calibrated porosity and pore morphology measurements."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from skimage.measure import regionprops

MEASUREMENT_COLUMNS = [
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


def measure_regions(label_image: np.ndarray, pixel_size: float) -> pd.DataFrame:
    """Measure each labeled pore region with calibrated length and area columns."""

    if pixel_size <= 0:
        raise ValueError("pixel_size must be positive.")
    labels = np.asarray(label_image)
    if labels.ndim != 2:
        raise ValueError("measure_regions expects a 2D label image.")

    rows: list[dict[str, Any]] = []
    height, width = labels.shape
    for region in regionprops(labels):
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
        min_row, min_col, max_row, max_col = region.bbox
        touches_border = min_row == 0 or min_col == 0 or max_row == height or max_col == width
        centroid_row, centroid_col = region.centroid
        rows.append(
            {
                "label": int(region.label),
                "area_px": area_px,
                "area_unit2": area_px * pixel_size**2,
                "equivalent_diameter_px": float(region.equivalent_diameter_area),
                "equivalent_diameter_unit": float(region.equivalent_diameter_area) * pixel_size,
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
    return pd.DataFrame(rows, columns=MEASUREMENT_COLUMNS)


def summarize_measurements(
    mask: np.ndarray,
    measurements: pd.DataFrame,
    *,
    pixel_size: float,
    unit: str,
    image_shape: tuple[int, int],
    threshold_method: str,
    threshold_value: float,
    pores: str,
    min_size: int,
    fill_holes: bool,
) -> dict[str, Any]:
    """Build JSON-serializable summary metrics for one analysis."""

    pore_pixels = int(np.count_nonzero(mask))
    analyzed_pixels = int(mask.size)
    porosity_percent = (pore_pixels / analyzed_pixels * 100.0) if analyzed_pixels else 0.0

    if measurements.empty:
        stats = {
            "mean_pore_area_unit2": None,
            "median_pore_area_unit2": None,
            "min_pore_area_unit2": None,
            "max_pore_area_unit2": None,
        }
    else:
        area = measurements["area_unit2"]
        stats = {
            "mean_pore_area_unit2": float(area.mean()),
            "median_pore_area_unit2": float(area.median()),
            "min_pore_area_unit2": float(area.min()),
            "max_pore_area_unit2": float(area.max()),
        }

    return {
        "image_width_px": int(image_shape[1]),
        "image_height_px": int(image_shape[0]),
        "analyzed_pixel_count": analyzed_pixels,
        "pore_pixel_count": pore_pixels,
        "porosity_percent": float(porosity_percent),
        "pore_count": int(len(measurements)),
        "pixel_size": float(pixel_size),
        "unit": unit,
        "threshold_method": threshold_method,
        "threshold_value": float(threshold_value),
        "pores": pores,
        "min_size": int(min_size),
        "fill_holes": bool(fill_holes),
        **stats,
    }
