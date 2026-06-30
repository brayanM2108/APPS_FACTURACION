# ui/theme.py
# Módulo central de tema y helpers para estandarizar ventanas

import tkinter as tk
from typing import Tuple

# Paleta Goleman (ajusta aquí y se replica en toda la app)
NAVY = "#000927"
ORANGE = "#F97838"
SKY = "#A7E2FF"
BLUE = "#1565C0"

BG = "#F5F7FA"
WHITE = "#FFFFFF"
TEXT = "#1E293B"
MUTED = "#64748B"
DANGER = "#C53030"
BORDER = "#E2E8F0"
SEL_BG = "#BEE3F8"

ACCENT = BLUE
ACCENT2 = "#0F4A8A"

# Fuentes
FONT_BASE = ("Segoe UI", 10)
FONT_HEADER = ("Segoe UI", 16, "bold")
FONT_SMALL = ("Segoe UI", 9)

# Tamaños por defecto (ancho x alto)
DEFAULT_SIZE = (1200, 800)
DEFAULT_MIN_SIZE = (820, 620)
SIZE_PRINCIPAL_VIEW = (1200, 800)
SIZE_CONSOLIDADOR_VIEW = (1200, 800)
COMPACT_SIZE = (900, 600)
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
        fullscreen: bool = False,
):
    if title:
        try:
            win.title(title)
        except Exception:
            pass

    if fullscreen:
        try:
            win.state("zoomed")
        except Exception:
            try:
                w = win.winfo_screenwidth()
                h = win.winfo_screenheight()
                win.geometry(f"{w}x{h}+0+0")
            except Exception:
                pass
    else:
        w, h = size if size is not None else DEFAULT_SIZE
        try:
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
