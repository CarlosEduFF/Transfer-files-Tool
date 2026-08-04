"""Assistente de voz: ouve comandos pelo microfone e responde falando.

Uso:
    python -m voice_assistant            # ouve pelo microfone
    python -m voice_assistant --texto    # le os comandos do teclado (nao precisa de microfone)
"""

import sys
from datetime import datetime

import requests
import pyttsx3
import speech_recognition as sr

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = 10

motor = pyttsx3.init()


def falar(texto):
    # O console do Windows usa cp1252; nomes de cidade acentuados quebrariam o print.
    codificacao = sys.stdout.encoding or "utf-8"
    print(f"[assistente] {texto}".encode(codificacao, errors="replace").decode(codificacao))
    motor.say(texto)
    motor.runAndWait()


def ouvir(reconhecedor, microfone):
    """Captura uma fala do microfone. Retorna o texto ou None."""
    with microfone as fonte:
        print("\nOuvindo...")
        try:
            audio = reconhecedor.listen(fonte, timeout=5, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            return None

    try:
        return reconhecedor.recognize_google(audio, language="pt-BR")
    except sr.UnknownValueError:
        falar("Nao entendi. Pode repetir?")
    except sr.RequestError:
        falar("Nao consegui acessar o servico de reconhecimento. Verifique sua internet.")
    return None


def buscar_cidade(nome):
    """Converte o nome da cidade em coordenadas. Retorna (nome, lat, lon) ou None."""
    resposta = requests.get(
        GEOCODING_URL,
        params={"name": nome, "count": 1, "language": "pt", "format": "json"},
        timeout=TIMEOUT,
    )
    resposta.raise_for_status()
    resultados = resposta.json().get("results")
    if not resultados:
        return None
    lugar = resultados[0]
    return lugar["name"], lugar["latitude"], lugar["longitude"]


def previsao_do_tempo(cidade):
    """Consulta a temperatura atual da cidade na API Open-Meteo (sem chave)."""
    try:
        lugar = buscar_cidade(cidade)
        if lugar is None:
            return f"Nao encontrei a cidade {cidade}."

        nome, lat, lon = lugar
        resposta = requests.get(
            FORECAST_URL,
            params={"latitude": lat, "longitude": lon, "current": "temperature_2m"},
            timeout=TIMEOUT,
        )
        resposta.raise_for_status()
        atual = resposta.json()["current"]
        return f"Agora em {nome} estao fazendo {atual['temperature_2m']} graus."
    except requests.RequestException:
        return "Nao consegui consultar a previsao do tempo agora."


def extrair_cidade(comando):
    """Pega o que vem depois de 'tempo' / 'tempo em'. Ex.: 'tempo em Recife' -> 'Recife'."""
    _, _, resto = comando.partition("tempo")
    cidade = resto.strip()
    for prefixo in ("em ", "de ", "da ", "do ", "no ", "na "):
        if cidade.startswith(prefixo):
            cidade = cidade[len(prefixo):]
            break
    return cidade.strip()


def processar(comando):
    """Executa o comando. Retorna False quando for para encerrar."""
    comando = comando.lower().strip()

    if "encerrar" in comando or "tchau" in comando:
        falar("Encerrando a assistente. Ate logo!")
        return False

    if "tempo" in comando:
        cidade = extrair_cidade(comando)
        if not cidade:
            falar("Qual cidade?")
            return True
        falar("Consultando a previsao do tempo...")
        falar(previsao_do_tempo(cidade))
        return True

    if "horas" in comando:
        falar(f"Sao {datetime.now():%H horas e %M minutos}.")
        return True

    falar("Nao conheco esse comando. Tente: previsao do tempo, horas, ou encerrar.")
    return True


def menu():
    """Menu de abertura. Retorna True para modo texto, False para voz, None para sair."""
    print("\n=== Assistente virtual ===")
    print("1) Conversar por voz (microfone)")
    print("2) Conversar por texto (teclado)")
    print("3) Ver os comandos disponiveis")
    print("0) Sair")

    while True:
        escolha = input("\nEscolha: ").strip()

        if escolha == "1":
            return False
        if escolha == "2":
            return True
        if escolha == "3":
            print("\nComandos:")
            print("  previsao do tempo <cidade>  - temperatura atual da cidade")
            print("  horas                       - diz a hora atual")
            print("  encerrar / tchau            - encerra a assistente")
            continue
        if escolha == "0":
            return None

        print("Opcao invalida.")


def main():
    # Sem argumentos: menu de abertura. Com --texto/--voz: modo direto.
    if "--texto" in sys.argv:
        modo_texto = True
    elif "--voz" in sys.argv:
        modo_texto = False
    else:
        modo_texto = menu()
        if modo_texto is None:
            return

    falar("Ola, eu sou a assistente virtual. Como posso ajuda-lo hoje?")

    reconhecedor = microfone = None
    if not modo_texto:
        try:
            reconhecedor = sr.Recognizer()
            microfone = sr.Microphone()
            with microfone as fonte:
                print("Ajustando ao ruido do ambiente...")
                reconhecedor.adjust_for_ambient_noise(fonte, duration=1)
        except (OSError, AttributeError) as erro:
            # Sem PyAudio ou sem microfone disponivel: cai para o modo texto.
            print(f"Microfone indisponivel ({erro}). Usando modo texto.")
            modo_texto = True

    while True:
        if modo_texto:
            comando = input("\nDigite seu comando: ")
        else:
            comando = ouvir(reconhecedor, microfone)
            if comando is None:
                continue
            print(f"Voce disse: {comando}")

        if not processar(comando):
            break


if __name__ == "__main__":
    main()
