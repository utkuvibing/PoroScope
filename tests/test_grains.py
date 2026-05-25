"""Tests for grain size analysis module."""

import numpy as np
import pandas as pd
import pytest
from skimage import morphology as morph
from skimage import measure


@pytest.fixture
def synthetic_grains():
    """Create a synthetic image with circular grains for testing."""
    np.random.seed(42)
    img = np.zeros((200, 200), dtype=np.uint8)
    # Draw 20 circular grains
    cy, cx = np.mgrid[0:200, 0:200]
    centers = [(30, 30), (30, 80), (30, 140), (30, 170),
               (80, 30), (80, 90), (80, 160),
               (130, 40), (130, 100), (130, 150),
               (170, 30), (170, 80), (170, 130), (170, 170)]
    for cy_c, cx_c in centers:
        mask = (cy - cy_c) ** 2 + (cx - cx_c) ** 2 < 400  # r=20px
        img[mask] = 200  # bright grains
    return img


@pytest.fixture
def touching_grains():
    """Grains that touch each other — watershed needed."""
    img = np.zeros((100, 100), dtype=np.uint8)
    cy, cx = np.mgrid[0:100, 0:100]
    # Two touching circles
    mask1 = (cy - 30) ** 2 + (cx - 30) ** 2 < 500
    mask2 = (cy - 30) ** 2 + (cx - 65) ** 2 < 500
    img[mask1 | mask2] = 200
    return img


def test_import():
    """Verify the grains module is importable."""
    from poroscope import grains
    assert grains is not None


def test_segment_grains_shape(synthetic_grains):
    """segment_grains returns a labeled image with correct shape."""
    from poroscope.grains import segment_grains
    labels = segment_grains(synthetic_grains)
    assert labels.shape == (200, 200)
    assert labels.dtype in (np.int32, np.int64)
    assert labels.max() > 1  # multiple grains detected


def test_segment_grains_touching(touching_grains):
    """Watershed separates touching grains."""
    from poroscope.grains import segment_grains
    labels = segment_grains(touching_grains)
    # Should detect at least 2 grains
    assert labels.max() >= 2


def test_measure_grains(synthetic_grains):
    """measure_grains returns DataFrame with expected columns."""
    from poroscope.grains import segment_grains, measure_grains
    labels = segment_grains(synthetic_grains)
    df = measure_grains(labels, pixel_size=1.0, unit="px")
    assert isinstance(df, pd.DataFrame)
    assert "label" in df.columns
    assert "equivalent_diameter_px" in df.columns
    assert "area_px" in df.columns
    assert "area_unit2" in df.columns
    assert "circularity" in df.columns
    assert len(df) >= 10  # should detect most grains


def test_measure_grains_calibration(synthetic_grains):
    """Calibrated measurements are correct with pixel_size."""
    from poroscope.grains import segment_grains, measure_grains
    labels = segment_grains(synthetic_grains)
    df = measure_grains(labels, pixel_size=0.5, unit="um")
    # area_unit2 should be area_px * 0.25 for each grain
    row = df.iloc[0]
    assert abs(row["area_unit2"] - row["area_px"] * 0.25) < 1e-6
    assert "circularity" in df.columns


def test_summarize_grains(synthetic_grains):
    """summarize_grains returns a dict with grain size statistics."""
    from poroscope.grains import segment_grains, measure_grains, summarize_grains
    labels = segment_grains(synthetic_grains)
    df = measure_grains(labels, pixel_size=0.5, unit="um")
    summary = summarize_grains(df)
    assert "grain_count" in summary
    assert "mean_grain_diameter_unit" in summary
    assert "median_grain_diameter_unit" in summary
    assert "std_grain_diameter_unit" in summary
    assert "min_grain_diameter_unit" in summary
    assert "max_grain_diameter_unit" in summary
    assert summary["grain_count"] > 0


def test_summarize_grains_empty():
    """Empty measurement yields None summary values."""
    from poroscope.grains import summarize_grains
    df = pd.DataFrame()
    summary = summarize_grains(df)
    assert summary["grain_count"] == 0
    assert summary["mean_grain_diameter_unit"] is None


def test_astm_grain_size():
    """ASTM grain size number calculation."""
    from poroscope.grains import astm_grain_size_number
    # For a known grains/mm² value
    grains_per_mm2 = 1000
    g = astm_grain_size_number(grains_per_mm2)
    # G = -2.9542 + 6.6459 * log10(1000) = -2.9542 + 6.6459 * 3 = 16.98
    assert abs(g - (-2.9542 + 6.6459 * 3)) < 0.01


def test_astm_grain_size_zero():
    """ASTM calculation raises for zero or negative grains/mm²."""
    from poroscope.grains import astm_grain_size_number
    with pytest.raises(ValueError):
        astm_grain_size_number(0)
    with pytest.raises(ValueError):
        astm_grain_size_number(-1)


def test_analyze_grains_pipeline(synthetic_grains):
    """End-to-end analyze_grains returns AnalysisResult-like object."""
    from poroscope.grains import analyze_grains
    result = analyze_grains(synthetic_grains, pixel_size=0.5, unit="um")
    assert result.labels is not None
    assert result.measurements is not None
    assert result.summary is not None
    assert "grain_count" in result.summary
    assert "mean_grain_diameter_unit" in result.summary
