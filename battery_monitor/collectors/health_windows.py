"""Relatório de desgaste no Windows via ``powercfg /batteryreport``."""

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from .base import HealthCollector
from ..domain.models import HealthReport


def _parse_mwh(text: Optional[str]) -> Optional[int]:
    """Extrai um número de uma string como '57.488 mWh' (formato pt-BR/EN)."""
    if not text:
        return None
    # remove separadores de milhar (ponto ou vírgula) e unidade
    digits = re.sub(r"[^\d]", "", text.split("mWh")[0])
    return int(digits) if digits else None


class WindowsHealthCollector(HealthCollector):
    """Gera o relatório HTML do Windows e extrai capacidade/ciclos."""

    def read(self) -> HealthReport:
        if os.name != "nt":
            return HealthReport.failed(
                "Relatório de desgaste disponível apenas no Windows."
            )

        tmp = Path(tempfile.gettempdir()) / "battery_monitor_report.html"
        try:
            subprocess.run(
                ["powercfg", "/batteryreport", "/output", str(tmp)],
                capture_output=True,
                timeout=30,
                check=True,
            )
        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            FileNotFoundError,
        ) as e:
            return HealthReport.failed(f"Falha ao gerar relatório: {e}")

        try:
            html = tmp.read_text(encoding="utf-8", errors="ignore")
        except OSError as e:
            return HealthReport.failed(f"Não foi possível ler o relatório: {e}")

        return self._parse(html)

    @staticmethod
    def _parse(html: str) -> HealthReport:
        def find(label: str) -> Optional[str]:
            m = re.search(
                rf"{label}</span></td><td[^>]*>([^<]*)", html, re.IGNORECASE
            )
            return m.group(1).strip() if m else None

        design = _parse_mwh(find("DESIGN CAPACITY"))
        full = _parse_mwh(find("FULL CHARGE CAPACITY"))
        cycles_raw = find("CYCLE COUNT")
        cycles = re.sub(r"[^\d]", "", cycles_raw) if cycles_raw else ""

        health = round(full / design * 100, 1) if design and full else None

        return HealthReport(
            design_mwh=design,
            full_mwh=full,
            health_pct=health,
            cycle_count=int(cycles) if cycles else None,
        )
