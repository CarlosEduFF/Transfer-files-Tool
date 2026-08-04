"""Monta um boletim de noticias a partir de um feed RSS e narra em mp3.

Uso:
    python -m news_bulletin                       # 5 noticias do feed padrao (G1)
    python -m news_bulletin --quantidade 3
    python -m news_bulletin --feed https://exemplo.com/rss.xml
    python -m news_bulletin --texto               # so imprime o boletim, sem gerar audio
"""

import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import requests
from gtts import gTTS

FEED_PADRAO = "https://g1.globo.com/rss/g1/"
SAIDA = Path("saida")
TIMEOUT = 10

# Alguns feeds trazem a materia inteira na descricao; um boletim precisa ser resumo.
LIMITE_DESCRICAO = 400

FEEDS = [
    ("G1 - geral", "https://g1.globo.com/rss/g1/"),
    ("G1 - tecnologia", "https://g1.globo.com/rss/g1/tecnologia/"),
    ("G1 - economia", "https://g1.globo.com/rss/g1/economia/"),
    ("BBC Brasil", "https://feeds.bbci.co.uk/portuguese/rss.xml"),
]

ORDINAIS = [
    "Primeira", "Segunda", "Terceira", "Quarta", "Quinta",
    "Sexta", "Setima", "Oitava", "Nona", "Decima",
]


def limpar_html(texto):
    """Remove tags HTML da descricao e normaliza os espacos."""
    sem_tags = re.sub(r"<[^>]+>", " ", texto or "")
    return re.sub(r"\s+", " ", sem_tags).strip()


def imprimir(texto):
    """Imprime sem quebrar em terminais que nao suportam todo o Unicode.

    Feeds RSS costumam trazer emojis, e o console do Windows usa cp1252 por padrao.
    """
    codificacao = sys.stdout.encoding or "utf-8"
    print(texto.encode(codificacao, errors="replace").decode(codificacao))


def buscar_noticias(feed_url, quantidade):
    """Le o feed RSS e retorna uma lista de (titulo, descricao)."""
    resposta = requests.get(
        feed_url,
        timeout=TIMEOUT,
        headers={"User-Agent": "Mozilla/5.0 (boletim-de-noticias)"},
    )
    resposta.raise_for_status()

    raiz = ET.fromstring(resposta.content)
    noticias = []
    for item in raiz.iter("item"):
        titulo = item.findtext("title", "").strip()
        descricao = limpar_html(item.findtext("description", ""))
        if titulo:
            noticias.append((titulo, descricao))
        if len(noticias) >= quantidade:
            break

    return noticias


def resumir(descricao, titulo):
    """Encurta a descricao para o tamanho de um boletim.

    Alguns feeds trazem a materia inteira na descricao, o que geraria um audio de
    varios minutos por noticia. Corta na ultima frase inteira dentro do limite.
    """
    if not descricao:
        return ""

    # Muitos feeds repetem o titulo no inicio da descricao.
    if descricao.startswith(titulo):
        descricao = descricao[len(titulo):].lstrip(" .:-")

    if len(descricao) <= LIMITE_DESCRICAO:
        return descricao

    corte = descricao[:LIMITE_DESCRICAO]
    fim_frase = corte.rfind(". ")
    if fim_frase > LIMITE_DESCRICAO // 3:
        return corte[:fim_frase + 1]
    return corte.rstrip() + "..."


def montar_boletim(noticias):
    """Monta o texto corrido que sera narrado."""
    partes = [f"Boletim de noticias de {datetime.now():%d de %B de %Y}."]

    for indice, (titulo, descricao) in enumerate(noticias):
        ordinal = ORDINAIS[indice] if indice < len(ORDINAIS) else f"Noticia {indice + 1}"
        partes.append(f"{ordinal} noticia: {titulo}.")
        resumo = resumir(descricao, titulo)
        if resumo:
            partes.append(resumo)

    partes.append("Esse foi o boletim. Ate a proxima.")
    return " ".join(partes)


def narrar(texto, destino):
    """Gera o mp3 narrado com gTTS."""
    destino.parent.mkdir(exist_ok=True)
    tts = gTTS(text=texto, lang="pt")
    tts.save(str(destino))
    return destino


def ler_argumento(nome, padrao):
    if nome in sys.argv:
        return sys.argv[sys.argv.index(nome) + 1]
    return padrao


def escolher_feed():
    """Menu de fontes. Retorna a URL do feed ou None se o usuario desistir."""
    print("\nFontes disponiveis:")
    for numero, (nome, _) in enumerate(FEEDS, start=1):
        print(f"{numero}) {nome}")
    print(f"{len(FEEDS) + 1}) Outro feed (informar URL)")

    escolha = input(f"\nEscolha [1]: ").strip() or "1"

    if escolha.isdigit():
        indice = int(escolha) - 1
        if 0 <= indice < len(FEEDS):
            return FEEDS[indice][1]
        if indice == len(FEEDS):
            url = input("URL do feed RSS: ").strip()
            return url or None

    print("Opcao invalida.")
    return None


def perguntar_quantidade():
    resposta = input("Quantas noticias? [5]: ").strip()
    if not resposta:
        return 5
    try:
        return max(1, int(resposta))
    except ValueError:
        print("Valor invalido, usando 5.")
        return 5


def menu():
    """Menu interativo. Retorna (feed, quantidade, so_texto) ou None para sair."""
    print("\n=== Boletim de noticias ===")
    print("1) Gerar boletim narrado (mp3)")
    print("2) Apenas ler o boletim (sem audio)")
    print("0) Sair")

    escolha = input("\nEscolha: ").strip()

    if escolha not in ("1", "2"):
        if escolha != "0":
            print("Opcao invalida.")
        return None

    feed = escolher_feed()
    if feed is None:
        return None

    return feed, perguntar_quantidade(), escolha == "2"


def executar(feed, quantidade, so_texto):
    print(f"\nBuscando noticias em {feed}...")
    try:
        noticias = buscar_noticias(feed, quantidade)
    except requests.RequestException as erro:
        print(f"Nao consegui acessar o feed: {erro}")
        return
    except ET.ParseError:
        print("O feed nao e um XML valido. Confira a URL.")
        return

    if not noticias:
        print("Nenhuma noticia encontrada nesse feed.")
        return

    boletim = montar_boletim(noticias)
    imprimir(f"\n{boletim}\n")

    if so_texto:
        return

    print("Gerando audio...")
    destino = SAIDA / "boletim.mp3"
    try:
        narrar(boletim, destino)
    except Exception as erro:
        # O gTTS divide textos longos em partes e as vezes uma delas falha, mesmo
        # com o mp3 ja gravado. So e erro de verdade se nao sobrou audio utilizavel.
        if destino.exists() and destino.stat().st_size > 1024:
            print(f"Aviso: o fim do boletim pode ter sido cortado ({erro}).")
        else:
            print(f"Nao consegui gerar o audio: {erro}")
            print("Dica: reduza a quantidade de noticias ou use a opcao 2 (so texto).")
            return

    print(f"Boletim narrado salvo em: {destino}")


def main():
    # Sem argumentos: menu interativo. Com argumentos: modo direto.
    if len(sys.argv) < 2:
        escolha = menu()
        if escolha is None:
            return
        executar(*escolha)
        return

    executar(
        ler_argumento("--feed", FEED_PADRAO),
        int(ler_argumento("--quantidade", 5)),
        "--texto" in sys.argv,
    )


if __name__ == "__main__":
    main()
