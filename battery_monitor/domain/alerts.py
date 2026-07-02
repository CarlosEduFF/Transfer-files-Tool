"""Regra pura para decidir quando avisar sobre a carga.

Mantém estado mínimo (se já avisou) para não repetir o alerta a cada
atualização. Sem I/O nem dependência de UI — totalmente testável.
"""

from dataclasses import dataclass
from typing import Optional

from ..config import LOW_BATTERY_PCT
from .models import BatteryStatus


@dataclass
class LowBatteryAlert:
    """Dispara uma vez quando a carga cruza o limite para baixo na bateria.

    Rearma quando a carga volta a subir acima do limite ou o cabo é
    conectado, evitando popups repetidos enquanto a carga oscila perto
    do limite.
    """

    threshold: int = LOW_BATTERY_PCT
    _fired: bool = False

    def check(self, status: BatteryStatus) -> Optional[str]:
        """Retorna a mensagem de alerta a exibir, ou None se nada a fazer."""
        if not status.present or status.plugged:
            self._fired = False          # na tomada: rearma
            return None

        if status.percent > self.threshold:
            self._fired = False          # acima do limite: rearma
            return None

        if self._fired:
            return None                  # já avisou nesta queda

        self._fired = True
        return (
            f"Bateria em {status.percent:.0f}% — conecte o carregador."
        )
