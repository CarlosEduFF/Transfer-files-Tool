"""Operação de extração de metadados de PDF."""

from __future__ import annotations

import json
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
class MetadataResult(Result):
    data: dict[str, Any] = field(default_factory=dict)
    output_format: str = "table"
    title: str = ""


@register
class MetadataOperation(Operation):
    name = "metadata"
    help = "Exibe metadados de um PDF."
    menu_label = "Ver metadados do PDF"
    params = [
        Param("input_pdf", ParamType.PDF, "Arquivo PDF de entrada"),
        Param(
            "fmt", ParamType.CHOICE, "Formato de saída",
            required=False, default="table", choices=("table", "json"),
            cli_flags=("--format", "-f"),
        ),
    ]

    def run(self, input_pdf: Path, fmt: str = "table") -> MetadataResult:
        if fmt not in ("table", "json"):
            raise ValidationError("Formato deve ser 'table' ou 'json'.")

        validate_pdf_path(input_pdf)
        doc = fitz.open(str(input_pdf))
        meta = doc.metadata
        page_count = doc.page_count
        is_encrypted = doc.is_encrypted
        doc.close()

        data = {
            "arquivo": input_pdf.name,
            "tamanho": format_size(input_pdf.stat().st_size),
            "páginas": page_count,
            "criptografado": is_encrypted,
            "formato": meta.get("format", ""),
            "título": meta.get("title", ""),
            "autor": meta.get("author", ""),
            "assunto": meta.get("subject", ""),
            "palavras-chave": meta.get("keywords", ""),
            "criador": meta.get("creator", ""),
            "produtor": meta.get("producer", ""),
            "data de criação": meta.get("creationDate", ""),
            "data de modificação": meta.get("modDate", ""),
        }

        return MetadataResult(
            message=f"Metadados de {input_pdf.name}",
            data=data,
            output_format=fmt,
            title=f"Metadados: {input_pdf.name}",
        )

    def render(self, result: Result, console: Any) -> None:
        if not isinstance(result, MetadataResult):
            return super().render(result, console)

        if result.output_format == "json":
            console.print(json.dumps(result.data, ensure_ascii=False, indent=2))
            return

        from rich.table import Table

        table = Table(title=result.title, show_lines=True)
        table.add_column("Campo", style="bold cyan", min_width=20)
        table.add_column("Valor")
        for key, value in result.data.items():
            table.add_row(key.capitalize(), str(value) if value else "[dim]—[/dim]")
        console.print(table)
