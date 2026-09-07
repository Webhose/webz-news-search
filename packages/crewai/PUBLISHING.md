# Publishing crewai-webzio to PyPI

## Prerequisites

- PyPI account and API token with upload scope
- `twine` installed (`pip install twine build`)

## Build

```bash
cd packages/crewai
python -m pip install build
python -m build
```

Artifacts land in `dist/`:

- `crewai_webzio-0.1.1-py3-none-any.whl`
- `crewai_webzio-0.1.1.tar.gz`

## Upload

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-xxxxxxxx
python -m twine upload dist/crewai_webzio-*
```

Or use `uv publish` if configured.

## Verify

```bash
pip install crewai-webzio
python -c "from crewai_webzio import WebzioNewsSearchTool; print(WebzioNewsSearchTool)"
```
