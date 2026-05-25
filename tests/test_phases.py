"""Tests for phase fraction analysis module."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def three_phase_image():
    """Synthetic 3-phase microstructure (background + phase1 + phase2)."""
    np.random.seed(42)
    img = np.zeros((100, 100), dtype=np.uint8)
    # Phase 1: circles with intensity 100
    cy, cx = np.mgrid[0:100, 0:100]
    mask1 = (cy - 30) ** 2 + (cx - 30) ** 2 < 500
    mask2 = (cy - 60) ** 2 + (cx - 70) ** 2 < 400
    img[mask1 | mask2] = 100
    # Phase 2: smaller bright inclusions
    mask3 = (cy - 20) ** 2 + (cx - 60) ** 2 < 100
    mask4 = (cy - 50) ** 2 + (cx - 25) ** 2 < 80
    mask5 = (cy - 80) ** 2 + (cx - 50) ** 2 < 60
    img[mask3 | mask4 | mask5] = 200
    return img


@pytest.fixture
def binary_phase_image():
    """Simple binary phase image (background + one phase)."""
    img = np.zeros((50, 50), dtype=np.uint8)
    img[10:30, 10:30] = 128  # phase
    return img


def test_import():
    """Verify the phases module is importable."""
    from poroscope import phases
    assert phases is not None


def test_multi_otsu(three_phase_image):
    """multi_otsu segments into expected number of phases."""
    from poroscope.phases import multi_otsu
    labels, thresholds = multi_otsu(three_phase_image, n_classes=3)
    assert labels.shape == three_phase_image.shape
    assert len(thresholds) == 2  # 3 classes = 2 thresholds
    assert labels.min() == 0
    assert labels.max() == 2  # classes 0, 1, 2
    # Check that intensities map to expected classes
    assert labels[three_phase_image == 0].max() == 0  # bg is darkest
    assert labels[three_phase_image == 200].max() >= 1  # brightest phase


def test_multi_otsu_invalid():
    """multi_otsu requires n_classes >= 2."""
    from poroscope.phases import multi_otsu
    with pytest.raises(ValueError):
        multi_otsu(np.zeros((10, 10)), n_classes=1)
    with pytest.raises(ValueError):
        multi_otsu(np.zeros((10, 10)), n_classes=6)


def test_measure_phase_fractions(three_phase_image):
    """measure_phase_fractions returns DataFrame with correct fractions."""
    from poroscope.phases import multi_otsu, measure_phase_fractions
    labels, _ = multi_otsu(three_phase_image, n_classes=3)
    df = measure_phase_fractions(labels, pixel_size=0.5, unit="um")
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["phase", "pixel_count", "area_unit2",
                                  "area_fraction", "area_fraction_percent"]
    assert len(df) == 3
    # Fractions should sum to ~1.0
    assert abs(df["area_fraction"].sum() - 1.0) < 0.01


def test_measure_phase_fractions_binary(binary_phase_image):
    """Binary phase image returns 2 phases with correct fractions."""
    from poroscope.phases import multi_otsu, measure_phase_fractions
    labels, _ = multi_otsu(binary_phase_image, n_classes=2)
    df = measure_phase_fractions(labels, pixel_size=1.0, unit="px")
    assert len(df) == 2
    assert df.iloc[1]["area_fraction"] > 0  # non-zero phase fraction


def test_summarize_phases(three_phase_image):
    """summarize_phases returns dict with phase fraction info."""
    from poroscope.phases import multi_otsu, measure_phase_fractions, summarize_phases
    labels, _ = multi_otsu(three_phase_image, n_classes=3)
    df = measure_phase_fractions(labels, pixel_size=0.5, unit="um")
    summary = summarize_phases(df)
    assert "n_phases" in summary
    assert summary["n_phases"] == 3
    assert "dominant_phase_index" in summary
    assert "phase_fractions" in summary


def test_summarize_phases_empty():
    """Empty measurements return None values."""
    from poroscope.phases import summarize_phases
    df = pd.DataFrame()
    summary = summarize_phases(df)
    assert summary["n_phases"] == 0


def test_analyze_phases_pipeline(three_phase_image):
    """End-to-end analyze_phases returns result with labels and summary."""
    from poroscope.phases import analyze_phases
    result = analyze_phases(three_phase_image, n_classes=3,
                            pixel_size=0.5, unit="um")
    assert result.labels is not None
    assert result.measurements is not None
    assert result.summary is not None
    assert result.summary["n_phases"] == 3


def test_analyze_phases_2_classes(binary_phase_image):
    """analyze_phases works with 2 classes (binary)."""
    from poroscope.phases import analyze_phases
    result = analyze_phases(binary_phase_image, n_classes=2,
                            pixel_size=1.0, unit="px")
    assert result.summary["n_phases"] == 2
