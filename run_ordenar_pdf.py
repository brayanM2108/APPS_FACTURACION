"""Launcher standalone para la feature de unir PDFs."""

import tkinter as tk

from features.agrupar_pdf.ui.view_pdf import VentanaUnirPDF


def main() -> None:
    # Root oculto: la ventana visible es solo la feature VentanaUnirPDF.
    root = tk.Tk()
    root.withdraw()

    ventana = VentanaUnirPDF(root)
    ventana.protocol("WM_DELETE_WINDOW", lambda: (ventana.destroy(), root.destroy()))

    # Cierra toda la app cuando el Toplevel se cierre.
    root.wait_window(ventana)
    if root.winfo_exists():
        root.destroy()


if __name__ == "__main__":
    main()

