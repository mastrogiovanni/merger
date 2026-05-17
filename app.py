#!/usr/bin/env python3
"""HTTP API for merging and combining Word documents."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from combine_docx import combine_docx
from merge_docx import merge_docx

app = FastAPI(title="Nando DOCX", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Mode = Literal["merge", "combine"]


def _validate_uploads(files: list[UploadFile]) -> None:
    if len(files) < 2:
        raise HTTPException(
            status_code=400,
            detail="Upload at least two .docx files.",
        )
    for upload in files:
        name = upload.filename or ""
        if not name.lower().endswith(".docx"):
            raise HTTPException(
                status_code=400,
                detail=f"Not a .docx file: {name or '(unnamed)'}",
            )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/process")
async def process(
    mode: Mode = Form(...),
    files: list[UploadFile] = File(...),
) -> Response:
    _validate_uploads(files)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        inputs: list[Path] = []

        for index, upload in enumerate(files):
            safe_name = Path(upload.filename or f"document-{index + 1}.docx").name
            if not safe_name.lower().endswith(".docx"):
                safe_name = f"{safe_name}.docx"
            dest = tmp_path / f"{index:03d}_{safe_name}"
            content = await upload.read()
            if not content:
                raise HTTPException(
                    status_code=400,
                    detail=f"Empty file: {upload.filename}",
                )
            dest.write_bytes(content)
            inputs.append(dest)

        output = tmp_path / "result.docx"
        try:
            if mode == "merge":
                merge_docx(inputs, output)
            else:
                combine_docx(inputs, output)
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        result_bytes = output.read_bytes()

    download_name = "merged.docx" if mode == "merge" else "combined.docx"
    return Response(
        content=result_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
    )


_FRONTEND_DIST = Path(__file__).resolve().parent / "frontend" / "dist"
if _FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=_FRONTEND_DIST, html=True), name="frontend")
