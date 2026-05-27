from hdmi_optimizer.config import (
    ALTURA_OTIMIZADA,
    FREQUENCIA_OTIMIZADA,
    LARGURA_OTIMIZADA,
)
from hdmi_optimizer.optimization.projection import definir_modo_projecao_apenas_tv
from hdmi_optimizer.optimization.resolution import (
    forcar_resolucao,
    forcar_resolucao_1080p,
)


class OptimizationService:
    def optimize_for_game(
        self,
        largura=LARGURA_OTIMIZADA,
        altura=ALTURA_OTIMIZADA,
        frequencia=FREQUENCIA_OTIMIZADA,
    ):
        try:
            definir_modo_projecao_apenas_tv()
            sucesso = forcar_resolucao(largura, altura, frequencia)

            if sucesso:
                print("\n[PRONTO] Ambiente otimizado. Voce ja pode iniciar o jogo.")

            return sucesso
        except Exception as exc:
            print(f"[ERRO] Ocorreu uma falha ao executar o algoritmo: {exc}")
            return False


def otimizar_ambiente_para_jogo(
    largura=LARGURA_OTIMIZADA,
    altura=ALTURA_OTIMIZADA,
    frequencia=FREQUENCIA_OTIMIZADA,
):
    return OptimizationService().optimize_for_game(largura, altura, frequencia)
