"""Operação de extração de texto de PDF."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz

from ..shared.errors import ValidationError
from ..shared.page_range import parse_page_range
from ..shared.validation import validate_pdf_path
from .base import Operation, Param, ParamType, Result
from .registry import register


@dataclass(frozen=True)
class TextResult(Result):
    text: str = ""
    saved: bool = False


@register
class ExtractTextOperation(Operation):
    name = "extract-text"
    help = "Extrai texto de um PDF."
    menu_label = "Extrair texto"
    params = [
        Param("input_pdf", ParamType.PDF, "Arquivo PDF de entrada"),
        Param(
            "pages", ParamType.PAGE_RANGE, "Páginas a extrair (padrão: todas)",
            required=False, cli_flags=("--pages", "-p"),
        ),
        Param(
            "backend", ParamType.CHOICE, "Motor de extração",
            required=False, default="fitz", choices=("fitz", "pdfplumber"),
            cli_flags=("--backend", "-b"),
        ),
        Param(
            "tables", ParamType.BOOL, "Extrair tabelas (apenas pdfplumber)",
            required=False, default=False, cli_flags=("--tables", "-t"),
        ),
        Param(
            "output", ParamType.OUTPUT_PATH,
            "Salvar texto em arquivo (padrão: exibir no terminal)",
            required=False, cli_flags=("--output", "-o"),
        ),
    ]

    def run(
        self,
        input_pdf: Path,
        pages: str | None = None,
        backend: str = "fitz",
        tables: bool = False,
        output: Path | None = None,
    ) -> TextResult:
        if backend not in ("fitz", "pdfplumber"):
            raise ValidationError("Backend deve ser 'fitz' ou 'pdfplumber'.")
        if tables and backend != "pdfplumber":
            raise ValidationError("A opção de tabelas requer backend 'pdfplumber'.")

        validate_pdf_path(input_pdf)

        if backend == "fitz":
            text = _extract_fitz(input_pdf, pages)
        else:
            text = _extract_pdfplumber(input_pdf, pages, tables)

        if output:
            output.write_text(text, encoding="utf-8")
            return TextResult(
                message=f"Texto extraído → {output}",
                outputs=[output],
                text=text,
                saved=True,
            )
        return TextResult(message="", text=text, saved=False)

    def render(self, result: Result, console: Any) -> None:
        if isinstance(result, TextResult) and not result.saved:
            console.print(result.text)
            return
        super().render(result, console)


def _extract_fitz(input_pdf: Path, pages: str | None) -> str:
    doc = fitz.open(str(input_pdf))
    total = doc.page_count
    page_list = parse_page_range(pages, total) if pages else list(range(total))

    parts: list[str] = []
    for p in page_list:
        parts.append(f"--- Página {p + 1} ---")
        parts.append(doc[p].get_text("text"))
    doc.close()
    return "\n".join(parts)


def _extract_pdfplumber(input_pdf: Path, pages: str | None, tables: bool) -> str:
    try:
        import pdfplumber
    except ImportError:
        raise ValidationError("pdfplumber não instalado. Execute: pip install pdfplumber")

    parts: list[str] = []
    with pdfplumber.open(str(input_pdf)) as pdf:
        total = len(pdf.pages)
        page_list = parse_page_range(pages, total) if pages else list(range(total))
        for p in page_list:
            page = pdf.pages[p]
            parts.append(f"--- Página {p + 1} ---")
            if tables:
                for table in page.extract_tables():
                    for row in table:
                        parts.append("\t".join(cell or "" for cell in row))
                    parts.append("")
            else:
                text = page.extract_text()
                if text:
                    parts.append(text)
    return "\n".join(parts)
