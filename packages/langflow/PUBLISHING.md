# Publishing lfx-webz to PyPI

## Prerequisites

- PyPI account and API token with upload scope
- `twine` installed (`pip install twine build`)

## Check

```bash
cd packages/langflow
lfx extension validate .
pytest
```

## Build

```bash
cd packages/langflow
python -m pip install build
python -m build
```

Artifacts land in `dist/`:

- `lfx_webz-0.1.0-py3-none-any.whl`
- `lfx_webz-0.1.0.tar.gz`

## Upload

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-xxxxxxxx
python -m twine upload dist/lfx_webz-*
```

Or use `uv publish` if configured.

## Verify

```bash
pip install lfx-webz
python -c "from components.lfx_webz.webz_news_search import WebzNewsSearchComponent; print(WebzNewsSearchComponent.display_name)"
```

Restart Langflow. The component is listed under the Webz.io bundle.

After the package is on PyPI, comment on [langflow-ai/langflow#15219](https://github.com/langflow-ai/langflow/issues/15219) with the package link: https://pypi.org/project/lfx-webz/
