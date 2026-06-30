import io
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox, filedialog

import cairosvg
from PIL import Image, ImageTk

from ui.theme import aplicar_theme_ventana, DEFAULT_SIZE, BG, WHITE, TEXT, MUTED, BORDER, ACCENT, ACCENT2, NAVY, ORANGE, SKY, BLUE
from features.asignar_facturacion.core.asignar_facturadores import cargar_facturadores, generar_excel


def _cargar_logo(size):
    try:
        logo_path = Path(__file__).parents[3] / "ui" / "LOGO_OSCURO.svg"
        if logo_path.exists():
            png_data = cairosvg.svg2png(url=str(logo_path), output_width=size, output_height=size)
            img = Image.open(io.BytesIO(png_data))
            return ImageTk.PhotoImage(img)
    except Exception:
        pass
    return None


def _cargar_icono(size):
    try:
        icono_path = Path(__file__).parents[3] / "ui" / "assets" / "asignar_facturacion.svg"
        if icono_path.exists():
            png_data = cairosvg.svg2png(url=str(icono_path), output_width=size, output_height=size)
            img = Image.open(io.BytesIO(png_data))
            return ImageTk.PhotoImage(img)
    except Exception:
        pass
    return None


def _round_rect(c, x1, y1, x2, y2, r, **kw):
    c.create_arc(x1, y1, x1 + r * 2, y1 + r * 2, start=90, extent=90, **kw)
    c.create_arc(x2 - r * 2, y1, x2, y1 + r * 2, start=0, extent=90, **kw)
    c.create_arc(x1, y2 - r * 2, x1 + r * 2, y2, start=180, extent=90, **kw)
    c.create_arc(x2 - r * 2, y2 - r * 2, x2, y2, start=270, extent=90, **kw)
    c.create_rectangle(x1 + r, y1, x2 - r, y2 + 1, **kw)
    c.create_rectangle(x1, y1 + r, x2 + 1, y2 - r, **kw)


class RoundedCard(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG, **kw)
        self._canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        self._canvas.pack(fill="both", expand=True)
        self._inner = tk.Frame(self._canvas, bg=WHITE)
        self.bind("<Configure>", self._redraw)

    def _redraw(self, e=None):
        self._canvas.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10 or h < 10:
            return
        r = 14
        _round_rect(self._canvas, 0, 0, w, h, r, fill=WHITE, outline=BORDER, width=1)
        iw = max(4, w - 2)
        ih = max(4, h - 2)
        self._canvas.create_window(w // 2, h // 2, window=self._inner, width=iw, height=ih, anchor="center")

    @property
    def content(self):
        return self._inner


class VentanaAsignarFacturacion(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        aplicar_theme_ventana(
            self,
            title="Asignar Facturación",
            size=DEFAULT_SIZE,
            min_size=None,
            bg=BG,
            resizable=(True, True),
            modal=True,
            fullscreen=True,
        )

        self._datos = cargar_facturadores()
        # {nombre: {'var_check': BooleanVar, 'var_filas': IntVar}}
        self._controles: dict = {}

        self._crear_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _crear_ui(self):
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        # ── Sidebar ──────────────────────────────────────────────
        side = tk.Frame(body, bg=NAVY, width=270)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        self._logo_img = _cargar_logo(160)
        if self._logo_img:
            tk.Label(side, image=self._logo_img, bg=NAVY).pack(pady=(28, 0))

        tk.Label(side, text="ASIGNAR\nFACTURACIÓN",
                 font=("Segoe UI", 16, "bold"), fg=WHITE, bg=NAVY,
                 anchor="w", justify="left").pack(padx=24, pady=(16, 8), fill="x")
        tk.Label(side, text="Genera filas por facturador/auxiliar en un archivo Excel.",
                 font=("Segoe UI", 10), fg=SKY, bg=NAVY,
                 anchor="w", wraplength=220, justify="left").pack(padx=24, fill="x")
        # Feature icon
        self._icon_sidebar = _cargar_icono(200)
        if self._icon_sidebar:
            icon_frame = tk.Frame(side, bg=NAVY, width=270, height=220)
            icon_frame.pack(fill="x", pady=(20, 0))
            icon_frame.pack_propagate(False)
            tk.Label(icon_frame, image=self._icon_sidebar, bg=NAVY).place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(side, text="Versión 2.0",
                 font=("Segoe UI", 9), fg=MUTED, bg=NAVY,
                 anchor="w").pack(padx=24, pady=(0, 24), side="bottom", fill="x")

        # ── Main content ─────────────────────────────────────────
        main = tk.Frame(body, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        # Header
        hdr = tk.Frame(main, bg=BG)
        hdr.pack(fill="x", padx=32, pady=(24, 20))
        col = tk.Frame(hdr, bg=BG)
        col.pack(side="left")
        tk.Label(col, text="Asignar Facturación",
                 font=("Segoe UI", 18, "bold"), fg=NAVY, bg=BG,
                 anchor="w").pack(anchor="w")
        tk.Label(col, text="Selecciona facturadores/auxiliares y la cantidad de filas.",
                 font=("Segoe UI", 10), fg=MUTED, bg=BG,
                 anchor="w").pack(anchor="w", pady=(2, 0))

        # ── Card: Facturadores ──────────────────────────────────
        card1 = RoundedCard(main)
        card1.pack(fill="both", expand=True, padx=32, pady=(0, 16))
        c1 = card1.content

        tk.Label(c1, text="Facturadores / Auxiliares",
                 font=("Segoe UI", 12, "bold"), fg=TEXT, bg=WHITE,
                 anchor="w").pack(padx=24, pady=(16, 8), fill="x")

        # Canvas con scroll (2 columnas: facturadores | auxiliares)
        sc_frame = tk.Frame(c1, bg=WHITE, highlightthickness=1, highlightbackground=BORDER)
        sc_frame.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        canvas = tk.Canvas(sc_frame, bg=WHITE, highlightthickness=0)
        scrollbar = ttk.Scrollbar(sc_frame, orient="vertical", command=canvas.yview)
        self._frame_scroll = tk.Frame(canvas, bg=WHITE)

        self._frame_scroll.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self._frame_scroll, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=2, pady=2)
        scrollbar.pack(side="right", fill="y")

        # Grid de 2 columnas dentro del scroll
        col_frame = tk.Frame(self._frame_scroll, bg=WHITE)
        col_frame.pack(fill="x", padx=8, pady=8)
        col_frame.grid_columnconfigure(0, weight=1, pad=8)
        col_frame.grid_columnconfigure(1, weight=1, pad=8)

        grupos = list(self._datos.items())
        for col_idx, (grupo, miembros) in enumerate(grupos):
            self._crear_seccion(col_frame, grupo, miembros, col_idx)

        # ── Card: Configuración ─────────────────────────────────
        card2 = RoundedCard(main)
        card2.pack(fill="x", padx=32, pady=(0, 20))
        c2 = card2.content

        tk.Label(c2, text="Configuración",
                 font=("Segoe UI", 12, "bold"), fg=TEXT, bg=WHITE,
                 anchor="w").pack(padx=24, pady=(16, 12), fill="x")

        global_row = tk.Frame(c2, bg=WHITE)
        global_row.pack(fill="x", padx=24, pady=(0, 16))
        tk.Label(global_row, text="Cantidad global (0 = usar individual):",
                 font=("Segoe UI", 9), fg=MUTED, bg=WHITE).pack(side="left", padx=(0, 8))
        self._var_cantidad_global = tk.IntVar(value=0)
        tk.Spinbox(
            global_row, from_=0, to=500,
            textvariable=self._var_cantidad_global,
            width=6, font=("Segoe UI", 10), relief="solid", bd=1,
        ).pack(side="left")

        # ── Action bar ───────────────────────────────────────────
        act = tk.Frame(main, bg=BG)
        act.pack(fill="x", padx=32, pady=(0, 20))

        tk.Button(
            act, text="✓  Seleccionar todo",
            font=("Segoe UI", 10),
            bg=BLUE, fg=WHITE, width=16, padx=8, pady=4,
            relief="flat", cursor="hand2",
            activebackground="#0F4A8A",
            command=self._seleccionar_todo,
        ).pack(side="left")

        tk.Button(
            act, text="✗  Limpiar selección",
            font=("Segoe UI", 10),
            bg=BLUE, fg=WHITE, width=16, padx=8, pady=4,
            relief="flat", cursor="hand2",
            activebackground="#0F4A8A",
            command=self._limpiar_seleccion,
        ).pack(side="left", padx=(8, 0))

        tk.Button(
            act, text="📥  Generar Excel",
            font=("Segoe UI", 10, "bold"),
            bg=ORANGE, fg=WHITE, width=16, padx=8, pady=4,
            relief="flat", cursor="hand2",
            activebackground="#E06020",
            command=self._generar,
        ).pack(side="left", padx=(8, 0))

        tk.Button(
            act, text="←  Volver",
            font=("Segoe UI", 10),
            bg=BLUE, fg=WHITE, width=16, padx=8, pady=4,
            relief="flat", cursor="hand2",
            activebackground="#0F4A8A",
            command=self.destroy,
        ).pack(side="right")

    def _crear_seccion(self, parent, titulo: str, miembros: list, col_idx: int):
        col_frame = tk.Frame(parent, bg=WHITE)
        col_frame.grid(row=0, column=col_idx, sticky="nsew", padx=6, pady=4)

        tk.Label(
            col_frame, text=titulo,
            font=("Segoe UI", 10, "bold"), bg=WHITE, fg=TEXT
        ).pack(anchor="w", pady=(0, 4))

        for nombre in miembros:
            fila = tk.Frame(col_frame, bg=WHITE,
                            highlightthickness=1, highlightbackground=BORDER)
            fila.pack(fill="x", pady=2)

            var_check = tk.BooleanVar(value=False)
            var_filas = tk.IntVar(value=1)

            self._controles[nombre] = {
                "var_check": var_check,
                "var_filas": var_filas,
            }

            tk.Checkbutton(
                fila, text=nombre,
                variable=var_check,
                font=("Segoe UI", 9), bg=WHITE, fg=TEXT,
                activebackground=WHITE, anchor="w"
            ).pack(side="left", padx=10, pady=6, fill="x", expand=True)

            tk.Label(fila, text="Filas:", font=("Segoe UI", 8),
                     bg=WHITE, fg=MUTED).pack(side="left")

            tk.Spinbox(
                fila, from_=1, to=500,
                textvariable=var_filas,
                width=5, font=("Segoe UI", 9)
            ).pack(side="left", padx=(2, 12), pady=4)

    # ── Acciones ──────────────────────────────────────────────────────────────

    def _seleccionar_todo(self):
        for ctrl in self._controles.values():
            ctrl["var_check"].set(True)

    def _limpiar_seleccion(self):
        for ctrl in self._controles.values():
            ctrl["var_check"].set(False)

    def _generar(self):
        seleccionados = [
            {"nombre": nombre, "filas": ctrl["var_filas"].get()}
            for nombre, ctrl in self._controles.items()
            if ctrl["var_check"].get()
        ]

        if not seleccionados:
            messagebox.showwarning("Sin selección",
                                   "Debes seleccionar al menos un facturador.", parent=self)
            return

        # Leer cantidad global (0 = no aplica)
        cantidad_global = self._var_cantidad_global.get()
        cantidad_global = cantidad_global if cantidad_global > 0 else None

        carpeta = filedialog.askdirectory(title="Selecciona carpeta de destino", parent=self)
        if not carpeta:
            return

        try:
            ruta = generar_excel(seleccionados, carpeta, cantidad_global=cantidad_global)
            messagebox.showinfo("Éxito", f"Archivo generado en:\n{ruta}", parent=self)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)