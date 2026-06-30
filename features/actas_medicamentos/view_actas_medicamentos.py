import io
import tkinter as tk
from pathlib import Path

import cairosvg
from PIL import Image, ImageTk

from features.actas_medicamentos.transposicion.ui.view_transponer_medicamentos import VentanaTransposicion
from features.actas_medicamentos.generador_actas.ui.view_generador_actas import VistaCarga
from ui.theme import aplicar_theme_ventana, COMPACT_SIZE, COMPACT_MIN, BG, WHITE, TEXT, MUTED, BORDER, ACCENT, ACCENT2, NAVY, ORANGE, SKY, BLUE


def _cargar_logo(size):
    logo_path = Path(__file__).parents[2] / "ui" / "LOGO_OSCURO.svg"
    if logo_path.exists():
        png_data = cairosvg.svg2png(url=str(logo_path), output_width=size, output_height=size)
        img = Image.open(io.BytesIO(png_data))
        return ImageTk.PhotoImage(img)
    return None


def _cargar_icono(size):
    icono_path = Path(__file__).parents[2] / "ui" / "assets" / "actas_medicamentos.svg"
    if icono_path.exists():
        png_data = cairosvg.svg2png(url=str(icono_path), output_width=size, output_height=size)
        img = Image.open(io.BytesIO(png_data))
        return ImageTk.PhotoImage(img)
    return None


class UIActasMedicamentos:
    def __init__(self, parent):
        self.ventana = tk.Toplevel(parent)
        # aplicar theme a esta ventana
        aplicar_theme_ventana(
            self.ventana,
            title="Actas Medicamentos",
            size=COMPACT_SIZE,
            min_size=COMPACT_MIN,
            bg=BG,
            resizable=(True, True),
            fullscreen=True,
        )

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
        body = tk.Frame(self.ventana, bg=BG)
        body.pack(fill="both", expand=True)

        # Sidebar
        side = tk.Frame(body, bg=NAVY, width=270)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        self._logo_img = _cargar_logo(160)
        if self._logo_img:
            tk.Label(side, image=self._logo_img, bg=NAVY).pack(pady=(28, 0))

        tk.Label(side, text="ACTAS\nMEDICAMENTOS",
                 font=("Segoe UI", 16, "bold"), fg=WHITE, bg=NAVY,
                 anchor="w", justify="left").pack(padx=24, pady=(16, 8), fill="x")
        tk.Label(side, text="Transposición y generación de actas ERON.",
                 font=("Segoe UI", 10), fg=SKY, bg=NAVY,
                 anchor="w", wraplength=220, justify="left").pack(padx=24, fill="x")
        # Feature icon
        self._icon_sidebar = _cargar_icono(200)
        if self._icon_sidebar:
            icon_frame = tk.Frame(side, bg=NAVY, width=270, height=220)
            icon_frame.pack(fill="x", pady=(20, 0))
            icon_frame.pack_propagate(False)
            tk.Label(icon_frame, image=self._icon_sidebar, bg=NAVY).place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(side, text="Versión 2.0",
                 font=("Segoe UI", 9), fg=MUTED, bg=NAVY,
                 anchor="w").pack(padx=24, pady=(0, 24), side="bottom", fill="x")

        # Main
        main = tk.Frame(body, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        hdr = tk.Frame(main, bg=BG)
        hdr.pack(fill="x", padx=32, pady=(24, 20))
        col = tk.Frame(hdr, bg=BG)
        col.pack(side="left")
        tk.Label(col, text="Actas Medicamentos",
                 font=("Segoe UI", 18, "bold"), fg=NAVY, bg=BG,
                 anchor="w").pack(anchor="w")
        tk.Label(col, text="¿Qué deseas hacer?",
                 font=("Segoe UI", 10), fg=MUTED, bg=BG,
                 anchor="w").pack(anchor="w", pady=(2, 0))

        self._boton_opcion(
            main,
            titulo="💊  Transposición de Medicamentos",
            descripcion="Convierte registros verticales a horizontales por paciente",
            comando=self._ir_a_transposicion
        )

        self._boton_opcion(
            main,
            titulo="📄  Generador de Actas ERON",
            descripcion="Genera PDFs de actas de medicamentos por ERON",
            comando=self._ir_a_generador
        )

        act = tk.Frame(main, bg=BG)
        act.pack(fill="x", padx=32, pady=(16, 0))
        tk.Button(
            act, text="←  Volver",
            font=("Segoe UI", 10),
            bg=BLUE, fg=WHITE, width=16, padx=8, pady=4,
            relief="flat", cursor="hand2",
            activebackground=ACCENT2,
            command=self.ventana.destroy
        ).pack(side="right")

        return body

    def _boton_opcion(self, parent, titulo, descripcion, comando):
        frame = tk.Frame(
            parent, bg=WHITE, cursor="hand2",
            highlightthickness=1, highlightbackground=BORDER
        )
        frame.pack(padx=30, fill="x", pady=5)
        frame.bind("<Button-1>", lambda e: comando())

        label_titulo = tk.Label(
            frame, text=titulo,
            font=("Segoe UI", 10, "bold"),
            bg=WHITE, fg=TEXT, anchor="w", cursor="hand2"
        )
        label_titulo.pack(padx=14, pady=(12, 2), fill="x")
        label_titulo.bind("<Button-1>", lambda e: comando())

        label_desc = tk.Label(
            frame, text=descripcion,
            font=("Segoe UI", 8),
            bg=WHITE, fg=MUTED, anchor="w", cursor="hand2"
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