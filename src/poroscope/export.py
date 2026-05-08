"""Result export helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import tifffile
from skimage import io as skio


def write_mask(path: str | Path, mask: np.ndarray) -> None:
    tifffile.imwrite(path, np.asarray(mask, dtype=np.uint8) * 255)


def write_overlay(path: str | Path, overlay: np.ndarray) -> None:
    skio.imsave(path, np.asarray(overlay, dtype=np.uint8), check_contrast=False)


def write_measurements(path: str | Path, measurements: pd.DataFrame) -> None:
    measurements.to_csv(path, index=False)


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    with Path(path).open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, default=_json_default, allow_nan=False)
        handle.write("\n")

