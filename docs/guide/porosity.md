# Porosity Analysis

Porosity analysis is the core feature of PoroScope. It detects pores in
microstructure images using thresholding and provides calibrated measurements.

## CLI Usage

```bash
poroscope analyze image.tif --pixel-size 0.5 --unit um --pores dark -o results/
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--pixel-size` | 1.0 | Physical length per pixel |
| `--unit` | px | Unit (um, nm, mm, etc.) |
| `--pores` | dark | 'dark' for pores below threshold, 'bright' for above |
| `--threshold` | otsu | 'otsu' or 'manual' |
| `--min-size` | 20 | Remove objects smaller than this pixel area |
| `--fill-holes` | False | Fill internal holes |
| `--crop` | - | Crop as: x y width height |

## Pipeline

```
image -> grayscale -> threshold -> pore mask -> cleanup -> measurements -> exports
```

## Output Files

All exports go to `output/<image_name>/`:

- `*_mask.tif` — Binary pore mask
- `*_overlay.png` — Overlay visualization
- `*_measurements.csv` — Per-pore measurements
- `*_summary.json` — Aggregate statistics
- `*_config.json` — Reproducibility config

## Batch Processing

```bash
poroscope batch images/ --pixel-size 0.5 --unit um --output batch_results/
```
