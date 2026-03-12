import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from features.asignar_facturacion.core.asignar_facturadores import cargar_facturadores, generar_excel


class VentanaAsignarFacturacion(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Asignar Facturación")
        self.geometry("560x620")
        self.resizable(False, False)
        self.configure(bg="#F0F4F8")
        self.grab_set()

        self._datos = cargar_facturadores()
        # {nombre: {'var_check': BooleanVar, 'var_filas': IntVar}}
        self._controles: dict = {}

        self._crear_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _crear_ui(self):
        tk.Label(
            self, text="Asignar Facturación",
            font=("Segoe UI", 14, "bold"), bg="#F0F4F8", fg="#1A365D"
        ).pack(pady=(20, 4))

        tk.Label(
            self, text="Selecciona facturadores/auxiliares y la cantidad de filas",
            font=("Segoe UI", 9), bg="#F0F4F8", fg="#718096"
        ).pack(pady=(0, 14))

        # ── Canvas con scroll ────────────────────────────────────────────────
        contenedor = tk.Frame(self, bg="#F0F4F8")
        contenedor.pack(fill="both", expand=True, padx=24)

        canvas = tk.Canvas(contenedor, bg="#F0F4F8", highlightthickness=0)
        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=canvas.yview)
        self._frame_scroll = tk.Frame(canvas, bg="#F0F4F8")

        self._frame_scroll.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self._frame_scroll, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ── Secciones ────────────────────────────────────────────────────────
        for grupo, miembros in self._datos.items():
            self._crear_seccion(grupo, miembros)

        # ── Botones ──────────────────────────────────────────────────────────
        frame_botones = tk.Frame(self, bg="#F0F4F8")
        frame_botones.pack(pady=16)

        # ── Cantidad global ──────────────────────────────────────────────────────
        frame_global = tk.Frame(self, bg="#F0F4F8")
        frame_global.pack(pady=(8, 0))

        tk.Label(
            frame_global, text="Cantidad global (0 = usar individual):",
            font=("Segoe UI", 9), bg="#F0F4F8", fg="#2D3748"
        ).pack(side="left", padx=(0, 8))

        self._var_cantidad_global = tk.IntVar(value=0)
        tk.Spinbox(
            frame_global, from_=0, to=500,
            textvariable=self._var_cantidad_global,
            width=6, font=("Segoe UI", 9)
        ).pack(side="left")

        tk.Button(
            frame_botones, text="Seleccionar todo",
            font=("Segoe UI", 9), bg="#EBF8FF", fg="#2B6CB0",
            relief="flat", padx=10, pady=6,
            command=self._seleccionar_todo
        ).pack(side="left", padx=6)

        tk.Button(
            frame_botones, text="Limpiar selección",
            font=("Segoe UI", 9), bg="#FFF5F5", fg="#C53030",
            relief="flat", padx=10, pady=6,
            command=self._limpiar_seleccion
        ).pack(side="left", padx=6)

        tk.Button(
            frame_botones, text="📥  Generar Excel",
            font=("Segoe UI", 10, "bold"), bg="#2B6CB0", fg="white",
            relief="flat", padx=16, pady=8,
            command=self._generar
        ).pack(side="left", padx=12)

    def _crear_seccion(self, titulo: str, miembros: list):
        # Encabezado del grupo
        tk.Label(
            self._frame_scroll, text=titulo,
            font=("Segoe UI", 10, "bold"), bg="#F0F4F8", fg="#2D3748"
        ).pack(anchor="w", pady=(12, 4))

        separador = tk.Frame(self._frame_scroll, bg="#CBD5E0", height=1)
        separador.pack(fill="x", pady=(0, 6))

        for nombre in miembros:
            fila = tk.Frame(self._frame_scroll, bg="white",
                            highlightthickness=1, highlightbackground="#E2E8F0")
            fila.pack(fill="x", pady=2)

            var_check = tk.BooleanVar(value=False)
            var_filas = tk.IntVar(value=1)

            self._controles[nombre] = {
                "var_check": var_check,
                "var_filas": var_filas,
            }

            # Checkbox + nombre
            tk.Checkbutton(
                fila, text=nombre,
                variable=var_check,
                font=("Segoe UI", 9), bg="white", fg="#2D3748",
                activebackground="white", anchor="w"
            ).pack(side="left", padx=10, pady=6, fill="x", expand=True)

            # Spinner de filas
            tk.Label(fila, text="Filas:", font=("Segoe UI", 8),
                     bg="white", fg="#718096").pack(side="left")

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