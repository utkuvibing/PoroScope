"""Command-line interface for PoroScope."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer

from .config import AnalysisConfig, Crop
from .pipeline import analyze_image

app = typer.Typer(help="Calibrated porosity analysis for microscopy images.")


@app.callback()
def main() -> None:
    """PoroScope command group."""


def _parse_crop(values: Optional[tuple[int, int, int, int]]) -> Crop | None:
    if values is None:
        return None
    return Crop(x=values[0], y=values[1], width=values[2], height=values[3])


@app.command()
def analyze(
    image_path: Annotated[Path, typer.Argument(help="PNG, JPG/JPEG, or TIFF image to analyze.")],
    pixel_size: Annotated[float, typer.Option("--pixel-size", help="Physical length per pixel.")] = 1.0,
    unit: Annotated[str, typer.Option("--unit", help="Physical length unit, for example um.")] = "px",
    pores: Annotated[str, typer.Option("--pores", help="'dark' for below-threshold pores, 'bright' for above-threshold pores.")] = "dark",
    threshold: Annotated[str, typer.Option("--threshold", help="'otsu' or 'manual'.")] = "otsu",
    threshold_value: Annotated[float | None, typer.Option("--threshold-value", help="Manual threshold in 0-255 intensity units; images are normalized to 0-255 before thresholding.")] = None,
    min_size: Annotated[int, typer.Option("--min-size", help="Remove pore objects smaller than this pixel area.")] = 20,
    fill_holes: Annotated[bool, typer.Option("--fill-holes", help="Fill internal holes in pore objects.")] = False,
    crop: Annotated[Optional[tuple[int, int, int, int]], typer.Option("--crop", help="Crop as x y width height.")] = None,
    output: Annotated[Path, typer.Option("--output", "-o", help="Output directory.")] = Path("results"),
    overwrite: Annotated[bool, typer.Option("--overwrite", help="Replace an existing result directory for this image.")] = False,
) -> None:
    """Analyze one image and export mask, overlay, CSV, summary JSON, and config JSON."""

    try:
        config = AnalysisConfig(
            pixel_size=pixel_size,
            unit=unit,
            pores=pores,  # type: ignore[arg-type]
            threshold=threshold,  # type: ignore[arg-type]
            threshold_value=threshold_value,
            min_size=min_size,
            fill_holes=fill_holes,
            crop=_parse_crop(crop),
        )
        result = analyze_image(image_path, config=config, output_dir=output, overwrite=overwrite)
    except Exception as exc:
        raise typer.BadParameter(str(exc)) from exc

    typer.echo(f"Analyzed: {image_path}")
    typer.echo(f"Porosity: {result.summary['porosity_percent']:.4f}%")
    typer.echo(f"Pores detected: {result.summary['pore_count']}")
    if result.output_paths:
        typer.echo(f"Results: {Path(result.output_paths['summary']).parent}")


if __name__ == "__main__":
    app()
