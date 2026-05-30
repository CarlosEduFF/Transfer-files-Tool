"""Operação de conversão de imagens em um PDF."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from ..shared.errors import UnsupportedFormatError, ValidationError
from ..shared.formatting import format_size
from .base import Operation, Param, ParamType, Result
from .registry import register

SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}


@register
class ImageToPdfOperation(Operation):
    name = "img2pdf"
    help = "Converte uma ou mais imagens em um PDF."
    menu_label = "Converter imagens em PDF"
    params = [
        Param(
            "images", ParamType.IMAGE_LIST,
            "Imagens a converter (PNG, JPG, BMP, TIFF, WEBP)",
        ),
        Param(
            "output", ParamType.OUTPUT_PATH, "Arquivo PDF de saída",
            required=False, default=Path("output.pdf"), cli_flags=("--output", "-o"),
        ),
    ]

    def run(self, images: list[Path], output: Path | None = None) -> Result:
        for p in images:
            if not p.exists():
                raise ValidationError(f"Arquivo não encontrado: {p}")
            if p.suffix.lower() not in SUPPORTED_FORMATS:
                raise UnsupportedFormatError(
                    f"Formato não suportado: '{p.suffix}'. Use: {', '.join(sorted(SUPPORTED_FORMATS))}"
                )

        out_path = output or Path("output.pdf")
        loaded = []
        for p in images:
            img = Image.open(str(p))
            if img.mode != "RGB":
                img = img.convert("RGB")
            loaded.append(img)

        if not loaded:
            raise ValidationError("Nenhuma imagem válida fornecida.")

        loaded[0].save(
            str(out_path),
            save_all=True,
            append_images=loaded[1:],
            resolution=72.0,
        )
        for img in loaded:
            img.close()

        return Result(
            message=f"{len(images)} imagem(ns) convertidas → {out_path}",
            outputs=[out_path],
            details=[("Tamanho", format_size(out_path.stat().st_size))],
        )
