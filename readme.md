"""
Battery Monitor — monitor de saúde e estado da bateria (Windows).

Funcionalidades:
  - Relatório de desgaste: capacidade de fábrica vs. capacidade atual e % de saúde.
  - Monitor em tempo real: carga (%), status do carregador e tempo restante.
  - Log histórico: grava amostras periódicas em um CSV para acompanhar a degradação.
  - Alerta de bateria baixa: avisa para conectar o carregador abaixo de 20% (na bateria).
  - Gráfico do histórico: visualiza a carga ao longo do tempo a partir do CSV.

Requisitos: Python 3.9+, psutil, matplotlib. (tkinter já vem com o Python no Windows.)
    pip install psutil matplotlib

Como executar (a partir da pasta do projeto):
    python -m battery_monitor

Estrutura (arquitetura em camadas):
    battery_monitor/
      __main__.py            ponto de entrada — injeta as dependências
      config.py              constantes (intervalos, limiares, caminho do log)
      domain/                tipos e regras puras (models, verdict)
      collectors/            coleta do SO (realtime via psutil, saúde via powercfg)
      storage/               persistência do histórico (CSV)
      ui/                    interface Tkinter (app, widgets)

Observação importante:
  Nenhum software "recupera" ou "desvicia" uma bateria de íon-lítio — a degradação
  é química/física (ciclos, calor, idade). Esta ferramenta serve para MONITORAR a
  saúde e ajudar você a decidir hábitos de uso e quando trocar a bateria.
"""
