import tkinter as tk
from tkinter import ttk


COLORS = {
    "surface": "#FFFFFF",
    "border": "#E2E8F0",
    "text_primary": "#0F172A",
}


def _make_style():
    style = ttk.Style()
    style.configure(
        "Toolbar.TButton",
        font=("Segoe UI", 9),
        padding=(10, 5),
        relief="flat",
    )
    style.configure(
        "Primary.TButton",
        font=("Segoe UI", 9, "bold"),
        padding=(10, 5),
        relief="flat",
    )


class Toolbar:
    def __init__(self, parent, callbacks):
        self.frame = tk.Frame(
            parent,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )

        _make_style()

        inner = tk.Frame(self.frame, bg=COLORS["surface"])
        inner.pack(fill="x", padx=12, pady=8)

        tk.Label(
            inner,
            text="Gestor de Archivos",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["surface"],
            fg=COLORS["text_primary"],
        ).pack(side="left", padx=(0, 16))

        sep = tk.Frame(inner, bg=COLORS["border"], width=1, height=24)
        sep.pack(side="left", padx=(0, 12))

        left_buttons = [
            ("Abrir carpeta", callbacks["abrir"], False),
            ("Cruzar Excel", callbacks["cruzar_excel"], False),
            ("Cruzar documentos", callbacks["cruzar_texto"], False),
            ("Cruzar carpetas", callbacks["cruzar_carpetas"], False),
            ("Exportar", callbacks["exportar_archivos"], False),
            ("Limpiar archivos", callbacks["limpiar_archivos"], False),
        ]

        for texto, cmd, _ in left_buttons:
            self._btn(inner, texto, cmd, primary=False)

        sep2 = tk.Frame(inner, bg=COLORS["border"], width=1, height=24)
        sep2.pack(side="left", padx=(8, 8))

        self._btn(inner, "Ejecutar", callbacks["ejecutar"], primary=True)
        self._btn(inner, "Limpiar operaciones", callbacks["limpiar"], primary=False)

    @staticmethod
    def _btn(parent, texto, cmd, primary=False):
        style = "Primary.TButton" if primary else "Toolbar.TButton"
        btn = ttk.Button(parent, text=texto, command=cmd, style=style)
        btn.pack(side="left", padx=(0, 4))
        return btn
