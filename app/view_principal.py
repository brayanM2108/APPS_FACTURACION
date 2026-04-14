import tkinter as tk
from features.actas_medicamentos import UIActasMedicamentos
from features.gestor_archivos.ui import VentanaGestor
from features.asignar_facturacion.ui import VentanaAsignarFacturacion
from features.agrupar_pdf.ui import VentanaUnirPDF
from features.informe_consolidado.ui import VentanaInformeConsolidado
from features.validar_rips import VentanaValidarRips
from features.comprimir_pdf.ui import VentanaComprimirPDF
from ui.theme import aplicar_theme_ventana, BG, DEFAULT_SIZE, DEFAULT_MIN_SIZE, SIZE_PRINCIPAL_VIEW

class VentanaPrincipal:
    def __init__(self):
        self.root = tk.Tk()
        # aplicar theme centralizado
        aplicar_theme_ventana(
            self.root,
            title="APP FACTURACION",
            size=SIZE_PRINCIPAL_VIEW,
            min_size=DEFAULT_MIN_SIZE,
            bg=BG,
            resizable=(False, False),
        )
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

        self._boton_feature(
            "📁  Gestor de Archivos",
            "Reorganiza archivos por lotes usando un plan Excel",
            self._abrir_gestor_archivos
        )

        self._boton_feature(
            "🧾  Asignar Facturación",
            "Genera filas por facturador/auxiliar en un archivo Excel",
            self._abrir_asignar_facturacion
        )

        self._boton_feature(
            "🧾  Unir pdf",
            "Une multiples archivos PDF en uno solo",
            self._abrir_unir_pdf
        )

        self._boton_feature(
            "🗜 Comprimir PDF",
            "Comprime PDFs para reducir su tamaño manteniendo la calidad",
            self._abrir_comprimir_pdf
        )

        self._boton_feature(
            "📊  Consolidar Informe",
            "Consolida el informe de Facturaciòn",
            self.abrir_consolidar_informe
        )

        self._boton_feature(
            "🧪  TRANSPONER RIPS A PLANTILLA",
            "Valida y genera transaccion, usuarios y consultas en plantilla de rips",
            self._abrir_validar_rips
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

    def _abrir_gestor_archivos(self):
        VentanaGestor(self.root)

    def _abrir_asignar_facturacion(self):
        VentanaAsignarFacturacion(self.root)

    def _abrir_unir_pdf(self):
        VentanaUnirPDF(self.root)

    def abrir_consolidar_informe(self):
        VentanaInformeConsolidado(self.root)

    def _abrir_validar_rips(self):
        VentanaValidarRips(self.root)

    def _abrir_comprimir_pdf(self):
        VentanaComprimirPDF(self.root)

    def iniciar(self):
        self.root.mainloop()