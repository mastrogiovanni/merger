#!/usr/bin/env python3
"""Combine Word (.docx) files with per-document section breaks (Combina Documenti).

Unlike a plain append merge, each input document starts in its own section so
page layout, orientation, and headers/footers from each source are preserved.
"""

from __future__ import annotations

import argparse
import sys
from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docxcompose.composer import Composer
from docxcompose.utils import NS, xpath

from merge_docx import validate_docx_inputs

# Section layout children copied from source w:sectPr to target w:sectPr.
_SECTION_LAYOUT_TAGS = frozenset(
    {
        "footnotePr",
        "endnotePr",
        "type",
        "pgSz",
        "pgMar",
        "paperSrc",
        "pgBorders",
        "lnNumType",
        "pgNumType",
        "cols",
        "formProt",
        "vAlign",
        "noEndnote",
        "titlePg",
        "textDirection",
        "bidi",
        "rtlGutter",
        "docGrid",
        "printerSettings",
    }
)


def _local_tag(element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _clear_section_layout(sect_pr) -> None:
    for child in list(sect_pr):
        if _local_tag(child) in _SECTION_LAYOUT_TAGS:
            sect_pr.remove(child)
    for ref in xpath(sect_pr, "w:headerReference|w:footerReference"):
        sect_pr.remove(ref)


def _apply_section_properties(src_sect_pr, dst_sect_pr, src_part, dst_part, composer) -> None:
    """Copy page setup and header/footer definitions from one section to another."""
    _clear_section_layout(dst_sect_pr)

    for child in src_sect_pr:
        if _local_tag(child) in _SECTION_LAYOUT_TAGS:
            dst_sect_pr.append(deepcopy(child))

    for ref in xpath(src_sect_pr, "w:headerReference|w:footerReference"):
        ref = deepcopy(ref)
        rid = ref.get("{%s}id" % NS["r"])
        rel = src_part.rels[rid]
        new_rel = composer.add_relationship(src_part, dst_part, rel)
        ref.set("{%s}id" % NS["r"], new_rel.rId)
        dst_sect_pr.append(ref)


class SectionCombiningComposer(Composer):
    """Composer that inserts a section break before each appended document."""

    def append(self, doc, remove_property_fields=True):
        self._begin_document_section(doc)
        super().append(doc, remove_property_fields=remove_property_fields)
        self._finalize_document_section(doc)

    def _begin_document_section(self, doc) -> None:
        """Start a new section for the incoming document's content."""
        self.doc.element.body.add_section_break()
        boundary = self.doc.sections[-2]
        boundary.start_type = WD_SECTION.NEW_PAGE
        _apply_section_properties(
            doc.sections[0]._sectPr,
            boundary._sectPr,
            doc.part,
            self.doc.part,
            self,
        )

    def _finalize_document_section(self, doc) -> None:
        """Apply the appended document's trailing section properties."""
        _apply_section_properties(
            doc.sections[-1]._sectPr,
            self.doc.sections[-1]._sectPr,
            doc.part,
            self.doc.part,
            self,
        )


def combine_docx(inputs: list[Path], output: Path) -> None:
    """Combine documents, resolving each file as its own section."""
    validate_docx_inputs(inputs)

    composer = SectionCombiningComposer(Document(str(inputs[0])))
    for path in inputs[1:]:
        composer.append(Document(str(path)))

    output.parent.mkdir(parents=True, exist_ok=True)
    composer.save(str(output))


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Combine Word (.docx) files into one document with a section break "
            "between each file (preserves per-document page setup and headers)."
        ),
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Input .docx files, in combine order",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        metavar="OUT.docx",
        help="Path for the combined output file",
    )
    args = parser.parse_args()

    inputs = [Path(f).resolve() for f in args.files]
    output = Path(args.output).resolve()

    try:
        combine_docx(inputs, output)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Wrote {output} ({len(inputs)} files combined)")


if __name__ == "__main__":
    main()
