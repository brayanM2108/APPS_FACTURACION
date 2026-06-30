import io
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

import cairosvg
from PIL import Image, ImageTk

from features.completar_rips.core.codigos_auxiliares import (
    GRUPO_SERVICIOS_NOMBRE_A_CODIGO,
    TIPOS_MODALIDAD_ATENCION_A_CODIGO,
    TIPOS_USUARIO_NOMBRE_A_CODIGO,
)
from features.completar_rips.core.completar_rips_service import (
    CompletarRipsConfig,
    CompletarRipsService,
)
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
        icono_path = Path(__file__).parents[3] / "ui" / "assets" / "completar_rips.svg"
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
    c.bind("<Enter>", lambda e: _btn_draw(c, width, 44, text,
                                          BG if outline else bg, fg, outline))
    c.bind("<Leave>", lambda e: _btn_draw(c, width, 44, text,
                                          bg, fg, outline))
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


class VentanaCompletarRips:
    def __init__(self, parent):
        self.ventana = tk.Toplevel(parent)

        aplicar_theme_ventana(
            self.ventana,
            title="Completar RIPS",
            size=DEFAULT_SIZE,
            min_size=None,
            bg=BG,
            resizable=(True, True),
            fullscreen=True,
        )

        self.var_informe = tk.StringVar()
        self.var_base_ppl = tk.StringVar()
        self.var_base_csv = tk.StringVar()
        self.var_salida = tk.StringVar()
        self.var_numero_factura = tk.StringVar()

        self.var_tipo_usuario = tk.StringVar()
        self.var_modalidad = tk.StringVar()
        self.var_grupo_servicios = tk.StringVar()
        self.var_modo_diagnostico = tk.StringVar()

        self._crear_ui()

    def _crear_ui(self):
        _configurar_estilos()

        body = tk.Frame(self.ventana, bg=BG)
        body.pack(fill="both", expand=True)

        # ── Sidebar ──────────────────────────────────────────────
        side = tk.Frame(body, bg=NAVY, width=270)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        # Logo (top)
        self._logo_img = _cargar_logo(160)
        if self._logo_img:
            logo_lbl = tk.Label(side, image=self._logo_img, bg=NAVY)
            logo_lbl.pack(pady=(28, 0))

        # Title
        tk.Label(side, text="COMPLETAR\nRIPS",
                 font=("Segoe UI", 16, "bold"), fg=WHITE, bg=NAVY,
                 anchor="w", justify="left").pack(padx=24, pady=(16, 8), fill="x")

        # Desc
        tk.Label(side, text="Completa la plantilla RIPS utilizando bases de facturación y parámetros obligatorios.",
                 font=("Segoe UI", 10), fg=SKY, bg=NAVY,
                 anchor="w", wraplength=220, justify="left").pack(padx=28, fill="x")

        # Feature icon
        self._icon_sidebar = _cargar_icono(200)
        if self._icon_sidebar:
            icon_frame = tk.Frame(side, bg=NAVY, width=270, height=220)
            icon_frame.pack(fill="x", pady=(20, 0))
            icon_frame.pack_propagate(False)
            tk.Label(icon_frame, image=self._icon_sidebar, bg=NAVY).place(relx=0.5, rely=0.5, anchor="center")

        # Version
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
        tk.Label(col, text="Completar plantilla RIPS",
                 font=("Segoe UI", 18, "bold"), fg=NAVY, bg=BG,
                 anchor="w").pack(anchor="w")
        tk.Label(col, text="Carga las bases y selecciona los parámetros obligatorios para completar la plantilla.",
                 font=("Segoe UI", 10), fg=MUTED, bg=BG,
                 anchor="w").pack(anchor="w", pady=(2, 0))

        # ── Card: Archivos requeridos ────────────────────────────
        card1 = RoundedCard(main)
        card1.pack(fill="x", padx=32, pady=(0, 20))
        c1 = card1.content

        tk.Label(c1, text="Archivos requeridos",
                 font=("Segoe UI", 12, "bold"), fg=TEXT, bg=WHITE,
                 anchor="w").pack(padx=24, pady=(20, 12), fill="x")

        self._fila_archivo(c1, "Informe de facturación (.xlsx)", self.var_informe, self._buscar_excel)
        self._fila_archivo(c1, "Pacientes creados (.csv)", self.var_base_csv, self._buscar_csv)
        self._fila_archivo(c1, "Base PPL (.xlxs)", self.var_base_ppl, self._buscar_excel_ppl)
        self._fila_archivo(c1, "Archivo salida (.xlsx)", self.var_salida, self._guardar_excel)
        self._fila_texto(c1, "Número de factura", self.var_numero_factura)

        tk.Label(c1, text="", font=("Segoe UI", 6), bg=WHITE).pack(pady=(0, 16))

        # ── Card: Parámetros obligatorios ────────────────────────
        card2 = RoundedCard(main)
        card2.pack(fill="x", padx=32, pady=(0, 20))
        c2 = card2.content

        tk.Label(c2, text="Parámetros obligatorios",
                 font=("Segoe UI", 12, "bold"), fg=TEXT, bg=WHITE,
                 anchor="w").pack(padx=24, pady=(20, 12), fill="x")

        grid_params = tk.Frame(c2, bg=WHITE)
        grid_params.pack(padx=24, pady=(0, 20), fill="x")
        grid_params.grid_columnconfigure(0, weight=1, pad=8)
        grid_params.grid_columnconfigure(1, weight=1, pad=8)

        params = [
            ("Modo diagnóstico", self.var_modo_diagnostico, ["FOMAG", "PPL"]),
            ("Tipo de usuario", self.var_tipo_usuario, list(TIPOS_USUARIO_NOMBRE_A_CODIGO.keys())),
            ("Modalidad tecnología salud", self.var_modalidad, list(TIPOS_MODALIDAD_ATENCION_A_CODIGO.keys())),
            ("Grupo servicios", self.var_grupo_servicios, list(GRUPO_SERVICIOS_NOMBRE_A_CODIGO.keys())),
        ]
        for i, (label, var, opts) in enumerate(params):
            self._fila_combo(grid_params, label, var, opts, row=i // 2, col=i % 2)

        # ── Action bar ───────────────────────────────────────────
        act = tk.Frame(main, bg=BG)
        act.pack(fill="x", padx=32, pady=(0, 16))

        self.btn_procesar = tk.Button(
            act, text="▶  Procesar",
            font=("Segoe UI", 10, "bold"),
            bg=ORANGE, fg=WHITE, width=16, padx=8, pady=4,
            relief="flat", cursor="hand2",
            activebackground="#E06020",
            command=self._procesar,
        )
        self.btn_procesar.pack(side="left")

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

    def _fila_texto(self, parent, texto, variable):
        fila = tk.Frame(parent, bg=WHITE)
        fila.pack(fill="x", pady=5, padx=24)

        tk.Label(
            fila, text=texto, width=26, anchor="w",
            font=("Segoe UI", 9), fg=MUTED, bg=WHITE,
        ).pack(side="left")

        ttk.Entry(
            fila, textvariable=variable, style="Rounded.TEntry",
        ).pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=4)

    def _fila_combo(self, parent, texto, variable, opciones, row=None, col=None):
        fila = tk.Frame(parent, bg=WHITE)
        if row is not None:
            fila.grid(row=row, column=col, sticky="ew", padx=4, pady=5)
        else:
            fila.pack(fill="x", pady=4)

        lbl = tk.Label(
            fila, text=texto, anchor="w",
            font=("Segoe UI", 9), fg=MUTED, bg=WHITE,
        )
        lbl.pack(fill="x")

        combo = ttk.Combobox(
            fila, textvariable=variable, values=opciones,
            state="readonly", font=("Segoe UI", 10),
        )
        combo.pack(fill="x", pady=(4, 0))

    def _buscar_excel(self, variable):
        ruta = filedialog.askopenfilename(
            title="Seleccionar informe de facturacion",
            filetypes=[("Excel", "*.xlsx *.xls")],
            parent=self.ventana,
        )

        if ruta:
            variable.set(ruta)

    def _buscar_excel_ppl(self, variable):
        ruta = filedialog.askopenfilename(
            title="Selecciona la base de PPL",
            filetypes=[("Excel", "*.xlsx *.xls")],
            parent=self.ventana,
        )

        if ruta:
            variable.set(ruta)

    def _buscar_csv(self, variable):
        ruta = filedialog.askopenfilename(
            title="Seleccionar base CSV",
            filetypes=[("CSV", "*.csv")],
            parent=self.ventana,
        )

        if ruta:
            variable.set(ruta)

    def _guardar_excel(self, variable):
        ruta = filedialog.asksaveasfilename(
            title="Guardar archivo de salida",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            parent=self.ventana,
        )

        if ruta:
            variable.set(ruta)

    # =========================================================
    # LOGS
    # =========================================================

    def _limpiar_logs(self):
        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", tk.END)
        self.txt_log.configure(state="disabled")

    def _agregar_log(self, texto):
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.txt_log.configure(state="normal")

        tag = "error" if texto.startswith("ERROR") else "ok"
        self.txt_log.insert(tk.END, f"[{timestamp}] {texto}\n", tag)

        self.txt_log.see(tk.END)

        self.txt_log.configure(state="disabled")

    def _actualizar_progreso(self, porcentaje, estado):
        self.barra["value"] = porcentaje
        self.lbl_porcentaje.config(text=f"{int(porcentaje)}%")
        self.lbl_estado.config(text=estado)

    # =========================================================
    # PROCESO
    # =========================================================

    def _procesar(self):
        source = Path(self.var_informe.get().strip())
        base = Path(self.var_base_csv.get().strip())
        output = Path(self.var_salida.get().strip())
        base_ppl = Path(self.var_base_ppl.get().strip())
        numero_factura = self.var_numero_factura.get().strip()

        if not self.var_modo_diagnostico.get().strip():
            messagebox.showerror("Error", "Selecciona el modo de diagnóstico.", parent=self.ventana)
            return

        if self.var_modo_diagnostico.get().strip() == "PPL":
            if not base_ppl.exists():
                messagebox.showerror("Error", "Selecciona una base PPL válida.", parent=self.ventana)
                return

        if not source.exists():
            messagebox.showerror(
                "Error",
                "Selecciona un informe de facturacion valido.",
                parent=self.ventana,
            )
            return

        if not base.exists():
            messagebox.showerror(
                "Error",
                "Selecciona una base CSV valida.",
                parent=self.ventana,
            )
            return

        if not output.parent.exists():
            messagebox.showerror(
                "Error",
                "La carpeta de salida no existe.",
                parent=self.ventana,
            )
            return

        if not numero_factura.isdigit():
            messagebox.showerror(
                "Error",
                "Ingresa un numero de factura valido.",
                parent=self.ventana,
            )
            return

        if not self.var_tipo_usuario.get().strip():
            messagebox.showerror(
                "Error",
                "Selecciona el tipo de usuario.",
                parent=self.ventana,
            )
            return

        if not self.var_modalidad.get().strip():
            messagebox.showerror(
                "Error",
                "Selecciona la modalidad de tecnologia salud.",
                parent=self.ventana,
            )
            return

        if not self.var_grupo_servicios.get().strip():
            messagebox.showerror(
                "Error",
                "Selecciona el grupo de servicios.",
                parent=self.ventana,
            )
            return

        if not self.var_modo_diagnostico.get().strip():
            messagebox.showerror("Error", "Selecciona el modo de diagnóstico.", parent=self.ventana)
            return

        if self.var_modo_diagnostico.get().strip() == "PPL":
            if not base_ppl.exists():
                messagebox.showerror("Error", "Selecciona una base PPL válida.", parent=self.ventana)
                return

        config = CompletarRipsConfig(
            informe_path=source,
            base_csv_path=base,
            output_path=output,
            numero_factura=int(numero_factura),
            base_ppl_path=base_ppl if self.var_modo_diagnostico.get().strip() == "PPL" else None,
            tipo_usuario=self.var_tipo_usuario.get().strip(),
            modalidad_tecnologia=self.var_modalidad.get().strip(),
            grupo_servicios=self.var_grupo_servicios.get().strip(),
            modo_diagnostico=self.var_modo_diagnostico.get().strip(),
        )

        self._actualizar_progreso(0, "Iniciando")

        self._agregar_log("--- Nueva ejecucion ---")
        self._agregar_log(f"Informe: {source}")
        self._agregar_log(f"Base CSV: {base}")
        self._agregar_log(f"Salida: {output}")
        self._agregar_log(f"Factura: {numero_factura}")

        self.btn_procesar.config(state="disabled")

        hilo = threading.Thread(
            target=self._ejecutar_hilo,
            args=(config,),
            daemon=True,
        )

        hilo.start()

    def _ejecutar_hilo(self, config: CompletarRipsConfig):
        try:
            self.ventana.after(
                0,
                lambda: self._actualizar_progreso(
                    15,
                    "Leyendo informe",
                ),
            )

            self.ventana.after(
                0,
                lambda: self._agregar_log(
                    "Leyendo informe de facturacion...",
                ),
            )

            servicio = CompletarRipsService(config)

            self.ventana.after(
                0,
                lambda: self._actualizar_progreso(
                    45,
                    "Procesando informacion",
                ),
            )

            self.ventana.after(
                0,
                lambda: self._agregar_log(
                    "Procesando registros RIPS...",
                ),
            )

            salida = servicio.ejecutar()

            self.ventana.after(
                0,
                lambda: self._actualizar_progreso(
                    100,
                    "Proceso finalizado",
                ),
            )

            self.ventana.after(
                0,
                lambda: self._finalizar_ok(str(salida)),
            )

        except Exception as exc:
            self.ventana.after(
                0,
                lambda e=str(exc): self._finalizar_error(e),
            )

    def _finalizar_ok(self, salida: str):
        self.btn_procesar.config(state="normal")

        self.lbl_estado.config(
            text="Proceso terminado",
            fg="#1565C0",
        )

        self._agregar_log(
            f"Archivo generado correctamente: {salida}"
        )

        messagebox.showinfo(
            "Exito",
            f"Archivo generado:\n{salida}",
            parent=self.ventana,
        )

    def _finalizar_error(self, error_texto: str):
        self.btn_procesar.config(state="normal")

        self.lbl_estado.config(
            text="Proceso con error",
            fg="#C53030",
        )

        self._agregar_log(
            f"ERROR: {error_texto}"
        )

        messagebox.showerror(
            "Error de procesamiento",
            error_texto,
            parent=self.ventana,
        )
