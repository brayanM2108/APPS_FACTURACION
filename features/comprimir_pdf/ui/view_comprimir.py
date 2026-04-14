"""
features/comprimir_pdf/ui/view_comprimir.py
Ventana standalone para comprimir un PDF individual.
Toda la logica vive en comprimir_service.py.
"""
import logging
import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from ui.theme import aplicar_theme_ventana, BG as THEME_BG

from features.comprimir_pdf.core.comprimir_service import (
    NIVELES,
    UMBRAL_DEFECTO,
    _fmt_bytes,
    comprimir_pdf,
    resumen_compresion,
    tamaño_bytes,
)

# Paleta
BG = "#F0F4F8"
WHITE = "#FFFFFF"
ACCENT = "#2B6CB0"
ACCENT2 = "#1A4A8A"
TEXT = "#2D3748"
MUTED = "#718096"
SUCCESS = "#276749"
BORDER = "#E2E8F0"
WARN_BG = "#FFFBEB"
WARN_FG = "#B7791F"


class _TkTextLogHandler(logging.Handler):
    """Handler que envia logs a un Text de Tk de forma segura desde cualquier hilo."""

    def __init__(self, text_widget: tk.Text):
        super().__init__()
        self._text = text_widget
        self.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S"))

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)

        def append() -> None:
            if not self._text.winfo_exists():
                return
            self._text.configure(state="normal")
            self._text.insert("end", msg + "\n")
            self._text.see("end")
            self._text.configure(state="disabled")

        try:
            self._text.after(0, append)
        except Exception:
            # Si la UI ya cerro, ignorar silenciosamente.
            pass


class VentanaComprimirPDF(tk.Toplevel):
    def __init__(self, parent: tk.Misc, archivo_inicial: str = ""):
        super().__init__(parent)
        # aplicar theme central
        aplicar_theme_ventana(
            self,
            title="Comprimir PDF",
            size=(600, 620),
            min_size=None,
            bg=THEME_BG,
            resizable=(False, False),
            modal=True,
        )

        self._comprimiendo = False
        self._t_inicio = 0.0
        self._tick_id: str | None = None

        self._log_handler: _TkTextLogHandler | None = None
        self._service_logger = logging.getLogger("features.comprimir_pdf.core.comprimir_service")

        self._build_ui()
        self._configurar_logs()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        if archivo_inicial:
            self._set_archivo(archivo_inicial)

    # UI
    def _build_ui(self):
        # Cabecera
        h = tk.Frame(self, bg=THEME_BG)
        h.pack(fill="x", padx=24, pady=(20, 4))
        tk.Label(
            h,
            text="Comprimir PDF",
            font=("Segoe UI", 16, "bold"),
            fg=ACCENT,
            bg=BG,
        ).pack(side="left")

        body = tk.Frame(self, bg=THEME_BG)
        body.pack(fill="both", expand=True, padx=24, pady=8)

        # Archivo origen
        tk.Label(body, text="Archivo a comprimir:", font=("Segoe UI", 9), fg=MUTED, bg=THEME_BG).pack(anchor="w")
        row = tk.Frame(body, bg=BG)
        row.pack(fill="x", pady=(2, 10))
        self._var_origen = tk.StringVar()
        tk.Entry(
            row,
            textvariable=self._var_origen,
            font=("Segoe UI", 9),
            bg=WHITE,
            fg=TEXT,
            relief="solid",
            bd=1,
            state="readonly",
        ).pack(side="left", fill="x", expand=True)
        self._btn(row, "Examinar...", self._elegir_origen, padx=10, pady=3).pack(side="left", padx=(6, 0))

        # Advertencia de tamaño
        self._warn_frame = tk.Frame(body, bg=WARN_BG, highlightthickness=1, highlightbackground="#F6E05E")
        self._warn_lbl = tk.Label(
            self._warn_frame,
            text="",
            font=("Segoe UI", 9),
            fg=WARN_FG,
            bg=WARN_BG,
            anchor="w",
            padx=10,
        )
        self._warn_lbl.pack(fill="x", pady=6)

        # Umbral configurable
        umbral_row = tk.Frame(body, bg=BG)
        umbral_row.pack(fill="x", pady=(0, 10))
        tk.Label(umbral_row, text="Umbral muy pesado:", font=("Segoe UI", 9), fg=MUTED, bg=BG).pack(side="left")
        self._umbral_var = tk.IntVar(value=UMBRAL_DEFECTO // (1024 * 1024))
        tk.Spinbox(
            umbral_row,
            from_=1,
            to=1024,
            textvariable=self._umbral_var,
            font=("Segoe UI", 9),
            width=5,
            bg=WHITE,
            relief="solid",
            bd=1,
            command=self._actualizar_advertencia,
        ).pack(side="left", padx=6)
        tk.Label(umbral_row, text="MB", font=("Segoe UI", 9), fg=MUTED, bg=BG).pack(side="left")

        # Nivel de compresion
        tk.Label(body, text="Nivel de compresion:", font=("Segoe UI", 9), fg=MUTED, bg=BG).pack(anchor="w")
        self._nivel_var = tk.StringVar(value="Medio")
        nivel_row = tk.Frame(body, bg=BG)
        nivel_row.pack(fill="x", pady=(2, 14))
        for nivel, desc in [
            ("Bajo", "calidad alta, poco ahorro"),
            ("Medio", "equilibrio recomendado"),
            ("Alto", "maximo ahorro, menor calidad"),
        ]:
            tk.Radiobutton(
                nivel_row,
                text=f"{nivel}  ({desc})",
                variable=self._nivel_var,
                value=nivel,
                font=("Segoe UI", 9),
                fg=TEXT,
                bg=BG,
                activebackground=BG,
                selectcolor=WHITE,
            ).pack(anchor="w")

        # Progreso + cronometro
        self._progress_var = tk.DoubleVar(value=0)
        self._progress = ttk.Progressbar(body, variable=self._progress_var, maximum=100, mode="determinate")
        self._progress_lbl = tk.Label(body, text="", font=("Segoe UI", 8), fg=MUTED, bg=BG)
        self._timer_lbl = tk.Label(body, text="", font=("Segoe UI", 13, "bold"), fg=ACCENT, bg=BG)

        # Resultado
        self._result_lbl = tk.Label(
            body,
            text="",
            font=("Segoe UI", 9),
            fg=SUCCESS,
            bg=BG,
            wraplength=520,
            justify="left",
        )

        # Boton principal
        self._btn_comprimir = self._btn(
            body,
            "Comprimir",
            self._comprimir,
            bg=ACCENT,
            fg="white",
            font=("Segoe UI", 11, "bold"),
            pady=8,
            width=20,
        )
        self._btn_comprimir.pack(pady=(4, 8))
        self._btn_comprimir.config(state="disabled")

        # Panel de logs
        tk.Label(body, text="Logs de proceso:", font=("Segoe UI", 9, "bold"), fg=TEXT, bg=BG).pack(anchor="w")
        log_wrap = tk.Frame(body, bg=BG)
        log_wrap.pack(fill="both", expand=True, pady=(4, 0))

        self._btn(body, "Volver", self._on_volver,
                  fg=MUTED, width=18, font=("Segoe UI", 9), pady=6).pack(pady=(8, 4))

        self._log_text = tk.Text(
            log_wrap,
            height=10,
            font=("Consolas", 9),
            bg=WHITE,
            fg=TEXT,
            relief="solid",
            bd=1,
            state="disabled",
            wrap="word",
        )

        scroll = ttk.Scrollbar(log_wrap, orient="vertical", command=self._log_text.yview)
        self._log_text.configure(yscrollcommand=scroll.set)
        self._log_text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")





    # Helper botón
    def _btn(self, parent, text, cmd, bg=WHITE, fg=TEXT, **kw):
        b = tk.Button(
            parent,
            text=text,
            command=cmd,
            bg=bg,
            fg=fg,
            relief="flat",
            bd=0,
            cursor="hand2",
            activebackground=ACCENT2,
            activeforeground="white",
            **kw,
        )
        b.bind("<Enter>", lambda e: b.config(bg=ACCENT2 if bg == ACCENT else BORDER))
        b.bind("<Leave>", lambda e: b.config(bg=bg))
        return b

    # Logs
    def _configurar_logs(self):
        self._log_handler = _TkTextLogHandler(self._log_text)
        self._log_handler.setLevel(logging.DEBUG)

        # Evita duplicados si se abre/cierra la ventana varias veces
        for h in list(self._service_logger.handlers):
            if isinstance(h, _TkTextLogHandler):
                self._service_logger.removeHandler(h)

        self._service_logger.addHandler(self._log_handler)
        self._service_logger.setLevel(logging.DEBUG)
        self._service_logger.propagate = False
        self._append_log("Logger conectado al servicio de compresion.")

    def _remover_logs(self):
        if self._log_handler is not None:
            try:
                self._service_logger.removeHandler(self._log_handler)
            except Exception:
                pass
            self._log_handler = None

    def _append_log(self, text: str):
        self._log_text.configure(state="normal")
        self._log_text.insert("end", text + "\n")
        self._log_text.see("end")
        self._log_text.configure(state="disabled")

    # Seleccion de archivo
    def _elegir_origen(self):
        path = filedialog.askopenfilename(parent=self, title="Seleccionar PDF", filetypes=[("PDF", "*.pdf")])
        if path:
            self._set_archivo(path)

    def _set_archivo(self, path: str):
        self._var_origen.set(path)
        self._actualizar_advertencia()
        self._btn_comprimir.config(state="normal")
        self._result_lbl.pack_forget()
        self._append_log(f"Archivo seleccionado: {path}")

    def _umbral_bytes(self) -> int:
        return max(1, self._umbral_var.get()) * 1024 * 1024

    def _actualizar_advertencia(self):
        path = self._var_origen.get()
        if not path:
            self._warn_frame.pack_forget()
            return

        size = tamaño_bytes(path)
        umbral = self._umbral_bytes()

        if size >= umbral:
            self._warn_lbl.config(
                text=f"Archivo pesado: {_fmt_bytes(size)} (supera el umbral de {_fmt_bytes(umbral)})"
            )
            self._warn_frame.pack(fill="x", pady=(0, 10))
        else:
            self._warn_frame.pack_forget()

    # Compresion
    def _comprimir(self):
        if self._comprimiendo:
            return

        origen = self._var_origen.get()
        if not origen:
            return

        destino = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar PDF comprimido",
            initialfile=os.path.splitext(os.path.basename(origen))[0] + "_comprimido.pdf",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
        )
        if not destino:
            return

        self._comprimiendo = True
        self._btn_comprimir.config(state="disabled", text="Comprimiendo...")
        self._result_lbl.pack_forget()
        self._progress_var.set(0)
        self._progress.pack(fill="x", pady=(8, 2))
        self._progress_lbl.config(text="Iniciando...")
        self._progress_lbl.pack()
        self._t_inicio = time.perf_counter()
        self._timer_lbl.config(text="00:00", fg=ACCENT)
        self._timer_lbl.pack()
        self._tick()

        self._append_log(f"Inicio compresion | nivel={self._nivel_var.get()} | destino={destino}")

        comprimir_pdf(
            origen=origen,
            destino=destino,
            nivel=self._nivel_var.get(),
            on_progress=lambda d, t: self.after(0, lambda a=d, b=t: self._on_progreso(a, b)),
            on_done=lambda ba, bd, el: self.after(0, lambda a=ba, b=bd, e=el: self._on_exito(destino, a, b, e)),
            on_error=lambda err: self.after(0, lambda e=err: self._on_error(e)),
        )

    # Cronometro
    def _tick(self):
        if not self._comprimiendo:
            return
        m, s = divmod(int(time.perf_counter() - self._t_inicio), 60)
        self._timer_lbl.config(text=f"{m:02d}:{s:02d}")
        self._tick_id = self.after(1000, self._tick)

    def _stop_timer(self):
        if self._tick_id:
            self.after_cancel(self._tick_id)
            self._tick_id = None

    # Callbacks
    def _on_progreso(self, done: int, total: int):
        if total <= 0:
            self._progress_var.set(0)
            self._progress_lbl.config(text="Procesando...")
            return

        pct = (done / total) * 100
        self._progress_var.set(pct)
        self._progress_lbl.config(text=f"Pagina {done}/{total} ({pct:.1f}%)")

    def _on_exito(self, destino: str, bytes_antes: int, bytes_despues: int, elapsed: float):
        self._comprimiendo = False
        self._stop_timer()

        m, s = divmod(int(elapsed), 60)
        tiempo = f"{m}m {s:02d}s" if m else f"{s}s"

        self._timer_lbl.config(fg=SUCCESS, text=f"OK {tiempo}")
        self._btn_comprimir.config(state="normal", text="Comprimir")
        self._progress.pack_forget()
        self._progress_lbl.pack_forget()

        resumen = resumen_compresion(bytes_antes, bytes_despues)
        self._result_lbl.config(text=f"Guardado en {os.path.basename(destino)}\n{resumen}", fg=SUCCESS)
        self._result_lbl.pack(pady=(6, 0))

        self._append_log(f"Exito: {resumen}")

    def _on_error(self, err: Exception):
        self._comprimiendo = False
        self._stop_timer()
        self._btn_comprimir.config(state="normal", text="Comprimir")
        self._progress.pack_forget()
        self._progress_lbl.pack_forget()
        self._timer_lbl.pack_forget()

        self._append_log(f"ERROR: {err}")
        messagebox.showerror("Error al comprimir", str(err), parent=self)

    def _on_close(self):
        self._remover_logs()
        self.destroy()

    def _on_volver(self):
        """Cerrar la ventana actual y devolver el foco al padre."""
        try:
            # liberar modal si aplica
            try:
                self.grab_release()
            except Exception:
                pass
            parent = self.master if hasattr(self, 'master') else None
            self.destroy()
            if parent:
                try:
                    parent.focus_force()
                except Exception:
                    pass
        except Exception as e:
            # En caso de error, mostrar diálogo y no impedir el cierre
            try:
                from tkinter import messagebox
                messagebox.showerror("Error", f"No se pudo volver: {e}", parent=self)
            except Exception:
                pass
