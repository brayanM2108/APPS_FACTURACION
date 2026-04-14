import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from features.informe_consolidado.core.consolidador_service import ejecutar_consolidacion
from ui.theme import aplicar_theme_ventana, DEFAULT_SIZE, DEFAULT_MIN_SIZE, BG


class VentanaInformeConsolidado:
    def __init__(self, parent):
        # Crear Toplevel y aplicar theme central
        self.ventana = tk.Toplevel(parent)
        aplicar_theme_ventana(
            self.ventana,
            title="Consolidar Informe",
            size=DEFAULT_SIZE,
            min_size=DEFAULT_MIN_SIZE,
            bg=BG,
            resizable=(False, False),
            modal=False,
        )

        self.var_factura_ele = tk.StringVar()
        self.var_facturado = tk.StringVar()
        self.var_facturacion_informe = tk.StringVar()
        self.var_consolidado = tk.StringVar()
        self.var_salida = tk.StringVar(value="PendienteConsolidar.xlsx")

        self._crear_ui()

    def _crear_ui(self):
        tk.Label(
            self.ventana,
            text="Consolidar Informe",
            font=("Segoe UI", 15, "bold"),
            bg="#F0F4F8",
            fg="#1A365D",
        ).pack(pady=(18, 4))

        tk.Label(
            self.ventana,
            text="Selecciona archivos de entrada, ejecuta y revisa progreso/logs.",
            font=("Segoe UI", 9),
            bg="#F0F4F8",
            fg="#718096",
        ).pack(pady=(0, 14))

        frame_form = tk.Frame(self.ventana, bg="#F0F4F8")
        frame_form.pack(fill="x", padx=22)

        self._fila_archivo(frame_form, "InfFacturElect.csv", self.var_factura_ele, self._buscar_csv)
        self._fila_archivo(frame_form, "FACTURADO 2025.xlsx", self.var_facturado, self._buscar_excel)
        self._fila_archivo(frame_form, "FACTURACION INFORME PY.xlsx", self.var_facturacion_informe, self._buscar_excel)
        self._fila_archivo(
            frame_form,
            "FACTURACION DE JULIO 2024 A DICIEMBRE 2025.xlsx",
            self.var_consolidado,
            self._buscar_excel,
        )
        self._fila_archivo(frame_form, "Salida (xlsx)", self.var_salida, self._guardar_excel)

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
            text="Ejecutar consolidacion",
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
            width=40,
            anchor="w",
            font=("Segoe UI", 9),
            bg="#F0F4F8",
            fg="#2D3748",
        ).pack(side="left")

        tk.Entry(fila, textvariable=variable, font=("Segoe UI", 9)).pack(side="left", fill="x", expand=True, padx=(0, 8))

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

    def _buscar_csv(self, variable):
        ruta = filedialog.askopenfilename(title="Seleccionar CSV", filetypes=[("CSV", "*.csv")])
        if ruta:
            variable.set(ruta)

    def _buscar_excel(self, variable):
        ruta = filedialog.askopenfilename(title="Seleccionar Excel", filetypes=[("Excel", "*.xlsx")])
        if ruta:
            variable.set(ruta)

    def _guardar_excel(self, variable):
        ruta = filedialog.asksaveasfilename(
            title="Guardar archivo de salida",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
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

    def _ejecutar(self):
        factura_ele = self.var_factura_ele.get().strip()
        facturado = self.var_facturado.get().strip()
        facturacion_informe = self.var_facturacion_informe.get().strip()
        consolidado = self.var_consolidado.get().strip()
        salida = self.var_salida.get().strip()

        if not all([factura_ele, facturado, facturacion_informe, consolidado, salida]):
            messagebox.showwarning("Datos incompletos", "Debes seleccionar todos los archivos.", parent=self.ventana)
            return

        self.btn_ejecutar.config(state="disabled")
        self._actualizar_progreso(0, "Iniciando")
        self._agregar_log("--- Nueva ejecucion ---")

        hilo = threading.Thread(
            target=self._ejecutar_hilo,
            args=(factura_ele, facturado, facturacion_informe, consolidado, salida),
            daemon=True,
        )
        hilo.start()

    def _ejecutar_hilo(self, factura_ele, facturado, facturacion_informe, consolidado, salida):
        def on_progress(valor, mensaje):
            self.ventana.after(0, lambda: self._actualizar_progreso(valor, mensaje))

        def on_log(mensaje):
            self.ventana.after(0, lambda: self._agregar_log(mensaje))

        exito, mensaje, salida_generada, log_path = ejecutar_consolidacion(
            factura_electronica_path=factura_ele,
            facturado_path=facturado,
            facturacion_informe_path=facturacion_informe,
            consolidado_path=consolidado,
            salida_path=salida,
            on_progress=on_progress,
            on_log=on_log,
        )

        self.ventana.after(0, lambda: self._finalizar_ejecucion(exito, mensaje, salida_generada, log_path))

    def _finalizar_ejecucion(self, exito, mensaje, salida_generada, log_path):
        self.btn_ejecutar.config(state="normal")

        if exito:
            self.lbl_estado.config(text="Proceso terminado", fg="#276749")
            messagebox.showinfo("Exito", mensaje, parent=self.ventana)
            if salida_generada:
                self._agregar_log(f"Salida: {salida_generada}")
        else:
            self.lbl_estado.config(text="Proceso con error", fg="#C53030")
            texto = mensaje
            if log_path:
                texto = f"{mensaje}\n\nRevisa log: {log_path}"
                self._agregar_log(f"Log de errores: {log_path}")
            messagebox.showerror("Error", texto, parent=self.ventana)

