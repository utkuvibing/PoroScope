"""Tests for particle analysis module."""

import numpy as np
import pandas as pd
import pytest
from skimage import morphology as morph


@pytest.fixture
def particle_image():
    """Image with separate circular particles of various sizes."""
    np.random.seed(42)
    img = np.zeros((200, 200), dtype=np.uint8)
    cy, cx = np.mgrid[0:200, 0:200]
    # Particles at different positions and sizes
    particles = [
        (30, 30, 10),   # (y, x, radius)
        (50, 80, 15),
        (90, 40, 8),
        (130, 150, 20),
        (170, 60, 12),
        (30, 160, 6),
        (80, 120, 18),
        (150, 100, 14),
        (180, 170, 9),
        (60, 170, 11),
    ]
    for cy_c, cx_c, r in particles:
        mask = (cy - cy_c) ** 2 + (cx - cx_c) ** 2 < r**2
        img[mask] = 200
    return img


@pytest.fixture
def binary_particles():
    """Binary mask with simple particles."""
    img = np.zeros((100, 100), dtype=bool)
    img[10:25, 10:25] = True   # square particle
    img[40:55, 40:55] = True   # square particle
    img[70:80, 70:78] = True   # small rectangle
    return img


def test_import():
    """Verify the particles module is importable."""
    from poroscope import particles
    assert particles is not None


def test_segment_particles(particle_image):
    """segment_particles labels each detected particle."""
    from poroscope.particles import segment_particles
    from poroscope.segmentation import threshold_image

    binary, _ = threshold_image(particle_image, method="otsu", pores="bright")
    labels = segment_particles(binary, min_size=10)
    assert labels.shape == (200, 200)
    assert labels.dtype in (np.int32, np.int64)
    # Should detect multiple particles
    assert labels.max() >= 8


def test_measure_particles(particle_image):
    """measure_particles returns DataFrame with expected columns."""
    from poroscope.particles import segment_particles, measure_particles
    from poroscope.segmentation import threshold_image

    binary, _ = threshold_image(particle_image, method="otsu", pores="bright")
    labels = segment_particles(binary, min_size=10)
    df = measure_particles(labels, pixel_size=1.0, unit="px")
    assert isinstance(df, pd.DataFrame)
    assert "label" in df.columns
    assert "equivalent_diameter_px" in df.columns
    assert "circularity" in df.columns
    assert "area_px" in df.columns
    assert len(df) >= 8


def test_measure_particles_calibrated(particle_image):
    """Calibrated measurements work correctly."""
    from poroscope.particles import segment_particles, measure_particles
    from poroscope.segmentation import threshold_image

    binary, _ = threshold_image(particle_image, method="otsu", pores="bright")
    labels = segment_particles(binary, min_size=10)
    df = measure_particles(labels, pixel_size=0.5, unit="um")
    row = df.iloc[0]
    assert abs(row["area_unit2"] - row["area_px"] * 0.25) < 1e-6


def test_particle_size_distribution(particle_image):
    """particle_size_distribution returns histogram bins."""
    from poroscope.particles import segment_particles, measure_particles, particle_size_distribution
    from poroscope.segmentation import threshold_image

    binary, _ = threshold_image(particle_image, method="otsu", pores="bright")
    labels = segment_particles(binary, min_size=10)
    df = measure_particles(labels, pixel_size=1.0, unit="px")
    hist = particle_size_distribution(df, bins=5)
    assert "bin_edges" in hist
    assert "bin_counts" in hist
    assert "bin_centers" in hist
    assert len(hist["bin_counts"]) == 5


def test_summarize_particles(particle_image):
    """summarize_particles returns dict with distribution stats."""
    from poroscope.particles import (segment_particles, measure_particles,
                                      summarize_particles)
    from poroscope.segmentation import threshold_image

    binary, _ = threshold_image(particle_image, method="otsu", pores="bright")
    labels = segment_particles(binary, min_size=10)
    df = measure_particles(labels, pixel_size=0.5, unit="um")
    summary = summarize_particles(df)
    assert "particle_count" in summary
    assert "mean_diameter_unit" in summary
    assert "median_diameter_unit" in summary
    assert "std_diameter_unit" in summary
    assert "min_diameter_unit" in summary
    assert "max_diameter_unit" in summary
    assert "mean_circularity" in summary


def test_summarize_particles_empty():
    """Empty measurements return None values."""
    from poroscope.particles import summarize_particles
    df = pd.DataFrame()
    summary = summarize_particles(df)
    assert summary["particle_count"] == 0


def test_analyze_particles_pipeline(particle_image):
    """End-to-end analyze_particles returns result with labels and summary."""
    from poroscope.particles import analyze_particles
    from poroscope.segmentation import threshold_image

    binary, _ = threshold_image(particle_image, method="otsu", pores="bright")
    result = analyze_particles(binary, pixel_size=0.5, unit="um",
                                min_size=10)
    assert result.labels is not None
    assert result.measurements is not None
    assert result.summary is not None
    assert result.summary["particle_count"] >= 8
