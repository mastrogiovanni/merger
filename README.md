# merge_docx

Merge multiple Word documents (`.docx`) into a single file from the command line.

## Requirements

- Python 3.9+
- [docxcompose](https://pypi.org/project/docxcompose/) (installs `python-docx` and `lxml` automatically)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
python merge_docx.py file1.docx file2.docx file3.docx -o merged.docx
```

Arguments:

| Argument | Description |
|----------|-------------|
| `FILE` … | One or more input `.docx` files, merged in the order given |
| `-o`, `--output` | Path for the merged output file (required) |

The first file is used as the base document; each following file is appended to it.

### Example

```bash
python merge_docx.py chapter1.docx chapter2.docx chapter3.docx -o book.docx
```

On success, the script prints the output path and how many files were merged.

## Limitations

- Only **`.docx`** files are supported (Office Open XML). Legacy **`.doc`** files must be saved as `.docx` in Word first.
- At least two input files are required.
- Documents with unusual custom XML or macros may not merge perfectly; typical Word content (text, styles, images, tables) is handled well.

## License

Use and modify as you like.
