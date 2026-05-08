from typer.testing import CliRunner
import numpy as np
import tifffile

from poroscope.cli import app


runner = CliRunner()


def test_cli_creates_expected_outputs(tmp_path):
    image = np.full((20, 20), 220, dtype=np.uint8)
    image[5:10, 5:10] = 20
    image_path = tmp_path / "sample.tif"
    tifffile.imwrite(image_path, image)
    output = tmp_path / "results"

    result = runner.invoke(
        app,
        [
            "analyze",
            str(image_path),
            "--pixel-size",
            "0.5",
            "--unit",
            "um",
            "--pores",
            "dark",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    result_dir = output / "sample"
    assert (result_dir / "sample_mask.tif").exists()
    assert (result_dir / "sample_overlay.png").exists()
    assert (result_dir / "sample_measurements.csv").exists()
    assert (result_dir / "sample_summary.json").exists()
    assert (result_dir / "sample_config.json").exists()


def test_cli_rejects_unsupported_format(tmp_path):
    path = tmp_path / "sample.bmp"
    path.write_bytes(b"not really an image")
    result = runner.invoke(app, ["analyze", str(path)])
    assert result.exit_code != 0
    assert "Unsupported image format" in result.output


def test_cli_rejects_invalid_pore_polarity(tmp_path):
    image = np.zeros((4, 4), dtype=np.uint8)
    image_path = tmp_path / "sample.tif"
    tifffile.imwrite(image_path, image)
    result = runner.invoke(app, ["analyze", str(image_path), "--pores", "middle"])
    assert result.exit_code != 0
    assert "pores must be" in result.output


def test_cli_accepts_crop(tmp_path):
    image = np.full((10, 10), 200, dtype=np.uint8)
    image[8:, :] = 0
    image_path = tmp_path / "sample.tif"
    tifffile.imwrite(image_path, image)

    result = runner.invoke(
        app,
        [
            "analyze",
            str(image_path),
            "--pixel-size",
            "1",
            "--unit",
            "um",
            "--crop",
            "0",
            "0",
            "10",
            "8",
            "--output",
            str(tmp_path / "results"),
        ],
    )

    assert result.exit_code == 0, result.output
