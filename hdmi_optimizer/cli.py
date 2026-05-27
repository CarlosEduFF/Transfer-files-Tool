import argparse

from hdmi_optimizer.config import (
    ALTURA_OTIMIZADA,
    FREQUENCIA_OTIMIZADA,
    INTERVALO_PADRAO,
    LARGURA_OTIMIZADA,
    LIMITE_RAM_PADRAO,
    LIMITE_VRAM_PADRAO,
    LOG_PADRAO,
)
from hdmi_optimizer.monitoring.service import monitorar_nvidia
from hdmi_optimizer.optimization.service import otimizar_ambiente_para_jogo


def criar_parser_monitor():
    parser = argparse.ArgumentParser(
        description="Monitora GPU/RAM/resolucao e pode acionar a otimizacao HDMI."
    )
    parser.add_argument("--log-file", default=LOG_PADRAO)
    parser.add_argument("--intervalo", type=float, default=INTERVALO_PADRAO)
    parser.add_argument(
        "--auto-otimizar",
        action="store_true",
        help="Chama a otimizacao ao detectar 4K + VRAM/RAM criticas.",
    )
    parser.add_argument("--limite-vram", type=float, default=LIMITE_VRAM_PADRAO)
    parser.add_argument("--limite-ram", type=float, default=LIMITE_RAM_PADRAO)
    return parser


def criar_parser_otimizador():
    parser = argparse.ArgumentParser(
        description="Otimiza a saida HDMI para reduzir gargalo de VRAM/RAM."
    )
    parser.add_argument("--largura", type=int, default=LARGURA_OTIMIZADA)
    parser.add_argument("--altura", type=int, default=ALTURA_OTIMIZADA)
    parser.add_argument("--frequencia", type=int, default=FREQUENCIA_OTIMIZADA)
    return parser


def main_monitor(argv=None):
    args = criar_parser_monitor().parse_args(argv)

    try:
        monitorar_nvidia(
            log_file=args.log_file,
            intervalo=args.intervalo,
            auto_otimizar=args.auto_otimizar,
            limite_vram=args.limite_vram,
            limite_ram=args.limite_ram,
        )
    except KeyboardInterrupt:
        print(f"\nMonitoramento encerrado. Analise o arquivo '{args.log_file}'.")

    return 0


def main_otimizador(argv=None):
    args = criar_parser_otimizador().parse_args(argv)
    sucesso = otimizar_ambiente_para_jogo(args.largura, args.altura, args.frequencia)
    return 0 if sucesso else 1
