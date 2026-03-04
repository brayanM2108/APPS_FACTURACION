import tkinter as tk
from tkinter import filedialog, messagebox
import threading
from features.actas_medicamentos.transposicion.core.transponer_medicamentos_service import procesar_archivo


class VentanaTransposicion:
    def __init__(self, parent, on_volver):
        self.on_volver = on_volver
        self.frame = tk.Frame(parent, bg="#F0F4F8")
        self.frame.pack(fill="both", expand=True)
        self._crear_ui()

    def _crear_ui(self):
        tk.Label(
            self.frame, text="Transposición de Medicamentos",
            font=("Segoe UI", 15, "bold"), bg="#F0F4F8", fg="#1A365D"
        ).pack(pady=(28, 4))

        tk.Label(
            self.frame, text="Convierte el archivo de vertical a horizontal por paciente",
            font=("Segoe UI", 9), bg="#F0F4F8", fg="#718096"
        ).pack(pady=(0, 20))

        # Selección de archivo
        frame_archivo = tk.Frame(self.frame, bg="#F0F4F8")
        frame_archivo.pack(padx=30, fill="x")

        tk.Label(
            frame_archivo, text="Archivo Excel (.xlsx):",
            font=("Segoe UI", 9, "bold"), bg="#F0F4F8", fg="#2D3748"
        ).pack(anchor="w")

        frame_input = tk.Frame(frame_archivo, bg="#F0F4F8")
        frame_input.pack(fill="x", pady=(4, 0))

        self.ruta_var = tk.StringVar()
        self.entry_ruta = tk.Entry(
            frame_input, textvariable=self.ruta_var,
            font=("Segoe UI", 9), relief="flat",
            bg="white", fg="#2D3748",
            highlightthickness=1, highlightbackground="#CBD5E0",
            highlightcolor="#4299E1"
        )
        self.entry_ruta.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))

        tk.Button(
            frame_input, text="Buscar",
            font=("Segoe UI", 9), relief="flat",
            bg="#4299E1", fg="white", cursor="hand2",
            activebackground="#3182CE", activeforeground="white",
            padx=14, pady=6,
            command=self._seleccionar_archivo
        ).pack(side="left")

        # Estado
        self.label_estado = tk.Label(
            self.frame, text="",
            font=("Segoe UI", 9), bg="#F0F4F8", fg="#718096",
            wraplength=480, justify="left"
        )
        self.label_estado.pack(padx=30, pady=(18, 0), anchor="w")

        # Botones
        frame_botones = tk.Frame(self.frame, bg="#F0F4F8")
        frame_botones.pack(pady=(20, 0))

        tk.Button(
            frame_botones, text="← Volver",
            font=("Segoe UI", 9), relief="flat",
            bg="#718096", fg="white", cursor="hand2",
            activebackground="#4A5568", activeforeground="white",
            padx=16, pady=8,
            command=self.on_volver                        # ✅ llama al orquestador
        ).pack(side="left", padx=(0, 10))

        self.btn_procesar = tk.Button(
            frame_botones, text="▶  Procesar archivo",
            font=("Segoe UI", 10, "bold"), relief="flat",
            bg="#2F855A", fg="white", cursor="hand2",
            activebackground="#276749", activeforeground="white",
            padx=20, pady=10,
            command=self._ejecutar
        )
        self.btn_procesar.pack(side="left")

    def _seleccionar_archivo(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo Excel",
            filetypes=[("Archivos Excel", "*.xlsx *.xls")]
        )
        if ruta:
            self.ruta_var.set(ruta)
            self.label_estado.config(text="Archivo seleccionado.", fg="#718096")

    def _ejecutar(self):
        ruta = self.ruta_var.get().strip()
        if not ruta:
            messagebox.showwarning(
                "Sin archivo", "Por favor selecciona un archivo Excel.",
                parent=self.frame                         # ✅ parent=self.frame, NO self.ventana
            )
            return

        self.btn_procesar.config(state="disabled", text="Procesando...")
        self.label_estado.config(text="Procesando, por favor espera...", fg="#D69E2E")
        self.frame.update()                               # ✅ self.frame, NO self.ventana

        threading.Thread(target=self._procesar_en_hilo, args=(ruta,), daemon=True).start()

    def _procesar_en_hilo(self, ruta):
        exito, mensaje, _ = procesar_archivo(ruta)
        self.frame.after(0, self._mostrar_resultado, exito, mensaje)  # ✅ self.frame

    def _mostrar_resultado(self, exito, mensaje):
        self.btn_procesar.config(state="normal", text="▶  Procesar archivo")
        if exito:
            self.label_estado.config(text=mensaje, fg="#276749")
        else:
            self.label_estado.config(text=f"Error: {mensaje}", fg="#C53030")

    def destruir(self):
        self.frame.destroy()                              # ✅ self.frame, NO self.ventana