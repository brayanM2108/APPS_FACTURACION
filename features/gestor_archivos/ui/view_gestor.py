import tkinter as tk
from tkinter import filedialog, messagebox
import threading


class VentanaGestor:
    def __init__(self, parent):
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Gestor de Archivos")
        self.ventana.geometry("560x400")
        self.ventana.resizable(False, False)
        self.ventana.configure(bg="#F0F4F8")
        self._crear_ui()

    def _crear_ui(self):
        tk.Label(
            self.ventana, text="📁 Gestor de Archivos",
            font=("Segoe UI", 15, "bold"), bg="#F0F4F8", fg="#1A365D"
        ).pack(pady=(28, 4))

        tk.Label(
            self.ventana, text="Crea un plan de movimiento o aplica cambios desde un Excel",
            font=("Segoe UI", 9), bg="#F0F4F8", fg="#718096"
        ).pack(pady=(0, 20))

        # Checkbox simular
        self.simular_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self.ventana, text="✓ Simular (no mover archivos realmente)",
            variable=self.simular_var,
            font=("Segoe UI", 9), bg="#F0F4F8", fg="#2D3748",
            activebackground="#F0F4F8", cursor="hand2"
        ).pack(pady=(0, 16))

        # Acciones
        frame_acciones = tk.Frame(self.ventana, bg="#F0F4F8")
        frame_acciones.pack(padx=30, fill="x")

        self._boton_accion(
            frame_acciones,
            "📋  Crear plan desde carpeta",
            "Escanea una carpeta y genera el Excel con el plan",
            self._crear_plan
        )

        self._boton_accion(
            frame_acciones,
            "✅  Aplicar cambios desde Excel",
            "Lee el Excel editado y ejecuta los movimientos",
            self._aplicar_cambios
        )

        # Estado
        self.label_estado = tk.Label(
            self.ventana, text="",
            font=("Segoe UI", 9), bg="#F0F4F8", fg="#718096",
            wraplength=480, justify="left"
        )
        self.label_estado.pack(padx=30, pady=(16, 0), anchor="w")

    def _boton_accion(self, parent, titulo, descripcion, comando):
        frame = tk.Frame(
            parent, bg="white", cursor="hand2",
            highlightthickness=1, highlightbackground="#E2E8F0"
        )
        frame.pack(fill="x", pady=4)

        # Vincular evento al frame
        frame.bind("<Button-1>", lambda e: comando())

        # Labels con eventos vinculados
        label_titulo = tk.Label(
            frame, text=titulo,
            font=("Segoe UI", 10, "bold"),
            bg="white", fg="#2D3748", anchor="w", cursor="hand2"
        )
        label_titulo.pack(padx=14, pady=(10, 2), fill="x")
        label_titulo.bind("<Button-1>", lambda e: comando())

        label_desc = tk.Label(
            frame, text=descripcion,
            font=("Segoe UI", 8),
            bg="white", fg="#718096", anchor="w", cursor="hand2"
        )
        label_desc.pack(padx=14, pady=(0, 10), fill="x")
        label_desc.bind("<Button-1>", lambda e: comando())

    def _crear_plan(self):
        carpeta = filedialog.askdirectory(title="Seleccionar carpeta a escanear")
        if not carpeta:
            return

        self.label_estado.config(text="⏳ Creando plan...", fg="#D69E2E")
        self.ventana.update()

        threading.Thread(target=self._crear_plan_hilo, args=(carpeta,), daemon=True).start()

    def _crear_plan_hilo(self, carpeta):
        from features.gestor_archivos.core.gestor_service import crear_tabla_edicion
        exito, mensaje, archivo_excel = crear_tabla_edicion(carpeta)

        # Usar after para ejecutar en el hilo principal
        self.ventana.after(0, lambda: self._mostrar_resultado_crear(exito, mensaje))

    def _aplicar_cambios(self):
        archivo_excel = filedialog.askopenfilename(
            title="Seleccionar plan Excel",
            filetypes=[("Archivos Excel", "*.xlsx")]
        )
        if not archivo_excel:
            return

        carpeta_destino = filedialog.askdirectory(title="Seleccionar carpeta destino")
        if not carpeta_destino:
            return

        self.label_estado.config(text="⏳ Aplicando cambios...", fg="#D69E2E")
        self.ventana.update()

        threading.Thread(
            target=self._aplicar_hilo,
            args=(archivo_excel, carpeta_destino, self.simular_var.get()),
            daemon=True
        ).start()

    def _aplicar_hilo(self, archivo_excel, carpeta_destino, simular):
        from features.gestor_archivos.core.gestor_service import aplicar_cambios
        exito, mensaje, log_path = aplicar_cambios(archivo_excel, carpeta_destino, simular)

        # Usar after para ejecutar en el hilo principal
        self.ventana.after(0, lambda: self._mostrar_resultado_aplicar(exito, mensaje, log_path))

    def _mostrar_resultado_crear(self, exito, mensaje):
        """Muestra el resultado de crear el plan"""
        color = "#276749" if exito else "#C53030"
        self.label_estado.config(text=mensaje, fg=color)

        # Mostrar messagebox
        if exito:
            messagebox.showinfo("✓ Plan creado", mensaje)
        else:
            messagebox.showwarning("⚠ Sin archivos", mensaje)

    def _mostrar_resultado_aplicar(self, exito, mensaje, log_path):
        """Muestra el resultado de aplicar cambios"""
        color = "#276749" if exito else "#C53030"
        self.label_estado.config(text=mensaje if exito else "Errores encontrados", fg=color)

        # Mostrar messagebox
        if exito:
            messagebox.showinfo("✓ Éxito", mensaje)
        else:
            messagebox.showwarning("⚠ Errores encontrados", mensaje)
