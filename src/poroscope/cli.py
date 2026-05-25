"""Command-line interface for PoroScope."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer

from .config import AnalysisConfig, Crop
from .batch import run_batch
from .grains import analyze_grains as _analyze_grains
from .io import load_image
from .particles import analyze_particles as _analyze_particles
from .phases import analyze_phases as _analyze_phases
from .pipeline import analyze_image
from .preprocessing import to_grayscale

app = typer.Typer(help="Calibrated microstructure analysis for microscopy images.")


@app.callback()
def main() -> None:
    """PoroScope command group."""


def _parse_crop(values: Optional[tuple[int, int, int, int]]) -> Crop | None:
    if values is None:
        return None
    return Crop(x=values[0], y=values[1], width=values[2], height=values[3])


def _load_and_prepare(image_path: Path, crop: tuple[int, int, int, int] | None = None):
    """Load image and convert to grayscale."""
    raw = load_image(image_path)
    gray = to_grayscale(raw)
    if crop:
        from .preprocessing import apply_crop
        parsed = _parse_crop(crop)
        gray = apply_crop(gray, parsed)
    return gray


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
    """Analyze one image for porosity and export results."""
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


@app.command()
def batch(
    image_dir: Annotated[Path, typer.Argument(help="Directory containing PNG, JPG/JPEG, or TIFF images.")],
    pixel_size: Annotated[float, typer.Option("--pixel-size", help="Physical length per pixel.")] = 1.0,
    unit: Annotated[str, typer.Option("--unit", help="Physical length unit, for example um.")] = "px",
    pores: Annotated[str, typer.Option("--pores", help="'dark' for below-threshold pores, 'bright' for above-threshold pores.")] = "dark",
    threshold: Annotated[str, typer.Option("--threshold", help="'otsu' or 'manual'.")] = "otsu",
    threshold_value: Annotated[float | None, typer.Option("--threshold-value", help="Manual threshold in 0-255 intensity units.")] = None,
    min_size: Annotated[int, typer.Option("--min-size", help="Remove pore objects smaller than this pixel area.")] = 20,
    fill_holes: Annotated[bool, typer.Option("--fill-holes", help="Fill internal holes in pore objects.")] = False,
    crop: Annotated[Optional[tuple[int, int, int, int]], typer.Option("--crop", help="Crop as x y width height.")] = None,
    output: Annotated[Path, typer.Option("--output", "-o", help="Output directory.")] = Path("results"),
    overwrite: Annotated[bool, typer.Option("--overwrite", help="Replace existing per-image result directories.")] = False,
    parallel: Annotated[bool, typer.Option("--parallel/--sequential", help="Use parallel processing.")] = True,
    max_workers: Annotated[int | None, typer.Option("--max-workers", help="Max parallel workers.")] = None,
    html_report: Annotated[bool, typer.Option("--html/--no-html", help="Generate HTML report.")] = True,
) -> None:
    """Batch-analyze all supported images in a directory for porosity."""
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
        result = run_batch(
            image_dir, config=config, output_dir=output,
            overwrite=overwrite, parallel=parallel,
            max_workers=max_workers, html_report=html_report,
        )
    except Exception as exc:
        raise typer.BadParameter(str(exc)) from exc

    typer.echo(f"Processed images: {len(result.processed)}")
    typer.echo(f"Failed images: {len(result.failed_files)}")
    typer.echo(f"Skipped unsupported files: {len(result.skipped_files)}")
    typer.echo(f"Batch CSV: {result.output_paths['batch_summary_csv']}")
    typer.echo(f"Batch JSON: {result.output_paths['batch_summary_json']}")
    if result.output_paths.get("batch_report_html"):
        typer.echo(f"HTML Report: {result.output_paths['batch_report_html']}")


@app.command()
def grains(
    image_path: Annotated[Path, typer.Argument(help="Image to analyze for grain size.")],
    pixel_size: Annotated[float, typer.Option("--pixel-size", help="Physical length per pixel.")] = 1.0,
    unit: Annotated[str, typer.Option("--unit", help="Physical length unit.")] = "px",
    min_distance: Annotated[int, typer.Option("--min-distance", help="Min distance between grain centers.")] = 5,
    exclude_border: Annotated[bool, typer.Option("--exclude-border", help="Exclude grains touching the border.")] = True,
    crop: Annotated[Optional[tuple[int, int, int, int]], typer.Option("--crop", help="Crop as x y width height.")] = None,
) -> None:
    """Analyze grain size distribution using watershed segmentation."""
    try:
        gray = _load_and_prepare(image_path, crop=crop)
        result = _analyze_grains(
            grayscale=gray,
            pixel_size=pixel_size,
            unit=unit,
            min_distance=min_distance,
            exclude_border=exclude_border,
        )
    except Exception as exc:
        raise typer.BadParameter(str(exc)) from exc

    typer.echo(f"Grain size analysis: {image_path}")
    typer.echo(f"  Grains detected: {result.summary['grain_count']}")
    typer.echo(f"  Mean diameter: {result.summary['mean_grain_diameter_unit']:.2f} {unit}")
    typer.echo(f"  Median diameter: {result.summary['median_grain_diameter_unit']:.2f} {unit}")
    typer.echo(f"  Std diameter: {result.summary['std_grain_diameter_unit']:.2f} {unit}")
    typer.echo(f"  Mean circularity: {result.summary['mean_circularity']:.4f}")
    if result.summary.get("astm_grain_size_number") is not None:
        typer.echo(f"  ASTM grain size number: {result.summary['astm_grain_size_number']:.2f}")


@app.command()
def phases(
    image_path: Annotated[Path, typer.Argument(help="Image to analyze for phase fractions.")],
    n_classes: Annotated[int, typer.Option("--n-classes", help="Number of phases to segment (2-5).")] = 3,
    pixel_size: Annotated[float, typer.Option("--pixel-size", help="Physical length per pixel.")] = 1.0,
    unit: Annotated[str, typer.Option("--unit", help="Physical length unit.")] = "px",
    crop: Annotated[Optional[tuple[int, int, int, int]], typer.Option("--crop", help="Crop as x y width height.")] = None,
) -> None:
    """Segment multi-phase microstructures using multi-Otsu thresholding."""
    try:
        gray = _load_and_prepare(image_path, crop=crop)
        result = _analyze_phases(
            grayscale=gray,
            n_classes=n_classes,
            pixel_size=pixel_size,
            unit=unit,
        )
    except Exception as exc:
        raise typer.BadParameter(str(exc)) from exc

    typer.echo(f"Phase analysis: {image_path}")
    typer.echo(f"  Phases detected: {result.summary['n_phases']}")
    typer.echo(f"  Dominant phase: #{result.summary['dominant_phase_index']} ({result.summary['dominant_phase_fraction']*100:.1f}%)")
    typer.echo("  Phase fractions:")
    for phase, frac in sorted(result.summary["phase_fractions"].items()):
        typer.echo(f"    Phase {phase}: {frac*100:.2f}%")


@app.command()
def particles(
    image_path: Annotated[Path, typer.Argument(help="Image to analyze for particles.")],
    pores: Annotated[str, typer.Option("--pores", help="'dark' or 'bright' particles.")] = "dark",
    pixel_size: Annotated[float, typer.Option("--pixel-size", help="Physical length per pixel.")] = 1.0,
    unit: Annotated[str, typer.Option("--unit", help="Physical length unit.")] = "px",
    min_size: Annotated[int, typer.Option("--min-size", help="Minimum particle area in pixels.")] = 10,
    exclude_border: Annotated[bool, typer.Option("--exclude-border", help="Exclude particles touching the border.")] = True,
    bins: Annotated[int, typer.Option("--bins", help="Number of histogram bins for size distribution.")] = 10,
    crop: Annotated[Optional[tuple[int, int, int, int]], typer.Option("--crop", help="Crop as x y width height.")] = None,
) -> None:
    """Detect and measure particles with shape analysis."""
    try:
        from .segmentation import threshold_image

        gray = _load_and_prepare(image_path, crop=crop)
        binary, _ = threshold_image(gray, method="otsu", pores=pores)  # type: ignore[arg-type]
        result = _analyze_particles(
            binary=binary,
            pixel_size=pixel_size,
            unit=unit,
            min_size=min_size,
            exclude_border=exclude_border,
            bins=bins,
        )
    except Exception as exc:
        raise typer.BadParameter(str(exc)) from exc

    typer.echo(f"Particle analysis: {image_path}")
    typer.echo(f"  Particles detected: {result.summary['particle_count']}")
    typer.echo(f"  Mean diameter: {result.summary['mean_diameter_unit']:.2f} {unit}")
    typer.echo(f"  Median diameter: {result.summary['median_diameter_unit']:.2f} {unit}")
    typer.echo(f"  Mean circularity: {result.summary['mean_circularity']:.4f}")
    typer.echo(f"  Mean convexity: {result.summary['mean_convexity']:.4f}")
    if result.size_distribution and result.size_distribution["bin_counts"]:
        counts = result.size_distribution["bin_counts"]
        centers = result.size_distribution["bin_centers"]
        typer.echo(f"  Size distribution ({bins} bins):")
        for i, (c, cnt) in enumerate(zip(centers, counts)):
            bar = "█" * max(1, int(cnt))
            typer.echo(f"    {c:.1f} {unit}: {cnt} {bar}")


if __name__ == "__main__":
    app()