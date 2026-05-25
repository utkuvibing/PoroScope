"""Thresholding, mask cleanup, and labeling."""

from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from skimage import filters, measure, morphology


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


def threshold_sauvola(
    grayscale: np.ndarray,
    window_size: int = 25,
    k: float = 0.2,
    r: float | None = None,
    pores: str = "dark",
) -> tuple[np.ndarray, np.ndarray]:
    """Apply Sauvola's local thresholding.

    Sauvola's method is robust for unevenly illuminated images and is
     particularly effective for SEM micrographs with varying brightness.

    Parameters
    ----------
    grayscale : np.ndarray
        2D grayscale image.
    window_size : int
        Size of the local neighborhood (must be odd, >= 5).
    k : float
        Sauvola sensitivity parameter. Default 0.2.
        Lower values = more sensitive (detects more).
    r : float, optional
        Dynamic range of standard deviation. Default is 128.
    pores : str
        'dark' for below-threshold, 'bright' for above-threshold.

    Returns
    -------
    mask : np.ndarray
        Binary mask (True = detected features).
    threshold_map : np.ndarray
        Per-pixel threshold values.
    """
    image = np.asarray(grayscale, dtype=np.float64)
    if image.ndim != 2:
        raise ValueError("threshold_sauvola expects a 2D grayscale image.")
    if window_size < 5 or window_size % 2 == 0:
        raise ValueError("window_size must be an odd integer >= 5.")
    if pores not in {"dark", "bright"}:
        raise ValueError("pores must be 'dark' or 'bright'.")

    # Normalize to [0, 1] for stable threshold computation
    img_min, img_max = image.min(), image.max()
    if img_max > img_min:
        image_norm = (image - img_min) / (img_max - img_min)
    else:
        image_norm = np.zeros_like(image)

    threshold_map = filters.threshold_sauvola(
        image_norm, window_size=window_size, k=k, r=r
    )
    if pores == "dark":
        mask = image_norm <= threshold_map
    else:
        mask = image_norm >= threshold_map
    return np.asarray(mask, dtype=bool), np.asarray(threshold_map, dtype=np.float64)


def threshold_niblack(
    grayscale: np.ndarray,
    window_size: int = 25,
    k: float = -0.2,
) -> tuple[np.ndarray, np.ndarray]:
    """Apply Niblack's local thresholding.

    Similar to Sauvola but with a simpler formula. Best for images with
    consistent local contrast.

    Parameters
    ----------
    grayscale : np.ndarray
        2D grayscale image.
    window_size : int
        Size of the local neighborhood (must be odd, >= 5).
    k : float
        Niblack sensitivity parameter. Default -0.2.
        Positive k detects bright features, negative detects dark features.

    Returns
    -------
    mask : np.ndarray
        Binary mask (True = detected features).
    threshold_map : np.ndarray
        Per-pixel threshold values.
    """
    image = np.asarray(grayscale, dtype=np.float64)
    if image.ndim != 2:
        raise ValueError("threshold_niblack expects a 2D grayscale image.")
    if window_size < 5 or window_size % 2 == 0:
        raise ValueError("window_size must be an odd integer >= 5.")

    threshold_map = filters.threshold_niblack(
        image, window_size=window_size, k=k
    )
    mask = image < threshold_map  # below threshold = dark features
    return np.asarray(mask, dtype=bool), np.asarray(threshold_map, dtype=np.float64)


def local_otsu(
    grayscale: np.ndarray,
    block_size: int = 25,
    pores: str = "dark",
) -> tuple[np.ndarray, np.ndarray]:
    """Apply local Otsu thresholding per image block.

    Divides the image into blocks and applies Otsu's method on each block
    independently. Effective for images with varying background.

    Parameters
    ----------
    grayscale : np.ndarray
        2D grayscale image.
    block_size : int
        Size of each block in pixels.
    pores : str
        'dark' or 'bright'.

    Returns
    -------
    mask : np.ndarray
        Binary mask.
    threshold_map : np.ndarray
        Per-pixel threshold values.
    """
    image = np.asarray(grayscale, dtype=np.float64)
    if image.ndim != 2:
        raise ValueError("local_otsu expects a 2D grayscale image.")
    if pores not in {"dark", "bright"}:
        raise ValueError("pores must be 'dark' or 'bright'.")

    thresh_image = filters.rank.otsu(
        image.astype(np.uint16),
        morphology.disk(block_size // 2),
    ).astype(np.float64)

    if pores == "dark":
        mask = image <= thresh_image
    else:
        mask = image > thresh_image

    return np.asarray(mask, dtype=bool), np.asarray(thresh_image, dtype=np.float64)
