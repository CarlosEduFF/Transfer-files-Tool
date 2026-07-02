"""Janela principal — orquestra coleta, persistência e exibição.

Esta camada não contém regra de negócio: ela apenas pede dados aos
collectors, formata via ``domain.verdict`` e desenha. Toda coleta lenta
roda em thread separada.
"""

import os
import threading
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox

from ..collectors.base import HealthCollector, RealtimeCollector
from ..config import LOG_EVERY_REFRESHES, REFRESH_MS
from ..domain.alerts import LowBatteryAlert
from ..domain.models import HealthReport
from ..domain.verdict import fmt_secs, health_verdict
from ..storage.csv_logger import CsvLogger
from .history_window import HistoryWindow
from .widgets import labeled_row


class BatteryApp(tk.Tk):
    def __init__(
        self,
        realtime: RealtimeCollector,
        health: HealthCollector,
        logger: CsvLogger,
    ):
        super().__init__()
        self._realtime = realtime
        self._health_collector = health
        self._logger = logger

        self.title("Monitor de Bateria")
        self.geometry("420x440")
        self.resizable(False, False)

        self._refresh_count = 0
        self._health: HealthReport | None = None
        self._alert = LowBatteryAlert()

        self._build_ui()
        self.refresh_health()        # roda em thread (powercfg é lento)
        self._tick()                 # inicia loop ao vivo

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        pad = {"padx": 16, "pady": 6}

        # --- Estado em tempo real ---
        live = ttk.LabelFrame(self, text="Tempo real")
        live.pack(fill="x", **pad)

        self.var_percent = tk.StringVar(value="—")
        self.var_status = tk.StringVar(value="—")
        self.var_time = tk.StringVar(value="—")

        labeled_row(live, "Carga:", self.var_percent)
        self.bar = ttk.Progressbar(live, length=360, maximum=100)
        self.bar.pack(padx=12, pady=(0, 8))
        labeled_row(live, "Status:", self.var_status)
        labeled_row(live, "Tempo restante:", self.var_time)

        # --- Saúde / desgaste ---
        health = ttk.LabelFrame(self, text="Saúde da bateria (desgaste)")
        health.pack(fill="x", **pad)

        self.var_design = tk.StringVar(value="—")
        self.var_full = tk.StringVar(value="—")
        self.var_cycles = tk.StringVar(value="—")
        self.var_health = tk.StringVar(value="calculando…")

        labeled_row(health, "Capacidade de fábrica:", self.var_design)
        labeled_row(health, "Capacidade atual:", self.var_full)
        labeled_row(health, "Ciclos de carga:", self.var_cycles)

        self.lbl_health = ttk.Label(
            health, textvariable=self.var_health, font=("Segoe UI", 11, "bold")
        )
        self.lbl_health.pack(anchor="w", padx=12, pady=(4, 10))

        # --- Ações ---
        actions = ttk.Frame(self)
        actions.pack(fill="x", **pad)
        ttk.Button(actions, text="Atualizar saúde", command=self.refresh_health).pack(
            side="left"
        )
        ttk.Button(actions, text="Abrir log CSV", command=self._open_log).pack(
            side="left", padx=8
        )
        ttk.Button(actions, text="Ver histórico", command=self._show_history).pack(
            side="left"
        )

        self.var_logstatus = tk.StringVar(value=f"Log: {self._logger.name}")
        ttk.Label(self, textvariable=self.var_logstatus, foreground="gray").pack(
            anchor="w", padx=16, pady=(0, 8)
        )

    # --------------------------------------------------- loop em tempo real
    def _tick(self) -> None:
        status = self._realtime.read()
        if not status.present:
            self.var_percent.set("sem bateria detectada")
        else:
            self.var_percent.set(f"{status.percent:.0f}%")
            self.bar["value"] = status.percent
            if status.plugged is None:
                self.var_status.set("desconhecido")
            elif status.plugged:
                self.var_status.set("⚡ carregando / na tomada")
            else:
                self.var_status.set("🔋 usando bateria")
            self.var_time.set(fmt_secs(status.secs_left))

            # alerta de bateria baixa (mostra uma vez por queda)
            message = self._alert.check(status)
            if message:
                messagebox.showwarning("Bateria baixa", message)

            # grava no log periodicamente
            self._refresh_count += 1
            if self._refresh_count % LOG_EVERY_REFRESHES == 1:
                health_pct = self._health.health_pct if self._health else None
                try:
                    self._logger.append(
                        round(status.percent, 1), status.plugged, health_pct
                    )
                    self.var_logstatus.set(
                        f"Log: {self._logger.name} "
                        f"(última gravação {datetime.now():%H:%M:%S})"
                    )
                except OSError:
                    pass

        self.after(REFRESH_MS, self._tick)

    # ------------------------------------------------------------- saúde
    def refresh_health(self) -> None:
        self.var_health.set("calculando… (gerando relatório do Windows)")
        threading.Thread(target=self._load_health, daemon=True).start()

    def _load_health(self) -> None:
        report = self._health_collector.read()
        self.after(0, lambda: self._apply_health(report))

    def _apply_health(self, report: HealthReport) -> None:
        self._health = report
        if report.error:
            self.var_health.set(report.error)
            self.lbl_health.configure(foreground="gray")
            return

        d, full = report.design_mwh, report.full_mwh
        cyc, h = report.cycle_count, report.health_pct

        self.var_design.set(f"{d:,} mWh".replace(",", ".") if d else "—")
        self.var_full.set(f"{full:,} mWh".replace(",", ".") if full else "—")
        self.var_cycles.set(str(cyc) if cyc is not None else "—")

        verdict, color = health_verdict(h)
        if h is not None:
            self.var_health.set(f"Saúde: {h:.0f}%  —  {verdict}")
        else:
            self.var_health.set(f"Saúde: {verdict}")
        self.lbl_health.configure(foreground=color)

    # ------------------------------------------------------------- ações
    def _open_log(self) -> None:
        if not self._logger.exists():
            messagebox.showinfo("Log", "Ainda não há dados gravados no log.")
            return
        try:
            os.startfile(self._logger.path)  # noqa: type-ignore  (Windows)
        except (AttributeError, OSError):
            messagebox.showinfo("Log", f"Arquivo de log:\n{self._logger.path}")

    def _show_history(self) -> None:
        HistoryWindow.open(self, self._logger.read_all())
