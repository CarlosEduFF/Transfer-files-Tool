"""Operações de divisão de PDF: extrair intervalo e dividir em N partes."""

from __future__ import annotations

from pathlib import Path

import fitz

from ..shared.errors import ValidationError
from ..shared.formatting import format_size
from ..shared.page_range import parse_page_range
from ..shared.validation import validate_pdf_path
from .base import Operation, Param, ParamType, Result
from .registry import register


def _output_path(input_path: Path, suffix: str, output: Path | None) -> Path:
    if output is not None:
        return output
    return input_path.parent / f"{input_path.stem}_{suffix}{input_path.suffix}"


@register
class SplitOperation(Operation):
    name = "split"
    help = "Extrai um intervalo de páginas de um PDF."
    menu_label = "Cortar páginas de um PDF"
    params = [
        Param("input_pdf", ParamType.PDF, "Arquivo PDF de entrada"),
        Param(
            "pages", ParamType.PAGE_RANGE,
            'Páginas a extrair: "1-5", "1,3,7" ou "2-4,8"',
            cli_flags=("--pages", "-p"),
        ),
        Param(
            "output", ParamType.OUTPUT_PATH, "Arquivo PDF de saída",
            required=False, cli_flags=("--output", "-o"),
        ),
    ]

    def run(self, input_pdf: Path, pages: str, output: Path | None = None) -> Result:
        validate_pdf_path(input_pdf)
        src = fitz.open(str(input_pdf))
        total = src.page_count

        page_list = parse_page_range(pages, total)

        out_path = _output_path(input_pdf, "split", output)
        out_doc = fitz.open()
        for p in page_list:
            out_doc.insert_pdf(src, from_page=p, to_page=p)
        out_doc.save(str(out_path))
        out_doc.close()
        src.close()

        return Result(
            message=f"Extraídas {len(page_list)} página(s) de {input_pdf.name}",
            outputs=[out_path],
            details=[
                ("Saída", f"{out_path} ({format_size(out_path.stat().st_size)})"),
            ],
        )


@register
class SplitPartsOperation(Operation):
    name = "split-parts"
    help = "Divide um PDF em múltiplas partes, cada uma com um intervalo de páginas."
    menu_label = "Dividir um PDF em várias partes"
    params = [
        Param("input_pdf", ParamType.PDF, "Arquivo PDF de entrada"),
        Param(
            "ranges", ParamType.STR,
            'Intervalos das partes separados por ";" (ex.: "1-3;4-7;8-10")',
            cli_flags=("--ranges", "-r"),
        ),
        Param(
            "output_dir", ParamType.OUTPUT_DIR, "Diretório de saída das partes",
            required=False, cli_flags=("--output-dir", "-o"),
        ),
    ]

    def run(
        self,
        input_pdf: Path,
        ranges: str | list[tuple[int, int]],
        output_dir: Path | None = None,
    ) -> Result:
        validate_pdf_path(input_pdf)
        src = fitz.open(str(input_pdf))
        total = src.page_count

        parts = _parse_parts(ranges, total)

        out_dir = output_dir or input_pdf.parent / f"{input_pdf.stem}_partes"
        out_dir.mkdir(parents=True, exist_ok=True)

        created: list[Path] = []
        details: list[tuple[str, str]] = []
        for i, (start, end) in enumerate(parts, start=1):
            out_doc = fitz.open()
            out_doc.insert_pdf(src, from_page=start - 1, to_page=end - 1)
            out_path = out_dir / f"{input_pdf.stem}_parte{i}.pdf"
            out_doc.save(str(out_path))
            out_doc.close()
            created.append(out_path)
            n_pages = end - start + 1
            details.append(
                (out_path.name, f"{n_pages} pág., {format_size(out_path.stat().st_size)}")
            )

        src.close()

        return Result(
            message=f"{len(created)} parte(s) criada(s) em {out_dir}",
            outputs=created,
            details=details,
        )


def _parse_parts(
    ranges: str | list[tuple[int, int]], total: int
) -> list[tuple[int, int]]:
    """Normaliza a especificação das partes para uma lista de (início, fim) 1-based."""
    if isinstance(ranges, str):
        parsed: list[tuple[int, int]] = []
        for chunk in ranges.split(";"):
            chunk = chunk.strip()
            if not chunk:
                continue
            if "-" in chunk:
                a, _, b = chunk.partition("-")
                bounds = (a, b)
            else:
                bounds = (chunk, chunk)
            try:
                start, end = int(bounds[0]), int(bounds[1])
            except ValueError:
                raise ValidationError(f"Parte inválida: '{chunk}'")
            parsed.append((start, end))
        parts = parsed
    else:
        parts = list(ranges)

    if not parts:
        raise ValidationError("Nenhuma parte especificada.")
    for start, end in parts:
        if start < 1 or end < start or end > total:
            raise ValidationError(
                f"Intervalo {start}-{end} fora dos limites (1-{total})"
            )
    return parts
