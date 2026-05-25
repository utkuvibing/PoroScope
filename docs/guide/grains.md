# Grain Size Analysis

Grain size analysis uses watershed-based segmentation to separate touching
grains and measure their size distribution.

## CLI Usage

```bash
poroscope grains image.tif --pixel-size 0.5 --unit um
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--pixel-size` | 1.0 | Physical length per pixel |
| `--unit` | px | Unit |
| `--min-distance` | 5 | Minimum distance between grain centers |
| `--exclude-border` | True | Exclude grains touching the border |

## Output

```
Grain size analysis: image.tif
  Grains detected: 4081
  Mean diameter: 4.28 um
  Median diameter: 3.70 um
  ASTM grain size number: -11.88
```

## ASTM Grain Size Number

The ASTM grain size number G is calculated as:

```
G = -2.9542 + 6.6459 * log10(grains_per_mm²)
```

Higher G = finer grains. Negative values indicate very fine microstructures.
