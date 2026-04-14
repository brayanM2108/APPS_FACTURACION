# ui/theme.py
# Módulo central de tema y helpers para estandarizar ventanas

import tkinter as tk
from typing import Tuple

# Paleta común (puedes ajustar colores aquí y se replicarán)
BG = "#F0F4F8"
WHITE = "#FFFFFF"
ACCENT = "#2B6CB0"
ACCENT2 = "#1A4A8A"
TEXT = "#2D3748"
MUTED = "#718096"
DANGER = "#C53030"
BORDER = "#E2E8F0"
SEL_BG = "#BEE3F8"

# Fuentes
FONT_BASE = ("Segoe UI", 10)
FONT_HEADER = ("Segoe UI", 16, "bold")
FONT_SMALL = ("Segoe UI", 9)

# Tamaños por defecto (ancho x alto)
DEFAULT_SIZE = (820, 580)      # tamaño por defecto para ventanas Toplevel grandes
DEFAULT_MIN_SIZE = (700, 480)  # tamaño mínimo por defecto
SIZE_PRINCIPAL_VIEW = (768, 720)

COMPACT_SIZE = (600, 420)      # tamaño para ventanas compactas (ej. compresión)
COMPACT_MIN = (520, 380)

# Helper: aplicar configuración base a una ventana (Tk o Toplevel)
def aplicar_theme_ventana(
        win: tk.Misc,
        *,
        title: str | None = None,
        size: Tuple[int, int] | None = None,
        min_size: Tuple[int, int] | None = None,
        bg: str | None = None,
        resizable: Tuple[bool, bool] = (False, False),
        modal: bool = False,
):
    if title:
        try:
            win.title(title)
        except Exception:
            pass

    w, h = size if size is not None else DEFAULT_SIZE
    try:
        # centrar en pantalla
        win.update_idletasks()
        screen_w = win.winfo_screenwidth()
        screen_h = win.winfo_screenheight()
        x = max(0, (screen_w - w) // 2)
        y = max(0, (screen_h - h) // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")
    except Exception:
        try:
            win.geometry(f"{w}x{h}")
        except Exception:
            pass

    if min_size:
        try:
            win.minsize(*min_size)
        except Exception:
            pass
    else:
        try:
            win.minsize(*DEFAULT_MIN_SIZE)
        except Exception:
            pass

    try:
        win.resizable(resizable[0], resizable[1])
    except Exception:
        pass

    if bg:
        try:
            win.configure(bg=bg)
        except Exception:
            pass
    else:
        try:
            win.configure(bg=BG)
        except Exception:
            pass

    if modal:
        try:
            win.grab_set()
        except Exception:
            pass
