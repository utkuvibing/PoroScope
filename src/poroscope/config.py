"""Configuration objects for PoroScope analysis."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


ThresholdMethod = Literal["otsu", "manual"]
PorePolarity = Literal["dark", "bright"]


@dataclass(frozen=True)
class Crop:
    """Rectangular crop in x, y, width, height pixel coordinates."""

    x: int
    y: int
    width: int
    height: int

    def validate(self, image_shape: tuple[int, int]) -> None:
        rows, cols = image_shape
        if self.x < 0 or self.y < 0 or self.width <= 0 or self.height <= 0:
            raise ValueError("Crop must use non-negative x/y and positive width/height.")
        if self.x + self.width > cols or self.y + self.height > rows:
            raise ValueError("Crop extends beyond image bounds.")

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class AnalysisConfig:
    """Complete reproducibility parameters for one v0.1 analysis run."""

    pixel_size: float
    unit: str
    pores: PorePolarity = "dark"
    threshold: ThresholdMethod = "otsu"
    threshold_value: float | None = None
    min_size: int = 20
    fill_holes: bool = False
    crop: Crop | None = None

    def validate(self) -> None:
        if self.pixel_size <= 0:
            raise ValueError("pixel_size must be positive.")
        if not self.unit:
            raise ValueError("unit must be a non-empty string.")
        if self.pores not in {"dark", "bright"}:
            raise ValueError("pores must be 'dark' or 'bright'.")
        if self.threshold not in {"otsu", "manual"}:
            raise ValueError("threshold must be 'otsu' or 'manual'.")
        if self.threshold == "manual" and self.threshold_value is None:
            raise ValueError("threshold_value is required when threshold='manual'.")
        if self.threshold == "otsu" and self.threshold_value is not None:
            raise ValueError("threshold_value is only valid when threshold='manual'.")
        if self.min_size < 0:
            raise ValueError("min_size must be non-negative.")

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["crop"] = self.crop.to_dict() if self.crop else None
        return data

