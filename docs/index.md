# PoroScope

**Calibrated microstructure analysis for microscopy and SEM images.**

PoroScope is an open-source Python toolkit that makes microstructure analysis
reproducible and accessible. From single-image porosity measurements to
multi-phase segmentation and grain size distribution — all through a clean CLI
and an interactive napari plugin.

## Features

- **Porosity analysis** — Otsu/manual thresholding, pore detection, calibrated measurements
- **Grain size analysis** — Watershed-based grain segmentation, ASTM grain size number
- **Phase fraction analysis** — Multi-class Otsu for 2-5 phase microstructures
- **Particle analysis** — Shape factors (circularity, convexity, solidity), size distribution
- **napari plugin** — Interactive analysis with visual overlays
- **Batch processing** — Analyze entire folders at once
- **Reproducible exports** — CSV measurements, JSON summaries, PNG/TIFF masks

## Quick Start

```bash
# Install
pip install poroscope

# Analyze porosity
poroscope analyze image.tif --pixel-size 0.5 --unit um --pores dark

# Grain size analysis
poroscope grains image.tif --pixel-size 0.5 --unit um

# Phase segmentation
poroscope phases image.tif --n-classes 3 --pixel-size 0.5 --unit um

# Particle analysis
poroscope particles image.tif --pixel-size 0.5 --unit um --pores bright
```

## napari Plugin

```bash
pip install poroscope[napari]
napari
```

Then open **Plugins → PoroScope** from the napari menu.

## Example Output

For the included synthetic microstructure example:

```text
Analyzed: synthetic_microstructure.png
Porosity: 9.4345%
Pores detected: 18
```

## Citation

```bibtex
@software{sahin_2025_poroscope,
  author = {Sahin, Utku},
  title = {PoroScope: Calibrated Microstructure Analysis for Microscopy Images},
  year = {2025},
  url = {https://github.com/utkuvibing/PoroScope}
}
```
