# Publishing movieclaw-webz to PyPI

## Prerequisites

- PyPI account and API token with upload scope
- `twine` installed (`pip install twine build`)

## Build

```bash
cd packages/movieclaw
python -m pip install build
python -m build
```

Artifacts land in `dist/`:

- `movieclaw_webz-0.1.0-py3-none-any.whl`
- `movieclaw_webz-0.1.0.tar.gz`

## Upload

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-xxxxxxxx
python -m twine upload dist/movieclaw_webz-*
```

Or use `uv publish` if configured.

## Verify

```bash
pip install movieclaw-webz
python -c "from movieclaw_webz import WebzNewsSearchProvider; print(WebzNewsSearchProvider)"
```
