"""Thresholding, mask cleanup, and labeling."""

from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from skimage import filters, measure

from .config import PorePolarity, ThresholdMethod


def threshold_image(
    grayscale: np.ndarray,
    method: ThresholdMethod = "otsu",
    pores: PorePolarity = "dark",
    threshold_value: float | None = None,
) -> tuple[np.ndarray, float]:
    """Create a boolean pore mask from a grayscale image."""

    if method not in {"otsu", "manual"}:
        raise ValueError("threshold method must be 'otsu' or 'manual'.")
    if pores not in {"dark", "bright"}:
        raise ValueError("pores must be 'dark' or 'bright'.")

    image = np.asarray(grayscale, dtype=np.float64)
    if image.ndim != 2:
        raise ValueError("threshold_image expects a 2D grayscale image.")

    if method == "otsu":
        if image.size == 0:
            raise ValueError("Cannot threshold an empty image.")
        value = float(filters.threshold_otsu(image))
    else:
        if threshold_value is None:
            raise ValueError("threshold_value is required for manual thresholding.")
        value = float(threshold_value)
        if value < 0.0 or value > 255.0:
            raise ValueError("Manual threshold_value must be between 0 and 255.")

    if pores == "dark":
        return image < value, value
    return image > value, value


def clean_mask(mask: np.ndarray, min_size: int = 20, fill_holes: bool = False) -> np.ndarray:
    """Remove very small pore objects and optionally fill internal holes."""

    if min_size < 0:
        raise ValueError("min_size must be non-negative.")
    cleaned = np.asarray(mask, dtype=bool)
    if min_size > 0:
        labels = measure.label(cleaned, connectivity=1)
        counts = np.bincount(labels.ravel())
        remove_labels = np.flatnonzero(counts < min_size)
        remove_labels = remove_labels[remove_labels != 0]
        if remove_labels.size:
            cleaned = cleaned.copy()
            cleaned[np.isin(labels, remove_labels)] = False
    if fill_holes:
        cleaned = ndi.binary_fill_holes(cleaned)
    return np.asarray(cleaned, dtype=bool)


def label_mask(mask: np.ndarray) -> np.ndarray:
    """Label pore regions using 4-connectivity in 2D."""

    return measure.label(np.asarray(mask, dtype=bool), connectivity=1)
