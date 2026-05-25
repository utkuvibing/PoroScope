# napari Plugin

PoroScope provides an interactive napari plugin for visual microstructure analysis.

## Installation

```bash
pip install poroscope[napari]
```

## Usage

1. Launch napari: `napari`
2. Open an image (File → Open)
3. Go to **Plugins → PoroScope**
4. Click the analysis button you want

## Available Actions

| Button | Description |
|--------|-------------|
| Analyze Porosity (Dark/Bright) | Generate pore mask overlay |
| Segment Grains | Watershed grain segmentation |
| 3-Phase / 4-Phase Segmentation | Multi-Otsu phase labeling |
| Analyze Particles (Dark/Bright) | Particle detection |

Results appear as labeled overlay layers in the viewer.
