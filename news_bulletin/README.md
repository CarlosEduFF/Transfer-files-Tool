# Boletim de noticias narrado

Busca noticias de um feed RSS, monta um boletim e gera um mp3 narrado — um mini podcast
automatico.

## Instalacao

```bash
pip install -r requirements.txt
```

## Uso

```bash
python -m news_bulletin                              # menu interativo
python -m news_bulletin --quantidade 3               # 3 noticias do G1
python -m news_bulletin --feed https://exemplo.com/rss.xml
python -m news_bulletin --texto                      # so imprime, sem gerar audio
```

O audio e salvo em `saida/boletim.mp3`.

O menu permite escolher a fonte entre os feeds ja cadastrados ou informar outra URL.

Descricoes muito longas sao resumidas (corte na ultima frase inteira, ate ~400
caracteres): alguns feeds trazem a materia completa, o que geraria um audio de varios
minutos por noticia.

## Alguns feeds RSS

| Fonte          | URL                                                |
|----------------|----------------------------------------------------|
| G1             | `https://g1.globo.com/rss/g1/`                     |
| G1 Tecnologia  | `https://g1.globo.com/rss/g1/tecnologia/`          |
| BBC Brasil     | `https://feeds.bbci.co.uk/portuguese/rss.xml`      |

O parse do XML usa a `xml.etree.ElementTree` da biblioteca padrao — sem dependencia extra.
O `gTTS` precisa de internet para gerar o audio.
