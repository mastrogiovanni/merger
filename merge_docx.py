#!/usr/bin/env python3
"""Merge multiple Word (.docx) files into a single document."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from docx import Document
from docxcompose.composer import Composer


def validate_docx_inputs(inputs: list[Path]) -> None:
    if len(inputs) < 2:
        raise ValueError("Provide at least two .docx files to merge")

    for path in inputs:
        if not path.is_file():
            raise FileNotFoundError(path)
        if path.suffix.lower() != ".docx":
            raise ValueError(f"Not a .docx file: {path}")


def merge_docx(inputs: list[Path], output: Path) -> None:
    validate_docx_inputs(inputs)

    composer = Composer(Document(str(inputs[0])))
    for path in inputs[1:]:
        composer.append(Document(str(path)))

    output.parent.mkdir(parents=True, exist_ok=True)
    composer.save(str(output))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge Word (.docx) files into one document.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Input .docx files, in merge order",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        metavar="OUT.docx",
        help="Path for the merged output file",
    )
    args = parser.parse_args()

    inputs = [Path(f).resolve() for f in args.files]
    output = Path(args.output).resolve()

    try:
        merge_docx(inputs, output)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Wrote {output} ({len(inputs)} files merged)")


if __name__ == "__main__":
    main()
