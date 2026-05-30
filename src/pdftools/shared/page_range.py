"""Parsing de intervalos de páginas (camada pura).

Aceita formatos como "1-5", "1,3,7" ou "2-4,8" e devolve uma lista de índices
0-based, sem duplicatas e preservando a ordem de aparição.
"""

from .errors import ValidationError


def parse_page_range(range_str: str, total_pages: int) -> list[int]:
    pages: list[int] = []
    parts = range_str.split(",")
    for part in parts:
        part = part.strip()
        if "-" in part:
            bounds = part.split("-")
            if len(bounds) != 2:
                raise ValidationError(f"Range inválido: '{part}'")
            try:
                start, end = int(bounds[0]), int(bounds[1])
            except ValueError:
                raise ValidationError(f"Range inválido: '{part}'")
            if start < 1 or end < start or end > total_pages:
                raise ValidationError(
                    f"Range '{part}' fora dos limites (1-{total_pages})"
                )
            pages.extend(range(start - 1, end))
        else:
            try:
                page = int(part)
            except ValueError:
                raise ValidationError(f"Número de página inválido: '{part}'")
            if page < 1 or page > total_pages:
                raise ValidationError(
                    f"Página {page} fora dos limites (1-{total_pages})"
                )
            pages.append(page - 1)

    seen: set[int] = set()
    unique: list[int] = []
    for p in pages:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique
