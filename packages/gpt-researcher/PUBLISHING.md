# Publishing gpt-researcher-webz to PyPI

## Prerequisites

- PyPI account and API token with upload scope
- `twine` installed (`pip install twine build`)

## Build

```bash
cd packages/gpt-researcher
python -m pip install build
python -m build
```

Artifacts land in `dist/`:

- `gpt_researcher_webz-0.1.0-py3-none-any.whl`
- `gpt_researcher_webz-0.1.0.tar.gz`

## Upload

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-xxxxxxxx
python -m twine upload dist/gpt_researcher_webz-*
```

Or use `uv publish` if configured.

## Verify

```bash
pip install gpt-researcher-webz
python -c "from gpt_researcher_webz import WebzSearch; print(WebzSearch)"
```
