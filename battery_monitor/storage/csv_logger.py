"""Persistência do histórico em CSV."""

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..config import LOG_PATH

_HEADER = ["timestamp", "percent", "plugged", "health_pct"]


@dataclass(frozen=True)
class LogEntry:
    """Uma amostra lida do CSV histórico."""

    timestamp: datetime
    percent: float
    plugged: Optional[bool]
    health_pct: Optional[float]


class CsvLogger:
    """Acrescenta linhas ao CSV histórico (cria o cabeçalho se for novo)."""

    def __init__(self, path: Path = LOG_PATH):
        self.path = path

    @property
    def name(self) -> str:
        return self.path.name

    def exists(self) -> bool:
        return self.path.exists()

    def append(
        self,
        percent: Optional[float],
        plugged: Optional[bool],
        health_pct: Optional[float],
    ) -> None:
        new_file = not self.path.exists()
        with self.path.open("a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new_file:
                w.writerow(_HEADER)
            w.writerow([
                datetime.now().isoformat(timespec="seconds"),
                percent,
                plugged,
                health_pct,
            ])

    def read_all(self) -> List[LogEntry]:
        """Lê o histórico, ignorando linhas malformadas."""
        if not self.path.exists():
            return []
        entries: List[LogEntry] = []
        with self.path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    entries.append(LogEntry(
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        percent=float(row["percent"]),
                        plugged=_parse_bool(row.get("plugged")),
                        health_pct=_parse_float(row.get("health_pct")),
                    ))
                except (ValueError, KeyError, TypeError):
                    continue  # pula linha corrompida
        return entries


def _parse_bool(text: Optional[str]) -> Optional[bool]:
    if text in ("True", "False"):
        return text == "True"
    return None


def _parse_float(text: Optional[str]) -> Optional[float]:
    try:
        return float(text) if text else None
    except (ValueError, TypeError):
        return None
