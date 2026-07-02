"""Janela secundária com o gráfico do histórico de carga."""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import List

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ..storage.csv_logger import LogEntry


class HistoryWindow(tk.Toplevel):
    """Plota carga (%) ao longo do tempo a partir do histórico."""

    def __init__(self, parent: tk.Misc, entries: List[LogEntry]):
        super().__init__(parent)
        self.title("Histórico de carga")
        self.geometry("680x420")

        fig = Figure(figsize=(6.6, 3.8), dpi=100)
        ax = fig.add_subplot(111)

        times = [e.timestamp for e in entries]
        charge = [e.percent for e in entries]
        ax.plot(times, charge, color="#2e7d32", linewidth=1.5)
        ax.fill_between(times, charge, alpha=0.1, color="#2e7d32")

        ax.set_ylim(0, 100)
        ax.set_ylabel("Carga (%)")
        ax.set_title("Carga da bateria ao longo do tempo")
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

        ttk.Label(
            self,
            text=f"{len(entries)} amostras registradas",
            foreground="gray",
        ).pack(anchor="w", padx=12, pady=(0, 8))

    @staticmethod
    def open(parent: tk.Misc, entries: List[LogEntry]) -> None:
        """Abre a janela, ou avisa se ainda não há dados suficientes."""
        if len(entries) < 2:
            messagebox.showinfo(
                "Histórico",
                "Ainda não há amostras suficientes para o gráfico.\n"
                "Deixe o monitor rodando por alguns minutos.",
            )
            return
        HistoryWindow(parent, entries)
