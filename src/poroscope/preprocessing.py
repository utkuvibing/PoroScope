"""Preprocessing helpers for v0.1 porosity analysis."""

from __future__ import annotations

import numpy as np
from skimage import exposure
from skimage.color import rgb2gray

from .config import Crop


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert 2D, RGB, or RGBA images to grayscale normalized to 0-255."""

    array = np.asarray(image)
    if array.ndim == 2:
        gray = array
    elif array.ndim == 3 and array.shape[2] in {3, 4}:
        rgb = array[..., :3]
        gray = rgb2gray(rgb)
    else:
        raise ValueError("Expected a 2D grayscale image or 3D RGB/RGBA image.")
    return normalize_to_uint8_range(gray)


def normalize_to_uint8_range(image: np.ndarray) -> np.ndarray:
    """Return a floating-point image in the 0-255 intensity range."""

    array = np.asarray(image)
    if array.dtype == np.bool_:
        return array.astype(np.float64) * 255.0
    if np.issubdtype(array.dtype, np.integer):
        info = np.iinfo(array.dtype)
        if info.max == info.min:
            return np.zeros(array.shape, dtype=np.float64)
        return array.astype(np.float64) / float(info.max) * 255.0

    array = array.astype(np.float64, copy=False)
    finite = array[np.isfinite(array)]
    if finite.size == 0:
        raise ValueError("Image contains no finite intensity values.")
    min_value = float(finite.min())
    max_value = float(finite.max())
    if min_value >= 0.0 and max_value <= 1.0:
        return np.clip(array, 0.0, 1.0) * 255.0
    if min_value >= 0.0 and max_value <= 255.0:
        return np.clip(array, 0.0, 255.0)
    if max_value == min_value:
        return np.zeros(array.shape, dtype=np.float64)
    return (array - min_value) / (max_value - min_value) * 255.0


def apply_crop(image: np.ndarray, crop: Crop | None) -> np.ndarray:
    """Apply an optional x, y, width, height crop."""

    if crop is None:
        return image
    crop.validate(image.shape[:2])
    return image[crop.y : crop.y + crop.height, crop.x : crop.x + crop.width]


def apply_clahe(
    image: np.ndarray,
    kernel_size: tuple[int, int] | None = None,
    clip_limit: float = 0.01,
    nbins: int = 256,
) -> np.ndarray:
    """Apply Contrast Limited Adaptive Histogram Equalization (CLAHE).

    Improves local contrast and is especially useful for SEM images with
    uneven illumination.

    Parameters
    ----------
    image : np.ndarray
        2D grayscale image.
    kernel_size : tuple[int, int], optional
        Size of the contextual region (kernel) in pixels.
        Default is 1/8 of image dimensions.
    clip_limit : float
        Clipping limit, normalized between 0 and 1. Higher values
        increase contrast. Default 0.01.
    nbins : int
        Number of histogram bins. Default 256.

    Returns
    -------
    np.ndarray
        CLAHE-enhanced image (float64, 0-255 range).
    """
    image = np.asarray(image)
    if image.ndim != 2:
        raise ValueError("CLAHE requires a 2D grayscale image.")

    if kernel_size is None:
        h, w = image.shape
        kernel_size = (max(8, h // 8), max(8, w // 8))

    # Normalize to [0, 1] for skimage equalization
    img_norm = image.astype(np.float64)
    img_min, img_max = img_norm.min(), img_norm.max()
    if img_max > img_min:
        img_norm = (img_norm - img_min) / (img_max - img_min)
    else:
        img_norm = np.zeros_like(img_norm)

    enhanced = exposure.equalize_adapthist(
        img_norm,
        kernel_size=kernel_size,
        clip_limit=clip_limit,
        nbins=nbins,
    )

    # Scale back to 0-255
    return enhanced * 255.0

