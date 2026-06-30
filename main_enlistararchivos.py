import tkinter as tk
from features.gestor_archivos.ui import VentanaGestor

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # ocultar ventana principal

    VentanaGestor(root)

    root.mainloop()

