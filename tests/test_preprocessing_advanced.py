"""Tests for advanced preprocessing (CLAHE)."""

import numpy as np
import pytest


@pytest.fixture
def uneven_illumination():
    """Image with uneven illumination — darker on one side."""
    np.random.seed(42)
    img = np.zeros((100, 200), dtype=np.float64)
    # Gradient across the image
    gradient = np.linspace(0.3, 1.0, 200)[None, :]
    # Some features
    noise = np.random.normal(0.5, 0.15, (100, 200))
    img = gradient * 255 + noise * 50
    return np.clip(img, 0, 255).astype(np.uint8)


@pytest.fixture
def low_contrast():
    """Low contrast image — narrow intensity range."""
    img = np.ones((50, 50), dtype=np.uint8) * 128
    img[20:30, 20:30] = 140
    img[30:40, 30:40] = 115
    return img


def test_import():
    from poroscope.preprocessing import apply_clahe
    assert apply_clahe is not None


def test_clahe_returns_same_shape(low_contrast):
    from poroscope.preprocessing import apply_clahe
    result = apply_clahe(low_contrast)
    assert result.shape == low_contrast.shape
    assert result.dtype == np.float64


def test_clahe_increases_contrast(low_contrast):
    """CLAHE should increase the intensity range (more contrast)."""
    from poroscope.preprocessing import apply_clahe
    original_range = low_contrast.max() - low_contrast.min()
    result = apply_clahe(low_contrast, clip_limit=0.03, kernel_size=(8, 8))
    result_range = result.max() - result.min()
    assert result_range > original_range * 1.5


def test_clahe_2d_only():
    """CLAH E requires 2D input."""
    from poroscope.preprocessing import apply_clahe
    with pytest.raises(ValueError, match="2D"):
        apply_clahe(np.zeros((10, 10, 3)))


def test_clahe_custom_kernel(uneven_illumination):
    """CLAHE works with different kernel sizes."""
    from poroscope.preprocessing import apply_clahe
    result = apply_clahe(uneven_illumination, kernel_size=(16, 16))
    assert result.shape == uneven_illumination.shape


def test_clahe_intensity_range(uneven_illumination):
    """CLAHE output should be in valid 0-255 range."""
    from poroscope.preprocessing import apply_clahe
    result = apply_clahe(uneven_illumination)
    assert result.min() >= 0.0
    assert result.max() <= 255.0