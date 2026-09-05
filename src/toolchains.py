"""
Detecção de linguagens/runtimes instalados e dos pacotes de cada gerenciador.

Tudo aqui é LENTO e roda sob demanda, nunca no ciclo do sampler. Medido nesta
máquina: `java -version` 2,9 s, `php --version` 2,4 s, `pip list` 8 s. Colocar
qualquer uma dessas chamadas no ciclo de 1 s travaria a UI — o mesmo problema de
GIL preso que a coleta de processos já causou neste projeto.

Por isso: o módulo não tem estado nem thread; quem chama decide quando (ver
ToolchainWorker em toolchains_worker.py).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# Impede o piscar de janelas de console a cada subprocesso no Windows. Sem isto,
# uma janela preta abre e fecha para cada comando executado.
_SEM_JANELA = 0x08000000

# Comandos que demoram (java, php) justificam um teto generoso; um teto curto
# marcaria como ausente uma linguagem que só é lenta para responder.
# Medido nesta máquina: java -version 2,9 s, php --version 2,4 s.
TIMEOUT_VERSAO = 15
# `npm list -g` levou 31 s aqui — daí a folga. Um teto apertado devolveria uma
# lista vazia, que na tela é indistinguível de "nada instalado".
TIMEOUT_PACOTES = 120


@dataclass(frozen=True)
class Pacote:
    """Um pacote/biblioteca instalado."""
    nome: str
    versao: str
    gerenciador: str  # "pip", "npm", ... — define o comando de desinstalação


@dataclass
class Toolchain:
    """
    Uma linguagem/runtime encontrado na máquina.

    Não é frozen porque os pacotes chegam depois da detecção inicial: listar é
    caro, então só acontece quando o usuário abre aquela linguagem.
    """
    nome: str            # "Python", "Node.js", ...
    comando: str         # executável encontrado no PATH
    caminho: str         # onde ele está
    versao: str          # já limpa, ex.: "3.12.6"
    gerenciador: str = ""    # gerenciador de pacotes associado, se houver
    no_path: bool = True     # False = achado só por caminho conhecido
    pacotes: list[Pacote] = field(default_factory=list)
    pacotes_carregados: bool = False


def _pastas_extras() -> list[Path]:
    """
    Pastas onde SDKs costumam se instalar sem entrar no PATH.

    O Android SDK e o Kotlin do Android Studio são o caso típico: ficam
    instalados e funcionais, mas invisíveis a `shutil.which`. Sem procurar aqui, a
    aba diria "não instalado" para algo que está na máquina — pior que não
    mostrar, porque é uma informação errada.
    """
    pastas: list[Path] = []

    sdk = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    candidatos_sdk = [Path(sdk)] if sdk else []
    local = os.environ.get("LOCALAPPDATA")
    if local:
        candidatos_sdk.append(Path(local) / "Android" / "Sdk")
    candidatos_sdk.append(Path("C:/Android/Sdk"))

    for base in candidatos_sdk:
        if not base.exists():
            continue
        pastas += [
            base / "platform-tools",              # adb
            base / "emulator",                    # emulator
            base / "cmdline-tools" / "latest" / "bin",  # sdkmanager, avdmanager
        ]
        break # o primeiro SDK válido basta; os candidatos apontam para o mesmo lugar

    # Kotlin e o JDK embutido vêm dentro do Android Studio.
    estudios = [Path("C:/Program Files/Android/Android Studio")]
    if local:
        estudios.append(Path(local) / "Programs" / "Android Studio")
    for base in estudios:
        if base.exists():
            pastas += [
                base / "plugins" / "Kotlin" / "kotlinc" / "bin",
                base / "jbr" / "bin",
            ]
            break

    return [p for p in pastas if p.exists()]


def _localizar(comando: str) -> str | None:
    """
    Caminho do executável: primeiro no PATH, depois nas pastas conhecidas.

    Devolve None se não encontrar em lugar nenhum.
    """
    achado = shutil.which(comando)
    if achado:
        return achado
    for pasta in _pastas_extras():
        for sufixo in (".exe", ".bat", ".cmd", ""):
            candidato = pasta / f"{comando}{sufixo}"
            if candidato.is_file():
                return str(candidato)
    return None


def _executar(cmd: list[str], timeout: int) -> str:
    """
    Roda um comando e devolve a saída, ou "" se falhar.

    Resolve o executável pelo PATH antes de chamar. No Windows, várias ferramentas
    do ecossistema JS são arquivos .CMD (npm, npx, yarn) e o CreateProcess não os
    executa a partir do nome: `subprocess.run(["npm", ...])` levanta
    FileNotFoundError. Era por isso que a lista de pacotes do npm vinha vazia —
    parecia "nenhum pacote instalado", mas o comando nem chegava a rodar.

    Um .CMD ainda precisa do cmd.exe para interpretá-lo, então ele entra via
    `cmd /c` com o caminho completo — sem shell=True, que exigiria montar a linha
    de comando como texto e escapar argumentos à mão.
    """
    caminho = _localizar(cmd[0])
    if not caminho:
        return ""

    if caminho.lower().endswith((".cmd", ".bat")):
        argv = ["cmd", "/c", caminho, *cmd[1:]]
    else:
        argv = [caminho, *cmd[1:]]

    try:
        r = subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout,
            creationflags=_SEM_JANELA, encoding="utf-8", errors="replace",
        )
        # Várias ferramentas (java, entre elas) escrevem a versão em stderr.
        return (r.stdout or "") + (r.stderr or "")
    except (subprocess.TimeoutExpired, OSError, ValueError):
        return ""


def _versao(texto: str) -> str | None:
    """
    Extrai o número de versão da saída, ou None se não houver um.

    None significa "o comando existe mas não reportou versão" — acontece com um
    runtime instalado pela metade (o .NET desta máquina responde com uma mensagem
    de erro). Sem esta checagem, a mensagem de erro inteira ia parar na coluna de
    versão da tabela.
    """
    m = re.search(r"\d+\.\d+(?:\.\d+)?(?:[-+.\w]*)?", texto)
    return m.group(0) if m else None


# Cada entrada: (nome exibido, executável, argumentos de versão, gerenciador).
# A ordem define a ordem na tela.
CATALOGO = [
    ("Python",      "python",  ["--version"],      "pip"),
    ("Node.js",     "node",    ["--version"],      "npm"),
    ("Java",        "java",    ["-version"],       ""),
    (".NET",        "dotnet",  ["--version"],      ""),
    ("Go",          "go",      ["version"],        ""),
    ("Rust",        "rustc",   ["--version"],      "cargo"),
    ("Flutter",     "flutter", ["--version"],      ""),
    ("Dart",        "dart",    ["--version"],      "pub"),
    # Ferramentas Android. Costumam ficar FORA do PATH — são localizadas via
    # ANDROID_HOME e pela instalação do Android Studio (ver _pastas_extras).
    ("Android SDK (adb)", "adb",        ["version"],     ""),
    ("Android Emulator",  "emulator",   ["-version"],    ""),
    ("Kotlin",            "kotlinc",    ["-version"],    ""),
    ("Android cmdline-tools", "sdkmanager", ["--version"], ""),
    ("Gradle",            "gradle",     ["--version"],   ""),
    ("Maven",             "mvn",        ["--version"],   ""),
    ("PHP",         "php",     ["--version"],      "composer"),
    ("Ruby",        "ruby",    ["--version"],      "gem"),
    ("Perl",        "perl",    ["--version"],      ""),
    ("Deno",        "deno",    ["--version"],      ""),
    ("Bun",         "bun",     ["--version"],      ""),
    ("Git",         "git",     ["--version"],      ""),
    ("GCC",         "gcc",     ["--version"],      ""),
]


def detectar(progresso=None, encontrado=None) -> list[Toolchain]:
    """
    Varre o PATH atrás das linguagens do catálogo e lê a versão de cada uma.

    `progresso` recebe (nome, indice, total) a cada item verificado.
    `encontrado` recebe cada Toolchain assim que ele é identificado, para a UI
    preencher a lista aos poucos em vez de ficar vazia até o fim: a varredura
    inteira leva ~6 s nesta máquina, e o `flutter --version` sozinho responde por
    ~5 s dela (java 2,9 s, php 2,4 s).

    Os comandos são consultados na ordem do catálogo, e os mais rápidos e comuns
    (python, node) vêm primeiro justamente para aparecerem logo.
    """
    achados: list[Toolchain] = []
    for i, (nome, comando, args, gerenciador) in enumerate(CATALOGO):
        if progresso:
            progresso(nome, i, len(CATALOGO))
        caminho = _localizar(comando)
        if not caminho:
            continue
        versao = _versao(_executar([comando, *args], TIMEOUT_VERSAO))
        if versao is None:
            # No PATH, mas não respondeu com uma versão: instalação incompleta ou
            # comando quebrado. Listar como se estivesse instalado seria enganoso.
            continue
        # O gerenciador só entra se ele próprio estiver disponível: ter Ruby não
        # garante ter gem no PATH. "pub" é a exceção — não é um executável, e sim
        # subcomando do dart, então acompanha a própria linguagem.
        if gerenciador == "pub":
            gm = "pub"
        else:
            gm = gerenciador if gerenciador and _localizar(gerenciador) else ""
        tc = Toolchain(
            nome=nome, comando=comando, caminho=caminho,
            versao=versao, gerenciador=gm,
            no_path=shutil.which(comando) is not None,
        )
        achados.append(tc)
        if encontrado:
            encontrado(tc)
    return achados


def listar_pacotes(gerenciador: str) -> list[Pacote]:
    """
    Pacotes instalados de um gerenciador. Custa segundos — chame fora da UI.
    """
    if gerenciador == "pip":
        saida = _executar(["pip", "list", "--format=json"], TIMEOUT_PACOTES)
        try:
            return sorted(
                (Pacote(p["name"], p["version"], "pip") for p in json.loads(saida)),
                key=lambda p: p.nome.lower(),
            )
        except (json.JSONDecodeError, KeyError, TypeError):
            return []

    if gerenciador == "npm":
        saida = _executar(
            ["npm", "list", "-g", "--depth=0", "--json"], TIMEOUT_PACOTES
        )
        try:
            deps = json.loads(saida).get("dependencies", {})
            return sorted(
                (Pacote(n, d.get("version", "?"), "npm") for n, d in deps.items()),
                key=lambda p: p.nome.lower(),
            )
        except (json.JSONDecodeError, AttributeError, TypeError):
            return []

    if gerenciador == "gem":
        saida = _executar(["gem", "list", "--local"], TIMEOUT_PACOTES)
        pacotes = []
        for linha in saida.splitlines():
            m = re.match(r"^(\S+)\s+\(([^)]+)\)", linha.strip())
            if m:
                pacotes.append(Pacote(m.group(1), m.group(2).split(",")[0].strip(), "gem"))
        return sorted(pacotes, key=lambda p: p.nome.lower())

    if gerenciador == "cargo":
        saida = _executar(["cargo", "install", "--list"], TIMEOUT_PACOTES)
        pacotes = []
        for linha in saida.splitlines():
            # Linhas de pacote não são indentadas; as dos binários são.
            m = re.match(r"^(\S+)\s+v([^\s:]+)", linha)
            if m:
                pacotes.append(Pacote(m.group(1), m.group(2), "cargo"))
        return sorted(pacotes, key=lambda p: p.nome.lower())

    if gerenciador == "pub":
        # "dart pub", não "pub": o executável pub isolado saiu do SDK há tempos.
        saida = _executar(["dart", "pub", "global", "list"], TIMEOUT_PACOTES)
        pacotes = []
        for linha in saida.splitlines():
            # Formato: "nome 1.2.3" ou "nome 1.2.3 at path ..."
            m = re.match(r"^(\S+)\s+(\d[^\s]*)", linha.strip())
            if m:
                pacotes.append(Pacote(m.group(1), m.group(2), "pub"))
        return sorted(pacotes, key=lambda p: p.nome.lower())

    if gerenciador == "composer":
        saida = _executar(
            ["composer", "global", "show", "--format=json"], TIMEOUT_PACOTES
        )
        try:
            itens = json.loads(saida).get("installed", [])
            return sorted(
                (Pacote(p["name"], p.get("version", "?"), "composer") for p in itens),
                key=lambda p: p.nome.lower(),
            )
        except (json.JSONDecodeError, KeyError, TypeError):
            return []

    return []


def comando_desinstalar(pacote: Pacote) -> list[str] | None:
    """
    Comando de desinstalação do pacote, ou None se o gerenciador não for suportado.

    Devolver o comando em vez de executá-lo é proposital: a UI mostra exatamente o
    que vai rodar antes de pedir confirmação. Desinstalar é destrutivo e nem sempre
    trivial de desfazer — diferente de encerrar um processo, que basta reabrir.
    """
    return {
        "pip": ["pip", "uninstall", "-y", pacote.nome],
        "npm": ["npm", "uninstall", "-g", pacote.nome],
        "gem": ["gem", "uninstall", "-x", "-I", pacote.nome],
        "cargo": ["cargo", "uninstall", pacote.nome],
        "pub": ["dart", "pub", "global", "deactivate", pacote.nome],
        "composer": ["composer", "global", "remove", pacote.nome],
    }.get(pacote.gerenciador)


def desinstalar(pacote: Pacote) -> tuple[bool, str]:
    """Executa a desinstalação. Devolve (deu certo, saída do comando)."""
    cmd = comando_desinstalar(pacote)
    if not cmd:
        return False, f"Desinstalação não suportada para '{pacote.gerenciador}'."
    saida = _executar(cmd, TIMEOUT_PACOTES)
    if not saida.strip():
        return False, "O comando não respondeu (tempo esgotado ou falha ao iniciar)."
    # Heurística deliberadamente conservadora: na dúvida, a UI relista os pacotes
    # e o usuário vê o estado real.
    erro = re.search(r"\b(error|não foi possível|cannot|failed|ERROR)\b", saida, re.I)
    return (not erro), saida.strip()
