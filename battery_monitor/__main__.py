"""Ponto de entrada: ``python -m battery_monitor``.

Monta as dependências concretas e injeta na janela. Trocar a fonte de
dados (outro SO, outro armazenamento) é uma mudança local a este arquivo.
"""

from .collectors.health_windows import WindowsHealthCollector
from .collectors.realtime import PsutilRealtimeCollector
from .storage.csv_logger import CsvLogger
from .ui.app import BatteryApp


def main() -> None:
    app = BatteryApp(
        realtime=PsutilRealtimeCollector(),
        health=WindowsHealthCollector(),
        logger=CsvLogger(),
    )
    app.mainloop()


if __name__ == "__main__":
    main()
