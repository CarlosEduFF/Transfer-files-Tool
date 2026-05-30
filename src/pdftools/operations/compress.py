"""Operação de compressão de PDF."""

from __future__ import annotations

from pathlib import Path

import fitz

from ..shared.formatting import format_size
from ..shared.validation import validate_pdf_path
from .base import Operation, Param, ParamType, Result
from .registry import register


@register
class CompressOperation(Operation):
    name = "compress"
    help = "Comprime um PDF reduzindo o tamanho do arquivo."
    menu_label = "Comprimir PDF"
    params = [
        Param("input_pdf", ParamType.PDF, "Arquivo PDF de entrada"),
        Param(
            "output", ParamType.OUTPUT_PATH, "Arquivo PDF de saída",
            required=False, cli_flags=("--output", "-o"),
        ),
    ]

    def run(self, input_pdf: Path, output: Path | None = None) -> Result:
        validate_pdf_path(input_pdf)
        original_size = input_pdf.stat().st_size

        doc = fitz.open(str(input_pdf))
        out_path = output or input_pdf.parent / f"{input_pdf.stem}_compressed{input_pdf.suffix}"
        doc.save(
            str(out_path),
            garbage=4,
            deflate=True,
            deflate_images=True,
            deflate_fonts=True,
            clean=True,
        )
        doc.close()

        compressed_size = out_path.stat().st_size
        reduction = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0

        return Result(
            message=f"PDF comprimido → {out_path}",
            outputs=[out_path],
            details=[
                ("Antes", format_size(original_size)),
                ("Depois", format_size(compressed_size)),
                ("Redução", f"{reduction:.1f}%"),
            ],
        )
