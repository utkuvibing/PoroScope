import numpy as np
import pytest
import tifffile
from skimage import io as skio

from poroscope.io import load_image


def test_load_png_jpg_and_tiff(tmp_path):
    image = np.full((6, 7), 128, dtype=np.uint8)
    png = tmp_path / "sample.png"
    jpg = tmp_path / "sample.jpg"
    tiff = tmp_path / "sample.tif"
    skio.imsave(png, image, check_contrast=False)
    skio.imsave(jpg, image, check_contrast=False)
    tifffile.imwrite(tiff, image)

    assert load_image(png).shape[:2] == image.shape
    assert load_image(jpg).shape[:2] == image.shape
    assert load_image(tiff).shape[:2] == image.shape


def test_unsupported_image_format_raises(tmp_path):
    path = tmp_path / "sample.bmp"
    path.write_bytes(b"not an image")
    with pytest.raises(ValueError, match="Unsupported image format"):
        load_image(path)

