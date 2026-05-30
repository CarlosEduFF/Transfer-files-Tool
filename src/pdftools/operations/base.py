"""Contrato base para operações do pdftools.

Cada operação declara seus metadados e parâmetros de forma agnóstica de
interface. A CLI (Typer) e o menu interativo consomem essa mesma declaração
para gerar suas interfaces automaticamente — adicionar uma operação não exige
tocar em nenhuma camada de apresentação.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable


class ParamType(Enum):
    """Tipos de entrada que uma operação pode declarar."""

    PDF = auto()          # caminho de um PDF existente
    PDF_LIST = auto()     # lista de PDFs existentes
    IMAGE_LIST = auto()   # lista de imagens existentes
    PAGE_RANGE = auto()   # string de intervalo de páginas (ex.: "1-3,5")
    INT = auto()          # inteiro (com min/max opcionais)
    CHOICE = auto()       # uma opção dentre `choices`
    STR = auto()          # texto livre
    OUTPUT_PATH = auto()  # caminho de arquivo de saída
    OUTPUT_DIR = auto()   # caminho de diretório de saída
    BOOL = auto()         # sim/não


@dataclass(frozen=True)
class Param:
    """Especificação de um parâmetro de operação — fonte única para CLI e menu."""

    name: str
    type: ParamType
    help: str
    required: bool = True
    default: Any = None
    choices: tuple[str, ...] | None = None
    cli_flags: tuple[str, ...] | None = None  # ex.: ("--pages", "-p")
    min: int | None = None
    max: int | None = None
    # Validador opcional extra: recebe o valor já convertido e levanta
    # ValidationError se inválido.
    validator: Callable[[Any], None] | None = None


@dataclass(frozen=True)
class Result:
    """Resultado genérico de uma operação.

    `message` é a linha de sucesso principal. `outputs` lista caminhos gerados.
    `details` são pares (rótulo, valor) exibidos abaixo. Operações com saída mais
    rica (tabelas) podem retornar uma subclasse e sobrescrever `Operation.render`.
    """

    message: str
    outputs: list[Any] = field(default_factory=list)
    details: list[tuple[str, str]] = field(default_factory=list)


class Operation:
    """Classe base de uma operação. Subclasses definem os atributos de classe
    e implementam `run`."""

    name: str = ""
    help: str = ""
    menu_label: str = ""
    params: list[Param] = []

    def run(self, **kwargs: Any) -> Result:  # pragma: no cover - contrato
        raise NotImplementedError

    def render(self, result: Result, console: Any) -> None:
        """Renderização padrão. Operações com tabela sobrescrevem este método."""
        console.print(f"[green]✓[/green] {result.message}")
        for label, value in result.details:
            console.print(f"  {label}: {value}")
