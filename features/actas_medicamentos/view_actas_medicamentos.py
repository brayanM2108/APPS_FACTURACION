import tkinter as tk
from features.actas_medicamentos.transposicion.ui.view_transponer_medicamentos import VentanaTransposicion
from features.actas_medicamentos.generador_actas.ui.view_generador_actas import VistaCarga


class UIActasMedicamentos:
    def __init__(self, parent):
        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Actas Medicamentos")
        self.ventana.geometry("560x400")
        self.ventana.resizable(False, False)
        self.ventana.configure(bg="#F0F4F8")

        self.vista_actual = None
        self._mostrar_menu()

    # ── NAVEGACIÓN ───────────────────────────────────────────

    def _mostrar_menu(self):
        self._destruir_vista_actual()
        self.vista_actual = self._construir_menu()

    def _ir_a_transposicion(self):
        self._destruir_vista_actual()
        # VentanaTransposicion usa Toplevel propio, le pasamos on_volver
        # para que el botón volver regrese al menú
        self.vista_actual = VentanaTransposicion(
            self.ventana,
            on_volver=self._mostrar_menu
        )

    def _ir_a_generador(self):
        self._destruir_vista_actual()
        # VistaCarga es un Frame, vive dentro de self.ventana
        self.vista_actual = VistaCarga(
            self.ventana,
            on_completado=self._ir_a_generacion,    # avanza a la siguiente vista
            on_volver=self._mostrar_menu             # regresa al menú
        )

    def _ir_a_generacion(self, datos):
        from features.actas_medicamentos.generador_actas.ui.view_generador_actas import VistaGeneracion
        self._destruir_vista_actual()
        self.vista_actual = VistaGeneracion(
            self.ventana,
            datos=datos,
            on_volver=self._ir_a_generador           # volver = regresa a VistaCarga
        )

    # ── MENÚ ─────────────────────────────────────────────────

    def _construir_menu(self):
        frame = tk.Frame(self.ventana, bg="#F0F4F8")
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame, text="Actas Medicamentos",
            font=("Segoe UI", 15, "bold"), bg="#F0F4F8", fg="#1A365D"
        ).pack(pady=(36, 6))

        tk.Label(
            frame, text="¿Qué deseas hacer?",
            font=("Segoe UI", 9), bg="#F0F4F8", fg="#718096"
        ).pack(pady=(0, 28))

        self._boton_opcion(
            frame,
            titulo="💊  Transposición de Medicamentos",
            descripcion="Convierte registros verticales a horizontales por paciente",
            comando=self._ir_a_transposicion
        )

        self._boton_opcion(
            frame,
            titulo="📄  Generador de Actas ERON",
            descripcion="Genera PDFs de actas de medicamentos por ERON",
            comando=self._ir_a_generador
        )

        return frame

    def _boton_opcion(self, parent, titulo, descripcion, comando):
        frame = tk.Frame(
            parent, bg="white", cursor="hand2",
            highlightthickness=1, highlightbackground="#E2E8F0"
        )
        frame.pack(padx=30, fill="x", pady=5)
        frame.bind("<Button-1>", lambda e: comando())

        label_titulo = tk.Label(
            frame, text=titulo,
            font=("Segoe UI", 10, "bold"),
            bg="white", fg="#2D3748", anchor="w", cursor="hand2"
        )
        label_titulo.pack(padx=14, pady=(12, 2), fill="x")
        label_titulo.bind("<Button-1>", lambda e: comando())

        label_desc = tk.Label(
            frame, text=descripcion,
            font=("Segoe UI", 8),
            bg="white", fg="#718096", anchor="w", cursor="hand2"
        )
        label_desc.pack(padx=14, pady=(0, 12), fill="x")
        label_desc.bind("<Button-1>", lambda e: comando())

    # ── UTILIDAD ─────────────────────────────────────────────

    def _destruir_vista_actual(self):
        if self.vista_actual is None:
            return
        if isinstance(self.vista_actual, tk.Frame):
            self.vista_actual.destroy()
        else:
            self.vista_actual.destruir()
        self.vista_actual = None