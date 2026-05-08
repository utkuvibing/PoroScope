import math

import numpy as np

from poroscope.measurements import MEASUREMENT_COLUMNS, measure_regions, summarize_measurements
from poroscope.segmentation import label_mask


def test_empty_mask_summary_and_headers():
    mask = np.zeros((5, 5), dtype=bool)
    labels = label_mask(mask)
    table = measure_regions(labels, pixel_size=0.5)
    summary = summarize_measurements(
        mask,
        table,
        pixel_size=0.5,
        unit="um",
        image_shape=mask.shape,
        threshold_method="manual",
        threshold_value=128,
        pores="dark",
        min_size=20,
        fill_holes=False,
    )
    assert list(table.columns) == MEASUREMENT_COLUMNS
    assert table.empty
    assert summary["porosity_percent"] == 0
    assert summary["pore_count"] == 0
    assert summary["mean_pore_area_unit2"] is None


def test_calibrated_area_and_equivalent_diameter():
    mask = np.zeros((7, 7), dtype=bool)
    mask[2:5, 2:5] = True
    table = measure_regions(label_mask(mask), pixel_size=0.5)
    row = table.iloc[0]
    assert row["area_px"] == 9
    assert row["area_unit2"] == 2.25
    assert math.isclose(
        row["equivalent_diameter_unit"],
        row["equivalent_diameter_px"] * 0.5,
    )


def test_porosity_known_mask():
    mask = np.zeros((10, 10), dtype=bool)
    mask[:2, :] = True
    table = measure_regions(label_mask(mask), pixel_size=1.0)
    summary = summarize_measurements(
        mask,
        table,
        pixel_size=1.0,
        unit="um",
        image_shape=mask.shape,
        threshold_method="manual",
        threshold_value=128,
        pores="bright",
        min_size=0,
        fill_holes=False,
    )
    assert summary["pore_pixel_count"] == 20
    assert summary["porosity_percent"] == 20


def test_single_pixel_region_handles_zero_perimeter_and_axis():
    mask = np.zeros((3, 3), dtype=bool)
    mask[1, 1] = True
    table = measure_regions(label_mask(mask), pixel_size=1.0)
    row = table.iloc[0]
    assert math.isnan(row["circularity"])
    assert math.isnan(row["aspect_ratio"])


def test_border_touching_pore_flagged():
    mask = np.zeros((5, 5), dtype=bool)
    mask[0:2, 1:3] = True
    table = measure_regions(label_mask(mask), pixel_size=1.0)
    assert bool(table.iloc[0]["touches_border"])

