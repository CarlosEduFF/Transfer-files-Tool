"""Modo linha de comando: argumentos/--file, sem prompts."""

import argparse
import sys
from pathlib import Path

from .menu import run_menu
from .migrator import DEFAULT_TARGET, migrate


def load_urls(args):
    urls = list(args.urls)
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
        for line in text.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls


def build_parser():
    parser = argparse.ArgumentParser(
        description="Migra repositórios GitHub para branches de um repo de destino, "
        "preservando o histórico."
    )
    parser.add_argument("urls", nargs="*", help="URLs de repositórios GitHub a migrar")
    parser.add_argument("--file", "-f", help="Arquivo texto com uma URL por linha")
    parser.add_argument(
        "--target", "-t", default=DEFAULT_TARGET,
        help=f"Repositório de destino no formato org/repo (padrão: {DEFAULT_TARGET})",
    )
    parser.add_argument(
        "--dir", "-d", default=".",
        help="Diretório onde clonar os repositórios (padrão: diretório atual)",
    )
    parser.add_argument(
        "--all-branches", action="store_true",
        help="Migra todas as branches remotas de cada repositório, com nomes originais",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.urls and not args.file:
        run_menu()
        return

    urls = load_urls(args)
    if not urls:
        parser.error("Forneça ao menos uma URL, via argumento ou --file.")

    base_dir = Path(args.dir).resolve()
    base_dir.mkdir(parents=True, exist_ok=True)

    failures = []
    for url in urls:
        try:
            migrate(url, base_dir, args.target, all_branches=args.all_branches)
        except Exception as exc:
            print(f"ERRO ao migrar {url}: {exc}\n", file=sys.stderr)
            failures.append(url)

    if failures:
        print("Falharam:", *failures, sep="\n  - ")
        sys.exit(1)


if __name__ == "__main__":
    main()
