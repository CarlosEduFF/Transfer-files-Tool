"""Operação de mesclagem de múltiplos PDFs."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import fitz

from ..shared.errors import ValidationError
from ..shared.formatting import format_size
from ..shared.validation import validate_pdf_path
from .base import Operation, Param, ParamType, Result
from .registry import register


@dataclass(frozen=True)
class MergeResult(Result):
    rows: list[tuple[str, int, str]] = field(default_factory=list)


@register
class MergeOperation(Operation):
    name = "merge"
    help = "Mescla múltiplos PDFs em um único arquivo."
    menu_label = "Mesclar múltiplos PDFs"
    params = [
        Param("input_pdfs", ParamType.PDF_LIST, "Dois ou mais PDFs a mesclar (em ordem)"),
        Param(
            "output", ParamType.OUTPUT_PATH, "Arquivo PDF de saída",
            required=False, default=Path("merged.pdf"), cli_flags=("--output", "-o"),
        ),
    ]

    def run(self, input_pdfs: list[Path], output: Path | None = None) -> MergeResult:
        if len(input_pdfs) < 2:
            raise ValidationError("São necessários pelo menos 2 arquivos para mesclar.")
        for p in input_pdfs:
            validate_pdf_path(p)

        out_path = output or Path("merged.pdf")
        merged = fitz.open()
        rows: list[tuple[str, int, str]] = []
        total_pages = 0
        for p in input_pdfs:
            sub = fitz.open(str(p))
            pages = sub.page_count
            merged.insert_pdf(sub)
            sub.close()
            total_pages += pages
            rows.append((p.name, pages, format_size(p.stat().st_size)))

        merged.save(str(out_path))
        merged.close()

        return MergeResult(
            message=f"Mesclados {len(input_pdfs)} arquivo(s) → {out_path}",
            outputs=[out_path],
            details=[
                ("Total", f"{total_pages} página(s) | {format_size(out_path.stat().st_size)}"),
            ],
            rows=rows,
        )

    def render(self, result: Result, console: Any) -> None:
        from rich.table import Table

        if isinstance(result, MergeResult) and result.rows:
            table = Table(title="Arquivos mesclados", show_lines=True)
            table.add_column("Arquivo", style="cyan")
            table.add_column("Páginas", justify="right")
            table.add_column("Tamanho", justify="right")
            for name, pages, size in result.rows:
                table.add_row(name, str(pages), size)
            console.print(table)
        super().render(result, console)
