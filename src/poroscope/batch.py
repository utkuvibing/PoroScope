"""Batch processing for folders of microscopy images."""

from __future__ import annotations

import concurrent.futures
import functools
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from . import __version__
from .config import AnalysisConfig
from .export import write_json
from .io import SUPPORTED_EXTENSIONS
from .pipeline import analyze_image
from .report import generate_html_report

BATCH_COLUMNS = [
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


@dataclass(frozen=True)
class BatchResult:
    processed: pd.DataFrame
    failed_files: list[dict[str, str]]
    skipped_files: list[str]
    output_paths: dict[str, str]


def find_supported_images(image_dir: str | Path) -> list[Path]:
    """Return supported image files directly inside a folder."""

    directory = Path(image_dir)
    if not directory.exists():
        raise FileNotFoundError(f"Image directory does not exist: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"IMAGE_DIR must be a directory: {directory}")
    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def find_unsupported_files(image_dir: str | Path) -> list[Path]:
    """Return unsupported regular files directly inside a folder."""

    directory = Path(image_dir)
    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() not in SUPPORTED_EXTENSIONS
    )


def _process_single_image(
    image_path: Path,
    config: AnalysisConfig,
    output_dir: Path,
    overwrite: bool,
) -> dict[str, Any] | dict[str, str]:
    """Process one image and return row data or error dict."""
    try:
        result = analyze_image(
            image_path,
            config=config,
            output_dir=output_dir,
            overwrite=overwrite,
        )
        summary = result.summary
        output_folder = ""
        if result.output_paths:
            output_folder = str(Path(result.output_paths["summary"]).parent)

        return {
            "image_name": image_path.name,
            "image_path": str(image_path),
            "porosity_percent": summary["porosity_percent"],
            "pore_count": summary["pore_count"],
            "analyzed_pixel_count": summary["analyzed_pixel_count"],
            "pore_pixel_count": summary["pore_pixel_count"],
            "mean_pore_area_unit2": summary["mean_pore_area_unit2"],
            "median_pore_area_unit2": summary["median_pore_area_unit2"],
            "min_pore_area_unit2": summary["min_pore_area_unit2"],
            "max_pore_area_unit2": summary["max_pore_area_unit2"],
            "output_folder": output_folder,
        }
    except Exception as exc:
        return {"image_path": str(image_path), "error": str(exc)}


def run_batch(
    image_dir: str | Path,
    *,
    config: AnalysisConfig,
    output_dir: str | Path,
    overwrite: bool = False,
    parallel: bool = True,
    max_workers: int | None = None,
    html_report: bool = True,
) -> BatchResult:
    """Analyze every supported image in a folder and write aggregate summaries.

    Parameters
    ----------
    image_dir : str | Path
        Directory containing images.
    config : AnalysisConfig
        Analysis configuration.
    output_dir : str | Path
        Output directory for results.
    overwrite : bool
        Overwrite existing per-image result directories.
    parallel : bool
        Use parallel processing (default: True).
    max_workers : int, optional
        Max worker processes. Defaults to CPU count.
    html_report : bool
        Generate HTML report (default: True).

    Returns
    -------
    BatchResult
        Processed results and output paths.
    """
    config.validate()
    directory = Path(image_dir)
    images = find_supported_images(directory)
    skipped = [str(path) for path in find_unsupported_files(directory)]
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    process_fn = functools.partial(
        _process_single_image,
        config=config,
        output_dir=output,
        overwrite=overwrite,
    )

    if parallel and len(images) > 1:
        n_workers = max_workers or min(os.cpu_count() or 4, len(images))
        with concurrent.futures.ProcessPoolExecutor(max_workers=n_workers) as executor:
            results = list(executor.map(process_fn, images))
    else:
        results = [process_fn(img) for img in images]

    # Separate successful results from failures
    rows: list[dict[str, Any]] = []
    failed: list[dict[str, str]] = []

    for r in results:
        if "error" in r:
            failed.append({"image_path": r["image_path"], "error": r["error"]})
        else:
            rows.append(r)

    processed = pd.DataFrame(rows, columns=BATCH_COLUMNS)
    csv_path = output / "batch_summary.csv"
    json_path = output / "batch_summary.json"
    processed.to_csv(csv_path, index=False)

    payload = {
        "poroscope_version": __version__,
        "image_dir": str(directory),
        "output_dir": str(output),
        "config": config.to_dict(),
        "processed_count": int(len(processed)),
        "failed_count": int(len(failed)),
        "skipped_count": int(len(skipped)),
        "processed_images": rows,
        "failed_files": failed,
        "skipped_files": skipped,
        "output_paths": {
            "batch_summary_csv": str(csv_path),
            "batch_summary_json": str(json_path),
        },
    }
    write_json(json_path, payload)

    # Generate HTML report
    html_path = output / "batch_report.html"
    if html_report:
        generate_html_report(json_path, html_path, title="PoroScope Batch Report")

    return BatchResult(
        processed=processed,
        failed_files=failed,
        skipped_files=skipped,
        output_paths={
            "batch_summary_csv": str(csv_path),
            "batch_summary_json": str(json_path),
            "batch_report_html": str(html_path) if html_report else "",
        },
    )