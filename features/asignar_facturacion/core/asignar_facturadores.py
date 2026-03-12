import json
import os
import pandas as pd

FACTURADORES_JSON = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "facturadores.json"
)


def cargar_facturadores() -> dict:
    if not os.path.exists(FACTURADORES_JSON):
        raise FileNotFoundError(f"No se encontró el archivo: {FACTURADORES_JSON}")

    with open(FACTURADORES_JSON, "r", encoding="utf-8") as f:
        contenido = f.read().strip()
        if not contenido:
            raise ValueError(f"El archivo JSON está vacío: {FACTURADORES_JSON}")
        return json.loads(contenido)


def generar_excel(
    seleccionados: list[dict],
    ruta_destino: str,
    cantidad_global: int | None = None
) -> str:
    """
    seleccionados   : lista de dicts con {'nombre': str, 'filas': int}
    ruta_destino    : carpeta donde se guarda el Excel
    cantidad_global : si se indica, aplica esa cantidad a TODOS los seleccionados
    Retorna la ruta del archivo generado.
    """
    if not seleccionados:
        raise ValueError("Debes seleccionar al menos un facturador.")

    filas = []
    for item in seleccionados:
        nombre = item["nombre"]
        cantidad = cantidad_global if cantidad_global is not None else item["filas"]
        for _ in range(cantidad):
            filas.append({"Facturador": nombre})

    df = pd.DataFrame(filas)
    ruta_archivo = os.path.join(ruta_destino, "asignacion_facturacion.xlsx")
    df.to_excel(ruta_archivo, index=False)
    return ruta_archivo
