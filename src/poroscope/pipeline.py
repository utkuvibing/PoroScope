"""End-to-end single-image porosity analysis pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from . import __version__
from .config import AnalysisConfig
from .export import write_json, write_mask, write_measurements, write_overlay
from .io import load_image
from .measurements import measure_regions, summarize_measurements
from .preprocessing import apply_crop, to_grayscale
from .segmentation import clean_mask, label_mask, threshold_image
from .visualization import create_overlay


@dataclass(frozen=True)
class AnalysisResult:
    grayscale: np.ndarray
    mask: np.ndarray
    labels: np.ndarray
    measurements: pd.DataFrame
    summary: dict[str, Any]
    config: AnalysisConfig
    output_paths: dict[str, str] | None = None


def analyze_image(
    image_path: str | Path,
    config: AnalysisConfig,
    output_dir: str | Path | None = None,
) -> AnalysisResult:
    """Run the complete v0.1 pipeline for one image."""

    config.validate()
    image_path = Path(image_path)
    raw = load_image(image_path)
    gray_full = to_grayscale(raw)
    gray = apply_crop(gray_full, config.crop)

    initial_mask, threshold_value = threshold_image(
        gray,
        method=config.threshold,
        pores=config.pores,
        threshold_value=config.threshold_value,
    )
    mask = clean_mask(initial_mask, min_size=config.min_size, fill_holes=config.fill_holes)
    labels = label_mask(mask)
    measurements = measure_regions(labels, config.pixel_size)
    summary = summarize_measurements(
        mask,
        measurements,
        pixel_size=config.pixel_size,
        unit=config.unit,
        image_shape=gray.shape,
        threshold_method=config.threshold,
        threshold_value=threshold_value,
        pores=config.pores,
        min_size=config.min_size,
        fill_holes=config.fill_holes,
    )
    summary.update(
        {
            "input_path": str(image_path),
            "crop": config.crop.to_dict() if config.crop else None,
            "poroscope_version": __version__,
        }
    )

    output_paths: dict[str, str] | None = None
    if output_dir is not None:
        output_paths = export_analysis(
            image_path=image_path,
            output_dir=Path(output_dir),
            grayscale=gray,
            mask=mask,
            measurements=measurements,
            summary=summary,
            config=config,
        )
        summary["output_paths"] = output_paths
        write_json(output_paths["summary"], summary)

    return AnalysisResult(
        grayscale=gray,
        mask=mask,
        labels=labels,
        measurements=measurements,
        summary=summary,
        config=config,
        output_paths=output_paths,
    )


def export_analysis(
    *,
    image_path: Path,
    output_dir: Path,
    grayscale: np.ndarray,
    mask: np.ndarray,
    measurements: pd.DataFrame,
    summary: dict[str, Any],
    config: AnalysisConfig,
) -> dict[str, str]:
    """Write all v0.1 output files and return their paths."""

    stem = image_path.stem
    result_dir = output_dir / stem
    result_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "mask": str(result_dir / f"{stem}_mask.tif"),
        "overlay": str(result_dir / f"{stem}_overlay.png"),
        "measurements": str(result_dir / f"{stem}_measurements.csv"),
        "summary": str(result_dir / f"{stem}_summary.json"),
        "config": str(result_dir / f"{stem}_config.json"),
    }

    write_mask(paths["mask"], mask)
    write_overlay(paths["overlay"], create_overlay(grayscale, mask))
    write_measurements(paths["measurements"], measurements)
    write_json(paths["config"], config.to_dict())
    return paths

