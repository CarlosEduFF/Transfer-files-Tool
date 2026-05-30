"""CLI Typer gerada dinamicamente a partir do registry de operações.

Para cada operação registrada, um comando Typer é criado convertendo seus
`Param` em argumentos/opções. Nenhuma operação precisa ser registrada
manualmente aqui — adicionar uma operação ao registry a faz surgir na CLI.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Optional

import typer

from .. import operations  # noqa: F401  (dispara o auto-registro)
from ..operations.base import Operation, Param, ParamType
from ..operations.registry import all as all_operations
from ..shared.errors import PdfToolsError
from .console import console

app = typer.Typer(
    name="pdftools",
    help="[bold]PDF Tools[/bold] — manipulação completa de PDFs via linha de comando.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def _annotation_for(param: Param) -> Any:
    """Tipo Python usado na anotação do parâmetro do comando."""
    if param.type in (ParamType.PDF, ParamType.OUTPUT_PATH, ParamType.OUTPUT_DIR):
        return Path if param.required else Optional[Path]
    if param.type in (ParamType.PDF_LIST, ParamType.IMAGE_LIST):
        return list[Path]
    if param.type == ParamType.INT:
        return int if param.required else Optional[int]
    if param.type == ParamType.BOOL:
        return bool
    # PAGE_RANGE, CHOICE, STR
    return str if param.required else Optional[str]


def _typer_default(param: Param) -> Any:
    """Constrói o objeto typer.Argument/Option que serve de default do parâmetro."""
    is_option = param.cli_flags is not None
    default_value = param.default
    if param.required and param.type != ParamType.BOOL:
        default_value = ...

    if param.choices:
        help_text = f"{param.help} [{'/'.join(param.choices)}]"
    else:
        help_text = param.help

    if is_option:
        return typer.Option(default_value, *param.cli_flags, help=help_text)
    return typer.Argument(default_value, help=help_text)


def _make_command(op: Operation):
    """Cria a função-callback do comando Typer para a operação `op`."""

    def command(**kwargs: Any) -> None:
        try:
            result = op.run(**kwargs)
        except PdfToolsError as e:
            raise typer.BadParameter(str(e))
        op.render(result, console)

    # Constrói dinamicamente a assinatura para o Typer inferir args/opções.
    parameters = []
    for p in op.params:
        parameters.append(
            inspect.Parameter(
                p.name,
                kind=inspect.Parameter.KEYWORD_ONLY,
                default=_typer_default(p),
                annotation=_annotation_for(p),
            )
        )
    command.__signature__ = inspect.Signature(parameters)
    command.__name__ = op.name.replace("-", "_")
    command.__doc__ = op.help
    return command


def _build() -> None:
    for op in all_operations():
        app.command(name=op.name, help=op.help)(_make_command(op))


# Importa o pacote de operações dispara o auto-registro, então construímos a CLI.
_build()
