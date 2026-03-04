import tkinter as tk
from features.actas_medicamentos import UIActasMedicamentos


class VentanaPrincipal:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("APP FACTURACION")
        self.root.geometry("768x720")
        self.root.resizable(False, False)
        self.root.configure(bg="#F0F4F8")
        self._crear_ui()

    def _crear_ui(self):
        tk.Label(
            self.root, text="APPS DE FACTURACIÓN",
            font=("Segoe UI", 16, "bold"), bg="#F0F4F8", fg="#1A365D"
        ).pack(pady=(32, 6))

        tk.Label(
            self.root, text="Seleccione la herramienta que desea utilizar",
            font=("Segoe UI", 9), bg="#F0F4F8", fg="#718096"
        ).pack(pady=(0, 28))

        self._boton_feature(
            "🏥  Actas Medicamentos",
            "Transposición y generación de actas ERON",
            self._abrir_actas_medicamentos
        )


    def _boton_feature(self, titulo, descripcion, comando):
        frame = tk.Frame(
            self.root, bg="white", cursor="hand2",
            highlightthickness=1, highlightbackground="#E2E8F0"
        )
        frame.pack(padx=30, fill="x", pady=4)
        frame.bind("<Button-1>", lambda e: comando())

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

    def _abrir_actas_medicamentos(self):
        UIActasMedicamentos(self.root)

    def iniciar(self):
        self.root.mainloop()