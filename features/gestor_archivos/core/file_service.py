import os
import shutil


class FileService:
    @staticmethod
    def _normalizar_ext_pdf(ruta):
        nombre, ext = os.path.splitext(ruta)
        if ext.lower() == ".pdf":
            return nombre + ".pdf"
        return ruta

    def _validar_origen(self, origen):
        if not origen:
            raise ValueError("No se indico el archivo origen.")

        if not os.path.isfile(origen):
            raise FileNotFoundError(f"No existe el archivo origen: {origen}")

    def _preparar_destino(self, destino):
        if not destino:
            raise ValueError("No se indico la ruta destino.")

        destino_dir = os.path.dirname(destino)
        if destino_dir:
            os.makedirs(destino_dir, exist_ok=True)

        if os.path.exists(destino):
            raise FileExistsError(f"Ya existe el archivo destino: {destino}")

    def _validar_carpeta_origen(self, origen):
        if not origen:
            raise ValueError("No se indico la carpeta origen.")

        if not os.path.isdir(origen):
            raise FileNotFoundError(f"No existe la carpeta origen: {origen}")

    def mover(self, origen, destino):
        self._validar_origen(origen)
        destino = self._normalizar_ext_pdf(destino)
        self._preparar_destino(destino)
        shutil.move(origen, destino)

    def copiar(self, origen, destino):
        self._validar_origen(origen)
        destino = self._normalizar_ext_pdf(destino)
        self._preparar_destino(destino)
        shutil.copy2(origen, destino)

    def eliminar(self, ruta):
        self._validar_origen(ruta)
        os.remove(ruta)

    def mover_carpeta(self, origen, destino):
        self._validar_carpeta_origen(origen)
        self._preparar_destino(destino)
        shutil.move(origen, destino)

    def copiar_carpeta(self, origen, destino):
        self._validar_carpeta_origen(origen)
        self._preparar_destino(destino)
        shutil.copytree(origen, destino)
