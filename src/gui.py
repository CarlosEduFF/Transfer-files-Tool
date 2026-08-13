import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
try:
    from engine import AudioEngine, note_to_midi
except ImportError:
    from src.engine import AudioEngine, note_to_midi

class MusicStudioGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("🎵 Estúdio de Composição Musical - Python Sequencer")
        self.geometry("960x700")
        self.minsize(850, 620)

        # Configuração de Estilo TTK
        self.style = ttk.Style(self)
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        # Cores customizadas
        self.configure(bg="#1e1e24")
        self.style.configure(".", background="#1e1e24", foreground="#f8f9fa", font=("Segoe UI", 10))
        self.style.configure("TLabel", background="#1e1e24", foreground="#f8f9fa")
        self.style.configure("TFrame", background="#1e1e24")
        self.style.configure("TLabelframe", background="#1e1e24", foreground="#00d26a", font=("Segoe UI", 10, "bold"))
        self.style.configure("TLabelframe.Label", background="#1e1e24", foreground="#00d26a")
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=5)
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#00d26a")
        self.style.configure("Treeview", font=("Segoe UI", 10), rowheight=24, background="#2b2d42", foreground="#ffffff", fieldbackground="#2b2d42")
        self.style.map("Treeview", background=[("selected", "#0d6efd")], foreground=[("selected", "#ffffff")])

        self.engine = AudioEngine()

        # Lista de notas na memória: [{'note': 'C4', 'duration': 1.0, 'volume': 100}, ...]
        self.notes_data = []

        self._build_ui()
        self._load_default_preset()

    def _build_ui(self):
        # 1. Cabeçalho
        header_frame = ttk.Frame(self, padding=10)
        header_frame.pack(fill=tk.X)

        title_lbl = ttk.Label(header_frame, text="🎵 Estúdio de Composição Musical", style="Header.TLabel")
        title_lbl.pack(side=tk.LEFT)

        preset_frame = ttk.Frame(header_frame)
        preset_frame.pack(side=tk.RIGHT)
        
        ttk.Label(preset_frame, text="Exemplos / Presets:").pack(side=tk.LEFT, padx=5)
        self.cb_presets = ttk.Combobox(preset_frame, values=[
            "Tema Game 8-Bit",
            "Brilha Brilha Estrelinha",
            "Asa Branca (Forró)",
            "Escala Maior de Dó"
        ], state="readonly", width=22)
        self.cb_presets.current(0)
        self.cb_presets.pack(side=tk.LEFT, padx=5)
        
        btn_load_preset = ttk.Button(preset_frame, text="Carregar Preset", command=self._on_load_preset)
        btn_load_preset.pack(side=tk.LEFT, padx=5)

        # 2. Configurações Globais (BPM, Timbre do Instrumento, Ritmo)
        settings_frame = ttk.LabelFrame(self, text="⚙️ Timbre do Instrumento, BPM & Acompanhamento", padding=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=5)

        # Instrumento / Timbre
        ttk.Label(settings_frame, text="Instrumento / Timbre:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.cb_wave = ttk.Combobox(settings_frame, values=[
            "Piano Acústico (Realista)",
            "Violão de Náilon",
            "Flauta (Sopro Suave)",
            "Órgão / Sanfona",
            "Sintetizador 8-Bit"
        ], state="readonly", width=25)
        self.cb_wave.current(0)
        self.cb_wave.grid(row=0, column=1, padx=5)

        # BPM
        ttk.Label(settings_frame, text="Velocidade (BPM):").grid(row=0, column=2, sticky=tk.W, padx=(15, 5))
        self.scale_bpm = tk.Scale(settings_frame, from_=60, to=240, orient=tk.HORIZONTAL, bg="#2b2d42", fg="#00d26a", highlightthickness=0, length=160)
        self.scale_bpm.set(140)
        self.scale_bpm.grid(row=0, column=3, padx=5)

        # Estilo de Acompanhamento
        ttk.Label(settings_frame, text="Ritmo / Bateria:").grid(row=0, column=4, sticky=tk.W, padx=(15, 5))
        self.cb_rhythm = ttk.Combobox(settings_frame, values=[
            "Apenas Melodia",
            "Pop / Rock (4/4)",
            "Eletrônico / Dance",
            "Valsa (3/4)",
            "Forró Tradicional",
            "Baião"
        ], state="readonly", width=18)
        self.cb_rhythm.current(0)
        self.cb_rhythm.grid(row=0, column=5, padx=5)

        # 3. Área Central (Tabela de Notas + Painel de Edição)
        main_content = ttk.Frame(self, padding=10)
        main_content.pack(fill=tk.BOTH, expand=True)

        # Tabela (Treeview) no lado esquerdo
        table_frame = ttk.LabelFrame(main_content, text="🎼 Sequência da Música (Notas)", padding=10)
        table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        columns = ("pos", "note", "dur", "vol")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("pos", text="#")
        self.tree.heading("note", text="Nota Musical")
        self.tree.heading("dur", text="Duração (Batidas)")
        self.tree.heading("vol", text="Volume (%)")

        self.tree.column("pos", width=40, anchor=tk.CENTER)
        self.tree.column("note", width=130, anchor=tk.CENTER)
        self.tree.column("dur", width=140, anchor=tk.CENTER)
        self.tree.column("vol", width=100, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # Painel de Edição de Nota no lado direito
        editor_frame = ttk.LabelFrame(main_content, text="📝 Adicionar / Editar Nota", padding=10)
        editor_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))

        # Nome da Nota
        ttk.Label(editor_frame, text="Nota:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.cb_note_name = ttk.Combobox(editor_frame, values=["C", "D", "E", "F", "G", "A", "B", "PAUSA"], state="readonly", width=8)
        self.cb_note_name.current(0)
        self.cb_note_name.grid(row=0, column=1, pady=5, padx=5)

        # Acidente
        ttk.Label(editor_frame, text="Acidente:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.cb_accidental = ttk.Combobox(editor_frame, values=["Nenhum", "# (Sustenido)", "b (Bemol)"], state="readonly", width=12)
        self.cb_accidental.current(0)
        self.cb_accidental.grid(row=1, column=1, pady=5, padx=5)

        # Oitava
        ttk.Label(editor_frame, text="Oitava:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.sb_octave = ttk.Spinbox(editor_frame, from_=2, to=6, width=5)
        self.sb_octave.set(4)
        self.sb_octave.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)

        # Duração
        ttk.Label(editor_frame, text="Duração:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.cb_duration = ttk.Combobox(editor_frame, values=[
            "1.0 (Semínima)",
            "0.5 (Colcheia)",
            "0.25 (Semicolcheia)",
            "1.5 (Semínima Pontuada)",
            "2.0 (Mínima)",
            "4.0 (Semibreve)"
        ], state="readonly", width=18)
        self.cb_duration.current(0)
        self.cb_duration.grid(row=3, column=1, pady=5, padx=5)

        # Volume
        ttk.Label(editor_frame, text="Volume:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.scale_volume = tk.Scale(editor_frame, from_=10, to=100, orient=tk.HORIZONTAL, bg="#2b2d42", fg="#00d26a", highlightthickness=0, length=120)
        self.scale_volume.set(100)
        self.scale_volume.grid(row=4, column=1, pady=5, padx=5)

        # Separador
        ttk.Separator(editor_frame, orient=tk.HORIZONTAL).grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)

        # Botões de Ação
        btn_add = ttk.Button(editor_frame, text="➕ Adicionar Nota", command=self._on_add_note)
        btn_add.grid(row=6, column=0, columnspan=2, sticky="ew", pady=3)

        btn_update = ttk.Button(editor_frame, text="✏️ Atualizar Selecionada", command=self._on_update_note)
        btn_update.grid(row=7, column=0, columnspan=2, sticky="ew", pady=3)

        btn_delete = ttk.Button(editor_frame, text="❌ Remover Selecionada", command=self._on_delete_note)
        btn_delete.grid(row=8, column=0, columnspan=2, sticky="ew", pady=3)

        move_frame = ttk.Frame(editor_frame)
        move_frame.grid(row=9, column=0, columnspan=2, sticky="ew", pady=3)
        btn_up = ttk.Button(move_frame, text="⬆️ Subir", command=self._on_move_up)
        btn_up.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        btn_down = ttk.Button(move_frame, text="⬇️ Descer", command=self._on_move_down)
        btn_down.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

        btn_clear = ttk.Button(editor_frame, text="🗑️ Limpar Tudo", command=self._on_clear_all)
        btn_clear.grid(row=10, column=0, columnspan=2, sticky="ew", pady=3)

        # 4. Painel de Controle de Playback & Exportação (Rodapé)
        footer_frame = ttk.LabelFrame(self, text="▶️ Playback & Exportação", padding=10)
        footer_frame.pack(fill=tk.X, padx=10, pady=10)

        self.btn_play = ttk.Button(footer_frame, text="▶️ PLAY (Tocar Música)", command=self._on_play)
        self.btn_play.pack(side=tk.LEFT, padx=10)

        self.btn_stop = ttk.Button(footer_frame, text="⏹️ PARAR", command=self._on_stop)
        self.btn_stop.pack(side=tk.LEFT, padx=10)

        # Checkbox para manter ligado / repetir em loop
        self.chk_loop_var = tk.BooleanVar(value=True)
        self.chk_loop = ttk.Checkbutton(footer_frame, text="🔄 Manter ligado (Repetir / Loop)", variable=self.chk_loop_var)
        self.chk_loop.pack(side=tk.LEFT, padx=10)

        btn_export = ttk.Button(footer_frame, text="💾 Exportar Arquivo MIDI", command=self._on_export_midi)
        btn_export.pack(side=tk.LEFT, padx=10)

        self.lbl_status = ttk.Label(footer_frame, text="Status: Pronto", font=("Segoe UI", 10, "italic"), foreground="#0dcaf0")
        self.lbl_status.pack(side=tk.RIGHT, padx=10)

    # ---------------- Lógica da Lista de Notas ----------------

    def _get_formatted_note_string(self) -> str:
        name = self.cb_note_name.get()
        if name == "PAUSA":
            return "PAUSA"
        acc = self.cb_accidental.get()
        acc_str = "#" if "#" in acc else ("b" if "b" in acc else "")
        octave = self.sb_octave.get()
        return f"{name}{acc_str}{octave}"

    def _get_duration_float(self) -> float:
        dur_str = self.cb_duration.get()
        try:
            val = float(dur_str.split()[0])
            return val
        except Exception:
            return 1.0

    def _update_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, n in enumerate(self.notes_data, 1):
            self.tree.insert("", tk.END, values=(i, n['note'], n['duration'], n['volume']))

    def _on_add_note(self):
        note_str = self._get_formatted_note_string()
        dur = self._get_duration_float()
        vol = int(self.scale_volume.get())

        self.notes_data.append({'note': note_str, 'duration': dur, 'volume': vol})
        self._update_tree()

    def _on_tree_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item_vals = self.tree.item(selected[0], "values")
        if not item_vals:
            return

        idx = int(item_vals[0]) - 1
        n = self.notes_data[idx]
        note_str = n['note']

        if note_str == "PAUSA":
            self.cb_note_name.set("PAUSA")
        else:
            if "#" in note_str:
                self.cb_accidental.set("# (Sustenido)")
                base_name = note_str[0]
                oct_val = note_str[2:]
            elif "b" in note_str:
                self.cb_accidental.set("b (Bemol)")
                base_name = note_str[0]
                oct_val = note_str[2:]
            else:
                self.cb_accidental.set("Nenhum")
                base_name = note_str[0]
                oct_val = note_str[1:]

            self.cb_note_name.set(base_name)
            if oct_val.isdigit():
                self.sb_octave.set(int(oct_val))

        dur_val = n['duration']
        for v in self.cb_duration['values']:
            if str(dur_val) in v:
                self.cb_duration.set(v)
                break

        self.scale_volume.set(n['volume'])

    def _on_update_note(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma nota na lista para atualizar.")
            return

        idx = int(self.tree.item(selected[0], "values")[0]) - 1
        note_str = self._get_formatted_note_string()
        dur = self._get_duration_float()
        vol = int(self.scale_volume.get())

        self.notes_data[idx] = {'note': note_str, 'duration': dur, 'volume': vol}
        self._update_tree()

    def _on_delete_note(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(self.tree.item(selected[0], "values")[0]) - 1
        del self.notes_data[idx]
        self._update_tree()

    def _on_move_up(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(self.tree.item(selected[0], "values")[0]) - 1
        if idx > 0:
            self.notes_data[idx], self.notes_data[idx - 1] = self.notes_data[idx - 1], self.notes_data[idx]
            self._update_tree()
            children = self.tree.get_children()
            self.tree.selection_set(children[idx - 1])

    def _on_move_down(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(self.tree.item(selected[0], "values")[0]) - 1
        if idx < len(self.notes_data) - 1:
            self.notes_data[idx], self.notes_data[idx + 1] = self.notes_data[idx + 1], self.notes_data[idx]
            self._update_tree()
            children = self.tree.get_children()
            self.tree.selection_set(children[idx + 1])

    def _on_clear_all(self):
        if messagebox.askyesno("Confirmar", "Deseja limpar toda a lista de notas?"):
            self.notes_data.clear()
            self._update_tree()

    # ---------------- Presets ----------------

    def _load_default_preset(self):
        self._on_load_preset()

    def _on_load_preset(self):
        preset_name = self.cb_presets.get()
        self.notes_data.clear()

        if preset_name == "Brilha Brilha Estrelinha" or preset_name == "Piano Clássico":
            twinkle = [
                ("C4", 1.0), ("C4", 1.0), ("G4", 1.0), ("G4", 1.0), ("A4", 1.0), ("A4", 1.0), ("G4", 2.0),
                ("F4", 1.0), ("F4", 1.0), ("E4", 1.0), ("E4", 1.0), ("D4", 1.0), ("D4", 1.0), ("C4", 2.0)
            ]
            for note, dur in twinkle:
                self.notes_data.append({'note': note, 'duration': dur, 'volume': 100})
            self.scale_bpm.set(110)
            self.cb_wave.set("Piano Acústico (Realista)")
            self.cb_rhythm.set("Pop / Rock (4/4)")

        elif preset_name == "Tema Game 8-Bit":
            mario = [
                ("E5", 0.25), ("E5", 0.25), ("PAUSA", 0.25), ("E5", 0.25), ("PAUSA", 0.25),
                ("C5", 0.25), ("E5", 0.5), ("G5", 0.5), ("PAUSA", 0.5), ("G4", 0.5)
            ]
            for note, dur in mario:
                self.notes_data.append({'note': note, 'duration': dur, 'volume': 100})
            self.scale_bpm.set(160)
            self.cb_wave.set("Sintetizador 8-Bit")
            self.cb_rhythm.set("Pop / Rock (4/4)")

        elif preset_name == "Asa Branca (Forró)":
            asa_branca = [
                ('G4', 0.5), ('A4', 0.5), ('B4', 1.0), ('D5', 1.0), ('D5', 1.0), ('B4', 1.0),
                ('C5', 1.0), ('C5', 2.0), ('G4', 0.5), ('A4', 0.5), ('B4', 1.0), ('D5', 1.0),
                ('D5', 1.0), ('C5', 1.0), ('B4', 2.0)
            ]
            for note, dur in asa_branca:
                self.notes_data.append({'note': note, 'duration': dur, 'volume': 100})
            self.scale_bpm.set(130)
            self.cb_wave.set("Órgão / Sanfona")
            self.cb_rhythm.set("Forró Tradicional")

        elif preset_name == "Escala Maior de Dó":
            scale = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]
            for n in scale:
                self.notes_data.append({'note': n, 'duration': 1.0, 'volume': 100})
            self.scale_bpm.set(120)
            self.cb_wave.set("Piano Acústico (Realista)")
            self.cb_rhythm.set("Apenas Melodia")

        self._update_tree()

    # ---------------- Execução e Exportação ----------------

    def _on_play(self):
        if not self.notes_data:
            messagebox.showwarning("Aviso", "Adicione notas antes de reproduzir!")
            return

        bpm = float(self.scale_bpm.get())
        rhythm = self.cb_rhythm.get()
        wave = self.cb_wave.get()
        is_loop = self.chk_loop_var.get()

        if is_loop:
            self.lbl_status.config(text="Status: 🔄 Reproduzindo (Manter ligado / Loop)...", foreground="#00d26a")
        else:
            self.lbl_status.config(text="Status: 🔊 Reproduzindo...", foreground="#00d26a")

        self.btn_play.config(state=tk.DISABLED)

        def _on_finished():
            self.after(0, lambda: self._playback_finished())

        self.engine.play(self.notes_data, tempo_bpm=bpm, rhythm_style=rhythm, wave_type=wave, on_finish=_on_finished, loop=is_loop)

    def _playback_finished(self):
        self.lbl_status.config(text="Status: Pronto", foreground="#0dcaf0")
        self.btn_play.config(state=tk.NORMAL)

    def _on_stop(self):
        self.engine.stop()
        self._playback_finished()

    def _on_export_midi(self):
        if not self.notes_data:
            messagebox.showwarning("Aviso", "A lista de notas está vazia!")
            return

        file_path = filedialog.asksaveasfilename(
            title="Salvar Arquivo MIDI",
            defaultextension=".mid",
            filetypes=[("Arquivos MIDI", "*.mid"), ("Todos os Arquivos", "*.*")]
        )
        if file_path:
            bpm = float(self.scale_bpm.get())
            try:
                self.engine.export_midi(self.notes_data, tempo_bpm=bpm, file_path=file_path)
                messagebox.showinfo("Sucesso", f"Arquivo MIDI salvo com sucesso em:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao exportar arquivo MIDI:\n{e}")

if __name__ == "__main__":
    app = MusicStudioGUI()
    app.mainloop()
