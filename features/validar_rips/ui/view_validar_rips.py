import io
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

import cairosvg
from PIL import Image, ImageTk

from features.validar_rips.core.validar_rips_service import CONFIG, ValidadorRipsService
from ui.theme import aplicar_theme_ventana, DEFAULT_SIZE, BG, WHITE, TEXT, MUTED, BORDER, ACCENT, ACCENT2, NAVY, ORANGE, SKY, BLUE


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
        icono_path = Path(__file__).parents[3] / "ui" / "assets" / "transponer_rips.svg"
        if icono_path.exists():
            png_data = cairosvg.svg2png(url=str(icono_path), output_width=size, output_height=size)
            img = Image.open(io.BytesIO(png_data))
            return ImageTk.PhotoImage(img)
    except Exception:
        pass
    return None


def _configurar_estilos():
    style = ttk.Style()
    style.configure("Rounded.TEntry",
                    fieldbackground=WHITE, foreground=TEXT, padding=6)
    style.configure("Secondary.TButton",
                    foreground=TEXT, padding=(14, 6))
    style.map("Secondary.TButton",
              background=[("active", "#F1F5F9")])


def _round_rect(c, x1, y1, x2, y2, r, **kw):
    c.create_arc(x1, y1, x1 + r * 2, y1 + r * 2, start=90, extent=90, **kw)
    c.create_arc(x2 - r * 2, y1, x2, y1 + r * 2, start=0, extent=90, **kw)
    c.create_arc(x1, y2 - r * 2, x1 + r * 2, y2, start=180, extent=90, **kw)
    c.create_arc(x2 - r * 2, y2 - r * 2, x2, y2, start=270, extent=90, **kw)
    c.create_rectangle(x1 + r, y1, x2 - r, y2 + 1, **kw)
    c.create_rectangle(x1, y1 + r, x2 + 1, y2 - r, **kw)


def _crear_btn(parent, text, comando, bg=ORANGE, fg=WHITE, width=150, outline=False):
    c = tk.Canvas(parent, bg=BG, highlightthickness=0, width=width, height=44)
    c.pack_propagate(False)
    _btn_draw(c, width, 44, text, bg, fg, outline)
    c.bind("<Button-1>", lambda e: comando())
    c.bind("<Enter>", lambda e: _btn_draw(c, width, 44, text, BG if outline else bg, fg, outline))
    c.bind("<Leave>", lambda e: _btn_draw(c, width, 44, text, bg, fg, outline))
    return c


def _btn_draw(c, w, h, text, bg, fg, outline):
    c.delete("all")
    kw = {"fill": bg, "outline": BORDER, "width": 1} if outline else {"fill": bg, "outline": ""}
    _round_rect(c, 0, 0, w, h, 14, **kw)
    c.create_text(w // 2, h // 2, text=text, fill=fg,
                  font=("Segoe UI", 11, "bold"))


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


class VentanaValidarRips:
    def __init__(self, parent):
        self.ventana = tk.Toplevel(parent)
        aplicar_theme_ventana(
            self.ventana,
            title="Validar RIPS",
            size=DEFAULT_SIZE,
            min_size=None,
            bg=BG,
            resizable=(True, True),
            fullscreen=True,
        )

        self.var_source = tk.StringVar(value=str(CONFIG.get("source_file", "")))
        self.var_template = tk.StringVar(value=str(CONFIG.get("template_file", "")))
        self.var_output = tk.StringVar(value=str(CONFIG.get("output_file", "")))

        self._crear_ui()

    def _crear_ui(self):
        _configurar_estilos()

        body = tk.Frame(self.ventana, bg=BG)
        body.pack(fill="both", expand=True)

        # ── Sidebar ──────────────────────────────────────────────
        side = tk.Frame(body, bg=NAVY, width=270)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        self._logo_img = _cargar_logo(160)
        if self._logo_img:
            tk.Label(side, image=self._logo_img, bg=NAVY).pack(pady=(28, 0))

        tk.Label(side, text="VALIDAR\nRIPS",
                 font=("Segoe UI", 16, "bold"), fg=WHITE, bg=NAVY,
                 anchor="w", justify="left").pack(padx=24, pady=(16, 8), fill="x")
        tk.Label(side, text="Valida y genera transacción, usuarios y consultas en plantilla de RIPS.",
                 font=("Segoe UI", 10), fg=SKY, bg=NAVY,
                 anchor="w", wraplength=220, justify="left").pack(padx=28, fill="x")
        # Feature icon
        self._icon_sidebar = _cargar_icono(200)
        if self._icon_sidebar:
            icon_frame = tk.Frame(side, bg=NAVY, width=270, height=220)
            icon_frame.pack(fill="x", pady=(20, 0))
            icon_frame.pack_propagate(False)
            tk.Label(icon_frame, image=self._icon_sidebar, bg=NAVY).place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(side, text="Versión 2.0",
                 font=("Segoe UI", 9), fg=MUTED, bg=NAVY,
                 anchor="w").pack(padx=28, pady=(0, 24), side="bottom", fill="x")

        # ── Main content ─────────────────────────────────────────
        main = tk.Frame(body, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        # Header
        hdr = tk.Frame(main, bg=BG)
        hdr.pack(fill="x", padx=32, pady=(24, 20))
        col = tk.Frame(hdr, bg=BG)
        col.pack(side="left")
        tk.Label(col, text="Validar RIPS",
                 font=("Segoe UI", 18, "bold"), fg=NAVY, bg=BG,
                 anchor="w").pack(anchor="w")
        tk.Label(col, text="Selecciona archivos de entrada/salida, ejecuta y revisa progreso/logs.",
                 font=("Segoe UI", 10), fg=MUTED, bg=BG,
                 anchor="w").pack(anchor="w", pady=(2, 0))

        # ── Card: Archivos ────────────────────────────────────────
        card1 = RoundedCard(main)
        card1.pack(fill="x", padx=32, pady=(0, 20))
        c1 = card1.content

        tk.Label(c1, text="Archivos requeridos",
                 font=("Segoe UI", 12, "bold"), fg=TEXT, bg=WHITE,
                 anchor="w").pack(padx=24, pady=(20, 12), fill="x")

        self._fila_archivo(c1, "Archivo origen (.xlsx)", self.var_source, self._buscar_excel)
        self._fila_archivo(c1, "Plantilla (.xlsm)", self.var_template, self._buscar_xlsm)
        self._fila_archivo(c1, "Archivo salida (.xlsm)", self.var_output, self._guardar_xlsm)
        tk.Label(c1, text="", font=("Segoe UI", 6), bg=WHITE).pack(pady=(0, 16))

        # ── Progress ─────────────────────────────────────────────
        prog = RoundedCard(main)
        prog.pack(fill="x", padx=32, pady=(0, 20))
        p = prog.content

        self.lbl_estado = tk.Label(
            p, text="Listo para iniciar",
            font=("Segoe UI", 10), fg=MUTED, bg=WHITE, anchor="w",
        )
        self.lbl_estado.pack(padx=24, pady=(14, 6), fill="x")

        bar_frame = tk.Frame(p, bg=WHITE)
        bar_frame.pack(padx=24, pady=(0, 4), fill="x")

        style = ttk.Style()
        style.configure("Goleman.Horizontal.TProgressbar",
                        troughcolor="#E5E7EB", background=ORANGE,
                        bordercolor=WHITE, lightcolor=ORANGE, darkcolor=ORANGE)
        self.barra = ttk.Progressbar(
            bar_frame, style="Goleman.Horizontal.TProgressbar",
            maximum=100, mode="determinate",
        )
        self.barra.pack(side="left", fill="x", expand=True)

        self.lbl_porcentaje = tk.Label(
            bar_frame, text="0%",
            font=("Segoe UI", 10, "bold"), fg=ORANGE, bg=WHITE, anchor="e",
        )
        self.lbl_porcentaje.pack(side="right", padx=(10, 0))

        tk.Label(p, text="", font=("Segoe UI", 4), bg=WHITE).pack(pady=(0, 14))

        # ── Action bar ───────────────────────────────────────────
        act = tk.Frame(main, bg=BG)
        act.pack(fill="x", padx=32, pady=(0, 16))

        self.btn_ejecutar = tk.Button(
            act, text="▶  Ejecutar",
            font=("Segoe UI", 10, "bold"),
            bg=ORANGE, fg=WHITE, width=16, padx=8, pady=4,
            relief="flat", cursor="hand2",
            activebackground="#E06020",
            command=self._ejecutar,
        )
        self.btn_ejecutar.pack(side="left")

        tk.Button(
            act, text="🗑  Limpiar logs",
            font=("Segoe UI", 10),
            bg=BLUE, fg=WHITE, width=16, padx=8, pady=4,
            relief="flat", cursor="hand2",
            activebackground="#0F4A8A",
            command=self._limpiar_logs,
        ).pack(side="left", padx=(8, 0))

        tk.Button(
            act, text="←  Volver",
            font=("Segoe UI", 10),
            bg=BLUE, fg=WHITE, width=16, padx=8, pady=4,
            relief="flat", cursor="hand2",
            activebackground="#0F4A8A",
            command=self.ventana.destroy,
        ).pack(side="right")

        # ── Card: Log ────────────────────────────────────────────
        card3 = RoundedCard(main)
        card3.pack(fill="both", expand=True, padx=32, pady=(0, 24))
        c3 = card3.content

        tk.Label(c3, text="Log de ejecución",
                 font=("Segoe UI", 12, "bold"), fg=TEXT, bg=WHITE,
                 anchor="w").pack(padx=24, pady=(16, 8), fill="x")

        self.txt_log = ScrolledText(
            c3, height=8,
            font=("Consolas", 10), bg="#0F1117", fg="#94A3B8",
            relief="flat", bd=0, padx=12, pady=10,
            state="disabled", cursor="arrow",
        )
        self.txt_log.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.txt_log.tag_config("ok", foreground="#22D3A5")
        self.txt_log.tag_config("error", foreground="#F87171")

    def _fila_archivo(self, parent, texto, variable, comando_buscar):
        fila = tk.Frame(parent, bg=WHITE)
        fila.pack(fill="x", pady=5, padx=24)

        tk.Label(
            fila, text=texto, width=26, anchor="w",
            font=("Segoe UI", 9), fg=MUTED, bg=WHITE,
        ).pack(side="left")

        ttk.Entry(
            fila, textvariable=variable, style="Rounded.TEntry",
        ).pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=4)

        ttk.Button(
            fila, text="Examinar", style="Secondary.TButton",
            command=lambda: comando_buscar(variable),
        ).pack(side="left")

    def _buscar_excel(self, variable):
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo origen",
            filetypes=[("Excel", "*.xlsx *.xls")],
            parent=self.ventana,
        )
        if ruta:
            variable.set(ruta)

    def _buscar_xlsm(self, variable):
        ruta = filedialog.askopenfilename(
            title="Seleccionar plantilla",
            filetypes=[("Excel Macro", "*.xlsm"), ("Excel", "*.xlsx *.xls")],
            parent=self.ventana,
        )
        if ruta:
            variable.set(ruta)

    def _guardar_xlsm(self, variable):
        ruta = filedialog.asksaveasfilename(
            title="Guardar archivo de salida",
            defaultextension=".xlsm",
            filetypes=[("Excel Macro", "*.xlsm"), ("Excel", "*.xlsx")],
            parent=self.ventana,
        )
        if ruta:
            variable.set(ruta)

    def _limpiar_logs(self):
        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", tk.END)
        self.txt_log.configure(state="disabled")

    def _agregar_log(self, texto):
        self.txt_log.configure(state="normal")
        tag = "error" if texto.startswith("ERROR") else "ok"
        self.txt_log.insert(tk.END, texto + "\n", tag)
        self.txt_log.see(tk.END)
        self.txt_log.configure(state="disabled")

    def _actualizar_progreso(self, porcentaje, estado):
        self.barra["value"] = porcentaje
        self.lbl_porcentaje.config(text=f"{int(porcentaje)}%")
        self.lbl_estado.config(text=estado)

    def _validar_inputs(self):
        source = Path(self.var_source.get().strip())
        template = Path(self.var_template.get().strip())
        output = Path(self.var_output.get().strip())

        if not source.exists():
            messagebox.showerror("Error", "Selecciona un archivo origen valido.", parent=self.ventana)
            return None
        if not template.exists():
            messagebox.showerror("Error", "Selecciona una plantilla valida.", parent=self.ventana)
            return None
        if not output.parent.exists():
            messagebox.showerror("Error", "La carpeta de salida no existe.", parent=self.ventana)
            return None

        return source, template, output

    def _ejecutar(self):
        validado = self._validar_inputs()
        if not validado:
            return

        source, template, output = validado

        self.btn_ejecutar.config(state="disabled")
        self._actualizar_progreso(0, "Iniciando")
        self._agregar_log("--- Nueva ejecucion ---")
        self._agregar_log(f"Origen: {source}")
        self._agregar_log(f"Plantilla: {template}")
        self._agregar_log(f"Salida: {output}")

        hilo = threading.Thread(
            target=self._ejecutar_hilo,
            args=(source, template, output),
            daemon=True,
        )
        hilo.start()

    def _ejecutar_hilo(self, source: Path, template: Path, output: Path):
        cfg = dict(CONFIG)
        cfg["source_file"] = str(source)
        cfg["template_file"] = str(template)
        cfg["output_file"] = str(output)

        def on_progress(valor, mensaje):
            self.ventana.after(0, lambda: self._actualizar_progreso(valor, mensaje))

        def on_log(mensaje):
            self.ventana.after(0, lambda: self._agregar_log(mensaje))

        try:
            servicio = ValidadorRipsService(config=cfg, on_log=on_log, on_progress=on_progress)
            salida = servicio.ejecutar()
            self.ventana.after(0, lambda: self._finalizar_ok(str(salida)))
        except Exception as exc:
            error_texto = str(exc)
            self.ventana.after(0, lambda e=error_texto: self._finalizar_error(e))


    def _finalizar_ok(self, salida):
        self.btn_ejecutar.config(state="normal")
        self.lbl_estado.config(text="Proceso terminado", fg="#1565C0")
        self._agregar_log(f"Archivo generado: {salida}")
        messagebox.showinfo("Exito", f"Archivo generado:\n{salida}", parent=self.ventana)

    def _finalizar_error(self, error_texto):
        self.btn_ejecutar.config(state="normal")
        self.lbl_estado.config(text="Proceso con error", fg="#C53030")
        self._agregar_log(f"ERROR: {error_texto}")
        messagebox.showerror("Error de procesamiento", error_texto, parent=self.ventana)
