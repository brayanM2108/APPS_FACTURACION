import os
import shutil
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

from features.agrupar_pdf.core.agrupar import unir_pdfs, exportar_auditoria_unificacion
from features.gestor_archivos.core.document_match_service import (
    exportar_coincidencias_excel,
)


COLORS = {
    "bg": "#F5F7FA",
    "surface": "#FFFFFF",
    "border": "#E2E8F0",
    "text_primary": "#1E293B",
    "text_secondary": "#64748B",
    "text_muted": "#94A3B8",
    "accent": "#1565C0",
    "accent_light": "#EFF6FF",
    "warn_bg": "#FEF3C7",
    "warn_fg": "#92400E",
}


def _apply_style():
    style = ttk.Style()
    style.configure(
        "Match.Treeview",
        background=COLORS["surface"],
        fieldbackground=COLORS["surface"],
        foreground=COLORS["text_primary"],
        font=("Segoe UI", 9),
        rowheight=28,
        borderwidth=0,
    )
    style.configure(
        "Match.Treeview.Heading",
        font=("Segoe UI", 9, "bold"),
        background=COLORS["bg"],
        foreground=COLORS["text_secondary"],
        relief="flat",
        borderwidth=0,
        padding=(10, 6),
    )
    style.map(
        "Match.Treeview",
        background=[("selected", COLORS["accent_light"])],
        foreground=[("selected", COLORS["accent"])],
    )
    style.layout("Match.Treeview", [("Match.Treeview.treearea", {"sticky": "nswe"})])


class DocumentMatchPanel:
    def __init__(
        self,
        parent,
        on_add_operation=None,
        on_log=None,
        on_progress=None,
        on_progress_reset=None,
    ):
        self.parent = parent
        self.on_add_operation = on_add_operation
        self.on_log = on_log
        self.on_progress = on_progress
        self.on_progress_reset = on_progress_reset
        self.resultado = None
        self.items = {}

        _apply_style()

        self.frame = tk.Frame(
            parent,
            bg=COLORS["surface"],
            highlightbackground=COLORS["border"],
            highlightthickness=0,
        )
        self._crear_ui()

    def _crear_ui(self):
        header = tk.Frame(self.frame, bg=COLORS["surface"])
        header.pack(fill="x", padx=16, pady=(14, 8))

        self.title_label = tk.Label(
            header,
            text="CRUCE DOCUMENTOS",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["surface"],
            fg=COLORS["text_primary"],
        )
        self.title_label.pack(side="left")

        self._export_btn = tk.Button(
            header,
            text="⬆  Exportar",
            font=("Segoe UI", 9),
            bg=COLORS["accent"],
            fg=COLORS["surface"],
            activebackground="#0D47A1",
            activeforeground=COLORS["surface"],
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4,
            command=self._exportar,
        )
        self._export_btn.pack(side="right")

        self.resumen_label = tk.Label(
            self.frame,
            text="Carga un Excel para ver coincidencias.",
            font=("Segoe UI", 9),
            bg=COLORS["surface"],
            fg=COLORS["text_muted"],
            anchor="w",
        )
        self.resumen_label.pack(fill="x", padx=16, pady=(0, 8))

        actions = tk.Frame(self.frame, bg=COLORS["surface"])
        actions.pack(fill="x", padx=16, pady=(0, 8))

        for texto, cmd in [
            ("Seleccionar todo", self.seleccionar_todos),
            ("Mover", lambda: self._crear_operacion("mover")),
            ("Copiar", lambda: self._crear_operacion("copiar")),
            ("Eliminar", lambda: self._crear_operacion("eliminar")),
            ("Copiar y unificar", self.copiar_y_unificar),
            ("Limpiar", self.limpiar),
        ]:
            self._action_btn(actions, texto, cmd)

        columns = ("documento", "archivo", "ruta")

        table_frame = tk.Frame(self.frame, bg=COLORS["surface"])
        table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="extended",
            style="Match.Treeview",
        )

        self.tree.heading("documento", text="Documento")
        self.tree.heading("archivo", text="Archivo")
        self.tree.heading("ruta", text="Ruta")

        self.tree.column("documento", width=110, stretch=False)
        self.tree.column("archivo", width=185)
        self.tree.column("ruta", width=270)

        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        self.sin_match_label = tk.Label(
            self.frame,
            text="",
            font=("Segoe UI", 8),
            bg=COLORS["warn_bg"],
            fg=COLORS["warn_fg"],
            anchor="w",
            padx=12,
            pady=6,
            wraplength=400,
        )

    @staticmethod
    def _action_btn(parent, texto, cmd):
        btn = tk.Button(
            parent,
            text=texto,
            command=cmd,
            font=("Segoe UI", 9),
            bg=COLORS["bg"],
            fg=COLORS["text_primary"],
            activebackground=COLORS["border"],
            activeforeground=COLORS["accent"],
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4,
        )
        btn.pack(side="left", padx=(0, 6))
        return btn

    def cargar_resultado(self, resultado):
        self.resultado = resultado
        self._actualizar_resumen()
        self._cargar_resultados()

    def limpiar(self):
        self.resultado = None
        self.items = {}
        self.tree.delete(*self.tree.get_children())
        self.resumen_label.config(
            text="Carga un Excel para ver coincidencias.",
            fg=COLORS["text_muted"],
        )
        self.title_label.config(text="CRUCE DOCUMENTOS")
        self.sin_match_label.config(text="")
        self.sin_match_label.pack_forget()

    def _actualizar_resumen(self):
        if not self.resultado:
            return

        total_docs = self.resultado["total_documentos"]
        total_arch = self.resultado["total_coincidencias"]
        sin = len(self.resultado["sin_coincidencia"])
        tipo = self.resultado.get("tipo", "archivos")

        if tipo == "carpetas":
            self.title_label.config(text="CRUCE CARPETAS")
        else:
            self.title_label.config(text="CRUCE DOCUMENTOS")

        self.resumen_label.config(
            text=f"{total_docs} valores  ·  {total_arch} {tipo}  ·  {sin} sin coincidencia",
            fg=COLORS["text_secondary"],
        )

        if self.resultado["sin_coincidencia"]:
            pendientes = ", ".join(self.resultado["sin_coincidencia"][:12])
            if len(self.resultado["sin_coincidencia"]) > 12:
                pendientes += "…"
            self.sin_match_label.config(text=f"Sin coincidencia: {pendientes}")
            self.sin_match_label.pack(fill="x", padx=12, pady=(0, 10))
        else:
            self.sin_match_label.config(text="")
            self.sin_match_label.pack_forget()

    def _cargar_resultados(self):
        self.tree.delete(*self.tree.get_children())
        self.items = {}

        if not self.resultado:
            return

        for item in self.resultado["coincidencias"]:
            item_id = self.tree.insert(
                "",
                "end",
                values=(item["documento"], item["archivo"], item["ruta"]),
            )
            self.items[item_id] = item

    def seleccionar_todos(self):
        items = self.tree.get_children()
        if not items:
            return
        self.tree.selection_set(items)
        self.tree.focus(items[0])

    def _crear_operacion(self, accion):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Sin selección", "Selecciona uno o más archivos primero.", parent=self.frame)
            return

        destino_base = None
        if accion in ["mover", "copiar"]:
            destino_base = filedialog.askdirectory(parent=self.frame, title="Seleccionar carpeta destino")
            if not destino_base:
                return

        operaciones = []
        rutas_agregadas = set()

        for item_id in selected:
            item = self.items.get(item_id)
            if not item:
                continue
            ruta = item["ruta"]
            if ruta in rutas_agregadas:
                continue
            rutas_agregadas.add(ruta)
            accion_op = accion
            if item.get("tipo") == "carpeta":
                accion_op = "mover_carpeta" if accion == "mover" else "copiar_carpeta"

            op = {"accion": accion_op, "origen": ruta}
            if destino_base:
                op["destino"] = os.path.join(destino_base, item["archivo"])
            operaciones.append(op)

        if not operaciones:
            return

        if self.on_add_operation:
            self.on_add_operation(operaciones)

        messagebox.showinfo(
            "Operaciones agregadas",
            f"{len(operaciones)} operaciones agregadas al panel principal.",
            parent=self.frame,
        )

    def copiar_y_unificar(self):
        archivos = self._archivos_unicos()

        if not archivos:
            messagebox.showwarning(
                "Sin archivos",
                "Primero realiza un cruce con coincidencias.",
                parent=self.frame,
            )
            return

        destino_base = filedialog.askdirectory(
            parent=self.frame,
            title="Seleccionar carpeta destino",
        )

        if not destino_base:
            return

        nombre_pdf = simpledialog.askstring(
            "Nombre del PDF",
            "Nombre del archivo unificado:",
            initialvalue="unificado.pdf",
            parent=self.frame,
        )

        if not nombre_pdf:
            return

        nombre_pdf = nombre_pdf.strip()
        if not nombre_pdf:
            return

        if not nombre_pdf.lower().endswith(".pdf"):
            nombre_pdf += ".pdf"

        destino_pdf = os.path.join(destino_base, nombre_pdf)

        if os.path.exists(destino_pdf):
            reemplazar = messagebox.askyesno(
                "Archivo existente",
                f"Ya existe el archivo:\n{destino_pdf}\n\nDeseas reemplazarlo?",
                parent=self.frame,
            )
            if not reemplazar:
                return

        self.resumen_label.config(
            text="Copiando archivos y preparando unificacion...",
            fg=COLORS["accent"],
        )
        self._emit_log(f"Iniciando copia de {len(archivos)} archivos hacia: {destino_base}")
        self._emit_progress(0, len(archivos), "Copiando documentos...")

        threading.Thread(
            target=self._copiar_y_unificar_thread,
            args=(archivos, destino_base, destino_pdf),
            daemon=True,
        ).start()

    def _archivos_unicos(self):
        if not self.resultado:
            return []

        archivos = []
        rutas_agregadas = set()

        for item in self.resultado["coincidencias"]:
            ruta = item["ruta"]

            if ruta in rutas_agregadas:
                continue

            rutas_agregadas.add(ruta)
            archivos.append(item)

        return archivos

    def _copiar_y_unificar_thread(self, archivos, destino_base, destino_pdf):
        try:
            copiados = []
            total_archivos = len(archivos)

            for index, item in enumerate(archivos, start=1):
                origen = item["ruta"]

                if not os.path.isfile(origen):
                    self._emit_log_threadsafe(
                        f"ERROR archivo no encontrado para copiar: {origen}",
                        True,
                    )
                    self._emit_progress_threadsafe(
                        index,
                        total_archivos,
                        f"Copiando documentos... {index}/{total_archivos}",
                    )
                    continue

                destino = self._ruta_copia_unica(
                    destino_base,
                    os.path.basename(origen),
                )
                shutil.copy2(origen, destino)
                copiados.append(destino)
                self._emit_log_threadsafe(
                    f"Copiado documento: {os.path.basename(origen)}"
                )
                self._emit_progress_threadsafe(
                    index,
                    total_archivos,
                    f"Copiando documentos... {index}/{total_archivos}",
                )

            pdfs = [
                path for path in copiados
                if path.lower().endswith(".pdf")
                and os.path.normcase(path) != os.path.normcase(destino_pdf)
            ]

            if not pdfs:
                self._reset_progress_threadsafe()
                self.frame.after(
                    0,
                    lambda: self._mostrar_error_unificacion(
                        "No se encontraron archivos PDF copiados para unificar."
                    ),
                )
                return

            self.frame.after(
                0,
                lambda: self._preparar_unificacion(len(copiados), len(pdfs)),
            )

            unir_pdfs(
                paths=pdfs,
                destino=destino_pdf,
                on_progress=lambda done, total: self.frame.after(
                    0,
                    lambda d=done, t=total: self._actualizar_unificacion(d, t),
                ),
                on_done=lambda total, paginas, omitidos, recuperados, paginas_recuperados, auditoria, segundos: self.frame.after(
                    0,
                    lambda: self._mostrar_exito_unificacion(
                        destino_pdf,
                        len(copiados),
                        total,
                        paginas,
                        omitidos,
                        auditoria,
                    ),
                ),
                on_error=lambda error: self.frame.after(
                    0,
                    lambda: self._mostrar_error_unificacion(str(error)),
                ),
            )
        except Exception as e:
            mensaje = str(e)
            self.frame.after(
                0,
                lambda: self._mostrar_error_unificacion(mensaje),
            )

    @staticmethod
    def _ruta_copia_unica(carpeta, nombre):
        base, extension = os.path.splitext(nombre)
        destino = os.path.join(carpeta, nombre)
        contador = 1

        while os.path.exists(destino):
            destino = os.path.join(carpeta, f"{base}_{contador}{extension}")
            contador += 1

        return destino

    def _mostrar_exito_unificacion(self, destino_pdf, copiados, unidos, paginas, omitidos, auditoria):
        omitidos_txt = f" ({len(omitidos)} omitidos)" if omitidos else ""
        ruta_auditoria = None
        try:
            ruta_auditoria = exportar_auditoria_unificacion(auditoria, destino_pdf)
            self._emit_log(f"Auditoria generada: {ruta_auditoria}")
        except Exception as e:
            self._emit_log(f"ERROR al generar auditoria: {e}", True)
        self._actualizar_resumen()
        self._reset_progress()
        self._emit_log(
            f"Unificacion finalizada: {os.path.basename(destino_pdf)} "
            f"({unidos} PDFs, {paginas} paginas)"
        )
        if omitidos:
            self._emit_log(f"PDFs omitidos durante la unificacion: {len(omitidos)}", True)
        messagebox.showinfo(
            "Copiar y unificar",
            f"Archivos copiados: {copiados}\n"
            f"PDFs unificados: {unidos}{omitidos_txt}\n"
            f"Paginas: {paginas}\n\n"
            f"Archivo generado:\n{destino_pdf}\n\n"
            f"Auditoria:\n{ruta_auditoria or 'no disponible'}",
            parent=self.frame,
        )

    def _mostrar_error_unificacion(self, mensaje):
        self._actualizar_resumen()
        self._reset_progress()
        self._emit_log(f"ERROR al copiar y unificar: {mensaje}", True)
        messagebox.showerror(
            "Error al copiar y unificar",
            mensaje,
            parent=self.frame,
        )

    def _preparar_unificacion(self, copiados, pdfs):
        self.resumen_label.config(
            text=f"{copiados} archivos copiados. Unificando {pdfs} PDFs...",
            fg=COLORS["accent"],
        )
        self._emit_log(f"{copiados} archivos copiados. Iniciando unificacion de {pdfs} PDFs.")
        self._emit_progress(0, pdfs, "Unificando archivos...")

    def _actualizar_unificacion(self, done, total):
        self.resumen_label.config(
            text=f"Unificando PDFs... {done}/{total}",
            fg=COLORS["accent"],
        )
        self._emit_log(f"Unificando archivos: {done}/{total}")
        self._emit_progress(done, total, f"Unificando archivos... {done}/{total}")

    def _emit_log(self, mensaje, error=False):
        if self.on_log:
            self.on_log(mensaje, error)

    def _emit_progress(self, current, total, text):
        if self.on_progress:
            self.on_progress(current, total, text)

    def _reset_progress(self):
        if self.on_progress_reset:
            self.on_progress_reset()

    def _emit_log_threadsafe(self, mensaje, error=False):
        self.frame.after(0, lambda: self._emit_log(mensaje, error))

    def _emit_progress_threadsafe(self, current, total, text):
        self.frame.after(0, lambda: self._emit_progress(current, total, text))

    def _reset_progress_threadsafe(self):
        self.frame.after(0, self._reset_progress)

    def _exportar(self):
        if not self.resultado:
            messagebox.showwarning("Sin resultados", "Primero realiza un cruce de documentos.", parent=self.frame)
            return

        ruta = filedialog.asksaveasfilename(
            parent=self.frame,
            title="Guardar coincidencias",
            defaultextension=".xlsx",
            filetypes=[("Archivos Excel", "*.xlsx")],
        )

        if not ruta:
            return

        try:
            exportar_coincidencias_excel(self.resultado, ruta)
        except Exception as e:
            messagebox.showerror("Error al exportar", str(e), parent=self.frame)
            return

        messagebox.showinfo("Exportado", f"Archivo guardado en:\n{ruta}", parent=self.frame)


class DocumentMatchWindow:
    def __init__(self, parent, resultado, on_add_operation=None):
        self.window = tk.Toplevel(parent)
        self.window.title("Coincidencias por documento")
        self.window.geometry("1100x620")
        self.window.minsize(900, 520)
        self.window.configure(bg=COLORS["bg"])

        self.panel = DocumentMatchPanel(self.window, on_add_operation=on_add_operation)
        self.panel.frame.pack(fill="both", expand=True)
        self.panel.cargar_resultado(resultado)
