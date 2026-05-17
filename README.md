# Word document merge tools

Command-line utilities to join multiple Word documents (`.docx`) into one file. Two modes are available:

| Script | Behavior |
|--------|----------|
| `merge_docx.py` | **Append** — stitches files end-to-end; fast, uses the first file’s section layout for most of the result |
| `combine_docx.py` | **Combine** — inserts a section break before each file and preserves each source’s page setup and headers/footers |

## Requirements

- Python 3.9+
- Node.js 18+ and npm (for the web UI only)
- [docxcompose](https://pypi.org/project/docxcompose/) (installs `python-docx` and `lxml` automatically)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Web app (frontend)

The React UI in `frontend/` lets you upload `.docx` files, reorder them, choose **Merge** or **Combine**, and download the result.

### Quick start (recommended)

From the project root:

```bash
chmod +x run.sh   # once, if needed
./run.sh
```

Then open **http://127.0.0.1:5173** in your browser. The script creates the venv if missing, installs Python and npm dependencies, and starts both the API (`:8000`) and the dev UI (`:5173`).

Press `Ctrl+C` to stop.

**Single-server mode** (builds the UI, serves API + static files on one port):

```bash
./run.sh --prod
```

Open **http://127.0.0.1:8000**.

### Manual start (development)

Use two terminals if you prefer to run services separately.

**Terminal 1 — API:**

```bash
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 — frontend:**

```bash
cd frontend
npm install
npm run dev
```

Open **http://127.0.0.1:5173**. Vite proxies `/api` requests to the backend on port 8000.

### Manual start (production-style)

```bash
cd frontend && npm install && npm run build && cd ..
source .venv/bin/activate
uvicorn app:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**.

## Which script to use

Use **`merge_docx.py`** when all inputs share the same layout (margins, orientation, headers) and you only need the text, styles, images, and tables in one continuous document.

Use **`combine_docx.py`** when each file has its own layout — for example one chapter in portrait and another in landscape, or different header/footer content per part. This matches the idea of Word’s per-document section handling (“combina documenti” in the sense of resolving separate sections), not the Review tab’s tracked-changes **Combine Revisions** feature.

## `merge_docx.py` — append merge

```bash
python merge_docx.py file1.docx file2.docx file3.docx -o merged.docx
```

| Argument | Description |
|----------|-------------|
| `FILE` … | Input `.docx` files, merged in the order given (at least two) |
| `-o`, `--output` | Output path (required) |

The first file is the base document; each following file is appended to it. Section properties from later files are largely ignored, so page size and headers from appended files may not carry over.

### Example

```bash
python merge_docx.py chapter1.docx chapter2.docx chapter3.docx -o book.docx
```

## `combine_docx.py` — section-aware combine

```bash
python combine_docx.py file1.docx file2.docx file3.docx -o combined.docx
```

Arguments are the same as for `merge_docx.py`.

For every file after the first, the tool:

1. Inserts a **new-page section break**
2. Copies **page setup** from that file (size, margins, orientation, columns, etc.)
3. Copies **header and footer** definitions into the output
4. Appends body content (paragraphs, tables, images, styles) via `docxcompose`
5. Applies the source file’s **final section** properties at the end of the combined document

Documents that already contain multiple sections keep their internal section breaks; only the boundary *between* input files is added.

### Example

```bash
python combine_docx.py cover.docx body.docx appendix.docx -o report.docx
```

## Programmatic use

Both modules expose a function you can import:

```python
from pathlib import Path
from merge_docx import merge_docx
from combine_docx import combine_docx

inputs = [Path("a.docx"), Path("b.docx")]
merge_docx(inputs, Path("out-merged.docx"))
combine_docx(inputs, Path("out-combined.docx"))
```

Input validation (`validate_docx_inputs`) is shared: at least two files, each must exist and have a `.docx` extension.

## Limitations

- Only **`.docx`** (Office Open XML) is supported. Save legacy **`.doc`** as `.docx` in Word first.
- At least two input files are required.
- Unusual custom XML, macros, or embedded objects may not transfer perfectly; normal Word content (text, styles, images, tables) works well.
- **`combine_docx.py`** does not merge tracked changes or comments the way Word’s Review → Combine does.
- Very complex multi-section sources may still need a manual check in Word after combining.

## License

Use and modify as you like.
