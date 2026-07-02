"""Constantes de configuração reunidas num só lugar."""

from pathlib import Path

# Caminho do CSV histórico — fica ao lado do pacote, no diretório do projeto.
LOG_PATH = Path(__file__).resolve().parent.parent / "battery_log.csv"

# Janela em tempo real
REFRESH_MS = 5000          # intervalo de atualização do monitor ao vivo
LOG_EVERY_REFRESHES = 12   # grava no CSV a cada N atualizações (~1 min)

# Alertas de carga
LOW_BATTERY_PCT = 20       # avisa para conectar abaixo deste valor (na bateria)

# Limiares de saúde (%) -> (rótulo, cor)
HEALTH_THRESHOLDS = (
    (80, "ótima", "#2e7d32"),
    (60, "boa", "#558b2f"),
    (40, "desgastada", "#ef6c00"),
)
HEALTH_WORST = ("muito desgastada — considere trocar", "#c62828")
HEALTH_UNKNOWN = ("desconhecida", "gray")
