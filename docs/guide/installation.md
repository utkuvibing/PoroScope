# Installation

## From PyPI

```bash
pip install poroscope
```

With napari plugin support:

```bash
pip install poroscope[napari]
```

## From Source

```bash
git clone https://github.com/utkuvibing/PoroScope.git
cd PoroScope
pip install -e ".[test,napari]"
```

## Requirements

- Python 3.10+
- numpy, scipy, scikit-image, pandas, matplotlib, typer

## Verify Installation

```bash
poroscope --help
```
