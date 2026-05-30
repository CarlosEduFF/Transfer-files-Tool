"""Operação de conversão de páginas de PDF em imagens."""

from __future__ import annotations

from pathlib import Path

import fitz

from ..shared.errors import ValidationError
from ..shared.page_range import parse_page_range
from ..shared.validation import validate_pdf_path
from .base import Operation, Param, ParamType, Result
from .registry import register


@register
class PdfToImageOperation(Operation):
    name = "pdf2img"
    help = "Converte páginas de um PDF em imagens (PNG ou JPG)."
    menu_label = "Converter PDF em imagens"
    params = [
        Param("input_pdf", ParamType.PDF, "Arquivo PDF de entrada"),
        Param(
            "fmt", ParamType.CHOICE, "Formato de saída",
            required=False, default="png", choices=("png", "jpg"),
            cli_flags=("--format", "-f"),
        ),
        Param(
            "dpi", ParamType.INT, "Resolução em DPI (72-600)",
            required=False, default=150, min=72, max=600,
            cli_flags=("--dpi", "-d"),
        ),
        Param(
            "pages", ParamType.PAGE_RANGE, "Páginas a converter (padrão: todas)",
            required=False, cli_flags=("--pages", "-p"),
        ),
        Param(
            "output_dir", ParamType.OUTPUT_DIR, "Diretório de saída das imagens",
            required=False, cli_flags=("--output-dir", "-o"),
        ),
    ]

    def run(
        self,
        input_pdf: Path,
        fmt: str = "png",
        dpi: int = 150,
        pages: str | None = None,
        output_dir: Path | None = None,
    ) -> Result:
        if fmt not in ("png", "jpg"):
            raise ValidationError("Formato deve ser 'png' ou 'jpg'.")
        if dpi < 72 or dpi > 600:
            raise ValidationError("DPI deve estar entre 72 e 600.")

        validate_pdf_path(input_pdf)
        doc = fitz.open(str(input_pdf))
        total = doc.page_count
        page_list = parse_page_range(pages, total) if pages else list(range(total))

        out_dir = output_dir or input_pdf.parent / f"{input_pdf.stem}_images"
        out_dir.mkdir(parents=True, exist_ok=True)
        mat = fitz.Matrix(dpi / 72, dpi / 72)

        saved: list[Path] = []
        ext = "jpeg" if fmt == "jpg" else "png"
        for p in page_list:
            pix = doc[p].get_pixmap(matrix=mat, alpha=False)
            out_file = out_dir / f"{input_pdf.stem}_page_{p + 1:04d}.{fmt}"
            pix.save(str(out_file), output=ext)
            saved.append(out_file)

        doc.close()

        return Result(
            message=f"{len(saved)} imagem(ns) salvas em {out_dir}",
            outputs=saved,
            details=[("Formato", f"{fmt.upper()} | DPI: {dpi}")],
        )
