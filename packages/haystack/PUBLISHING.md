# Publishing webz-haystack to PyPI

## Prerequisites

- PyPI account and API token with upload scope
- `twine` installed (`pip install twine build`)

## Build

```bash
cd packages/haystack
python -m pip install build
python -m build
```

Artifacts land in `dist/`:

- `webz_haystack-0.1.0-py3-none-any.whl`
- `webz_haystack-0.1.0.tar.gz`

## Upload

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-xxxxxxxx
python -m twine upload dist/webz_haystack-*
```

Or use `uv publish` if configured.

## Verify

```bash
pip install webz-haystack
python -c "from haystack_integrations.components.websearch.webz import WebzWebSearch; print(WebzWebSearch)"
```
