"""Pacote de operações.

Importar este pacote dispara o auto-registro de todas as operações no registry.
Para adicionar uma nova operação, crie um módulo aqui com uma classe decorada
com @register e adicione o import correspondente abaixo.
"""

from . import (  # noqa: F401
    compress,
    extract_text,
    html_to_pdf,
    image_to_pdf,
    merge,
    metadata,
    pdf_to_image,
    rotate,
    split,
)
from .registry import all, get, register  # noqa: F401

__all__ = ["all", "get", "register"]
