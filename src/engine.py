import os
import time
import threading
import numpy as np
import pygame
from midiutil import MIDIFile

# Mapeamento de nomes de notas para deslocamento de tom (semitons a partir de C)
NOTE_OFFSETS = {
    "C": 0, "C#": 1, "Db": 1,
    "D": 2, "D#": 3, "Eb": 3,
    "E": 4,
    "F": 5, "F#": 6, "Gb": 6,
    "G": 7, "G#": 8, "Ab": 8,
    "A": 9, "A#": 10, "Bb": 10,
    "B": 11,
}

def note_to_midi(note_str: str) -> int:
    """Converte nome de nota como 'C4', 'F#4', 'Bb5' para número MIDI. C4 = 60."""
    note_str = note_str.strip().upper()
    if not note_str:
        return 60
    
    octave_str = ""
    while note_str and (note_str[-1].isdigit() or note_str[-1] == '-'):
        octave_str = note_str[-1] + octave_str
        note_str = note_str[:-1]
    
    octave = int(octave_str) if octave_str else 4
    name = note_str.capitalize()
    
    offset = NOTE_OFFSETS.get(name, 0)
    return 12 * (octave + 1) + offset

def midi_to_freq(midi_num: int) -> float:
    """Converte número MIDI em frequência Hz."""
    return 440.0 * (2.0 ** ((midi_num - 69) / 12.0))

class AudioEngine:
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.current_sound = None
        self.current_channel = None
        self.playback_thread = None
        self.is_playing = False
        self.loop = False
        try:
            pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=1, buffer=1024)
        except Exception:
            pass

    def generate_wave(self, freq: float, dur_sec: float, wave_type: str = "Piano Acústico (Realista)") -> np.ndarray:
        """Gera instrumentos com harmônicos e decaimento realista (Piano, Violão, Flauta, Órgão, 8-Bit)."""
        num_samples = int(self.sample_rate * dur_sec)
        if num_samples <= 0:
            return np.array([], dtype=np.float32)

        t = np.linspace(0, dur_sec, num_samples, False)

        if "Piano" in wave_type:
            # Síntese Aditiva de Piano Acústico com decaimento exponencial de corda martelada
            # Harmônicos: f, 2f, 3f, 4f, 5f
            h1 = np.sin(freq * t * 2 * np.pi) * np.exp(-2.5 * t / dur_sec)
            h2 = 0.5 * np.sin(2 * freq * t * 2 * np.pi) * np.exp(-4.5 * t / dur_sec)
            h3 = 0.25 * np.sin(3 * freq * t * 2 * np.pi) * np.exp(-7.0 * t / dur_sec)
            h4 = 0.12 * np.sin(4 * freq * t * 2 * np.pi) * np.exp(-10.0 * t / dur_sec)
            h5 = 0.06 * np.sin(5 * freq * t * 2 * np.pi) * np.exp(-14.0 * t / dur_sec)
            
            wave = (h1 + h2 + h3 + h4 + h5) * 0.6
            
            # Envelope de martelo (ataque super rápido + release natural)
            env = np.ones(num_samples, dtype=np.float32)
            attack = min(int(self.sample_rate * 0.005), num_samples // 4)
            if attack > 0:
                env[:attack] = np.linspace(0, 1, attack)
            return wave * env

        elif "Violão" in wave_type or "Guit" in wave_type:
            # Síntese de Violão de Náilon / Corda dedilhada
            h1 = np.sin(freq * t * 2 * np.pi) * np.exp(-3.0 * t / dur_sec)
            h2 = 0.6 * np.sin(2 * freq * t * 2 * np.pi) * np.exp(-5.0 * t / dur_sec)
            h3 = 0.3 * np.sin(3 * freq * t * 2 * np.pi) * np.exp(-8.0 * t / dur_sec)
            h4 = 0.15 * np.sin(4 * freq * t * 2 * np.pi) * np.exp(-11.0 * t / dur_sec)
            wave = (h1 + h2 + h3 + h4) * 0.65
            env = np.ones(num_samples, dtype=np.float32)
            attack = min(int(self.sample_rate * 0.008), num_samples // 4)
            if attack > 0:
                env[:attack] = np.linspace(0, 1, attack)
            return wave * env

        elif "Flauta" in wave_type:
            # Flauta / Instrumento de Sopro (fundamental pura + vibrato leve)
            vibrato = 1.0 + 0.008 * np.sin(6.0 * t * 2 * np.pi)  # vibrato de 6 Hz
            h1 = np.sin(freq * vibrato * t * 2 * np.pi)
            h2 = 0.15 * np.sin(2 * freq * vibrato * t * 2 * np.pi)
            wave = (h1 + h2) * 0.7
            env = np.ones(num_samples, dtype=np.float32)
            attack = min(int(self.sample_rate * 0.04), num_samples // 4)
            release = min(int(self.sample_rate * 0.04), num_samples // 4)
            if attack > 0:
                env[:attack] = np.linspace(0, 1, attack)
            if release > 0:
                env[-release:] = np.linspace(1, 0, release)
            return wave * env

        elif "Órgão" in wave_type or "Acordeão" in wave_type:
            # Órgão / Sanfona (registros de oitava 8' + 4' + 2')
            h1 = np.sin(freq * t * 2 * np.pi)
            h2 = 0.7 * np.sin(2 * freq * t * 2 * np.pi)
            h3 = 0.4 * np.sin(3 * freq * t * 2 * np.pi)
            h4 = 0.3 * np.sin(4 * freq * t * 2 * np.pi)
            wave = (h1 + h2 + h3 + h4) * 0.4
            env = np.ones(num_samples, dtype=np.float32)
            attack = min(int(self.sample_rate * 0.015), num_samples // 4)
            release = min(int(self.sample_rate * 0.02), num_samples // 4)
            if attack > 0:
                env[:attack] = np.linspace(0, 1, attack)
            if release > 0:
                env[-release:] = np.linspace(1, 0, release)
            return wave * env

        elif "Quadrada" in wave_type or "8-Bit" in wave_type or "Synth" in wave_type:
            # Onda Quadrada (Sintetizador 8-bit)
            wave = np.sign(np.sin(freq * t * 2 * np.pi)) * 0.4
            env = np.ones(num_samples, dtype=np.float32)
            rel = min(int(self.sample_rate * 0.02), num_samples // 4)
            if rel > 0:
                env[-rel:] = np.linspace(1, 0, rel)
            return wave * env

        else:
            # Onda Senoidal Padrão
            wave = np.sin(freq * t * 2 * np.pi) * 0.7
            env = np.ones(num_samples, dtype=np.float32)
            rel = min(int(self.sample_rate * 0.02), num_samples // 4)
            if rel > 0:
                env[-rel:] = np.linspace(1, 0, rel)
            return wave * env

    def click(self, freq=1000, dur_ms=30, amp=1.0) -> np.ndarray:
        """Gera tom percussivo curto."""
        num_samples = int(self.sample_rate * (dur_ms / 1000.0))
        t = np.linspace(0, dur_ms / 1000.0, num_samples, False)
        wave = amp * np.sin(freq * t * 2 * np.pi)
        return np.int16(wave * 32767)

    def generate_mix(self, notes_list: list, tempo_bpm: float = 120, rhythm_style: str = "Apenas Melodia", wave_type: str = "Seno (Suave)") -> np.ndarray:
        """
        notes_list: Lista de dicionários [{'note': 'C4', 'duration': 1.0, 'volume': 100}, ...]
        rhythm_style: "Apenas Melodia", "Pop / Rock (4/4)", "Eletrônico / Dance", "Valsa (3/4)", "Forró Tradicional", "Baião"
        wave_type: Forma de onda do instrumento
        """
        if not notes_list:
            return np.array([], dtype=np.int16)

        seconds_per_beat = 60.0 / tempo_bpm

        # 1. Gerar Melodia Principal
        melody_chunks = []
        total_beats = 0.0

        for n_item in notes_list:
            note_str = n_item.get('note', 'C4')
            dur_beats = float(n_item.get('duration', 1.0))
            vol_pct = float(n_item.get('volume', 100)) / 100.0

            total_beats += dur_beats
            dur_sec = dur_beats * seconds_per_beat
            num_samples = int(self.sample_rate * dur_sec)

            if note_str.upper() in ["PAUSA", "REST"]:
                wave_int16 = np.zeros(num_samples, dtype=np.int16)
            else:
                midi_num = note_to_midi(note_str)
                freq = midi_to_freq(midi_num)
                wave_float = self.generate_wave(freq, dur_sec, wave_type) * vol_pct
                wave_int16 = np.int16(np.clip(wave_float * 32767, -32768, 32767))

            melody_chunks.append(wave_int16)

        audio_melody = np.concatenate(melody_chunks) if melody_chunks else np.array([], dtype=np.int16)

        if rhythm_style in ["Nenhum", "Apenas Melodia"]:
            return audio_melody

        # 2. Gerar Acompanhamento Rítmico / Baixo conforme o estilo escolhido
        total_samples = len(audio_melody)
        audio_perc = np.zeros(total_samples, dtype=np.int32)
        audio_bass = np.zeros(total_samples, dtype=np.int32)

        first_midi = note_to_midi(notes_list[0].get('note', 'C4')) if notes_list else 60
        root_bass_midi = max(36, first_midi - 24)
        bass_freq = midi_to_freq(root_bass_midi)
        fifth_bass_freq = midi_to_freq(root_bass_midi + 7)

        # Subdivisão para percussão
        beats_count = int(np.ceil(total_beats * 2))  # meia batida

        for i in range(beats_count):
            sub_dur = seconds_per_beat / 2.0
            sample_start = int(i * sub_dur * self.sample_rate)

            if rhythm_style == "Pop / Rock (4/4)":
                # Bumbo no 1 e 3, Caixa no 2 e 4, Hi-hat em todas
                beat_idx = (i // 2) % 4
                is_sub = (i % 2 != 0)

                hit = np.array([], dtype=np.int16)
                if not is_sub:
                    if beat_idx in [0, 2]:  # Kick
                        hit = self.click(freq=120, dur_ms=80, amp=0.9)
                    else:  # Snare
                        hit = self.click(freq=500, dur_ms=40, amp=0.7)
                hihat = self.click(freq=3000, dur_ms=15, amp=0.2)
                
                # Junta percussão
                combo = np.zeros(max(len(hit), len(hihat)), dtype=np.int32)
                if len(hit) > 0:
                    combo[:len(hit)] += hit.astype(np.int32)
                combo[:len(hihat)] += hihat.astype(np.int32)

            elif rhythm_style == "Eletrônico / Dance":
                # Four-on-the-floor Kick em cada batida + Hihat no contratempo
                is_sub = (i % 2 != 0)
                if not is_sub:
                    hit = self.click(freq=100, dur_ms=90, amp=1.0)
                else:
                    hit = self.click(freq=2500, dur_ms=25, amp=0.35)
                combo = hit.astype(np.int32)

            elif rhythm_style == "Valsa (3/4)":
                beat_idx = (i // 2) % 3
                is_sub = (i % 2 != 0)
                if not is_sub:
                    if beat_idx == 0:  # Bumbo forte no 1
                        hit = self.click(freq=150, dur_ms=100, amp=0.9)
                    else:  # Toques leves no 2 e 3
                        hit = self.click(freq=700, dur_ms=30, amp=0.4)
                else:
                    hit = np.array([], dtype=np.int16)
                combo = hit.astype(np.int32)

            elif rhythm_style in ["Forró Tradicional", "Baião"]:
                if rhythm_style == "Baião":
                    if i % 4 == 0:
                        hit = self.click(freq=180, dur_ms=100, amp=0.9)
                    elif i % 4 == 3:
                        hit = self.click(freq=220, dur_ms=70, amp=0.7)
                    else:
                        hit = self.click(freq=750, dur_ms=25, amp=0.4)
                else:  # Forró
                    if i % 2 == 0:
                        hit = self.click(freq=200, dur_ms=110, amp=0.8)
                    else:
                        hit = self.click(freq=850, dur_ms=30, amp=0.5)
                tri = self.click(freq=1600, dur_ms=20, amp=0.25)
                combo = np.zeros(max(len(hit), len(tri)), dtype=np.int32)
                if len(hit) > 0:
                    combo[:len(hit)] += hit.astype(np.int32)
                combo[:len(tri)] += tri.astype(np.int32)
            else:
                combo = np.array([], dtype=np.int32)

            if len(combo) > 0:
                end_pos = min(total_samples, sample_start + len(combo))
                avail_len = end_pos - sample_start
                if avail_len > 0:
                    audio_perc[sample_start:end_pos] += combo[:avail_len]

        # Baixo simples para os ritmos
        num_beats = int(np.ceil(total_beats))
        for b in range(num_beats):
            freq = bass_freq if b % 2 == 0 else fifth_bass_freq
            dur_sec = min(seconds_per_beat, (total_sec := total_beats * seconds_per_beat) - (b * seconds_per_beat))
            if dur_sec <= 0:
                break
            b_samples = int(self.sample_rate * dur_sec)
            t = np.linspace(0, dur_sec, b_samples, False)
            wave = np.sin(freq * t * 2 * np.pi) * 0.25
            b_start = int(b * seconds_per_beat * self.sample_rate)
            b_end = min(total_samples, b_start + b_samples)
            if b_end > b_start:
                audio_bass[b_start:b_end] += np.int32(wave[:b_end - b_start] * 32767)

        # Mixagem final
        mix = audio_melody.astype(np.int32) + audio_bass + audio_perc
        mix = np.clip(mix, -32768, 32767).astype(np.int16)
        return mix

    def play(self, notes_list: list, tempo_bpm: float = 120, rhythm_style: str = "Apenas Melodia", wave_type: str = "Seno (Suave)", on_finish=None, loop: bool = False):
        self.stop()
        mix_data = self.generate_mix(notes_list, tempo_bpm, rhythm_style, wave_type)
        if len(mix_data) == 0:
            if on_finish:
                on_finish()
            return

        self.is_playing = True
        self.loop = loop

        def _play_thread():
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=1, buffer=1024)
                
                sound = pygame.mixer.Sound(buffer=mix_data)
                self.current_sound = sound
                self.current_channel = sound.play(loops=-1 if self.loop else 0)
                
                while self.is_playing and self.current_channel and self.current_channel.get_busy():
                    time.sleep(0.05)
            except Exception as e:
                print("Erro na reprodução de áudio:", e)
            finally:
                self.is_playing = False
                if on_finish:
                    on_finish()

        self.playback_thread = threading.Thread(target=_play_thread, daemon=True)
        self.playback_thread.start()

    def stop(self):
        self.is_playing = False
        self.loop = False
        if self.current_channel:
            try:
                self.current_channel.stop()
            except Exception:
                pass
            self.current_channel = None
        if self.current_sound:
            try:
                self.current_sound.stop()
            except Exception:
                pass
            self.current_sound = None

    def export_midi(self, notes_list: list, tempo_bpm: float, file_path: str):
        mf = MIDIFile(1)
        track = 0
        channel = 0
        mf.addTempo(track, 0, tempo_bpm)

        time_pos = 0.0
        for n_item in notes_list:
            note_str = n_item.get('note', 'C4')
            dur = float(n_item.get('duration', 1.0))
            vol = int(n_item.get('volume', 100))

            if note_str.upper() not in ["PAUSA", "REST"]:
                midi_num = note_to_midi(note_str)
                mf.addNote(track, channel, midi_num, time_pos, dur, vol)

            time_pos += dur

        with open(file_path, "wb") as f:
            mf.writeFile(f)
