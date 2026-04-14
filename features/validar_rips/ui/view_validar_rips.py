import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from features.validar_rips.core.validar_rips_service import CONFIG, ValidadorRipsService
from ui.theme import aplicar_theme_ventana, BG


class VentanaValidarRips:
    def __init__(self, parent):
        self.ventana = tk.Toplevel(parent)
        aplicar_theme_ventana(
            self.ventana,
            title="Validar RIPS",
            size=(760, 620),
            min_size=None,
            bg=BG,
            resizable=(False, False),
        )

        self.var_source = tk.StringVar(value=str(CONFIG.get("source_file", "")))
        self.var_template = tk.StringVar(value=str(CONFIG.get("template_file", "")))
        self.var_output = tk.StringVar(value=str(CONFIG.get("output_file", "")))

        self._crear_ui()

    def _crear_ui(self):
        tk.Label(
            self.ventana,
            text="Validar RIPS",
            font=("Segoe UI", 15, "bold"),
            bg="#F0F4F8",
            fg="#1A365D",
        ).pack(pady=(18, 4))

        tk.Label(
            self.ventana,
            text="Selecciona archivos de entrada/salida, ejecuta y revisa progreso/logs.",
            font=("Segoe UI", 9),
            bg="#F0F4F8",
            fg="#718096",
        ).pack(pady=(0, 14))

        frame_form = tk.Frame(self.ventana, bg="#F0F4F8")
        frame_form.pack(fill="x", padx=22)

        self._fila_archivo(frame_form, "Archivo origen (.xlsx)", self.var_source, self._buscar_excel)
        self._fila_archivo(frame_form, "Plantilla (.xlsm)", self.var_template, self._buscar_xlsm)
        self._fila_archivo(frame_form, "Archivo salida (.xlsm)", self.var_output, self._guardar_xlsm)

        frame_estado = tk.Frame(self.ventana, bg="#F0F4F8")
        frame_estado.pack(fill="x", padx=22, pady=(12, 4))

        self.lbl_estado = tk.Label(
            frame_estado,
            text="Listo para iniciar",
            font=("Segoe UI", 9),
            bg="#F0F4F8",
            fg="#2D3748",
            anchor="w",
        )
        self.lbl_estado.pack(fill="x")

        self.barra = ttk.Progressbar(frame_estado, maximum=100, mode="determinate")
        self.barra.pack(fill="x", pady=(6, 0))

        self.lbl_porcentaje = tk.Label(
            frame_estado,
            text="0%",
            font=("Segoe UI", 9, "bold"),
            bg="#F0F4F8",
            fg="#2B6CB0",
            anchor="e",
        )
        self.lbl_porcentaje.pack(fill="x", pady=(4, 0))

        frame_acciones = tk.Frame(self.ventana, bg="#F0F4F8")
        frame_acciones.pack(fill="x", padx=22, pady=(8, 8))

        self.btn_ejecutar = tk.Button(
            frame_acciones,
            text="Ejecutar validacion",
            font=("Segoe UI", 10, "bold"),
            bg="#2B6CB0",
            fg="white",
            relief="flat",
            padx=16,
            pady=8,
            command=self._ejecutar,
        )
        self.btn_ejecutar.pack(side="left")

        tk.Button(
            frame_acciones,
            text="Limpiar logs",
            font=("Segoe UI", 9),
            bg="#EDF2F7",
            fg="#2D3748",
            relief="flat",
            padx=12,
            pady=8,
            command=self._limpiar_logs,
        ).pack(side="left", padx=8)

        tk.Button(
            frame_acciones,
            text="Volver",
            font=("Segoe UI", 9),
            bg="#E2E8F0",
            fg="#2D3748",
            relief="flat",
            padx=12,
            pady=8,
            command=self.ventana.destroy,
        ).pack(side="right", padx=8)

        tk.Label(
            self.ventana,
            text="Log de ejecucion",
            font=("Segoe UI", 10, "bold"),
            bg="#F0F4F8",
            fg="#2D3748",
        ).pack(anchor="w", padx=22)

        self.txt_log = ScrolledText(self.ventana, height=16, font=("Consolas", 9))
        self.txt_log.pack(fill="both", expand=True, padx=22, pady=(6, 18))
        self.txt_log.configure(state="disabled")

    def _fila_archivo(self, parent, texto, variable, comando_buscar):
        fila = tk.Frame(parent, bg="#F0F4F8")
        fila.pack(fill="x", pady=4)

        tk.Label(
            fila,
            text=texto,
            width=32,
            anchor="w",
            font=("Segoe UI", 9),
            bg="#F0F4F8",
            fg="#2D3748",
        ).pack(side="left")

        tk.Entry(fila, textvariable=variable, font=("Segoe UI", 9)).pack(
            side="left", fill="x", expand=True, padx=(0, 8)
        )

        tk.Button(
            fila,
            text="...",
            width=4,
            font=("Segoe UI", 9),
            bg="#E2E8F0",
            fg="#2D3748",
            relief="flat",
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
        self.txt_log.insert(tk.END, texto + "\n")
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
        self.lbl_estado.config(text="Proceso terminado", fg="#276749")
        self._agregar_log(f"Archivo generado: {salida}")
        messagebox.showinfo("Exito", f"Archivo generado:\n{salida}", parent=self.ventana)

    def _finalizar_error(self, error_texto):
        self.btn_ejecutar.config(state="normal")
        self.lbl_estado.config(text="Proceso con error", fg="#C53030")
        self._agregar_log(f"ERROR: {error_texto}")
        messagebox.showerror("Error de procesamiento", error_texto, parent=self.ventana)
