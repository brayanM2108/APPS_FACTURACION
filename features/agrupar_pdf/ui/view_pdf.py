"""
features/agrupar_pdf/ui/view_pdf.py
Ventana Toplevel del agrupador/unificador de PDFs.
REDISEÑO UI/UX — lógica de negocio intacta.
"""
import io
import os
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

import cairosvg
from PIL import Image, ImageTk

from features.agrupar_pdf.core.agrupar import (
    cargar_metadatos_async,
    unir_pdfs,
    unir_pdfs_por_carpeta,
    exportar_auditoria_unificacion,
)
from features.comprimir_pdf.core.comprimir_service import (
    es_pesado, UMBRAL_DEFECTO, _fmt_bytes, tamaño_bytes,
)
from features.comprimir_pdf.ui.view_comprimir import VentanaComprimirPDF
from ui.theme import aplicar_theme_ventana, DEFAULT_SIZE, DEFAULT_MIN_SIZE

# ── Paleta Goleman ────────────────────────────────────────────────────────────
NAVY         = "#000927"
ORANGE       = "#F97838"
SKY          = "#A7E2FF"
BLUE         = "#1565C0"
BG           = "#F5F7FA"
WHITE        = "#FFFFFF"
TEXT         = "#1E293B"
MUTED        = "#64748B"
DANGER       = "#C53030"
DANGER_LIGHT = "#FEF2F2"
SUCCESS      = "#1565C0"
SUCCESS_LIGHT= "#EFF6FF"
BORDER       = "#E2E8F0"
BORDER2      = "#CBD5E0"
SEL_BG       = "#DBEAFE"
ACCENT       = BLUE
ACCENT2      = "#0F4A8A"
ACCENT_LIGHT = "#EFF6FF"


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
        icono_path = Path(__file__).parents[3] / "ui" / "assets" / "agrupar_pdf.svg"
        if icono_path.exists():
            png_data = cairosvg.svg2png(url=str(icono_path), output_width=size, output_height=size)
            img = Image.open(io.BytesIO(png_data))
            return ImageTk.PhotoImage(img)
    except Exception:
        pass
    return None


PAGE_SIZE = 200


class VentanaUnirPDF(tk.Toplevel):
    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        aplicar_theme_ventana(
            self,
            title="Unir PDFs",
            size=DEFAULT_SIZE,
            min_size=DEFAULT_MIN_SIZE,
            bg=BG,
            resizable=(True, True),
            modal=True,
            fullscreen=True,
        )

        # ── Estado ────────────────────────────────────────────────────────────
        self.pdf_files:     list[str]      = []
        self._page_cache:   dict[str, int] = {}
        self._drag_start:   int | None     = None
        self._current_page: int            = 0
        self._merging:      bool           = False
        self._t_inicio:     float          = 0.0
        self._tick_id:      str | None     = None

        # search_var se crea ANTES de _build_ui para que el trace no falle
        self._search_var = tk.StringVar()

        self._build_ui()

        # El trace se añade DESPUÉS de que _listbox ya existe
        self._search_var.trace_add("write", lambda *_: self._refresh_list())

        self._refresh_list()

    # =========================================================================
    # Construcción de la UI
    # =========================================================================

    def _build_ui(self):
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True)

        # ── NAVY Sidebar ────────────────────────────────────────
        side = tk.Frame(outer, bg=NAVY, width=270)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        self._logo_img = _cargar_logo(160)
        if self._logo_img:
            tk.Label(side, image=self._logo_img, bg=NAVY).pack(pady=(28, 0))

        tk.Label(side, text="UNIR\nPDFs",
                 font=("Segoe UI", 16, "bold"), fg=WHITE, bg=NAVY,
                 anchor="w", justify="left").pack(padx=24, pady=(16, 8), fill="x")
        tk.Label(side, text="Agrega, reordena y exporta tus archivos PDF.",
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

        # ── Main content ────────────────────────────────────────
        main = tk.Frame(outer, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        self._build_header(main)
        body = tk.Frame(main, bg=BG)
        body.pack(fill="both", expand=True)
        self._build_list_panel(body)   # crea self._listbox
        self._build_sidebar(body)
        self._build_statusbar(main)

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self, parent):
        header = tk.Frame(parent, bg=WHITE, highlightthickness=1,
                          highlightbackground=BORDER)
        header.pack(fill="x", side="top")

        tk.Frame(header, bg=ORANGE, height=3).pack(fill="x")

        inner = tk.Frame(header, bg=WHITE)
        inner.pack(fill="x", padx=20, pady=12)

        # Icono + títulos
        left = tk.Frame(inner, bg=WHITE)
        left.pack(side="left")

        titles = tk.Frame(left, bg=WHITE)
        titles.pack(side="left", padx=(10, 0))
        tk.Label(titles, text="Unir PDFs",
                 font=("Segoe UI", 15, "bold"), fg=TEXT, bg=WHITE).pack(anchor="w")
        tk.Label(titles, text="Agrega, reordena y exporta tus archivos",
                 font=("Segoe UI", 9), fg=MUTED, bg=WHITE).pack(anchor="w")

        # Stats derecha
        right = tk.Frame(inner, bg=WHITE)
        right.pack(side="right")

        self._stat_files = tk.StringVar(value="0")
        self._stat_pages = tk.StringVar(value="0")

        for var, label in ((self._stat_files, "archivos"),
                           (self._stat_pages, "páginas")):
            col = tk.Frame(right, bg=WHITE)
            col.pack(side="left", padx=12)
            tk.Label(col, textvariable=var,
                     font=("Segoe UI", 16, "bold"), fg=ACCENT, bg=WHITE).pack()
            tk.Label(col, text=label,
                     font=("Segoe UI", 9), fg=MUTED, bg=WHITE).pack()

    # ── Panel lista ───────────────────────────────────────────────────────────

    def _build_list_panel(self, parent):
        col = tk.Frame(parent, bg=BG)
        col.pack(side="left", fill="both", expand=True,
                 padx=(16, 8), pady=16)

        # Cabecera de lista
        list_header = tk.Frame(col, bg=BG)
        list_header.pack(fill="x", pady=(0, 6))

        self._list_count_lbl = tk.Label(
            list_header, text="Sin archivos",
            font=("Segoe UI", 9, "bold"), fg=MUTED, bg=BG,
        )
        self._list_count_lbl.pack(side="left")

        # Campo de búsqueda (usa self._search_var ya creado en __init__)
        search_entry = tk.Entry(
            list_header, textvariable=self._search_var,
            font=("Segoe UI", 9), bg=WHITE, fg=TEXT,
            relief="solid", bd=1, width=18,
        )
        _PLACEHOLDER = "🔍  Buscar…"
        search_entry.insert(0, _PLACEHOLDER)

        def _on_focus_in(e):
            if search_entry.get() == _PLACEHOLDER:
                search_entry.delete(0, "end")

        def _on_focus_out(e):
            if not search_entry.get():
                # Silencia el trace mientras se inserta el placeholder
                search_entry.insert(0, _PLACEHOLDER)

        search_entry.bind("<FocusIn>",  _on_focus_in)
        search_entry.bind("<FocusOut>", _on_focus_out)
        search_entry.pack(side="right")

        # Listbox con borde
        list_frame = tk.Frame(col, bg=WHITE, highlightthickness=1,
                              highlightbackground=BORDER)
        list_frame.pack(fill="both", expand=True)

        sb = ttk.Scrollbar(list_frame, orient="vertical")
        sb.pack(side="right", fill="y")

        self._listbox = tk.Listbox(
            list_frame,
            yscrollcommand=sb.set,
            bg=WHITE, fg=TEXT,
            selectbackground=SEL_BG, selectforeground=TEXT,
            activestyle="none",
            font=("Segoe UI", 10),
            bd=0, highlightthickness=0,
            relief="flat", cursor="hand2",
            selectmode="extended",
        )
        self._listbox.pack(side="left", fill="both", expand=True, padx=2, pady=2)
        sb.config(command=self._listbox.yview)

        self._listbox.bind("<ButtonPress-1>",  self._drag_start_cb)
        self._listbox.bind("<B1-Motion>",       self._drag_motion_cb)
        self._listbox.bind("<ButtonRelease-1>", self._drag_end_cb)

        # Paginación
        nav = tk.Frame(col, bg=BG)
        nav.pack(fill="x", pady=(8, 0))

        self._btn_prev = self._nav_btn(nav, "‹", self._page_prev)
        self._btn_prev.pack(side="left")

        self._page_label = tk.Label(nav, text="Pág. 1 / 1",
                                    font=("Segoe UI", 9), fg=MUTED, bg=BG)
        self._page_label.pack(side="left", padx=8)

        self._btn_next = self._nav_btn(nav, "›", self._page_next)
        self._btn_next.pack(side="left")

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self, parent):
        side = tk.Frame(parent, bg=WHITE, highlightthickness=1,
                        highlightbackground=BORDER, width=220)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        inner = tk.Frame(side, bg=WHITE)
        inner.pack(fill="both", expand=True, padx=14, pady=(16, 14))

        # Agregar
        tk.Label(inner, text="AGREGAR",
                 font=("Segoe UI", 8, "bold"), fg=MUTED, bg=WHITE,
                 anchor="w").pack(fill="x", pady=(0, 6))
        self._sb_btn(inner, "＋  Agregar PDFs", self.agregar_archivos,
                     style="primary").pack(fill="x", pady=(0, 12))

        # Ordenar
        tk.Label(inner, text="ORDENAR SELECCIÓN",
                 font=("Segoe UI", 8, "bold"), fg=MUTED, bg=WHITE,
                 anchor="w").pack(fill="x", pady=(0, 4))
        order_row = tk.Frame(inner, bg=WHITE)
        order_row.pack(fill="x", pady=(0, 4))
        self._sb_btn(order_row, "↑  Subir", self.mover_arriba).pack(
            side="left", fill="x", expand=True, padx=(0, 3))
        self._sb_btn(order_row, "↓  Bajar", self.mover_abajo).pack(
            side="left", fill="x", expand=True, padx=(3, 0))

        # Gestión
        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", pady=(8, 6))
        tk.Label(inner, text="GESTIÓN",
                 font=("Segoe UI", 8, "bold"), fg=MUTED, bg=WHITE,
                 anchor="w").pack(fill="x", pady=(0, 4))
        self._sb_btn(inner, "🗑  Eliminar selección", self.eliminar_seleccion,
                     style="secondary").pack(fill="x", pady=(0, 3))
        self._sb_btn(inner, "✖  Limpiar todo", self.limpiar_todo,
                     style="ghost").pack(fill="x", pady=(0, 12))

        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", pady=(0, 10))

        # Nombre de salida
        tk.Label(inner, text="Nombre de salida:",
                 font=("Segoe UI", 9), fg=MUTED, bg=WHITE).pack(anchor="w")
        self._output_name = tk.Entry(
            inner, font=("Segoe UI", 10), bg=BG, fg=TEXT,
            relief="solid", bd=1, insertbackground=ACCENT,
        )
        self._output_name.insert(0, "resultado.pdf")
        self._output_name.pack(fill="x", pady=(3, 12))

        # Exportar
        tk.Label(inner, text="EXPORTAR",
                 font=("Segoe UI", 8, "bold"), fg=MUTED, bg=WHITE,
                 anchor="w").pack(fill="x", pady=(0, 4))
        self._btn_merge = self._sb_btn(
            inner, "💾  Unir y Guardar", self.unir,
            style="primary", big=True,
        )
        self._btn_merge.pack(fill="x", pady=(0, 5))

        self._btn_merge_folders = self._sb_btn(
            inner, "📁  Unir por carpeta", self.unir_por_carpeta,
        )
        self._btn_merge_folders.pack(fill="x", pady=(0, 12))

        # Progress
        self._progress_var = tk.DoubleVar(value=0)
        self._progress = ttk.Progressbar(
            inner, variable=self._progress_var,
            maximum=100, length=170, mode="determinate",
        )
        self._progress_lbl = tk.Label(inner, text="",
                                      font=("Segoe UI", 8), fg=MUTED, bg=WHITE)
        self._timer_lbl = tk.Label(
            inner, text="",
            font=("Segoe UI", 14, "bold"), fg=ACCENT, bg=WHITE,
        )

        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", pady=(8, 10))

        # Volver
        self._sb_btn(inner, "← Volver", self._on_volver,
                     style="ghost").pack(fill="x")

    # ── Barra de estado ───────────────────────────────────────────────────────

    def _build_statusbar(self, parent):
        bar = tk.Frame(parent, bg=WHITE, highlightthickness=1,
                       highlightbackground=BORDER)
        bar.pack(fill="x", side="bottom")

        self._status_dot = tk.Label(bar, text="●", font=("Segoe UI", 9),
                                    fg=BORDER2, bg=WHITE)
        self._status_dot.pack(side="left", padx=(10, 4), pady=6)

        self._status_var = tk.StringVar(value="Agrega archivos PDF para comenzar.")
        tk.Label(bar, textvariable=self._status_var,
                 font=("Segoe UI", 9), fg=MUTED, bg=WHITE,
                 anchor="w").pack(side="left", pady=6)

        right = tk.Frame(bar, bg=WHITE)
        right.pack(side="right", padx=12)

        self._chip_files = tk.Label(right, text="0 archivos",
                                    font=("Segoe UI", 9), fg=MUTED, bg=WHITE)
        self._chip_files.pack(side="left", padx=6)

        tk.Label(right, text="·", font=("Segoe UI", 9),
                 fg=BORDER2, bg=WHITE).pack(side="left")

        self._chip_pages = tk.Label(right, text="0 págs. indexadas",
                                    font=("Segoe UI", 9), fg=MUTED, bg=WHITE)
        self._chip_pages.pack(side="left", padx=6)

    # =========================================================================
    # Helpers de construcción
    # =========================================================================

    def _section_label(self, parent, text: str, top: int = 0):
        if top:
            tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=(top, 6))
        tk.Label(parent, text=text.upper(),
                 font=("Segoe UI", 8, "bold"), fg=MUTED, bg=WHITE,
                 anchor="w").pack(fill="x", pady=(0, 5))

    def _separator(self, parent):
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=10)

    def _sb_btn(self, parent, text, cmd,
                style="normal", big=False) -> tk.Button:
        styles = {
            "primary": dict(bg=ORANGE,        fg=WHITE,  abg="#E06020"),
            "secondary": dict(bg=BLUE,        fg=WHITE,  abg=ACCENT2),
            "ghost":   dict(bg=WHITE,         fg=MUTED,  abg=BG),
            "normal":  dict(bg=BLUE,          fg=WHITE,  abg=ACCENT2),
        }
        s   = styles.get(style, styles["normal"])
        fnt = ("Segoe UI", 11, "bold") if big else ("Segoe UI", 10)
        b   = tk.Button(
            parent, text=text, command=cmd,
            bg=s["bg"], fg=s["fg"], font=fnt,
            pady=8 if big else 6,
            relief="flat", bd=0, cursor="hand2",
            activebackground=s["abg"],
            activeforeground=WHITE if style in ("primary", "secondary", "normal") else s["fg"],
        )
        b.bind("<Enter>", lambda e, _b=b, _bg=s["abg"]: _b.config(bg=_bg))
        b.bind("<Leave>", lambda e, _b=b, _bg=s["bg"]:  _b.config(bg=_bg))
        return b

    def _nav_btn(self, parent, text, cmd) -> tk.Button:
        b = tk.Button(
            parent, text=text, command=cmd,
            font=("Segoe UI", 12), bg=WHITE, fg=TEXT,
            relief="solid", bd=1, padx=8, pady=2,
            cursor="hand2", activebackground=ACCENT_LIGHT,
        )
        b.bind("<Enter>", lambda e: b.config(bg=ACCENT_LIGHT, fg=ACCENT))
        b.bind("<Leave>", lambda e: b.config(bg=WHITE, fg=TEXT))
        return b

    # =========================================================================
    # Paginación
    # =========================================================================

    @property
    def _total_pages(self) -> int:
        return max(1, -(-len(self.pdf_files) // PAGE_SIZE))

    def _page_prev(self):
        if self._current_page > 0:
            self._current_page -= 1
            self._refresh_list()

    def _page_next(self):
        if self._current_page < self._total_pages - 1:
            self._current_page += 1
            self._refresh_list()

    # =========================================================================
    # Refresh lista
    # =========================================================================

    def _refresh_list(self):
        self._listbox.delete(0, "end")

        query = self._search_var.get().strip().lower()

        if query.startswith("🔍"):
            query = ""

        files = [
            p for p in self.pdf_files
            if not query or query in os.path.basename(p).lower()
        ]

        start = self._current_page * PAGE_SIZE
        end = min(start + PAGE_SIZE, len(files))

        for path in files[start:end]:
            self._listbox.insert("end", os.path.basename(path))

        n = len(self.pdf_files)

        total_p = sum(
            v for v in self._page_cache.values()
            if v > 0
        )

        self._stat_files.set(str(n))
        self._stat_pages.set(str(total_p))

        self._chip_files.config(
            text=f"{n} archivos"
        )

        self._chip_pages.config(
            text=f"{total_p} págs. indexadas"
        )

        count_txt = (
            f"{n} archivos cargados"
            if n else
            "Sin archivos"
        )

        self._list_count_lbl.config(
            text=count_txt
        )

        self._page_label.config(
            text=f"Pág. {self._current_page + 1} / {self._total_pages}"
        )

    # =========================================================================
    # Acciones (lógica de negocio INTACTA del original)
    # =========================================================================

    def agregar_archivos(self):
        paths = filedialog.askopenfilenames(
            parent=self,
            title="Seleccionar PDFs",
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos", "*.*")],
        )
        nuevos = [p for p in paths if p not in self.pdf_files]
        if not nuevos:
            return
        self.pdf_files.extend(nuevos)
        self._refresh_list()
        self._btn_merge.config(state="disabled", text="⏳ Indexando…")
        cargar_metadatos_async(
            nuevos,
            self._page_cache,
            on_progress=lambda path, n: self.after(0, self._refresh_list),
            on_done=lambda: self.after(0, self._fin_indexado),
        )

    def eliminar_seleccion(self):
        sel = list(self._listbox.curselection())
        if not sel:
            return
        start = self._current_page * PAGE_SIZE
        for idx in sorted(sel, reverse=True):
            real = start + idx
            if real < len(self.pdf_files):
                self.pdf_files.pop(real)
        if self._current_page >= self._total_pages:
            self._current_page = max(0, self._total_pages - 1)
        self._refresh_list()

    def mover_arriba(self):
        sel = self._listbox.curselection()
        if not sel:
            return
        start = self._current_page * PAGE_SIZE
        idx = start + sel[0]
        if idx == 0:
            return
        self.pdf_files[idx - 1], self.pdf_files[idx] = \
            self.pdf_files[idx], self.pdf_files[idx - 1]
        self._refresh_list()
        new = sel[0] - 1
        if new < 0:
            self._current_page -= 1
            self._refresh_list()
            new = PAGE_SIZE - 1
        self._listbox.selection_set(new)

    def mover_abajo(self):
        sel = self._listbox.curselection()
        if not sel:
            return
        start = self._current_page * PAGE_SIZE
        idx = start + sel[0]
        if idx >= len(self.pdf_files) - 1:
            return
        self.pdf_files[idx + 1], self.pdf_files[idx] = \
            self.pdf_files[idx], self.pdf_files[idx - 1]
        self._refresh_list()
        new = sel[0] + 1
        if new >= PAGE_SIZE:
            self._current_page += 1
            self._refresh_list()
            new = 0
        self._listbox.selection_set(new)

    def limpiar_todo(self):
        if self.pdf_files and messagebox.askyesno(
                "Confirmar", "¿Limpiar toda la lista?", parent=self):
            self.pdf_files.clear()
            self._page_cache.clear()
            self._current_page = 0
            self._refresh_list()

    def unir(self):
        if self._merging:
            return
        if not self.pdf_files:
            messagebox.showwarning("Sin archivos",
                                   "Agrega al menos un PDF.", parent=self)
            return
        name = self._output_name.get().strip() or "resultado.pdf"
        if not name.lower().endswith(".pdf"):
            name += ".pdf"
        destino = filedialog.asksaveasfilename(
            parent=self, title="Guardar PDF unido",
            initialfile=name, defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
        )
        if not destino:
            return
        self._merging = True
        self._btn_merge.config(state="disabled", text="⏳ Uniendo…")
        self._btn_merge_folders.config(state="disabled")
        self._progress_var.set(0)
        self._progress.pack(fill="x", pady=(4, 0))
        self._progress_lbl.pack()
        self._t_inicio = time.perf_counter()
        self._timer_lbl.config(text="00:00")
        self._timer_lbl.pack(pady=(6, 0))
        self._tick()
        unir_pdfs(
            paths=list(self.pdf_files),
            destino=destino,
            on_progress=lambda done, total: self.after(
                0, lambda d=done, t=total: self._on_progreso(d, t)),
            on_done=lambda n_files, n_pages, omitidos, recuperados,
                           paginas_recuperados, auditoria, elapsed: self.after(
                0, lambda f=n_files, p=n_pages, o=omitidos, r=recuperados,
                          pr=paginas_recuperados, a=auditoria, e=elapsed:
                self._on_exito(destino, f, p, o, r, pr, a, e)),
            on_error=lambda err: self.after(
                0, lambda e=err: self._on_error(e)),
        )

    def unir_por_carpeta(self):
        if self._merging:
            return
        root_dir = filedialog.askdirectory(
            parent=self, title="Seleccionar carpeta raíz")
        if not root_dir:
            return
        output_dir = filedialog.askdirectory(
            parent=self, title="Seleccionar carpeta destino")
        if not output_dir:
            return
        if not messagebox.askyesno(
                "Confirmar",
                "Se generará un PDF por cada subcarpeta (primer nivel)\n"
                "usando el nombre de la carpeta.\n\n"
                "Los PDFs se guardarán en la carpeta destino seleccionada.\n\n"
                "¿Deseas continuar?",
                parent=self):
            return
        self._merging = True
        self._btn_merge.config(state="disabled")
        self._btn_merge_folders.config(state="disabled", text="⏳ Uniendo…")
        self._progress_var.set(0)
        self._progress.pack(fill="x", pady=(4, 0))
        self._progress_lbl.pack()
        self._t_inicio = time.perf_counter()
        self._timer_lbl.config(text="00:00")
        self._timer_lbl.pack(pady=(6, 0))
        self._tick()
        unir_pdfs_por_carpeta(
            root_dir=root_dir,
            output_dir=output_dir,
            on_progress=lambda done, total, carpeta, destino: self.after(
                0, lambda d=done, t=total, c=carpeta, dst=destino:
                self._on_progreso_carpetas(d, t, c, dst)),
            on_done=lambda total_carpetas, pdfs_generados, total_paginas,
                           carpetas_sin_pdfs, omitidos_por_carpeta,
                           recuperados_por_carpeta, elapsed: self.after(
                0, lambda tc=total_carpetas, pg=pdfs_generados,
                          tp=total_paginas, cs=carpetas_sin_pdfs,
                          op=omitidos_por_carpeta, rp=recuperados_por_carpeta,
                          e=elapsed:
                self._on_exito_carpetas(tc, pg, tp, cs, op, rp, e)),
            on_error=lambda err: self.after(
                0, lambda e=err: self._on_error(e)),
        )

    def _on_volver(self):
        try:
            try:
                self.grab_release()
            except Exception:
                pass
            parent = self.master if hasattr(self, "master") else None
            self.destroy()
            if parent:
                try:
                    parent.focus_force()
                except Exception:
                    pass
        except Exception as e:
            try:
                messagebox.showerror("Error", f"No se pudo volver: {e}", parent=self)
            except Exception:
                pass

    def _fin_indexado(self):
        self._refresh_list()
        self._btn_merge.config(state="normal", text="💾  Unir y Guardar")

    # =========================================================================
    # Cronómetro
    # =========================================================================

    def _tick(self):
        if not self._merging:
            return
        elapsed = time.perf_counter() - self._t_inicio
        mins, secs = divmod(int(elapsed), 60)
        self._timer_lbl.config(text=f"{mins:02d}:{secs:02d}")
        self._tick_id = self.after(1000, self._tick)

    def _stop_timer(self):
        if self._tick_id:
            self.after_cancel(self._tick_id)
            self._tick_id = None

    # =========================================================================
    # Callbacks de progreso
    # =========================================================================

    def _on_progreso(self, done: int, total: int):
        pct = done / total * 100
        self._progress_var.set(pct)
        self._progress_lbl.config(text=f"{done}/{total} archivos…")
        self._status_var.set(f"Uniendo… {done}/{total} archivos")

    def _on_progreso_carpetas(self, done: int, total: int,
                              carpeta: str, destino: str):
        pct = (done / total * 100) if total else 0
        nombre = os.path.basename(carpeta) or carpeta
        self._progress_var.set(pct)
        self._progress_lbl.config(text=f"{done}/{total} carpetas…")
        self._status_var.set(
            f"Procesando: {nombre} → {os.path.basename(destino)}")

    # =========================================================================
    # Callbacks de éxito / error
    # =========================================================================

    def _on_exito(self, destino, n_files, n_pages, omitidos,
                  recuperados, paginas_recuperados, auditoria, elapsed):
        self._merging = False
        self._stop_timer()
        self._btn_merge.config(state="normal", text="💾  Unir y Guardar")
        self._btn_merge_folders.config(state="normal", text="📁  Unir por carpeta")
        self._progress.pack_forget()
        self._progress_lbl.pack_forget()

        mins, secs = divmod(int(elapsed), 60)
        tiempo_str = f"{mins}m {secs:02d}s" if mins else f"{secs}s"
        self._timer_lbl.config(fg=ACCENT, text=f"✔ {tiempo_str}")

        omitidos_str = (f" · {len(omitidos)} omitido{'s' if len(omitidos) != 1 else ''}"
                        if omitidos else "")
        self._status_var.set(
            f"✔ Guardado: {os.path.basename(destino)}  "
            f"({n_files} archivos · {n_pages} páginas{omitidos_str} · {tiempo_str})"
        )
        self._status_dot.config(fg=SUCCESS)

        ruta_auditoria = None
        try:
            ruta_auditoria = exportar_auditoria_unificacion(auditoria, destino)
        except Exception as e:
            messagebox.showwarning(
                "Auditoría",
                f"No se pudo generar la auditoría en Excel:\n{e}",
                parent=self,
            )

        self._mostrar_detalle_omitidos(omitidos, recuperados, paginas_recuperados)

        size = tamaño_bytes(destino)
        if es_pesado(destino, UMBRAL_DEFECTO):
            if messagebox.askyesno(
                    "Archivo pesado",
                    f"El PDF resultante pesa {_fmt_bytes(size)}, "
                    f"lo que supera el umbral de {_fmt_bytes(UMBRAL_DEFECTO)}.\n\n"
                    f"¿Deseas comprimirlo ahora?",
                    parent=self):
                VentanaComprimirPDF(self, archivo_inicial=destino)
                return

        messagebox.showinfo(
            "¡Listo!",
            f"PDF guardado:\n{destino}\n\n"
            f"📄 {n_pages} páginas de {n_files} archivos"
            f"{omitidos_str}\n"
            f"⏱ Tiempo total: {tiempo_str}\n"
            f"📊 Auditoría: {ruta_auditoria or 'no disponible'}",
            parent=self,
        )

    def _on_exito_carpetas(self, total_carpetas, pdfs_generados, total_paginas,
                           carpetas_sin_pdfs, omitidos_por_carpeta,
                           recuperados_por_carpeta, elapsed):
        self._merging = False
        self._stop_timer()
        self._btn_merge.config(state="normal", text="💾  Unir y Guardar")
        self._btn_merge_folders.config(state="normal", text="📁  Unir por carpeta")
        self._progress.pack_forget()
        self._progress_lbl.pack_forget()

        mins, secs = divmod(int(elapsed), 60)
        tiempo_str = f"{mins}m {secs:02d}s" if mins else f"{secs}s"
        self._timer_lbl.config(fg=ACCENT, text=f"✔ {tiempo_str}")

        sin_pdfs_str = (f" · {len(carpetas_sin_pdfs)} sin PDF"
                        if carpetas_sin_pdfs else "")
        self._status_var.set(
            f"✔ Uniones por carpeta completadas: "
            f"{pdfs_generados}/{total_carpetas} PDFs"
            f" · {total_paginas} páginas{sin_pdfs_str} · {tiempo_str}"
        )
        self._status_dot.config(fg=SUCCESS)

        if carpetas_sin_pdfs or omitidos_por_carpeta or recuperados_por_carpeta:
            self._mostrar_detalle_carpetas(
                carpetas_sin_pdfs, omitidos_por_carpeta, recuperados_por_carpeta)

        messagebox.showinfo(
            "¡Listo!",
            f"Proceso finalizado.\n\n"
            f"Carpetas procesadas: {total_carpetas}\n"
            f"PDFs generados: {pdfs_generados}\n"
            f"Total de páginas: {total_paginas}\n"
            f"Tiempo total: {tiempo_str}",
            parent=self,
        )

    def _on_error(self, err: Exception):
        self._merging = False
        self._stop_timer()
        self._btn_merge.config(state="normal", text="💾  Unir y Guardar")
        self._btn_merge_folders.config(state="normal", text="📁  Unir por carpeta")
        self._progress.pack_forget()
        self._progress_lbl.pack_forget()
        self._timer_lbl.pack_forget()
        messagebox.showerror("Error",
                             f"No se pudo unir los PDFs:\n{err}", parent=self)

    # =========================================================================
    # Ventanas de detalle
    # =========================================================================

    def _mostrar_detalle_omitidos(self, omitidos, recuperados, paginas_recuperados):
        win = tk.Toplevel(self)
        win.title("Detalle de recuperación y omitidos")
        win.configure(bg=BG)
        win.geometry("720x420")
        win.minsize(600, 360)
        win.transient(self)
        win.grab_set()

        tk.Label(win, text="Detalle de la ejecución",
                 font=("Segoe UI", 11, "bold"), fg=TEXT, bg=BG).pack(
            anchor="w", padx=12, pady=(12, 6))

        texto = ScrolledText(win, height=16, font=("Consolas", 9))
        texto.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        texto.insert("end", "Recuperados con pypdf:\n")
        if recuperados:
            for path in recuperados:
                pag = paginas_recuperados.get(path)
                suf = (f" (página {pag})"
                       if isinstance(pag, int) and pag > 0 else "")
                texto.insert("end", f"  - {path}{suf}\n")
        else:
            texto.insert("end", "  (ninguno)\n")

        texto.insert("end", "\nArchivos omitidos:\n")
        if omitidos:
            for path in omitidos:
                texto.insert("end", f"  - {path}\n")
        else:
            texto.insert("end", "  (ninguno)\n")

        texto.configure(state="disabled")
        tk.Button(win, text="Cerrar", font=("Segoe UI", 9),
                  bg=BORDER, fg=TEXT, relief="flat", padx=12, pady=6,
                  command=win.destroy).pack(pady=(0, 12))
        self.wait_window(win)

    def _mostrar_detalle_carpetas(self, carpetas_sin_pdfs,
                                  omitidos_por_carpeta, recuperados_por_carpeta):
        win = tk.Toplevel(self)
        win.title("Detalle por carpeta")
        win.configure(bg=BG)
        win.geometry("760x460")
        win.minsize(640, 380)
        win.transient(self)
        win.grab_set()

        tk.Label(win, text="Detalle de la ejecución",
                 font=("Segoe UI", 11, "bold"), fg=TEXT, bg=BG).pack(
            anchor="w", padx=12, pady=(12, 6))

        texto = ScrolledText(win, height=16, font=("Consolas", 9))
        texto.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        texto.insert("end", "Carpetas sin PDFs:\n")
        for path in (carpetas_sin_pdfs or ["  (ninguna)"]):
            texto.insert("end", f"  - {path}\n")

        texto.insert("end", "\nArchivos omitidos por carpeta:\n")
        if omitidos_por_carpeta:
            for carpeta, omitidos in omitidos_por_carpeta.items():
                texto.insert("end", f"  {carpeta}:\n")
                for path in omitidos:
                    texto.insert("end", f"    - {path}\n")
        else:
            texto.insert("end", "  (ninguno)\n")

        texto.insert("end", "\nRecuperados por carpeta (pypdf):\n")
        if recuperados_por_carpeta:
            for carpeta, recuperados in recuperados_por_carpeta.items():
                texto.insert("end", f"  {carpeta}:\n")
                for path in recuperados:
                    texto.insert("end", f"    - {path}\n")
        else:
            texto.insert("end", "  (ninguno)\n")

        texto.configure(state="disabled")
        tk.Button(win, text="Cerrar", font=("Segoe UI", 9),
                  bg=BORDER, fg=TEXT, relief="flat", padx=12, pady=6,
                  command=win.destroy).pack(pady=(0, 12))
        self.wait_window(win)

    # =========================================================================
    # Drag & drop (idéntico al original)
    # =========================================================================

    def _drag_start_cb(self, event):
        self._drag_start = self._listbox.nearest(event.y)

    def _drag_motion_cb(self, event):
        if self._drag_start is None:
            return
        lb_idx = self._listbox.nearest(event.y)
        if lb_idx == self._drag_start:
            return
        start    = self._current_page * PAGE_SIZE
        real_src = start + self._drag_start
        real_dst = start + lb_idx
        if 0 <= real_dst < len(self.pdf_files):
            self.pdf_files.insert(real_dst, self.pdf_files.pop(real_src))
            self._drag_start = lb_idx
            self._refresh_list()
            self._listbox.selection_set(lb_idx)

    def _drag_end_cb(self, _event):
        self._drag_start = None