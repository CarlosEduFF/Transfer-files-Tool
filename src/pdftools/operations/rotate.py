"""Operação de rotação de páginas de PDF."""

from __future__ import annotations

from pathlib import Path

import fitz

from ..shared.errors import ValidationError
from ..shared.formatting import format_size
from ..shared.page_range import parse_page_range
from ..shared.validation import validate_pdf_path
from .base import Operation, Param, ParamType, Result
from .registry import register


@register
class RotateOperation(Operation):
    name = "rotate"
    help = "Rotaciona páginas de um PDF."
    menu_label = "Rotacionar páginas"
    params = [
        Param("input_pdf", ParamType.PDF, "Arquivo PDF de entrada"),
        Param(
            "degrees", ParamType.CHOICE, "Ângulo de rotação (múltiplo de 90)",
            choices=("90", "180", "270", "-90", "-180", "-270"),
            cli_flags=("--degrees", "-d"),
        ),
        Param(
            "pages", ParamType.PAGE_RANGE, "Páginas a rotacionar (padrão: todas)",
            required=False, cli_flags=("--pages", "-p"),
        ),
        Param(
            "output", ParamType.OUTPUT_PATH, "Arquivo PDF de saída",
            required=False, cli_flags=("--output", "-o"),
        ),
    ]

    def run(
        self,
        input_pdf: Path,
        degrees: int | str,
        pages: str | None = None,
        output: Path | None = None,
    ) -> Result:
        degrees = int(degrees)
        if degrees % 90 != 0:
            raise ValidationError("O ângulo de rotação deve ser múltiplo de 90.")

        validate_pdf_path(input_pdf)
        doc = fitz.open(str(input_pdf))
        total = doc.page_count

        page_list = parse_page_range(pages, total) if pages else list(range(total))

        for p in page_list:
            page = doc[p]
            page.set_rotation((page.rotation + degrees) % 360)

        out_path = output or input_pdf.parent / f"{input_pdf.stem}_rotated{input_pdf.suffix}"
        doc.save(str(out_path))
        doc.close()

        return Result(
            message=f"Rotacionadas {len(page_list)} página(s) em {degrees}° → {out_path}",
            outputs=[out_path],
            details=[("Tamanho", format_size(out_path.stat().st_size))],
        )
