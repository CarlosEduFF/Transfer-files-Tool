"""Operação de conversão de HTML/URL em PDF."""

from __future__ import annotations

import logging
from pathlib import Path

from ..shared.errors import ValidationError
from ..shared.formatting import format_size
from .base import Operation, Param, ParamType, Result
from .registry import register


@register
class HtmlToPdfOperation(Operation):
    name = "html2pdf"
    help = "Converte um arquivo HTML ou URL em PDF."
    menu_label = "Converter HTML/URL em PDF"
    params = [
        Param("source", ParamType.STR, "Caminho de arquivo HTML ou URL (http/https)"),
        Param(
            "output", ParamType.OUTPUT_PATH, "Arquivo PDF de saída",
            required=False, default=Path("output.pdf"), cli_flags=("--output", "-o"),
        ),
        Param(
            "base_url", ParamType.STR, "URL base para assets relativos",
            required=False, cli_flags=("--base-url", "-b"),
        ),
    ]

    def run(
        self,
        source: str,
        output: Path | None = None,
        base_url: str | None = None,
    ) -> Result:
        is_url = source.startswith("http://") or source.startswith("https://")
        src_path = None
        if not is_url:
            src_path = Path(source)
            if not src_path.exists():
                raise ValidationError(f"Arquivo não encontrado: {source}")

        try:
            import weasyprint
        except (ImportError, OSError) as e:
            raise ValidationError(
                "WeasyPrint não pôde ser carregado. Verifique a instalação das "
                f"bibliotecas nativas (GTK). Detalhe: {e}"
            )

        logging.getLogger("weasyprint").setLevel(logging.ERROR)
        logging.getLogger("weasyprint.progress").setLevel(logging.ERROR)
        logging.getLogger("fonttools").setLevel(logging.ERROR)

        out_path = output or Path("output.pdf")

        if is_url:
            html = weasyprint.HTML(url=source)
        else:
            resolved_base = base_url or str(src_path.parent)
            html = weasyprint.HTML(filename=str(src_path), base_url=resolved_base)

        html.write_pdf(str(out_path))

        return Result(
            message=f"HTML convertido → {out_path}",
            outputs=[out_path],
            details=[("Tamanho", format_size(out_path.stat().st_size))],
        )
