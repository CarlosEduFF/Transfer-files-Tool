"""Menu interativo gerado a partir do registry de operações.

O menu lista todas as operações registradas e, ao escolher uma, coleta os
valores de cada `Param` via prompts simples (input/print), executa a operação
e renderiza o resultado com o mesmo `render` usado pela CLI. Adicionar uma
operação ao registry a faz surgir aqui automaticamente.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .. import operations  # noqa: F401  (dispara o auto-registro)
from ..operations.base import Operation, Param, ParamType
from ..operations.registry import all as all_operations
from ..shared.errors import PdfToolsError
from .console import console

_IMAGE_FORMATS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}


def _header() -> None:
    print()
    print("=" * 50)
    print("        PDF Tools — Menu Interativo")
    print("=" * 50)
    print()


class _Abort(Exception):
    """Sinaliza que o usuário encerrou a entrada (EOF/Ctrl-C ou stdin vazio)."""


def _input(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        raw = input(f"  > {prompt}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        # Sem stdin interativo: usa o default se houver, senão aborta para não
        # entrar em loop infinito.
        if default:
            return default
        raise _Abort
    return raw or default


def _ask_existing_pdf(prompt: str) -> Path:
    while True:
        raw = _input(prompt)
        p = Path(raw)
        if p.exists() and p.suffix.lower() == ".pdf":
            return p
        print(f"  Arquivo não encontrado ou não é um PDF: {raw}")


def _ask_pdf_list(prompt: str) -> list[Path]:
    print(f"  {prompt}. Digite um por linha; deixe em branco para finalizar.")
    paths: list[Path] = []
    while True:
        raw = _input(f"PDF {len(paths) + 1}")
        if not raw:
            if len(paths) < 2:
                print("  Adicione pelo menos 2 arquivos.")
                continue
            return paths
        p = Path(raw)
        if not p.exists() or p.suffix.lower() != ".pdf":
            print(f"  Arquivo inválido: {raw}")
            continue
        paths.append(p)


def _ask_image_list(prompt: str) -> list[Path]:
    print(f"  {prompt}. Digite uma por linha; deixe em branco para finalizar.")
    images: list[Path] = []
    while True:
        raw = _input(f"Imagem {len(images) + 1}")
        if not raw:
            if not images:
                print("  Adicione pelo menos 1 imagem.")
                continue
            return images
        p = Path(raw)
        if not p.exists() or p.suffix.lower() not in _IMAGE_FORMATS:
            print(f"  Arquivo inválido ou formato não suportado: {raw}")
            continue
        images.append(p)


def _ask_choice(param: Param) -> str:
    choices = param.choices or ()
    options = "/".join(choices)
    default = str(param.default) if param.default is not None else ""
    while True:
        raw = _input(f"{param.help} ({options})", default=default)
        if raw in choices:
            return raw
        print(f"  Opção inválida. Escolha entre: {options}")


def _ask_int(param: Param) -> int:
    default = str(param.default) if param.default is not None else ""
    while True:
        raw = _input(param.help, default=default)
        if not raw.lstrip("-").isdigit():
            print("  Digite um número inteiro.")
            continue
        value = int(raw)
        if param.min is not None and value < param.min:
            print(f"  Valor mínimo: {param.min}")
            continue
        if param.max is not None and value > param.max:
            print(f"  Valor máximo: {param.max}")
            continue
        return value


def _ask_bool(param: Param) -> bool:
    default = "s" if param.default else "n"
    raw = _input(f"{param.help} (s/n)", default=default).lower()
    return raw in ("s", "sim", "y", "yes")


def _collect(param: Param) -> Any:
    """Coleta o valor de um parâmetro conforme seu tipo."""
    if param.type == ParamType.PDF:
        return _ask_existing_pdf(param.help)
    if param.type == ParamType.PDF_LIST:
        return _ask_pdf_list(param.help)
    if param.type == ParamType.IMAGE_LIST:
        return _ask_image_list(param.help)
    if param.type == ParamType.CHOICE:
        return _ask_choice(param)
    if param.type == ParamType.INT:
        return _ask_int(param)
    if param.type == ParamType.BOOL:
        return _ask_bool(param)
    if param.type in (ParamType.OUTPUT_PATH, ParamType.OUTPUT_DIR):
        raw = _input(f"{param.help} (Enter para padrão)")
        return Path(raw) if raw else None
    # PAGE_RANGE, STR
    raw = _input(param.help + ("" if param.required else " (Enter para pular)"))
    return raw if raw else (None if not param.required else raw)


def _run_operation(op: Operation) -> None:
    print(f"\n--- {op.menu_label or op.name} ---")
    kwargs: dict[str, Any] = {}
    for param in op.params:
        value = _collect(param)
        # Omite opcionais vazios para usar os defaults da operação.
        if value is None and not param.required:
            continue
        kwargs[param.name] = value

    try:
        result = op.run(**kwargs)
    except PdfToolsError as e:
        print(f"\n  Erro: {e}")
        return
    op.render(result, console)


def run_menu() -> None:
    ops = all_operations()
    _header()
    try:
        while True:
            for i, op in enumerate(ops, start=1):
                print(f"  [{i}] {op.menu_label or op.name}")
            print("  [0] Sair")
            print()

            choice = _input("Escolha uma opção")
            if choice == "0":
                print("\n  Até mais!\n")
                return

            if not choice.isdigit() or not (1 <= int(choice) <= len(ops)):
                print(f"  Opção inválida: {choice!r}\n")
                continue

            op = ops[int(choice) - 1]
            try:
                _run_operation(op)
            except _Abort:
                print("\n  Operação cancelada.")
            except Exception as e:  # salvaguarda contra erros inesperados
                print(f"\n  Erro inesperado: {e}")

            print()
            again = _input("Voltar ao menu? (s/n)", default="s").lower()
            if again not in ("s", "sim", "y", "yes"):
                print("\n  Até mais!\n")
                return
    except _Abort:
        print("\n  Até mais!\n")
