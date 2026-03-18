"""
features/ordernar_pdf/ui.py
Ventana Toplevel del agrupador/unificador de PDFs.
Toda la lógica de negocio vive en core.py.
"""
import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from features.ordernar_pdf.core.agrupar import cargar_metadatos_async, unir_pdfs

# ── Paleta (alineada con el resto de la app) ──────────────────────────────────
BG      = "#F0F4F8"
WHITE   = "#FFFFFF"
ACCENT  = "#2B6CB0"
ACCENT2 = "#1A4A8A"
TEXT    = "#2D3748"
MUTED   = "#718096"
DANGER  = "#C53030"
BORDER  = "#E2E8F0"
SEL_BG  = "#BEE3F8"

PAGE_SIZE = 200   # items visibles por página


class VentanaUnirPDF(tk.Toplevel):
    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        self.title("Unir PDFs")
        self.geometry("820x580")
        self.minsize(700, 480)
        self.configure(bg=BG)
        self.resizable(True, True)
        self.grab_set()             # modal

        # Estado
        self.pdf_files:    list[str]      = []
        self._page_cache:  dict[str, int] = {}
        self._drag_start:  int | None     = None
        self._current_page: int           = 0
        self._merging:     bool           = False
        self._t_inicio:    float          = 0.0
        self._tick_id:     str | None     = None   # id del after() del cronómetro

        self._build_ui()
        self._refresh_list()

    # ── Construcción de la UI ─────────────────────────────────────────────────
    def _build_ui(self):
        # Cabecera
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=24, pady=(20, 6))
        tk.Label(header, text="📄 Unir PDFs",
                 font=("Segoe UI", 16, "bold"), fg=ACCENT, bg=BG).pack(side="left")
        tk.Label(header, text="une, reordena y exporta",
                 font=("Segoe UI", 9), fg=MUTED, bg=BG).pack(side="left", padx=10)

        # Panel central
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=24, pady=6)
        self._build_list_panel(main)
        self._build_sidebar(main)

        # Barra de estado
        bar = tk.Frame(self, bg=WHITE, highlightthickness=1,
                       highlightbackground=BORDER)
        bar.pack(fill="x", side="bottom")
        self._status_var = tk.StringVar(value="Agrega archivos PDF para comenzar.")
        tk.Label(bar, textvariable=self._status_var,
                 font=("Segoe UI", 9), fg=MUTED, bg=WHITE,
                 anchor="w", padx=12).pack(side="left", pady=5)
        self._total_label = tk.Label(bar, text="",
                                     font=("Segoe UI", 9), fg=MUTED, bg=WHITE,
                                     anchor="e", padx=12)
        self._total_label.pack(side="right", pady=5)

    def _build_list_panel(self, parent):
        col = tk.Frame(parent, bg=BG)
        col.pack(side="left", fill="both", expand=True)

        # Paginación
        nav = tk.Frame(col, bg=BG)
        nav.pack(fill="x", pady=(0, 4))
        self._btn_prev = self._btn(nav, "◀", self._page_prev,
                                   font=("Segoe UI", 9), padx=8, pady=2)
        self._btn_prev.pack(side="left")
        self._page_label = tk.Label(nav, text="Pág. 1 / 1",
                                    font=("Segoe UI", 9), fg=MUTED, bg=BG)
        self._page_label.pack(side="left", padx=8)
        self._btn_next = self._btn(nav, "▶", self._page_next,
                                   font=("Segoe UI", 9), padx=8, pady=2)
        self._btn_next.pack(side="left")

        # Listbox
        frame = tk.Frame(col, bg=WHITE, highlightthickness=1,
                         highlightbackground=BORDER)
        frame.pack(fill="both", expand=True)
        sb = ttk.Scrollbar(frame, orient="vertical")
        sb.pack(side="right", fill="y")
        self._listbox = tk.Listbox(
            frame, yscrollcommand=sb.set,
            bg=WHITE, fg=TEXT,
            selectbackground=SEL_BG, selectforeground=TEXT,
            activestyle="none", font=("Segoe UI", 10),
            bd=0, highlightthickness=0, relief="flat", cursor="hand2",
        )
        self._listbox.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        sb.config(command=self._listbox.yview)

        self._listbox.bind("<ButtonPress-1>",  self._drag_start_cb)
        self._listbox.bind("<B1-Motion>",       self._drag_motion_cb)
        self._listbox.bind("<ButtonRelease-1>", self._drag_end_cb)

    def _build_sidebar(self, parent):
        side = tk.Frame(parent, bg=BG)
        side.pack(side="left", fill="y", padx=(12, 0))
        cfg = dict(width=18, font=("Segoe UI", 10), pady=6)

        self._btn(side, "＋  Agregar PDFs",  self.agregar_archivos,
                  bg=ACCENT, fg="white", **cfg).pack(pady=4)
        self._btn(side, "🗑  Eliminar",       self.eliminar_seleccion,
                  fg=DANGER, **cfg).pack(pady=4)
        self._btn(side, "↑  Subir",          self.mover_arriba, **cfg).pack(pady=4)
        self._btn(side, "↓  Bajar",          self.mover_abajo, **cfg).pack(pady=4)
        self._btn(side, "✖  Limpiar todo",   self.limpiar_todo,
                  fg=MUTED, **cfg).pack(pady=4)

        ttk.Separator(side, orient="horizontal").pack(fill="x", pady=10)

        tk.Label(side, text="Nombre de salida:",
                 font=("Segoe UI", 9), fg=MUTED, bg=BG).pack(anchor="w")
        self._output_name = tk.Entry(
            side, font=("Segoe UI", 10), bg=WHITE, fg=TEXT,
            relief="solid", bd=1,
        )
        self._output_name.insert(0, "resultado.pdf")
        self._output_name.pack(fill="x", pady=(2, 10))

        self._btn_merge = self._btn(
            side, "💾  Unir y Guardar", self.unir,
            bg=ACCENT, fg="white",
            width=18, font=("Segoe UI", 11, "bold"), pady=8,
        )
        self._btn_merge.pack(pady=4)

        # Progreso (oculto hasta que se use)
        self._progress_var = tk.DoubleVar(value=0)
        self._progress = ttk.Progressbar(
            side, variable=self._progress_var,
            maximum=100, length=160, mode="determinate",
        )
        self._progress_lbl = tk.Label(side, text="",
                                      font=("Segoe UI", 8), fg=MUTED, bg=BG)

        # Cronómetro (oculto hasta que se use)
        self._timer_lbl = tk.Label(
            side, text="",
            font=("Segoe UI", 13, "bold"), fg=ACCENT, bg=BG,
        )

    # ── Helper botón ──────────────────────────────────────────────────────────
    def _btn(self, parent, text, cmd,
             bg=WHITE, fg=TEXT, **kwargs) -> tk.Button:
        b = tk.Button(parent, text=text, command=cmd,
                      bg=bg, fg=fg, relief="flat", bd=0, cursor="hand2",
                      activebackground=ACCENT2, activeforeground="white",
                      **kwargs)
        b.bind("<Enter>", lambda e: b.config(
            bg=ACCENT2 if bg == ACCENT else BORDER))
        b.bind("<Leave>", lambda e: b.config(bg=bg))
        return b

    # ── Paginación ────────────────────────────────────────────────────────────
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

    # ── Actualizar lista ──────────────────────────────────────────────────────
    def _refresh_list(self):
        lb = self._listbox
        lb.delete(0, "end")

        start = self._current_page * PAGE_SIZE
        end   = min(start + PAGE_SIZE, len(self.pdf_files))
        for i, path in enumerate(self.pdf_files[start:end], start + 1):
            name  = os.path.basename(path)
            pages = self._page_cache.get(path)
            suffix = "…" if pages is None else ("⚠ error" if pages == -1 else f"{pages} pág.")
            lb.insert("end", f"  {i:04d}.  {name}  ({suffix})")

        tp = self._total_pages
        cp = self._current_page
        self._page_label.config(text=f"Pág. {cp + 1} / {tp}")
        self._btn_prev.config(state="normal" if cp > 0 else "disabled")
        self._btn_next.config(state="normal" if cp < tp - 1 else "disabled")

        n = len(self.pdf_files)
        total_p = sum(v for v in self._page_cache.values() if v > 0)
        self._total_label.config(
            text=f"{n} archivos  |  {total_p} págs. indexadas")
        self._status_var.set(
            f"{n} archivo{'s' if n != 1 else ''} cargado{'s' if n != 1 else ''}."
            if n else "Agrega archivos PDF para comenzar."
        )

    # ── Acciones públicas ─────────────────────────────────────────────────────
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

        # Delega la lectura de metadatos al core (no bloquea la UI)
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
            self.pdf_files[idx], self.pdf_files[idx + 1]
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
        self._progress_var.set(0)
        self._progress.pack(fill="x", pady=(4, 0))
        self._progress_lbl.pack()

        # Arrancar cronómetro
        self._t_inicio = time.perf_counter()
        self._timer_lbl.config(text="00:00")
        self._timer_lbl.pack(pady=(6, 0))
        self._tick()

        # Delega la unión al core
        unir_pdfs(
            paths=list(self.pdf_files),
            destino=destino,
            on_progress=lambda done, total: self.after(
                0, lambda d=done, t=total: self._on_progreso(d, t)),
            on_done=lambda n_files, n_pages, elapsed: self.after(
                0, lambda f=n_files, p=n_pages, e=elapsed: self._on_exito(destino, f, p, e)),
            on_error=lambda err: self.after(
                0, lambda e=err: self._on_error(e)),
        )

    def _fin_indexado(self):
        self._refresh_list()
        self._btn_merge.config(state="normal", text="💾  Unir y Guardar")

    # ── Cronómetro ────────────────────────────────────────────────────────────
    def _tick(self):
        """Se llama cada segundo mientras _merging sea True."""
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

    # ── Callbacks de progreso ─────────────────────────────────────────────────
    def _on_progreso(self, done: int, total: int):
        pct = done / total * 100
        self._progress_var.set(pct)
        self._progress_lbl.config(text=f"{done}/{total} archivos…")

    def _on_exito(self, destino: str, n_files: int, n_pages: int, elapsed: float):
        self._merging = False
        self._stop_timer()
        self._btn_merge.config(state="normal", text="💾  Unir y Guardar")
        self._progress.pack_forget()
        self._progress_lbl.pack_forget()

        mins, secs = divmod(int(elapsed), 60)
        tiempo_str = f"{mins}m {secs:02d}s" if mins else f"{secs}s"
        self._timer_lbl.config(fg=ACCENT, text=f"✔ {tiempo_str}")

        self._status_var.set(
            f"✔ Guardado: {os.path.basename(destino)}  "
            f"({n_files} archivos · {n_pages} páginas · {tiempo_str})"
        )
        messagebox.showinfo(
            "¡Listo!",
            f"PDF guardado:\n{destino}\n\n"
            f"📄 {n_pages} páginas de {n_files} archivos\n"
            f"⏱ Tiempo total: {tiempo_str}",
            parent=self,
        )

    def _on_error(self, err: Exception):
        self._merging = False
        self._stop_timer()
        self._btn_merge.config(state="normal", text="💾  Unir y Guardar")
        self._progress.pack_forget()
        self._progress_lbl.pack_forget()
        self._timer_lbl.pack_forget()
        messagebox.showerror("Error", f"No se pudo unir los PDFs:\n{err}", parent=self)

    # ── Drag & drop ───────────────────────────────────────────────────────────
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