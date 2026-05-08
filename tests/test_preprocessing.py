import numpy as np
import pytest

from poroscope.config import Crop
from poroscope.preprocessing import apply_crop, to_grayscale


def test_grayscale_2d_passes_shape():
    image = np.arange(9, dtype=np.uint8).reshape(3, 3)
    gray = to_grayscale(image)
    assert gray.shape == (3, 3)
    assert gray.dtype == np.float64


def test_rgb_converts_to_2d_grayscale():
    image = np.zeros((4, 5, 3), dtype=np.uint8)
    image[..., 0] = 255
    gray = to_grayscale(image)
    assert gray.shape == (4, 5)
    assert np.all(gray > 0)


def test_rgba_ignores_alpha_channel():
    image = np.zeros((2, 2, 4), dtype=np.uint8)
    image[..., :3] = 255
    image[..., 3] = 0
    gray = to_grayscale(image)
    assert gray.shape == (2, 2)
    assert np.allclose(gray, 255)


def test_crop_applies_xy_width_height():
    image = np.arange(25).reshape(5, 5)
    cropped = apply_crop(image, Crop(x=1, y=2, width=3, height=2))
    assert cropped.shape == (2, 3)
    np.testing.assert_array_equal(cropped, image[2:4, 1:4])


def test_invalid_crop_raises():
    image = np.zeros((5, 5))
    with pytest.raises(ValueError, match="beyond image bounds"):
        apply_crop(image, Crop(x=4, y=4, width=2, height=2))

