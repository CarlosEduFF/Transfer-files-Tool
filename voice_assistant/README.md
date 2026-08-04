# Assistente de voz

Assistente de linha de comando que ouve comandos pelo microfone e responde falando.

## Instalacao

```bash
pip install -r requirements.txt
```

Se o `pip install pyaudio` falhar no Windows, o assistente ainda funciona no modo texto
(`--texto`) — o PyAudio so e necessario para o microfone.

## Uso

```bash
python -m voice_assistant            # menu interativo (escolhe voz ou texto)
python -m voice_assistant --voz      # direto no modo voz
python -m voice_assistant --texto    # direto no modo texto
```

Se nao houver microfone disponivel, o programa avisa e cai automaticamente para o modo texto.

## Comandos

| Comando                    | O que faz                                      |
|----------------------------|------------------------------------------------|
| `previsao do tempo Recife` | Temperatura atual da cidade (API Open-Meteo)   |
| `horas`                    | Diz a hora atual                               |
| `encerrar` / `tchau`       | Encerra a assistente                           |

A consulta de clima usa a [Open-Meteo](https://open-meteo.com), que e gratuita e nao exige
chave de API.
