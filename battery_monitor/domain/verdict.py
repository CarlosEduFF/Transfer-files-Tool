"""Regras puras de formatação e classificação — totalmente testáveis."""

from typing import Optional, Tuple

from ..config import HEALTH_THRESHOLDS, HEALTH_UNKNOWN, HEALTH_WORST


def fmt_secs(secs: Optional[int]) -> str:
    """Formata segundos restantes como '1h 05min', ou '—' se desconhecido."""
    if secs is None:
        return "—"
    h, m = divmod(secs // 60, 60)
    return f"{h}h {m:02d}min"


def health_verdict(pct: Optional[float]) -> Tuple[str, str]:
    """Retorna (rótulo, cor) para uma porcentagem de saúde da bateria."""
    if pct is None:
        return HEALTH_UNKNOWN
    for threshold, label, color in HEALTH_THRESHOLDS:
        if pct >= threshold:
            return label, color
    return HEALTH_WORST
