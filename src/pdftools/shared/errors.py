"""Hierarquia de erros do pdftools.

Camada pura: não depende de typer, rich nem de bibliotecas de PDF.
A camada de apresentação é responsável por traduzir estes erros para o
formato do framework (ex.: typer.BadParameter).
"""


class PdfToolsError(Exception):
    """Erro base de todas as operações do pdftools."""


class ValidationError(PdfToolsError):
    """Entrada inválida fornecida pelo usuário (página, formato, opção, etc.)."""


class PdfOpenError(PdfToolsError):
    """Não foi possível abrir ou ler o arquivo PDF."""


class UnsupportedFormatError(PdfToolsError):
    """Formato de arquivo não suportado para a operação."""
