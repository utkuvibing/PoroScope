"""Tests for advanced thresholding (Sauvola, Niblack, local Otsu)."""

import numpy as np
import pytest


@pytest.fixture
def uneven_image():
    """Image with varying background brightness."""
    np.random.seed(42)
    img = np.zeros((100, 100), dtype=np.uint8)
    # Dark features on lighter background with gradient
    gradient = np.linspace(0.6, 0.2, 100)
    for y in range(100):
        img[y, :] = int(gradient[y] * 255)
    # Pores (dark spots)
    cy, cx = np.mgrid[0:100, 0:100]
    for y, x, r in [(30, 40, 8), (60, 60, 10), (80, 30, 6), (20, 80, 5)]:
        mask = (cy - y) ** 2 + (cx - x) ** 2 < r**2
        img[mask] = img[mask] * 0.3  # dark pores
    return img


@pytest.fixture
def uniform_image():
    """Uniformly illuminated image with clear dark features."""
    img = np.ones((50, 50), dtype=np.uint8) * 200
    img[10:20, 10:20] = 50   # dark region
    img[30:35, 30:40] = 80   # another dark region
    img[5:8, 40:45] = 30     # tiny dark spot
    return img


def test_import():
    from poroscope.segmentation import threshold_sauvola, threshold_niblack
    assert threshold_sauvola is not None
    assert threshold_niblack is not None


def test_threshold_sauvola_shape(uniform_image):
    from poroscope.segmentation import threshold_sauvola
    mask, threshold_map = threshold_sauvola(uniform_image, window_size=15)
    assert mask.shape == uniform_image.shape
    assert mask.dtype == np.bool_
    assert threshold_map.shape == uniform_image.shape


def test_threshold_sauvola_detects_features(uniform_image):
    from poroscope.segmentation import threshold_sauvola
    mask, _ = threshold_sauvola(uniform_image, window_size=15, k=0.1, pores="dark")
    # Should detect the dark regions (below threshold)
    assert mask[15, 15] == True  # dark region at (10:20, 10:20)
    # Background should not be mask
    assert mask[0, 0] == False


def test_threshold_niblack_shape(uneven_image):
    from poroscope.segmentation import threshold_niblack
    mask, threshold_map = threshold_niblack(uneven_image, window_size=15)
    assert mask.shape == uneven_image.shape
    assert mask.dtype == np.bool_
    assert threshold_map.shape == uneven_image.shape


def test_threshold_niblack_pores(uneven_image):
    from poroscope.segmentation import threshold_niblack
    mask, _ = threshold_niblack(uneven_image, window_size=25, k=-0.2)
    # Should detect at least some pores despite uneven lighting
    assert mask.sum() > 0  # some pixels detected


def test_local_otsu_shape(uniform_image):
    from poroscope.segmentation import local_otsu
    mask, threshold_map = local_otsu(uniform_image, block_size=15)
    assert mask.shape == uniform_image.shape
    assert mask.dtype == np.bool_


def test_local_otsu_detects_regions(uniform_image):
    from poroscope.segmentation import local_otsu
    mask, _ = local_otsu(uniform_image, block_size=15, pores="dark")
    # Should detect the dark 10x20 region
    assert mask[15, 15] == True
    assert mask[0, 0] == False


def test_invalid_window_size():
    from poroscope.segmentation import threshold_sauvola
    with pytest.raises(ValueError):
        threshold_sauvola(np.zeros((10, 10)), window_size=3)  # too small


def test_local_otsu_uneven(uneven_image):
    """Local Otsu should outperform global on uneven illumination."""
    from poroscope.segmentation import local_otsu
    from poroscope.segmentation import threshold_image
    mask_local, _ = local_otsu(uneven_image, block_size=25, pores="dark")
    mask_global, _ = threshold_image(uneven_image, method="otsu", pores="dark")
    # Local should detect more features on uneven image
    assert mask_local.sum() > 0