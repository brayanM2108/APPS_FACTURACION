import tkinter as tk
from features.agrupar_pdf.ui import VentanaUnirPDF

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # ocultar ventana principal

    VentanaUnirPDF(root)

    root.mainloop()