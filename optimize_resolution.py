from hdmi_optimizer.cli import criar_parser_otimizador, main_otimizador
from hdmi_optimizer.optimization.projection import definir_modo_projecao_apenas_tv
from hdmi_optimizer.optimization.resolution import forcar_resolucao, forcar_resolucao_1080p
from hdmi_optimizer.optimization.service import otimizar_ambiente_para_jogo


def criar_parser():
    return criar_parser_otimizador()


def main(argv=None):
    return main_otimizador(argv)


if __name__ == "__main__":
    raise SystemExit(main())
