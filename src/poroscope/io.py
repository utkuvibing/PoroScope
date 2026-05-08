"""Image loading utilities."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import tifffile
from skimage import io as skio

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}


def validate_image_path(path: str | Path) -> Path:
    image_path = Path(path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image file does not exist: {image_path}")
    if image_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(f"Unsupported image format '{image_path.suffix}'. Supported: {supported}")
    return image_path


def load_image(path: str | Path) -> np.ndarray:
    """Load PNG, JPG/JPEG, or TIFF image into a NumPy array."""

    image_path = validate_image_path(path)
    if image_path.suffix.lower() in {".tif", ".tiff"}:
        image = tifffile.imread(image_path)
    else:
        image = skio.imread(image_path)
    if image.size == 0:
        raise ValueError("Loaded image is empty.")
    return np.asarray(image)

