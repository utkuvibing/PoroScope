# Examples

PoroScope v0.1 uses small synthetic images in the test suite to keep examples reproducible and license-safe.

After installing locally, run a synthetic or user-provided image with:

```bash
poroscope analyze image.tif --pixel-size 0.5 --unit um --pores dark --output results/
```

Use `--crop x y width height` to exclude scale bars, labels, or SEM metadata regions from analysis.

