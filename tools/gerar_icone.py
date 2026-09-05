"""
Gera Icon.ico a partir de Icon.png.

Rode uma vez (ou de novo, se o Icon.png mudar):

    python tools/gerar_icone.py

O .ico é o formato nativo de ícone do Windows e carrega várias resoluções num
arquivo só. Com ele pronto no disco, o app apenas carrega o arquivo — todo o
tratamento abaixo sai do caminho da abertura.

O Icon.png original precisa de dois ajustes, ambos descobertos testando o ícone
na barra de tarefas:

1. O desenho é um quadrado azul de cantos arredondados com uma margem branca em
   volta, e o PNG é opaco. Sem recortar a margem e sem apagar o branco que sobra
   nos cantos, a barra de tarefas mostra um quadrado branco.

2. O branco precisa sair por preenchimento a partir das bordas, não por cor: o
   monitor desenhado no centro também é branco, e removê-lo por cor apagaria
   parte do próprio desenho.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM = RAIZ / "Icon.png"
DESTINO = RAIZ / "Icon.ico"

# Resoluções embutidas no .ico. 16 é a barra de título, 32/48 a barra de tarefas
# (e o Alt+Tab), 256 o modo "ícones grandes" do Explorer.
TAMANHOS = [16, 24, 32, 48, 64, 128, 256]

LIMIAR = 235 # a partir daqui o pixel conta como o branco do fundo


def _area_do_desenho(img: Image.Image) -> tuple[int, int, int, int]:
    """Caixa quadrada em volta do desenho, descartando a margem branca."""
    # getbbox() ignora só o preto, então inverte-se a lógica: um mapa onde o
    # desenho é branco e a margem é preta dá a caixa certa em uma chamada em C.
    cinza = img.convert("L").point(lambda v: 0 if v >= LIMIAR else 255)
    caixa = cinza.getbbox()
    if caixa is None:
        return (0, 0, img.width, img.height)

    esq, topo, dir_, base = caixa
    # Quadrado centrado: um recorte alguns pixels fora do quadrado se propaga na
    # escala e gera pixmaps não-quadrados (15x16), que o Windows rejeita na barra
    # de tarefas.
    lado = min(dir_ - esq, base - topo)
    cx, cy = (esq + dir_) // 2, (topo + base) // 2
    x = max(0, min(cx - lado // 2, img.width - lado))
    y = max(0, min(cy - lado // 2, img.height - lado))
    return (x, y, x + lado, y + lado)


def _apagar_fundo(img: Image.Image) -> Image.Image:
    """
    Torna transparente o branco ligado às bordas, preservando o do centro.

    Usa ImageDraw.floodfill a partir dos quatro cantos: o branco do monitor
    desenhado no meio não encosta na borda, então não é alcançado.
    """
    from PIL import ImageDraw

    img = img.convert("RGBA")
    largura, altura = img.size
    for canto in ((0, 0), (largura - 1, 0), (0, altura - 1), (largura - 1, altura - 1)):
        if img.getpixel(canto)[:3] >= (LIMIAR, LIMIAR, LIMIAR):
            ImageDraw.floodfill(img, canto, (0, 0, 0, 0), thresh=40)
    return img


def main() -> int:
    if not ORIGEM.exists():
        print(f"não encontrei {ORIGEM}")
        return 1

    img = Image.open(ORIGEM)
    print(f"origem: {img.size[0]}x{img.size[1]} modo={img.mode}")

    img = img.crop(_area_do_desenho(img))
    print(f"recorte: {img.size[0]}x{img.size[1]}")

    img = _apagar_fundo(img)

    # LANCZOS: a redução de ~1060 px para 16 px é agressiva, e um filtro simples
    # deixaria o desenho serrilhado nos tamanhos pequenos.
    img.resize((256, 256), Image.LANCZOS).save(
        DESTINO, format="ICO", sizes=[(t, t) for t in TAMANHOS]
    )
    print(f"gerado: {DESTINO} ({DESTINO.stat().st_size / 1024:.0f} KB) "
          f"com {len(TAMANHOS)} resoluções")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
