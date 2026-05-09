"""Generate a lightweight synthetic microstructure image for PoroScope examples."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import tifffile
from skimage import draw, filters, io, util


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
TIFF_PATH = DATA_DIR / "synthetic_microstructure.tif"
PNG_PATH = DATA_DIR / "synthetic_microstructure.png"


def generate_synthetic_microstructure(size: int = 256, seed: int = 7) -> np.ndarray:
    """Create a deterministic grayscale ceramic/metal-like porosity proxy."""

    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size]
    background = 205 + 12 * np.sin(x / 34.0) + 8 * np.cos(y / 29.0)
    image = background + rng.normal(0, 4, size=(size, size))

    pores = [
        (54, 58, 17),
        (86, 174, 13),
        (128, 96, 22),
        (164, 188, 19),
        (202, 62, 15),
        (212, 136, 11),
        (42, 210, 10),
    ]
    for row, col, radius in pores:
        row_scale = rng.uniform(0.75, 1.25)
        col_scale = rng.uniform(0.75, 1.3)
        angle = rng.uniform(-0.45, 0.45)
        rr, cc = draw.ellipse(
            row,
            col,
            radius * row_scale,
            radius * col_scale,
            rotation=angle,
            shape=image.shape,
        )
        pore_intensity = rng.uniform(20, 48)
        image[rr, cc] = pore_intensity + rng.normal(0, 3, size=rr.shape)

    for _ in range(12):
        row = int(rng.integers(18, size - 18))
        col = int(rng.integers(18, size - 18))
        radius = int(rng.integers(3, 7))
        rr, cc = draw.disk((row, col), radius, shape=image.shape)
        image[rr, cc] = rng.uniform(35, 70)

    image = filters.gaussian(image, sigma=0.6, preserve_range=True)
    image = np.clip(image, 0, 255)
    return image.astype(np.uint8)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    image = generate_synthetic_microstructure()
    tifffile.imwrite(TIFF_PATH, image)
    io.imsave(PNG_PATH, util.img_as_ubyte(image), check_contrast=False)
    print(f"Wrote {TIFF_PATH}")
    print(f"Wrote {PNG_PATH}")


if __name__ == "__main__":
    main()

