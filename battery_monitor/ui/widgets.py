"""Pequenos helpers de layout reutilizáveis pela UI."""

import tkinter as tk
from tkinter import ttk


def labeled_row(parent: tk.Misc, label: str, var: tk.StringVar) -> None:
    """Cria uma linha 'rótulo: valor' onde o valor acompanha ``var``."""
    f = ttk.Frame(parent)
    f.pack(fill="x", padx=12, pady=2)
    ttk.Label(f, text=label, width=20).pack(side="left")
    ttk.Label(f, textvariable=var, font=("Segoe UI", 10, "bold")).pack(side="left")
