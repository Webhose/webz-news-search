"""Execute the mcp-webz notebook with real keys and save outputs.

Skips the environment-specific cells (pip install, .env echo) and the
try-it-yourself placeholder demo, matching how the sibling cookbook
notebooks are committed. Fails loudly if a secret reaches an output.
"""

import os
import pathlib
import sys
import tempfile

import nbformat
from nbclient import NotebookClient

SRC = pathlib.Path(sys.argv[1])

SKIP_MARKERS = (
    "%pip install",
    "!echo",
    'your_query = "Your Query Here"',
    'Markdown(custom_response["content"])',
    "print_mcp_calls(custom_response)",
)

SECRETS = [v for v in (os.getenv("GROQ_API_KEY"), os.getenv("WEBZ_API_TOKEN")) if v]
if len(SECRETS) != 2:
    raise SystemExit("set GROQ_API_KEY and WEBZ_API_TOKEN")

nb = nbformat.read(SRC, as_version=4)

skipped = {}
kept = []
for index, cell in enumerate(nb.cells):
    source = cell.get("source", "")
    if cell.cell_type == "code" and any(m in source for m in SKIP_MARKERS):
        skipped[index] = cell
    else:
        kept.append(cell)

print(f"executing {len(kept)} cells, skipping {len(skipped)}")
nb.cells = kept

with tempfile.TemporaryDirectory() as workdir:
    client = NotebookClient(
        nb,
        timeout=600,
        kernel_name="python3",
        resources={"metadata": {"path": workdir}},
    )
    client.execute()

# put the skipped cells back where they were, without outputs
for index in sorted(skipped):
    cell = skipped[index]
    cell["outputs"] = []
    cell["execution_count"] = None
    nb.cells.insert(index, cell)

serialized = nbformat.writes(nb)
for secret in SECRETS:
    if secret in serialized:
        raise SystemExit("ABORT: a secret leaked into the notebook")

SRC.write_text(serialized + "\n", encoding="utf-8")

executed = sum(1 for c in nb.cells if c.get("outputs"))
print(f"wrote {SRC} — {executed} cells now carry outputs, no secrets found")
