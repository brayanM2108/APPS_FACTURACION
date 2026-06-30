import os
from concurrent.futures import ThreadPoolExecutor

from features.gestor_archivos.core.file_service import FileService


class OperationsService:
    def __init__(self, logger=None, progress_callback=None):
        self.file_service = FileService()
        self.logger = logger
        self.progress_callback = progress_callback

    def ejecutar_operaciones(self, operaciones):
        total = len(operaciones)

        if total == 0:
            return []

        completados = 0
        resultados = []

        def procesar(op):
            accion = op["accion"]
            origen = op["origen"]
            destino = op.get("destino")

            try:
                if accion == "mover":
                    self.file_service.mover(origen, destino)
                elif accion == "copiar":
                    self.file_service.copiar(origen, destino)
                elif accion == "eliminar":
                    self.file_service.eliminar(origen)
                elif accion == "mover_carpeta":
                    self.file_service.mover_carpeta(origen, destino)
                elif accion == "copiar_carpeta":
                    self.file_service.copiar_carpeta(origen, destino)
                else:
                    raise ValueError(f"Accion no soportada: {accion}")

                if self.logger:
                    self.logger(f"OK {accion.upper()} -> {os.path.basename(origen)}")

                return {"ok": True, "operacion": op, "error": None}

            except Exception as e:
                if self.logger:
                    self.logger(f"ERROR {os.path.basename(origen)} -> {str(e)}", error=True)

                return {"ok": False, "operacion": op, "error": str(e)}

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(procesar, op) for op in operaciones]

            for future in futures:
                resultados.append(future.result())
                completados += 1

                if self.progress_callback:
                    self.progress_callback(completados, total)

        return resultados
