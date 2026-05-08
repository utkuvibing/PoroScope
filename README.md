# PoroScope

PoroScope is an open-source Python toolkit for calibrated porosity analysis in microscopy and SEM microstructure images.

The v0.1 scope is deliberately narrow: one reliable single-image workflow from image loading to pore segmentation, calibrated measurements, and reproducible exports.

```text
image -> grayscale -> threshold -> pore mask -> cleanup -> measurements -> exports
```

## Current v0.1 Scope

Included:

- PNG, JPG/JPEG, and TIFF image loading.
- Grayscale conversion.
- Otsu and manual thresholding.
- Pore polarity selection with `--pores dark` or `--pores bright`.
- Small object removal and optional hole filling.
- Connected component labeling.
- Calibrated measurements with `--pixel-size` and `--unit`.
- Porosity percentage and per-pore measurement table.
- Mask, overlay, CSV, summary JSON, and config JSON export.
- Single-image CLI.
- Unit tests with synthetic images.

Not included in v0.1:

- napari plugin.
- Streamlit dashboard.
- HTML/PDF reports.
- Batch processing.
- Saved calibration profiles.
- Adaptive thresholding or CLAHE.
- Multiphase segmentation.
- Deep learning.
- Full ImageJ/Fiji validation.

## Installation

From a local checkout:

```bash
pip install -e ".[test]"
```

## CLI Quick Start

Analyze an image with Otsu thresholding:

```bash
poroscope analyze image.tif --pixel-size 0.5 --unit um --pores dark --output results/
```

Analyze bright pores with a manual threshold:

```bash
poroscope analyze image.tif \
  --pixel-size 0.5 \
  --unit um \
  --pores bright \
  --threshold manual \
  --threshold-value 128 \
  --output results/
```

Crop away scale bars, labels, or SEM metadata before analysis:

```bash
poroscope analyze image.tif \
  --pixel-size 0.5 \
  --unit um \
  --pores dark \
  --crop 0 0 1024 900 \
  --output results/
```

Crop format is `x y width height`, in pixels. The crop is applied before thresholding and all reported measurements refer to the cropped analysis region.

## Calibration

Use `--pixel-size` to provide the physical length represented by one pixel.

Example:

```text
--pixel-size 0.5 --unit um
```

This means each pixel is `0.5 um` wide. Lengths are multiplied by `pixel_size`; areas are multiplied by `pixel_size^2`.

## Pore Polarity

Pores can appear dark or bright depending on imaging mode and preprocessing.

- `--pores dark`: pixels below the threshold are pores.
- `--pores bright`: pixels above the threshold are pores.

## Output Files

For `image.tif`, PoroScope writes:

```text
results/
└── image/
    ├── image_mask.tif
    ├── image_overlay.png
    ├── image_measurements.csv
    ├── image_summary.json
    └── image_config.json
```

The CSV contains one row per detected pore. If no pores are detected, PoroScope writes a valid CSV with headers and zero rows.

## Important Input Guidance

Do not include scale bars, image labels, microscope overlays, or SEM metadata bands in the analyzed region. These features can be segmented as pores and bias porosity. Use `--crop` or pre-crop images before analysis.

## Limitations

PoroScope v0.1 performs binary 2D porosity analysis only. Results depend on image quality, threshold choice, and calibration accuracy. It does not infer 3D porosity from 2D sections and does not replace domain review of segmentation quality.

## Roadmap

- v0.2: batch processing, reusable config files, improved examples.
- v0.3: napari plugin and interactive threshold preview.
- v0.4: HTML reports, saved calibration profiles, validation datasets.
- v1.0: stable API, documentation site, archived DOI release, publication-ready validation.

## Citation

If you use PoroScope in academic work, please cite the archived release once available. Citation metadata is provided in `CITATION.cff` and will be updated for release DOI metadata.

## License

PoroScope is released under the BSD-3-Clause license.

