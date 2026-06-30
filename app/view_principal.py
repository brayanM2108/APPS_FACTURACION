import datetime
import io
import os
import tkinter as tk

import cairosvg
import time
from PIL import Image, ImageTk

from features.actas_medicamentos import UIActasMedicamentos
from features.asignar_facturacion.ui import VentanaAsignarFacturacion
from features.agrupar_pdf.ui import VentanaUnirPDF
from features.informe_consolidado.ui import VentanaInformeConsolidado
from features.validar_rips import VentanaValidarRips
from features.comprimir_pdf.ui import VentanaComprimirPDF
from features.completar_rips.ui import VentanaCompletarRips
from features.gestor_archivos.ui.gestor_view import VentanaGestorModerno
from features.gestor_archivos.ui.view_gestor import VentanaGestor
from ui.theme import aplicar_theme_ventana, BG, DEFAULT_SIZE, DEFAULT_MIN_SIZE, SIZE_PRINCIPAL_VIEW

NAVY = "#000927"
ORANGE = "#F97838"
SKY = "#A7E2FF"
BLUE = "#1565C0"
WHITE = "#FFFFFF"
BG2 = "#F5F7FA"
TEXT = "#1E293B"
TEXT_SECONDARY = "#64748B"
BORDER = "#E2E8F0"

LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "ui", "LOGO_OSCURO.svg")


def _cargar_logo(size):
    try:
        if os.path.exists(LOGO_PATH):
            png_data = cairosvg.svg2png(url=LOGO_PATH, output_width=size, output_height=size)
            img = Image.open(io.BytesIO(png_data))
            return ImageTk.PhotoImage(img)
    except Exception:
        pass
    return None


def _cargar_icono(name, size):
    try:
        icono_path = os.path.join(os.path.dirname(__file__), "..", "ui", "assets", name)
        if os.path.exists(icono_path):
            png_data = cairosvg.svg2png(url=icono_path, output_width=size, output_height=size)
            img = Image.open(io.BytesIO(png_data))
            return ImageTk.PhotoImage(img)
    except Exception:
        pass
    return None


class VentanaPrincipal:
    def __init__(self):
        self.root = tk.Tk()
        aplicar_theme_ventana(
            self.root,
            title="APP FACTURACION",
            size=(880, 780),
            min_size=DEFAULT_MIN_SIZE,
            bg=BG2,
            resizable=(True, True),
            fullscreen=True,
        )
        self._crear_ui()

    def _crear_ui(self):
        hero = tk.Frame(self.root, bg=NAVY, height=120)
        hero.pack(fill="x")
        hero.pack_propagate(False)

        self._logo_img = _cargar_logo(180)
        if self._logo_img:
            logo_lbl = tk.Label(hero, image=self._logo_img, bg=NAVY)
            logo_lbl.place(x=28, rely=0.5, anchor="w")

        hero_inner = tk.Frame(hero, bg=NAVY)
        hero_inner.place(relx=0.5, rely=0.5, anchor="center")

        text_col = tk.Frame(hero_inner, bg=NAVY)
        text_col.pack(side="left")

        tk.Label(text_col, text="GOLEMAN FACTURACIÓN HUB",
                 font=("Segoe UI", 20, "bold"), fg=WHITE, bg=NAVY,
                 anchor="w").pack(anchor="w")
        tk.Label(text_col, text="Herramientas de productividad para el área de facturación",
                 font=("Segoe UI", 10), fg=SKY, bg=NAVY,
                 anchor="w").pack(anchor="w")

        tk.Frame(self.root, bg=ORANGE, height=3).pack(fill="x")

        container = tk.Frame(self.root, bg=BG2)
        container.pack(fill="both", expand=True, padx=40, pady=20)

        self._icon_images = {}
        features = [
            ("actas_medicamentos.svg", "📋", "Actas Medicamentos", "Transposición y generación de actas ERON", self._abrir_actas_medicamentos),
            ("gestor_archivos.svg", "📁", "Gestor de Archivos", "Reorganiza archivos por lotes usando un plan Excel", self._abrir_gestor_archivos),
            ("asignar_facturacion.svg", "👥", "Asignar Facturación", "Genera filas por facturador/auxiliar en un archivo Excel", self._abrir_asignar_facturacion),
            ("agrupar_pdf.svg", "📑", "Unir PDF", "Une múltiples archivos PDF en uno solo", self._abrir_unir_pdf),
            ("comprimir_pdf.svg", "🗜", "Comprimir PDF", "Comprime PDFs para reducir su tamaño manteniendo la calidad", self._abrir_comprimir_pdf),
            ("consolidar_informe.svg", "📊", "Consolidar Informe", "Consolida el informe de Facturación", self.abrir_consolidar_informe),
            ("transponer_rips.svg", "🔄", "Transponer RIPS", "Valida y genera transacción, usuarios y consultas en plantilla de RIPS", self._abrir_validar_rips),
            ("completar_rips.svg", "🏥", "Completar RIPS", "Completa los archivos de RIPS", self._abrir_completar_rips),
        ]

        for i, (svg, emoji, titulo, desc, comando) in enumerate(features):
            card = self._card_feature(container, svg, emoji, titulo, desc, comando)
            card.grid(row=i // 2, column=i % 2, sticky="nsew", padx=8, pady=8)

        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        for r in range(4):
            container.grid_rowconfigure(r, weight=1)

        footer = tk.Frame(self.root, bg=WHITE, height=36)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        tk.Label(footer, text="Versión 2.0.0  ·  Goleman IPS - Área de Facturación  · " + datetime.datetime.now().strftime("%Y-%m-%d"),
                 font=("Segoe UI", 9), fg=TEXT_SECONDARY, bg=WHITE).pack(pady=8)

    def _card_feature(self, parent, svg_name, emoji, titulo, descripcion, comando):
        card = tk.Frame(
            parent, bg=WHITE, cursor="hand2",
            highlightthickness=1, highlightbackground=BORDER,
        )

        img = None
        if svg_name:
            key = svg_name.replace(".svg", "")
            if key not in self._icon_images:
                self._icon_images[key] = _cargar_icono(svg_name, 96)
            img = self._icon_images.get(key)

        row = tk.Frame(card, bg=WHITE)
        row.pack(fill="x", padx=20, pady=(20, 16))

        icon_lbl = tk.Label(row, bg=WHITE)
        if img:
            icon_lbl.config(image=img)
        else:
            icon_lbl.config(text=emoji, font=("Segoe UI", 28))
        icon_lbl.pack(side="left", padx=(0, 16))

        text_col = tk.Frame(row, bg=WHITE)
        text_col.pack(side="left", fill="x", expand=True)

        tk.Label(text_col, text=titulo, font=("Segoe UI", 13, "bold"),
                 fg=TEXT, bg=WHITE, anchor="w").pack(anchor="w", fill="x")

        tk.Label(text_col, text=descripcion, font=("Segoe UI", 9),
                 fg=TEXT_SECONDARY, bg=WHITE, anchor="w", wraplength=260).pack(
            anchor="w", fill="x", pady=(2, 0))

        tk.Label(row, text="→", font=("Segoe UI", 16),
                 fg=TEXT_SECONDARY, bg=WHITE).pack(side="right", padx=(10, 0))

        card.bind("<Button-1>", lambda e, c=comando: c())

        def bind_children(w):
            for child in w.winfo_children():
                child.bind("<Button-1>", lambda e, c=comando: c())
                bind_children(child)
        bind_children(card)

        return card

    def _abrir_actas_medicamentos(self):
        UIActasMedicamentos(self.root)

    def _abrir_gestor_archivos(self):
        VentanaGestorModerno(self.root)

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

    def _abrir_completar_rips(self):
        VentanaCompletarRips(self.root)

    def iniciar(self):
        self.root.mainloop()
