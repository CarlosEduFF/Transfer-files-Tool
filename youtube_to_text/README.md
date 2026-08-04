# YouTube to Text

Baixa um video do YouTube e transcreve a fala para texto, em um comando so.

## Quando usar esta ferramenta (e quando usar a AudioTranscriber)

| | YouTube to Text | AudioTranscriber |
|---|---|---|
| Entrada | URL do YouTube ou arquivo local | arquivo local |
| Motor | API do Google (SpeechRecognition) | Whisper (local) |
| Internet | necessaria | so no download do modelo |
| Falantes | nao identifica | identifica (diarizacao) |
| Saida | TXT | TXT, JSON, SRT |

Use esta aqui quando o audio estiver **no YouTube** e voce quiser o texto rapidamente.
Para transcrever arquivos que ja estao no disco, com mais qualidade e identificacao de
falantes, use a **AudioTranscriber**.

## Instalacao

```bash
pip install -r requirements.txt
```

Para baixar do YouTube, instale tambem o [Node.js](https://nodejs.org): o YouTube exige
execucao de JavaScript para liberar as URLs, e sem isso o download falha com HTTP 403.
Transcrever arquivos locais nao precisa disso.

## Uso

```bash
python -m youtube_to_text                        # menu interativo
python -m youtube_to_text <url-do-youtube>
python -m youtube_to_text caminho/do/video.mp4
python -m youtube_to_text <url> --bloco 30       # blocos de 30s em vez de 50s
```

A transcricao e salva em `saida/<nome-do-video>.txt`.

## Como funciona

1. `yt-dlp` baixa o audio do video (ou o arquivo local e usado direto)
2. `moviepy` converte para WAV 16kHz mono — o formato que o `speech_recognition` aceita
3. O audio e transcrito em blocos de ~50s, porque o reconhecedor do Google rejeita
   audios longos demais
4. Os blocos sao juntados e salvos em `.txt`

Trechos sem fala reconhecivel sao pulados com um aviso, sem interromper o resto.
