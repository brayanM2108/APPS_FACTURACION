import tkinter as tk

from features.gestor_archivos.ui.gestor_view import VentanaGestorModerno


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    VentanaGestorModerno(root)

    root.mainloop()

