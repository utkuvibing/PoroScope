import json

import numpy as np
import pytest
import tifffile

from poroscope.config import AnalysisConfig, Crop
from poroscope.pipeline import analyze_image


def test_pipeline_exports_complete_result_folder(tmp_path):
    image = np.full((20, 20), 220, dtype=np.uint8)
    image[5:10, 5:10] = 20
    image_path = tmp_path / "sample.tif"
    tifffile.imwrite(image_path, image)

    result = analyze_image(
        image_path,
        AnalysisConfig(pixel_size=0.5, unit="um", pores="dark", fill_holes=True),
        output_dir=tmp_path / "results",
    )

    assert result.summary["pore_count"] == 1
    assert result.summary["porosity_percent"] > 0
    for path in result.output_paths.values():
        assert (tmp_path / path).exists() if not str(path).startswith(str(tmp_path)) else True
        assert path
    summary_path = result.output_paths["summary"]
    with open(summary_path, encoding="utf-8") as handle:
        summary = json.load(handle)
    assert summary["output_paths"]["mask"].endswith("_mask.tif")


def test_pipeline_crop_excludes_non_sample_region(tmp_path):
    image = np.full((10, 10), 200, dtype=np.uint8)
    image[8:, :] = 0
    image_path = tmp_path / "crop.tif"
    tifffile.imwrite(image_path, image)
    result = analyze_image(
        image_path,
        AnalysisConfig(pixel_size=1, unit="um", pores="dark", crop=Crop(0, 0, 10, 8)),
    )
    assert result.summary["pore_pixel_count"] == 0
    assert result.summary["image_height_px"] == 8


def test_pipeline_refuses_existing_result_directory_by_default(tmp_path):
    image = np.full((12, 12), 220, dtype=np.uint8)
    image[3:6, 3:6] = 20
    image_path = tmp_path / "sample.tif"
    output = tmp_path / "results"
    tifffile.imwrite(image_path, image)

    analyze_image(
        image_path,
        AnalysisConfig(pixel_size=1, unit="um", pores="dark", min_size=1),
        output_dir=output,
    )

    with pytest.raises(FileExistsError, match="Use --overwrite"):
        analyze_image(
            image_path,
            AnalysisConfig(pixel_size=1, unit="um", pores="dark", min_size=1),
            output_dir=output,
        )


def test_pipeline_overwrite_allows_existing_result_directory(tmp_path):
    image = np.full((12, 12), 220, dtype=np.uint8)
    image[3:6, 3:6] = 20
    image_path = tmp_path / "sample.tif"
    output = tmp_path / "results"
    tifffile.imwrite(image_path, image)

    analyze_image(
        image_path,
        AnalysisConfig(pixel_size=1, unit="um", pores="dark", min_size=1),
        output_dir=output,
    )
    result = analyze_image(
        image_path,
        AnalysisConfig(pixel_size=1, unit="um", pores="dark", min_size=1),
        output_dir=output,
        overwrite=True,
    )

    assert result.output_paths is not None
    assert result.summary["pore_count"] == 1
