"""Overlay rendering for visual segmentation checks."""

from __future__ import annotations

import numpy as np
from skimage.segmentation import find_boundaries


def create_overlay(grayscale: np.ndarray, mask: np.ndarray, alpha: float = 0.38) -> np.ndarray:
    """Create an RGB overlay with red pore fill and yellow pore boundaries."""

    gray = np.asarray(grayscale, dtype=np.float64)
    gray = np.clip(gray, 0.0, 255.0)
    base = np.stack([gray, gray, gray], axis=-1)

    pore_color = np.array([255.0, 40.0, 40.0])
    overlay = base.copy()
    pore_mask = np.asarray(mask, dtype=bool)
    overlay[pore_mask] = (1.0 - alpha) * overlay[pore_mask] + alpha * pore_color

    boundaries = find_boundaries(pore_mask, mode="outer")
    overlay[boundaries] = np.array([255.0, 230.0, 0.0])
    return np.clip(overlay, 0, 255).astype(np.uint8)

