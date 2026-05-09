import json

import numpy as np
import pandas as pd
import pytest
import tifffile
from skimage import io as skio

from poroscope.batch import find_supported_images, run_batch
from poroscope.config import AnalysisConfig


def _write_synthetic_tif(path, pore_slice=(slice(5, 10), slice(5, 10))):
    image = np.full((20, 20), 220, dtype=np.uint8)
    image[pore_slice] = 20
    tifffile.imwrite(path, image)


def test_batch_detects_supported_images_and_skips_unsupported_files(tmp_path):
    _write_synthetic_tif(tmp_path / "a.tif")
    _write_synthetic_tif(tmp_path / "b.tiff")
    image = np.full((12, 12), 180, dtype=np.uint8)
    skio.imsave(tmp_path / "c.png", image, check_contrast=False)
    skio.imsave(tmp_path / "d.jpg", image, check_contrast=False)
    (tmp_path / "notes.txt").write_text("not an image", encoding="utf-8")

    supported = find_supported_images(tmp_path)
    result = run_batch(
        tmp_path,
        config=AnalysisConfig(pixel_size=0.5, unit="um", pores="dark", min_size=1),
        output_dir=tmp_path / "results",
    )

    assert [path.name for path in supported] == ["a.tif", "b.tiff", "c.png", "d.jpg"]
    assert result.skipped_files == [str(tmp_path / "notes.txt")]
    assert len(result.processed) == 4


def test_batch_creates_per_image_outputs_and_aggregate_files(tmp_path):
    _write_synthetic_tif(tmp_path / "sample_a.tif")
    _write_synthetic_tif(tmp_path / "sample_b.tif", pore_slice=(slice(2, 8), slice(3, 9)))
    output = tmp_path / "results"

    result = run_batch(
        tmp_path,
        config=AnalysisConfig(pixel_size=0.5, unit="um", pores="dark", min_size=1),
        output_dir=output,
    )

    assert len(result.processed) == 2
    for stem in ["sample_a", "sample_b"]:
        assert (output / stem / f"{stem}_mask.tif").exists()
        assert (output / stem / f"{stem}_overlay.png").exists()
        assert (output / stem / f"{stem}_measurements.csv").exists()
        assert (output / stem / f"{stem}_summary.json").exists()
        assert (output / stem / f"{stem}_config.json").exists()

    csv_path = output / "batch_summary.csv"
    json_path = output / "batch_summary.json"
    assert csv_path.exists()
    assert json_path.exists()

    csv = pd.read_csv(csv_path)
    with json_path.open(encoding="utf-8") as handle:
        payload = json.load(handle)

    assert list(csv.columns) == [
        "image_name",
        "image_path",
        "porosity_percent",
        "pore_count",
        "analyzed_pixel_count",
        "pore_pixel_count",
        "mean_pore_area_unit2",
        "median_pore_area_unit2",
        "min_pore_area_unit2",
        "max_pore_area_unit2",
        "output_folder",
    ]
    assert payload["processed_count"] == 2
    assert payload["failed_files"] == []


def test_batch_records_failed_supported_images_and_continues(tmp_path):
    _write_synthetic_tif(tmp_path / "good.tif")
    (tmp_path / "bad.tif").write_bytes(b"not a valid tif")
    output = tmp_path / "results"

    result = run_batch(
        tmp_path,
        config=AnalysisConfig(pixel_size=0.5, unit="um", pores="dark", min_size=1),
        output_dir=output,
    )

    assert len(result.processed) == 1
    assert len(result.failed_files) == 1
    assert result.failed_files[0]["image_path"].endswith("bad.tif")
    with (output / "batch_summary.json").open(encoding="utf-8") as handle:
        payload = json.load(handle)
    assert payload["failed_count"] == 1
    assert payload["processed_count"] == 1


def test_batch_overwrite_behavior(tmp_path):
    _write_synthetic_tif(tmp_path / "sample.tif")
    output = tmp_path / "results"
    config = AnalysisConfig(pixel_size=0.5, unit="um", pores="dark", min_size=1)

    first = run_batch(tmp_path, config=config, output_dir=output)
    second = run_batch(tmp_path, config=config, output_dir=output)
    third = run_batch(tmp_path, config=config, output_dir=output, overwrite=True)

    assert len(first.processed) == 1
    assert len(second.processed) == 0
    assert len(second.failed_files) == 1
    assert "overwrite" in second.failed_files[0]["error"]
    assert len(third.processed) == 1
    assert third.failed_files == []


def test_batch_rejects_non_directory(tmp_path):
    image_path = tmp_path / "sample.tif"
    _write_synthetic_tif(image_path)
    with pytest.raises(NotADirectoryError):
        find_supported_images(image_path)

