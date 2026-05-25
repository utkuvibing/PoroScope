# Contributing

Contributions are welcome! Here's how to get started.

## Development Setup

```bash
git clone https://github.com/utkuvibing/PoroScope.git
cd PoroScope
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test,napari]"
```

## Running Tests

```bash
pytest tests/ -v
```

## Code Style

- Type hints everywhere
- NumPy-style docstrings
- Follow existing patterns in the codebase

## Pull Request Process

1. Fork the repo
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a PR

## License

BSD-3-Clause
