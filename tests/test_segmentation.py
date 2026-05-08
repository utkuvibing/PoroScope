import numpy as np
import pytest

from poroscope.segmentation import clean_mask, label_mask, threshold_image


def test_otsu_threshold_separates_simple_image_dark_pores():
    image = np.full((10, 10), 200.0)
    image[2:5, 2:5] = 20.0
    mask, value = threshold_image(image, method="otsu", pores="dark")
    assert value > 20
    assert mask[3, 3]
    assert not mask[0, 0]


def test_manual_threshold_dark_and_bright_polarity():
    image = np.array([[10.0, 200.0]])
    dark, _ = threshold_image(image, method="manual", pores="dark", threshold_value=100)
    bright, _ = threshold_image(image, method="manual", pores="bright", threshold_value=100)
    assert dark.tolist() == [[True, False]]
    assert bright.tolist() == [[False, True]]


def test_invalid_manual_threshold_raises():
    image = np.zeros((2, 2))
    with pytest.raises(ValueError, match="between 0 and 255"):
        threshold_image(image, method="manual", pores="dark", threshold_value=300)


def test_remove_small_objects_keeps_min_size_or_larger():
    mask = np.zeros((8, 8), dtype=bool)
    mask[0, 0] = True
    mask[2:4, 2:4] = True
    cleaned = clean_mask(mask, min_size=4)
    assert not cleaned[0, 0]
    assert cleaned[2:4, 2:4].all()


def test_fill_holes():
    mask = np.ones((5, 5), dtype=bool)
    mask[2, 2] = False
    cleaned = clean_mask(mask, min_size=0, fill_holes=True)
    assert cleaned[2, 2]


def test_empty_mask_cleanup_and_labeling():
    mask = np.zeros((5, 5), dtype=bool)
    cleaned = clean_mask(mask, min_size=20, fill_holes=True)
    labels = label_mask(cleaned)
    assert not cleaned.any()
    assert labels.max() == 0


def test_label_mask_counts_known_objects():
    mask = np.zeros((6, 6), dtype=bool)
    mask[1:3, 1:3] = True
    mask[4, 4] = True
    labels = label_mask(mask)
    assert labels.max() == 2

