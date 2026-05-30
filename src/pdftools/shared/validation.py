"""Validação de caminhos de PDF (camada pura)."""

from pathlib import Path

import fitz

from .errors import PdfOpenError, ValidationError


def validate_pdf_path(path: Path) -> None:
    if not path.exists():
        raise ValidationError(f"Arquivo não encontrado: {path}")
    if not path.is_file():
        raise ValidationError(f"Não é um arquivo: {path}")
    try:
        doc = fitz.open(str(path))
        doc.close()
    except Exception as e:
        raise PdfOpenError(f"Não foi possível abrir o PDF: {e}")
