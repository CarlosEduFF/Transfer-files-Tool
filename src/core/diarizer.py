"""
Speaker Diarization - Identificacao de falantes
===============================================
Usa o pyannote.audio para identificar quem fala em cada trecho do audio
e cruza essa informacao com os segmentos do Whisper.

Dependencias:
    pip install pyannote.audio
"""

import os
import shutil
from pathlib import Path


class Diarizer:
    MODEL_ID = "pyannote/speaker-diarization-3.1"
    SEGMENTATION_ID = "pyannote/segmentation-3.0"
    EMBEDDING_ID = "pyannote/wespeaker-voxceleb-resnet34-LM"
    COMMUNITY_ID = "pyannote/speaker-diarization-community-1"

    def __init__(self, hf_token: str | None = None, device: str = "cpu"):
        """
        Inicializa o pipeline de diarizacao.

        Args:
            hf_token: Token de acesso do HuggingFace
            device: "cpu" ou "cuda"
        """
        try:
            from pyannote.audio import Pipeline
        except ImportError:
            print("Biblioteca 'pyannote.audio' nao encontrada.")
            print("   Instale com: pip install pyannote.audio")
            raise

        print("Carregando modelo de diarizacao...")
        self.pipeline = self._carregar_pipeline(Pipeline, hf_token)

        if device == "cuda":
            import torch

            self.pipeline.to(torch.device("cuda"))

        print("Modelo de diarizacao carregado!")

    @classmethod
    def _carregar_pipeline(cls, Pipeline, hf_token: str | None):
        """
        Tenta carregar primeiro do cache local, sem internet.

        Se ainda nao estiver baixado, tenta baixar do Hugging Face usando o
        token. Depois do primeiro download, a tentativa offline deve funcionar.
        """
        try:
            return cls._carregar_pipeline_do_cache(Pipeline)
        except Exception as erro_cache:
            print(f"Cache local offline incompleto: {erro_cache}")
            if not hf_token:
                raise RuntimeError(
                    "Para baixar o modelo pela primeira vez, conecte a internet "
                    "e configure o token Hugging Face. Depois disso, ele podera "
                    "rodar offline pelo cache local."
                ) from erro_cache

        print("Tentando baixar/atualizar modelo pelo Hugging Face...")
        pipeline = Pipeline.from_pretrained(
            cls.MODEL_ID,
            token=hf_token,
            cache_dir=cls._hub_cache_dir(),
        )
        if pipeline is None:
            raise RuntimeError(
                "Nao foi possivel carregar o modelo. Verifique se voce aceitou "
                "os termos no Hugging Face e se o token tem permissao de leitura."
            )
        return pipeline

    @classmethod
    def _carregar_pipeline_do_cache(cls, Pipeline):
        import yaml

        cls._copiar_cache_huggingface_existente()

        config_path = cls._arquivo_no_cache(cls.MODEL_ID, "config.yaml")
        segmentation_path = cls._arquivo_no_cache(cls.SEGMENTATION_ID, "pytorch_model.bin")
        embedding_path = cls._arquivo_no_cache(cls.EMBEDDING_ID, "pytorch_model.bin")
        community_path = cls._snapshot_dir(cls.COMMUNITY_ID)
        cls._arquivo_no_cache(cls.COMMUNITY_ID, "plda/xvec_transform.npz")
        cls._arquivo_no_cache(cls.COMMUNITY_ID, "plda/plda.npz")

        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        params = config["pipeline"]["params"]
        params["segmentation"] = str(segmentation_path)
        params["embedding"] = str(embedding_path)
        params["plda"] = {
            "checkpoint": str(community_path),
            "subfolder": "plda",
        }

        env_anterior = os.environ.get("HF_HUB_OFFLINE")
        try:
            os.environ["HF_HUB_OFFLINE"] = "1"
            pipeline = Pipeline.from_pretrained(config)
            if pipeline is None:
                raise RuntimeError("Pipeline nao foi carregado do cache local.")
            print("Modelo carregado do cache local.")
            return pipeline
        finally:
            if env_anterior is None:
                os.environ.pop("HF_HUB_OFFLINE", None)
            else:
                os.environ["HF_HUB_OFFLINE"] = env_anterior

    @staticmethod
    def _hub_cache_dir() -> Path:
        hf_hub_cache = os.environ.get("HF_HUB_CACHE")
        if hf_hub_cache:
            return Path(hf_hub_cache)

        base_path = Path(__file__).resolve().parents[1]
        return base_path / "data" / "models" / "huggingface" / "hub"

    @staticmethod
    def _cache_padrao_huggingface() -> Path:
        hf_home = os.environ.get("HF_HOME")
        if hf_home:
            return Path(hf_home) / "hub"

        return Path.home() / ".cache" / "huggingface" / "hub"

    @classmethod
    def _copiar_cache_huggingface_existente(cls) -> None:
        destino_base = cls._hub_cache_dir()
        origem_base = cls._cache_padrao_huggingface()

        if destino_base == origem_base or not origem_base.is_dir():
            return

        for model_id in (
            cls.MODEL_ID,
            cls.SEGMENTATION_ID,
            cls.EMBEDDING_ID,
            cls.COMMUNITY_ID,
        ):
            repo = f"models--{model_id.replace('/', '--')}"
            origem = origem_base / repo
            destino = destino_base / repo

            if origem.is_dir() and not destino.exists():
                print(f"Copiando modelo Hugging Face para data/models: {model_id}")
                destino.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(origem, destino)

    @classmethod
    def _snapshot_dir(cls, model_id: str) -> Path:
        repo_dir = cls._hub_cache_dir() / f"models--{model_id.replace('/', '--')}"
        snapshots_dir = repo_dir / "snapshots"

        ref_path = repo_dir / "refs" / "main"
        if ref_path.is_file():
            commit = ref_path.read_text(encoding="utf-8").strip()
            snapshot = snapshots_dir / commit
            if snapshot.is_dir():
                return snapshot

        snapshots = [p for p in snapshots_dir.glob("*") if p.is_dir()]
        if snapshots:
            return max(snapshots, key=lambda p: p.stat().st_mtime)

        raise FileNotFoundError(f"snapshot nao encontrado para {model_id}")

    @classmethod
    def _arquivo_no_cache(cls, model_id: str, filename: str) -> Path:
        path = cls._snapshot_dir(model_id) / filename
        if not path.is_file():
            raise FileNotFoundError(f"{filename} nao encontrado no cache de {model_id}")
        return path

    @staticmethod
    def _extrair_annotation(diarizacao):
        """
        Normaliza diferentes retornos do pyannote para um Annotation.

        Versoes novas podem retornar DiarizeOutput, que guarda o Annotation
        em speaker_diarization/exclusive_speaker_diarization.
        """
        if hasattr(diarizacao, "itertracks"):
            return diarizacao

        for atributo in (
            "exclusive_speaker_diarization",
            "speaker_diarization",
            "annotation",
        ):
            annotation = getattr(diarizacao, atributo, None)
            if annotation is not None and hasattr(annotation, "itertracks"):
                return annotation

        return None

    def diarizar(self, caminho_audio: str):
        """
        Executa a diarizacao no audio.

        Args:
            caminho_audio: Caminho para o arquivo de audio

        Returns:
            Annotation do pyannote com os intervalos de cada falante.
        """
        print("Identificando falantes no audio...")

        # Em vez de passar o caminho do arquivo, carregamos o audio na memoria
        # usando o Whisper e passamos o tensor para o pyannote.
        import torch
        import whisper

        try:
            # Whisper carrega sempre em 16000Hz, mono (1D numpy array).
            audio_array = whisper.load_audio(caminho_audio)

            # pyannote espera formato (channel, time) -> (1, N).
            waveform = torch.from_numpy(audio_array).unsqueeze(0)
            audio_in_memory = {"waveform": waveform, "sample_rate": 16000}

            diarizacao = self.pipeline(audio_in_memory)
        except Exception as e:
            print(f"Erro ao decodificar audio para diarizacao: {e}")
            raise

        annotation = self._extrair_annotation(diarizacao)
        if annotation is None:
            print(f"Formato de saida da diarizacao desconhecido: {type(diarizacao)}")
            return None

        falantes = set()
        for _, _, falante in annotation.itertracks(yield_label=True):
            falantes.add(falante)

        print(f"{len(falantes)} falante(s) identificado(s)")
        return annotation

    @staticmethod
    def merge(segments: list, diarizacao) -> list:
        """
        Cruza os segmentos do Whisper com a diarizacao do pyannote.

        Para cada segmento do Whisper, identifica qual falante estava falando
        naquele momento, baseado na maior sobreposicao de tempo.

        Args:
            segments: Lista de segmentos do Whisper (com 'start', 'end', 'text')
            diarizacao: Resultado do pyannote

        Returns:
            Lista de segmentos enriquecidos com campo 'speaker'
        """
        diarizacao = Diarizer._extrair_annotation(diarizacao)

        if diarizacao is None:
            print("Formato de saida desconhecido: diarizacao ignorada")
            return []

        intervalos_falantes = []
        for turn, _, speaker in diarizacao.itertracks(yield_label=True):
            intervalos_falantes.append(
                {
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": speaker,
                }
            )

        speakers_unicos = []
        for intervalo in intervalos_falantes:
            if intervalo["speaker"] not in speakers_unicos:
                speakers_unicos.append(intervalo["speaker"])

        mapa_nomes = {}
        for i, speaker in enumerate(speakers_unicos, 1):
            mapa_nomes[speaker] = f"Falante {i}"

        segmentos_enriquecidos = []
        for seg in segments:
            seg_start = seg["start"]
            seg_end = seg["end"]

            melhor_falante = "Desconhecido"
            maior_sobreposicao = 0.0

            for intervalo in intervalos_falantes:
                inicio_overlap = max(seg_start, intervalo["start"])
                fim_overlap = min(seg_end, intervalo["end"])
                sobreposicao = max(0, fim_overlap - inicio_overlap)

                if sobreposicao > maior_sobreposicao:
                    maior_sobreposicao = sobreposicao
                    melhor_falante = mapa_nomes[intervalo["speaker"]]

            segmentos_enriquecidos.append(
                {
                    "start": seg_start,
                    "end": seg_end,
                    "text": seg["text"],
                    "speaker": melhor_falante,
                }
            )

        return segmentos_enriquecidos
