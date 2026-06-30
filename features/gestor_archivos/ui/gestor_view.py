import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from features.gestor_archivos.core.document_match_service import (
    cruzar_carpetas_texto,
    cruzar_documentos_archivos,
    cruzar_documentos_texto,
)
from features.gestor_archivos.core.operations_service import OperationsService
from features.gestor_archivos.core.scan_service import escanear_carpeta
from features.gestor_archivos.ui.document_match_window import DocumentMatchPanel
from features.gestor_archivos.ui.explorer_panel import ExplorerPanel
from features.gestor_archivos.ui.logs_panel import LogsPanel
from features.gestor_archivos.ui.operations_panel import OperationsPanel
from features.gestor_archivos.ui.toolbar import Toolbar


class VentanaGestorModerno:
    def __init__(self, parent=None):
        self.root = tk.Toplevel(parent)
        self.root.title("Gestor de Archivos")
        self.root.configure(bg="#F8FAFC")
        try:
            self.root.state("zoomed")
        except Exception:
            self.root.geometry("1400x800")
        self.root.minsize(1100, 700)

        self.operaciones = []
        self.carpeta_actual = None
        self.ejecutando = False
        self.escaneando = False

        self._crear_ui()

    def _crear_ui(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_rowconfigure(2, weight=0)
        self.root.grid_rowconfigure(3, weight=0)

        self.toolbar = Toolbar(
            self.root,
            {
                "abrir": self.abrir_carpeta,
                "cruzar_excel": self.cruzar_excel_documentos,
                "cruzar_texto": self.abrir_cruce_documentos_texto,
                "cruzar_carpetas": self.abrir_cruce_carpetas_texto,
                "exportar_archivos": self.exportar_archivos_listados,
                "limpiar_archivos": self.limpiar_archivos_listados,
                "ejecutar": self.ejecutar,
                "limpiar": self.limpiar,
            },
        )
        self.toolbar.frame.grid(row=0, column=0, sticky="ew")

        main_paned = tk.PanedWindow(
            self.root,
            orient="horizontal",
            sashrelief="flat",
            bg="#CBD5E1",
        )
        main_paned.grid(row=1, column=0, sticky="nsew")

        self.explorer = ExplorerPanel(
            main_paned,
            on_add_operation=self.agregar_operaciones,
        )
        main_paned.add(self.explorer.frame, minsize=650)

        self.match_panel = DocumentMatchPanel(
            main_paned,
            on_add_operation=self.agregar_operaciones,
            on_log=self._log_direct,
            on_progress=self._set_task_progress,
            on_progress_reset=self._reset_task_progress,
        )
        main_paned.add(self.match_panel.frame, minsize=380)

        self.operations_panel = OperationsPanel(self.root)
        self.operations_panel.frame.grid(row=2, column=0, sticky="ew")

        bottom = tk.Frame(self.root, bg="#F8FAFC")
        bottom.grid(row=3, column=0, sticky="ew")

        self.logs = LogsPanel(bottom)
        self.logs.frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        self.progress = ttk.Progressbar(bottom, mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=(0, 10))

        self.estado = tk.Label(
            bottom,
            text="0 operaciones pendientes",
            anchor="w",
            bg="#F8FAFC",
            fg="#475569",
            font=("Segoe UI", 9),
        )
        self.estado.pack(fill="x", padx=10, pady=(0, 10))

    def abrir_carpeta(self):
        if self.ejecutando or self.escaneando:
            return

        carpeta = filedialog.askdirectory(title="Seleccionar carpeta")

        if not carpeta:
            return

        self.carpeta_actual = carpeta
        self.logs.log(f"Escaneando carpeta: {carpeta}")
        self._iniciar_animacion_escaneo()
        self.match_panel.limpiar()

        threading.Thread(
            target=self._scan_thread,
            args=(carpeta,),
            daemon=True,
        ).start()

    def _scan_thread(self, carpeta):
        try:
            archivos = escanear_carpeta(carpeta)
            self.root.after(
                0,
                lambda: self._cargar_archivos_ui(archivos),
            )
        except Exception as e:
            mensaje = str(e)
            self.root.after(
                0,
                lambda: self._mostrar_error_escaneo(mensaje),
            )

    def _cargar_archivos_ui(self, archivos):
        self._detener_animacion_escaneo()
        self.explorer.cargar_archivos(archivos)
        self.estado.config(text=f"{len(self.operaciones)} operaciones pendientes")
        self.logs.log(f"OK {len(archivos)} archivos encontrados")

    def _mostrar_error_escaneo(self, mensaje):
        self._detener_animacion_escaneo()
        self.estado.config(text=f"{len(self.operaciones)} operaciones pendientes")
        self.logs.log(f"ERROR al escanear carpeta: {mensaje}", True)

    def _iniciar_animacion_escaneo(self):
        self.escaneando = True
        self.progress.configure(mode="indeterminate")
        self.progress.start(12)
        self.estado.config(text="Escaneando carpeta...")

    def _detener_animacion_escaneo(self):
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress["value"] = 0
        self.escaneando = False

    def cruzar_excel_documentos(self):
        if self.ejecutando:
            return

        if not self.explorer.archivos:
            messagebox.showwarning(
                "Sin carpeta analizada",
                "Primero abre y analiza una carpeta.",
            )
            return

        archivo_excel = filedialog.askopenfilename(
            title="Seleccionar Excel con columna DOCUMENTOS",
            filetypes=[("Archivos Excel", "*.xlsx")],
        )

        if not archivo_excel:
            return

        self.logs.log(f"Cruzando documentos desde: {archivo_excel}")

        threading.Thread(
            target=self._cruzar_excel_thread,
            args=(archivo_excel, list(self.explorer.archivos)),
            daemon=True,
        ).start()

    def abrir_cruce_documentos_texto(self):
        if self.ejecutando:
            return

        if not self.explorer.archivos:
            messagebox.showwarning(
                "Sin carpeta analizada",
                "Primero abre y analiza una carpeta.",
            )
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Cruzar documentos")
        dialog.geometry("520x420")
        dialog.minsize(420, 320)
        dialog.configure(bg="#F8FAFC")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(
            dialog,
            text="Pega los documentos a cruzar",
            font=("Segoe UI", 10, "bold"),
            bg="#F8FAFC",
            fg="#0F172A",
            anchor="w",
        ).pack(fill="x", padx=12, pady=(12, 6))

        text = tk.Text(
            dialog,
            height=14,
            font=("Consolas", 10),
            wrap="none",
        )
        text.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        text.focus_set()

        actions = tk.Frame(dialog, bg="#F8FAFC")
        actions.pack(fill="x", padx=12, pady=(0, 12))

        def cruzar():
            contenido = text.get("1.0", "end").strip()

            if not contenido:
                messagebox.showwarning(
                    "Sin documentos",
                    "Pega al menos un documento para cruzar.",
                    parent=dialog,
                )
                return

            dialog.destroy()
            self.logs.log("Cruzando documentos pegados por el usuario")
            threading.Thread(
                target=self._cruzar_documentos_texto_thread,
                args=(contenido, list(self.explorer.archivos)),
                daemon=True,
            ).start()

        ttk.Button(
            actions,
            text="Cruzar",
            command=cruzar,
        ).pack(side="right")

        ttk.Button(
            actions,
            text="Cancelar",
            command=dialog.destroy,
        ).pack(side="right", padx=(0, 8))

    def abrir_cruce_carpetas_texto(self):
        if self.ejecutando:
            return

        if not self.explorer.carpetas:
            messagebox.showwarning(
                "Sin carpetas analizadas",
                "Primero abre y analiza una carpeta.",
            )
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Cruzar carpetas")
        dialog.geometry("520x420")
        dialog.minsize(420, 320)
        dialog.configure(bg="#F8FAFC")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(
            dialog,
            text="Pega nombres o partes del nombre de carpeta",
            font=("Segoe UI", 10, "bold"),
            bg="#F8FAFC",
            fg="#0F172A",
            anchor="w",
        ).pack(fill="x", padx=12, pady=(12, 6))

        text = tk.Text(
            dialog,
            height=14,
            font=("Consolas", 10),
            wrap="none",
        )
        text.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        text.focus_set()

        actions = tk.Frame(dialog, bg="#F8FAFC")
        actions.pack(fill="x", padx=12, pady=(0, 12))

        def cruzar():
            contenido = text.get("1.0", "end").strip()

            if not contenido:
                messagebox.showwarning(
                    "Sin datos",
                    "Pega al menos un nombre de carpeta para cruzar.",
                    parent=dialog,
                )
                return

            dialog.destroy()
            self.logs.log("Cruzando nombres de carpeta pegados por el usuario")
            resultado = cruzar_carpetas_texto(contenido, list(self.explorer.carpetas))
            self._mostrar_resultado_cruce(resultado)

        ttk.Button(
            actions,
            text="Cruzar",
            command=cruzar,
        ).pack(side="right")

        ttk.Button(
            actions,
            text="Cancelar",
            command=dialog.destroy,
        ).pack(side="right", padx=(0, 8))

    def _cruzar_excel_thread(self, archivo_excel, archivos):
        try:
            resultado = cruzar_documentos_archivos(archivo_excel, archivos)
        except Exception as e:
            mensaje = str(e)
            self.root.after(
                0,
                lambda: messagebox.showerror("Error al cruzar Excel", mensaje),
            )
            self.root.after(
                0,
                lambda: self.logs.log(f"ERROR al cruzar Excel: {mensaje}", True),
            )
            return

        self.root.after(
            0,
            lambda: self._mostrar_resultado_cruce(resultado),
        )

    def _cruzar_documentos_texto_thread(self, texto, archivos):
        try:
            resultado = cruzar_documentos_texto(texto, archivos)
        except Exception as e:
            mensaje = str(e)
            self.root.after(
                0,
                lambda: messagebox.showerror("Error al cruzar documentos", mensaje),
            )
            self.root.after(
                0,
                lambda: self.logs.log(f"ERROR al cruzar documentos: {mensaje}", True),
            )
            return

        self.root.after(
            0,
            lambda: self._mostrar_resultado_cruce(resultado),
        )

    def _mostrar_resultado_cruce(self, resultado):
        tipo = resultado.get("tipo", "archivos")
        self.logs.log(
            "OK cruce finalizado: "
            f"{resultado['total_coincidencias']} {tipo} encontrados para "
            f"{resultado['total_documentos']} valores"
        )

        self.match_panel.cargar_resultado(resultado)

    def exportar_archivos_listados(self):
        archivos = self.explorer.obtener_archivos_listados()

        if not archivos:
            messagebox.showwarning(
                "Sin archivos",
                "No hay archivos listados para exportar.",
            )
            return

        ruta = filedialog.asksaveasfilename(
            title="Guardar archivos listados",
            defaultextension=".xlsx",
            filetypes=[("Archivos Excel", "*.xlsx")],
        )

        if not ruta:
            return

        try:
            import pandas as pd

            df = pd.DataFrame(archivos)
            df = df.rename(
                columns={
                    "nombre": "NOMBRE",
                    "ruta": "RUTA",
                    "extension": "EXTENSION",
                    "peso": "PESO",
                    "carpeta": "CARPETA",
                }
            )
            columnas = ["NOMBRE", "RUTA", "EXTENSION", "PESO", "CARPETA"]
            df[columnas].to_excel(ruta, index=False)
        except Exception as e:
            messagebox.showerror(
                "Error al exportar",
                str(e),
            )
            self.logs.log(f"ERROR al exportar archivos: {str(e)}", True)
            return

        self.logs.log(f"OK archivos exportados: {ruta}")
        messagebox.showinfo(
            "Exportado",
            f"Se exportaron {len(archivos)} archivos.",
        )

    def limpiar_archivos_listados(self):
        if self.ejecutando or self.escaneando:
            return

        self.carpeta_actual = None
        self.explorer.limpiar_archivos()
        self.match_panel.limpiar()
        self.logs.log("OK Archivos listados limpiados")

    def agregar_operaciones(self, operaciones):
        if self.ejecutando:
            return

        self.operaciones.extend(operaciones)
        self.operations_panel.agregar_operaciones(operaciones)
        self.estado.config(text=f"{len(self.operaciones)} operaciones pendientes")
        self.logs.log(f"OK {len(operaciones)} operaciones agregadas")

    def ejecutar(self):
        if self.ejecutando:
            return

        if not self.operaciones:
            messagebox.showwarning(
                "Sin operaciones",
                "No hay operaciones pendientes",
            )
            return

        confirmar = messagebox.askyesno(
            "Confirmar",
            f"Ejecutar {len(self.operaciones)} operaciones?",
        )

        if not confirmar:
            return

        self.ejecutando = True
        self.progress["value"] = 0
        self.progress["maximum"] = len(self.operaciones)
        self.estado.config(text="Procesando operaciones...")

        operaciones = list(self.operaciones)

        threading.Thread(
            target=self._execute_thread,
            args=(operaciones,),
            daemon=True,
        ).start()

    def _execute_thread(self, operaciones):
        service = OperationsService(
            logger=self._log_threadsafe,
            progress_callback=self._progress_threadsafe,
        )

        resultados = service.ejecutar_operaciones(operaciones)
        exitosas = [r["operacion"] for r in resultados if r["ok"]]
        fallidas = [r for r in resultados if not r["ok"]]

        self.root.after(
            0,
            lambda: self._finalizar_ejecucion(exitosas, fallidas),
        )

    def _finalizar_ejecucion(self, exitosas, fallidas):
        self.operaciones.clear()
        self.operations_panel.limpiar()
        self.ejecutando = False

        self.estado.config(
            text=f"Finalizado: {len(exitosas)} correctas, {len(fallidas)} con error"
        )

        if self.carpeta_actual:
            self._iniciar_animacion_escaneo()
            threading.Thread(
                target=self._scan_thread,
                args=(self.carpeta_actual,),
                daemon=True,
            ).start()

        if fallidas:
            messagebox.showwarning(
                "Operaciones finalizadas con errores",
                f"{len(exitosas)} operaciones correctas.\n"
                f"{len(fallidas)} operaciones tuvieron errores. Revisa los logs.",
            )
        else:
            messagebox.showinfo(
                "Completado",
                "Operaciones finalizadas correctamente",
            )

    def _log_threadsafe(self, mensaje, error=False):
        self.root.after(
            0,
            lambda: self.logs.log(mensaje, error),
        )

    def _progress_threadsafe(self, current, total):
        self.root.after(
            0,
            lambda: self._update_progress(current, total),
        )

    def _update_progress(self, current, total):
        self.progress["value"] = current
        porcentaje = int((current / total) * 100)
        self.estado.config(text=f"Procesando... {current}/{total} ({porcentaje}%)")

    def _set_task_progress(self, current, total, text):
        total = max(1, total)
        self.progress.configure(mode="determinate")
        self.progress["maximum"] = total
        self.progress["value"] = current
        porcentaje = int((current / total) * 100)
        self.estado.config(text=f"{text} ({porcentaje}%)")

    def _reset_task_progress(self):
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress["value"] = 0
        self.estado.config(text=f"{len(self.operaciones)} operaciones pendientes")

    def _log_direct(self, mensaje, error=False):
        self.logs.log(mensaje, error)

    def limpiar(self):
        if self.ejecutando:
            return

        self.operaciones.clear()
        self.operations_panel.limpiar()
        self.estado.config(text="0 operaciones pendientes")
        self.logs.log("OK Operaciones limpiadas")
