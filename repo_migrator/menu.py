"""Modo interativo: pergunta URLs, destino e confirma antes de migrar."""

import sys
from pathlib import Path

from . import git_ops
from .migrator import DEFAULT_TARGET, migrate


def prompt_urls():
    print("Cole as URLs dos repositórios (uma por linha). Linha vazia para finalizar:")
    urls = []
    while True:
        line = input("> ").strip()
        if not line:
            break
        urls.append(line)
    return urls


def _check_branches(urls):
    print("\nVerificando branches remotas...")
    branch_plan = {}
    for url in urls:
        name = git_ops.repo_name_from_url(url)
        try:
            branches = git_ops.list_remote_branches(url)
        except Exception as exc:
            print(f"  - {name}: erro ao consultar branches ({exc})")
            branches = []
        branch_plan[url] = branches
        if len(branches) > 1:
            print(f"  - {name}: {len(branches)} branches encontradas ({', '.join(branches)})")
        else:
            print(f"  - {name}: 1 branch")
    return branch_plan


def _ask_all_branches(branch_plan):
    all_branches_urls = set()
    multi_branch_urls = [url for url, b in branch_plan.items() if len(b) > 1]
    if not multi_branch_urls:
        return all_branches_urls

    print()
    for url in multi_branch_urls:
        name = git_ops.repo_name_from_url(url)
        answer = input(
            f"'{name}' tem múltiplas branches. Migrar todas com nomes originais? [s/N]: "
        ).strip().lower()
        if answer == "s":
            all_branches_urls.add(url)
    return all_branches_urls


def run_menu():
    print("=== Migração de repositórios GitHub ===\n")

    while True:
        urls = prompt_urls()
        if urls:
            break
        print("Nenhuma URL informada, tente novamente.\n")

    target = input(f"Repositório de destino [{DEFAULT_TARGET}]: ").strip() or DEFAULT_TARGET
    dir_input = input("Pasta onde clonar [.]: ").strip() or "."
    base_dir = Path(dir_input).resolve()

    branch_plan = _check_branches(urls)
    all_branches_urls = _ask_all_branches(branch_plan)

    print("\nResumo:")
    for url in urls:
        if url in all_branches_urls:
            print(f"  - {url}  ->  {len(branch_plan[url])} branches (nomes originais)")
        else:
            print(f"  - {url}  ->  branch '{git_ops.repo_name_from_url(url)}'")
    print(f"Destino: {target}")
    print(f"Pasta:   {base_dir}\n")

    confirm = input("Confirmar e executar? [s/N]: ").strip().lower()
    if confirm != "s":
        print("Cancelado.")
        return

    base_dir.mkdir(parents=True, exist_ok=True)
    failures = []
    for url in urls:
        try:
            migrate(url, base_dir, target, all_branches=url in all_branches_urls)
        except Exception as exc:
            print(f"ERRO ao migrar {url}: {exc}\n", file=sys.stderr)
            failures.append(url)

    if failures:
        print("Falharam:", *failures, sep="\n  - ")
        sys.exit(1)
    else:
        print("Todas as migrações concluídas com sucesso.")
