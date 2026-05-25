# Phase Analysis

Phase analysis segments multi-phase microstructures using multi-class Otsu
thresholding.

## CLI Usage

```bash
poroscope phases image.tif --n-classes 3 --pixel-size 0.5 --unit um
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--n-classes` | 3 | Number of phases (2-5) |
| `--pixel-size` | 1.0 | Physical length per pixel |
| `--unit` | px | Unit |

## Output

```
Phase analysis: image.tif
  Phases detected: 3
  Dominant phase: #0 (54.5%)
  Phase fractions:
    Phase 0: 54.51%
    Phase 1: 42.35%
    Phase 2: 3.14%
```
