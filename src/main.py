import os
import sys
import time
import warnings

# 🤫 SILENCIA AVISOS CHATOS (torchcodec, etc)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*torchcodec.*")

from config import get_base_path, configurar_ffmpeg, carregar_hf_token, garantir_pastas

# 🔥 EXECUTA PRIMEIRO
configurar_ffmpeg()

# 👇 Só depois disso vêm os outros imports
from menu import menu_configuracao
from utils import escolher_audio, listar_todos_audios, resolver_device
from core.transcriber import Transcriber
from core.file_manager import salvar_saida


def processar_audio(audio, transcriber, config, device, output_dir, diarizer=None):
    """
    Processa um único áudio: transcreve, diariza (se ativado) e salva.

    Args:
        audio: Caminho do arquivo de áudio
        transcriber: Instância do Transcriber (Whisper)
        config: Dicionário de configuração do menu
        device: Dispositivo (cpu/cuda)
        output_dir: Pasta de saída
        diarizer: Instância do Diarizer (ou None)

    Returns:
        Caminho do arquivo de saída gerado
    """
    nome_arquivo = os.path.basename(audio)
    print(f"\n{'='*60}")
    print(f"🎙️  Processando: {nome_arquivo}")
    print(f"{'='*60}")

    inicio = time.time()

    # Transcrição com Whisper
    resultado = transcriber.transcrever(audio, config["idioma"])

    # Diarização (separação de falantes)
    segmentos_diarizados = None

    if diarizer is not None:
        try:
            diarizacao = diarizer.diarizar(audio)
            segmentos_diarizados = type(diarizer).merge(
                resultado["segments"],
                diarizacao
            )
            print(f"✅ Diarização concluída para: {nome_arquivo}")
        except Exception as e:
            print(f"⚠️  Erro na diarização de {nome_arquivo}: {e}")
            print("   Continuando sem separação de falantes...")

    # Salva resultado
    saida = salvar_saida(
        resultado,
        audio,
        config["formato"],
        output_dir,
        segmentos_diarizados=segmentos_diarizados
    )

    duracao = time.time() - inicio
    print(f"✅ Concluído: {nome_arquivo} ({duracao:.1f}s) → {os.path.basename(saida)}")

    return saida


def preparar_diarizer(config, device):
    """Prepara o Diarizer se diarização foi solicitada."""
    if not config["diarizar"]:
        return None

    hf_token = carregar_hf_token()

    if not hf_token:
        print("\nToken HuggingFace nao encontrado.")
        print("Tentando carregar diarizacao pelo cache local offline...")

    try:
        from core.diarizer import Diarizer
        return Diarizer(hf_token, device)
    except ImportError:
        print("\n⚠️  pyannote.audio não instalado.")
        print("   Instale com: pip install pyannote.audio")
        print("   Continuando sem separação de falantes...\n")
        return None
    except Exception as e:
        print(f"\n⚠️  Erro ao carregar diarização: {e}")
        print("   Continuando sem separação de falantes...\n")
        return None


def modo_unico(input_dir, output_dir, config, device, transcriber, diarizer):
    """Processa um único áudio escolhido pelo usuário."""
    audio = escolher_audio(input_dir)
    if audio is None:
        return

    saida = processar_audio(audio, transcriber, config, device, output_dir, diarizer)
    print(f"\n✅ Arquivo gerado: {saida}")


def modo_fila(input_dir, output_dir, config, device, transcriber, diarizer):
    """Processa todos os áudios da pasta sequencialmente (um por um)."""
    audios = listar_todos_audios(input_dir)
    if not audios:
        return

    total = len(audios)
    print(f"\n📋 Iniciando processamento em FILA de {total} áudio(s)...\n")

    inicio_total = time.time()
    resultados = []

    for i, audio in enumerate(audios, 1):
        print(f"\n[{i}/{total}] ─────────────────────────────────")
        saida = processar_audio(audio, transcriber, config, device, output_dir, diarizer)
        resultados.append(saida)

    duracao_total = time.time() - inicio_total

    print(f"\n{'='*60}")
    print(f"🏁 PROCESSAMENTO EM FILA CONCLUÍDO!")
    print(f"   📊 {total} arquivo(s) processado(s) em {duracao_total:.1f}s")
    print(f"   📁 Saída em: {output_dir}")
    print(f"{'='*60}")
    for saida in resultados:
        print(f"   ✅ {os.path.basename(saida)}")


def modo_paralelo(input_dir, output_dir, config, device, transcriber, diarizer):
    """Processa todos os áudios da pasta simultaneamente (paralelo)."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    audios = listar_todos_audios(input_dir)
    if not audios:
        return

    total = len(audios)

    # Limita workers para não estourar memória
    # GPU: max 2 (VRAM é compartilhada), CPU: max 4
    if device == "cuda":
        max_workers = min(2, total)
        print(f"\n⚠️  Modo paralelo com GPU: limitado a {max_workers} processo(s) simultâneo(s)")
        print("   (para evitar estouro de memória VRAM)")
    else:
        max_workers = min(4, total)

    print(f"\n⚡ Iniciando processamento PARALELO de {total} áudio(s)")
    print(f"   Workers simultâneos: {max_workers}\n")

    inicio_total = time.time()
    resultados = []
    erros = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submete todas as tarefas
        futures = {}
        for audio in audios:
            future = executor.submit(
                processar_audio,
                audio, transcriber, config, device, output_dir, diarizer
            )
            futures[future] = os.path.basename(audio)

        # Coleta resultados conforme completam
        for future in as_completed(futures):
            nome = futures[future]
            try:
                saida = future.result()
                resultados.append(saida)
            except Exception as e:
                print(f"❌ Erro ao processar {nome}: {e}")
                erros.append(nome)

    duracao_total = time.time() - inicio_total

    print(f"\n{'='*60}")
    print(f"🏁 PROCESSAMENTO PARALELO CONCLUÍDO!")
    print(f"   📊 {len(resultados)}/{total} arquivo(s) em {duracao_total:.1f}s")
    print(f"   📁 Saída em: {output_dir}")
    if erros:
        print(f"   ❌ Falhas: {', '.join(erros)}")
    print(f"{'='*60}")
    for saida in resultados:
        print(f"   ✅ {os.path.basename(saida)}")


def main():
    base_path = get_base_path()
    garantir_pastas()

    # 📁 Estrutura padrão
    input_dir = os.path.join(base_path, "data", "input")
    output_dir = os.path.join(base_path, "data", "output")

    # 🔧 Garante que as pastas existem
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # ⚙️ Menu de configuração
    config = menu_configuracao()
    device = resolver_device(config["device"])

    # 🧠 Carrega modelos (uma vez só, reutiliza para todos os áudios)
    transcriber = Transcriber(config["modelo"], device)
    diarizer = preparar_diarizer(config, device)

    # 🚀 Executa o modo escolhido
    modo = config["modo"]

    if modo == "unico":
        modo_unico(input_dir, output_dir, config, device, transcriber, diarizer)
    elif modo == "fila":
        modo_fila(input_dir, output_dir, config, device, transcriber, diarizer)
    elif modo == "paralelo":
        modo_paralelo(input_dir, output_dir, config, device, transcriber, diarizer)


if __name__ == "__main__":
    main()
