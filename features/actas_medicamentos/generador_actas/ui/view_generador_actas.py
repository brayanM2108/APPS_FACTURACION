import tkinter as tk
from tkinter import filedialog
import os


class VistaCarga:
    def __init__(self, parent, on_completado, on_volver):
        self.on_completado = on_completado
        self.on_volver = on_volver
        self.frame = tk.Frame(parent, bg="#F0F4F8")
        self.frame.pack(fill="both", expand=True)
        self._crear_ui()

    def _crear_ui(self):
        tk.Label(
            self.frame, text="Generador de Actas ERON",
            font=("Segoe UI", 15, "bold"), bg="#F0F4F8", fg="#1A365D"
        ).pack(pady=(28, 4))

        tk.Label(
            self.frame, text="Paso 1: Selecciona el archivo Excel con los datos y la hoja 'pdf'",
            font=("Segoe UI", 9), bg="#F0F4F8", fg="#718096"
        ).pack(pady=(0, 24))

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
        tk.Entry(
            frame_input, textvariable=self.ruta_var,
            font=("Segoe UI", 9), relief="flat",
            bg="white", fg="#2D3748",
            highlightthickness=1, highlightbackground="#CBD5E0",
            highlightcolor="#4299E1"
        ).pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))

        tk.Button(
            frame_input, text="Buscar",
            font=("Segoe UI", 9), relief="flat",
            bg="#4299E1", fg="white", cursor="hand2",
            activebackground="#3182CE", activeforeground="white",
            padx=14, pady=6,
            command=self._seleccionar_archivo
        ).pack(side="left")

        # Carpeta de salida
        frame_salida = tk.Frame(self.frame, bg="#F0F4F8")
        frame_salida.pack(padx=30, fill="x", pady=(16, 0))

        tk.Label(
            frame_salida, text="Carpeta de salida para los PDFs:",
            font=("Segoe UI", 9, "bold"), bg="#F0F4F8", fg="#2D3748"
        ).pack(anchor="w")

        frame_salida_input = tk.Frame(frame_salida, bg="#F0F4F8")
        frame_salida_input.pack(fill="x", pady=(4, 0))

        self.carpeta_var = tk.StringVar()
        tk.Entry(
            frame_salida_input, textvariable=self.carpeta_var,
            font=("Segoe UI", 9), relief="flat",
            bg="white", fg="#2D3748",
            highlightthickness=1, highlightbackground="#CBD5E0",
            highlightcolor="#4299E1"
        ).pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))

        tk.Button(
            frame_salida_input, text="Buscar",
            font=("Segoe UI", 9), relief="flat",
            bg="#4299E1", fg="white", cursor="hand2",
            activebackground="#3182CE", activeforeground="white",
            padx=14, pady=6,
            command=self._seleccionar_carpeta
        ).pack(side="left")

        # Estado
        self.label_estado = tk.Label(
            self.frame, text="",
            font=("Segoe UI", 9), bg="#F0F4F8", fg="#718096",
            wraplength=480, justify="left"
        )
        self.label_estado.pack(padx=30, pady=(18, 0), anchor="w")

        # Botones — ambos en el mismo frame_botones     # ✅ sin duplicado de btn_cargar
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

        self.btn_cargar = tk.Button(
            frame_botones, text="📥  Cargar datos",
            font=("Segoe UI", 10, "bold"), relief="flat",
            bg="#2F855A", fg="white", cursor="hand2",
            activebackground="#276749", activeforeground="white",
            padx=20, pady=10,
            command=self._cargar
        )
        self.btn_cargar.pack(side="left")                # ✅ .pack() separado para guardar referencia

    def _seleccionar_archivo(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo Excel",
            filetypes=[("Archivos Excel", "*.xlsx *.xls")]
        )
        if ruta:
            self.ruta_var.set(ruta)
            if not self.carpeta_var.get():
                self.carpeta_var.set(os.path.dirname(ruta))

    def _seleccionar_carpeta(self):
        carpeta = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        if carpeta:
            self.carpeta_var.set(carpeta)

    def _cargar(self):
        from features.actas_medicamentos.generador_actas.core.generador_actas_service import cargar_datos

        ruta = self.ruta_var.get().strip()
        carpeta = self.carpeta_var.get().strip()

        if not ruta:
            self.label_estado.config(text="Por favor selecciona un archivo Excel.", fg="#C53030")
            return
        if not carpeta:
            self.label_estado.config(text="Por favor selecciona una carpeta de salida.", fg="#C53030")
            return

        self.btn_cargar.config(state="disabled", text="Cargando...")
        self.label_estado.config(text="Leyendo archivo...", fg="#D69E2E")
        self.frame.update()

        exito, mensaje, df, erons = cargar_datos(ruta)

        self.btn_cargar.config(state="normal", text="📥  Cargar datos")

        if exito:
            self.label_estado.config(text=mensaje, fg="#276749")
            self.on_completado({
                'ruta_archivo': ruta,
                'carpeta_salida': carpeta,
                'df': df,
                'erons': erons
            })
        else:
            self.label_estado.config(text=f"Error: {mensaje}", fg="#C53030")

    def destruir(self):
        self.frame.destroy()


# ========================================
# VISTA DE GENERACIÓN DE PDFs
# ========================================

class VistaGeneracion:
    def __init__(self, parent, datos, on_volver):
        """
        datos = { 'ruta_archivo': str, 'carpeta_salida': str, 'df': DataFrame, 'erons': list }
        """
        self.datos = datos
        self.on_volver = on_volver
        self.frame = tk.Frame(parent, bg="#F0F4F8")
        self.frame.pack(fill="both", expand=True)
        self._crear_ui()

    def _crear_ui(self):
        from tkinter import filedialog

        tk.Label(
            self.frame, text="Generador de Actas ERON",
            font=("Segoe UI", 15, "bold"), bg="#F0F4F8", fg="#1A365D"
        ).pack(pady=(28, 4))

        tk.Label(
            self.frame, text="Paso 2: Configura la generación de PDFs",
            font=("Segoe UI", 9), bg="#F0F4F8", fg="#718096"
        ).pack(pady=(0, 20))

        # Información de datos cargados
        frame_info = tk.Frame(self.frame, bg="white", highlightthickness=1, highlightbackground="#E2E8F0")
        frame_info.pack(padx=30, fill="x", pady=(0, 20))

        tk.Label(
            frame_info,
            text=f"✅ Datos cargados: {len(self.datos['erons'])} ERON(s) encontrados",
            font=("Segoe UI", 9, "bold"), bg="white", fg="#276749", anchor="w"
        ).pack(padx=14, pady=10, fill="x")

        # Imagen de firma (opcional)
        frame_firma = tk.Frame(self.frame, bg="#F0F4F8")
        frame_firma.pack(padx=30, fill="x", pady=(0, 16))

        tk.Label(
            frame_firma, text="Imagen de firma (opcional):",
            font=("Segoe UI", 9, "bold"), bg="#F0F4F8", fg="#2D3748"
        ).pack(anchor="w")

        frame_firma_input = tk.Frame(frame_firma, bg="#F0F4F8")
        frame_firma_input.pack(fill="x", pady=(4, 0))

        self.firma_var = tk.StringVar()
        tk.Entry(
            frame_firma_input, textvariable=self.firma_var,
            font=("Segoe UI", 9), relief="flat",
            bg="white", fg="#2D3748",
            highlightthickness=1, highlightbackground="#CBD5E0",
            highlightcolor="#4299E1"
        ).pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))

        tk.Button(
            frame_firma_input, text="Buscar",
            font=("Segoe UI", 9), relief="flat",
            bg="#4299E1", fg="white", cursor="hand2",
            activebackground="#3182CE", activeforeground="white",
            padx=14, pady=6,
            command=self._seleccionar_firma
        ).pack(side="left")

        # Estado
        self.label_estado = tk.Label(
            self.frame, text="",
            font=("Segoe UI", 9), bg="#F0F4F8", fg="#718096",
            wraplength=480, justify="left"
        )
        self.label_estado.pack(padx=30, pady=(10, 0), anchor="w")

        # Botones
        frame_botones = tk.Frame(self.frame, bg="#F0F4F8")
        frame_botones.pack(pady=(20, 0))

        tk.Button(
            frame_botones, text="← Volver",
            font=("Segoe UI", 9), relief="flat",
            bg="#718096", fg="white", cursor="hand2",
            activebackground="#4A5568", activeforeground="white",
            padx=16, pady=8,
            command=self.on_volver
        ).pack(side="left", padx=(0, 10))

        self.btn_generar = tk.Button(
            frame_botones, text="📄  Generar PDFs",
            font=("Segoe UI", 10, "bold"), relief="flat",
            bg="#2F855A", fg="white", cursor="hand2",
            activebackground="#276749", activeforeground="white",
            padx=20, pady=10,
            command=self._generar_pdfs
        )
        self.btn_generar.pack(side="left")

    def _seleccionar_firma(self):
        from tkinter import filedialog
        ruta = filedialog.askopenfilename(
            title="Seleccionar imagen de firma",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg")]
        )
        if ruta:
            self.firma_var.set(ruta)

    def _generar_pdfs(self):
        import threading
        from features.actas_medicamentos.generador_actas.core.generador_actas_service import (
            cargar_imagen_firma, cargar_logo_desde_ruta, generar_todos_los_pdfs, CARPETA_LOGO, NOMBRE_ARCHIVO_LOGO
        )

        firma_ruta = self.firma_var.get().strip()

        self.btn_generar.config(state="disabled", text="Generando...")
        self.label_estado.config(text="Iniciando generación de PDFs...", fg="#D69E2E")
        self.frame.update()

        def _generar_en_hilo():
            try:
                # Cargar firma si se proporcionó
                if firma_ruta:
                    firma_cargada = cargar_imagen_firma(firma_ruta)
                    if not firma_cargada:
                        self.frame.after(0, lambda: self._mostrar_resultado(
                            False, "No se pudo cargar la imagen de firma."
                        ))
                        return

                # Cargar logo
                logo_cargado = cargar_logo_desde_ruta(CARPETA_LOGO, NOMBRE_ARCHIVO_LOGO)
                if not logo_cargado:
                    self.frame.after(0, lambda: self._mostrar_resultado(
                        False, "No se pudo cargar el logo desde la carpeta de datos."
                    ))
                    return

                # Generar PDFs
                exito, mensaje, archivos = generar_todos_los_pdfs(
                    self.datos['df'],
                    self.datos['erons'],
                    self.datos['carpeta_salida']
                )

                self.frame.after(0, lambda: self._mostrar_resultado(exito, mensaje))

            except Exception as e:
                self.frame.after(0, lambda: self._mostrar_resultado(
                    False, f"Error durante la generación: {str(e)}"
                ))

        threading.Thread(target=_generar_en_hilo, daemon=True).start()

    def _mostrar_resultado(self, exito, mensaje):
        self.btn_generar.config(state="normal", text="📄  Generar PDFs")
        if exito:
            self.label_estado.config(text=mensaje, fg="#276749")
        else:
            self.label_estado.config(text=f"Error: {mensaje}", fg="#C53030")

    def destruir(self):
        self.frame.destroy()


