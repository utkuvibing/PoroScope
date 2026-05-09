# Examples

PoroScope v0.1 uses lightweight synthetic images to keep examples reproducible and license-safe.

## Regenerate the Synthetic Example

From the repository root:

```bash
python examples/generate_synthetic_example.py
```

This writes:

```text
examples/data/synthetic_microstructure.tif
examples/data/synthetic_microstructure.png
```

The image is a deterministic grayscale proxy for a ceramic/metal microstructure: bright matrix background, dark pore-like regions, and slight smooth intensity variation/noise.

## Run the CLI Example

After installing locally, run:

```bash
poroscope analyze examples/data/synthetic_microstructure.tif \
  --pixel-size 0.5 \
  --unit um \
  --pores dark \
  --threshold otsu \
  --min-size 20 \
  --fill-holes \
  --output examples/results \
  --overwrite
```

Expected outputs:

```text
examples/results/synthetic_microstructure/synthetic_microstructure_mask.tif
examples/results/synthetic_microstructure/synthetic_microstructure_overlay.png
examples/results/synthetic_microstructure/synthetic_microstructure_measurements.csv
examples/results/synthetic_microstructure/synthetic_microstructure_summary.json
examples/results/synthetic_microstructure/synthetic_microstructure_config.json
```

The README also includes `synthetic_microstructure_mask.png` as a GitHub-friendly preview of the exported TIFF mask.

## Analyze Your Own Image

Use the same CLI pattern for a user-provided image:

```bash
poroscope analyze image.tif --pixel-size 0.5 --unit um --pores dark --output results/
```

Use `--crop x y width height` to exclude scale bars, labels, or SEM metadata regions from analysis.
