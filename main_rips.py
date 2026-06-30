import tkinter as tk

from features.completar_rips.ui import VentanaCompletarRips
from features.validar_rips import VentanaValidarRips
from ui.theme import BG, SIZE_PRINCIPAL_VIEW, aplicar_theme_ventana


class VentanaRips:
    def __init__(self):
        self.root = tk.Tk()
        aplicar_theme_ventana(
            self.root,
            title="RIPS",
            size=SIZE_PRINCIPAL_VIEW,
            min_size=(620, 420),
            bg=BG,
            resizable=(False, False),
        )
        self._crear_ui()

    def _crear_ui(self):
        tk.Label(
            self.root,
            text="Herramientas RIPS",
            font=("Segoe UI", 16, "bold"),
            bg="#F0F4F8",
            fg="#1A365D",
        ).pack(pady=(32, 6))

        tk.Label(
            self.root,
            text="Seleccione la herramienta que desea utilizar",
            font=("Segoe UI", 9),
            bg="#F0F4F8",
            fg="#718096",
        ).pack(pady=(0, 28))

        self._boton_feature(
            "Validar RIPS",
            "Valida y genera transaccion, usuarios y consultas en plantilla RIPS",
            self._abrir_validar_rips,
        )

        self._boton_feature(
            "Completar RIPS",
            "Completa archivos de RIPS desde informe, base CSV y parametros",
            self._abrir_completar_rips,
        )

    def _boton_feature(self, titulo, descripcion, comando):
        frame = tk.Frame(
            self.root,
            bg="white",
            cursor="hand2",
            highlightthickness=1,
            highlightbackground="#E2E8F0",
        )
        frame.pack(padx=30, fill="x", pady=5)
        frame.bind("<Button-1>", lambda _event: comando())

        label_titulo = tk.Label(
            frame,
            text=titulo,
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#2D3748",
            anchor="w",
            cursor="hand2",
        )
        label_titulo.pack(padx=14, pady=(10, 2), fill="x")
        label_titulo.bind("<Button-1>", lambda _event: comando())

        label_desc = tk.Label(
            frame,
            text=descripcion,
            font=("Segoe UI", 8),
            bg="white",
            fg="#718096",
            anchor="w",
            cursor="hand2",
        )
        label_desc.pack(padx=14, pady=(0, 10), fill="x")
        label_desc.bind("<Button-1>", lambda _event: comando())

    def _abrir_validar_rips(self):
        VentanaValidarRips(self.root)

    def _abrir_completar_rips(self):
        VentanaCompletarRips(self.root)

    def iniciar(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = VentanaRips()
    app.iniciar()
