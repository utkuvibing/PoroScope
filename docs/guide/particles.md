# Particle Analysis

Particle analysis detects individual particles, measures shape factors,
and computes size distributions.

## CLI Usage

```bash
poroscope particles image.tif --pixel-size 0.5 --unit um --pores dark
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--pores` | dark | 'dark' or 'bright' particles |
| `--pixel-size` | 1.0 | Physical length per pixel |
| `--min-size` | 10 | Minimum particle area in pixels |
| `--exclude-border` | True | Exclude border-touching particles |
| `--bins` | 10 | Histogram bins for size distribution |

## Shape Factors

- **Circularity**: 4π × Area / Perimeter² (1.0 = perfect circle)
- **Convexity**: Convex hull area / Object area
- **Solidity**: Object area / Convex hull area
- **Aspect Ratio**: Major axis / Minor axis
- **Eccentricity**: 0 = circle, 1 = line segment

## Output

```
Particle analysis: image.tif
  Particles detected: 352
  Mean diameter: 4.16 um
  Mean circularity: 0.9035
  Size distribution (5 bins):
    6.0 um: 332 ████████
   14.4 um: 14  ███
```
