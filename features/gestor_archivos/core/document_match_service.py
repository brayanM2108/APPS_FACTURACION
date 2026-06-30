import os
import re

import pandas as pd


COLUMNA_DOCUMENTOS = "DOCUMENTOS"


def _normalizar_documento(valor):
    if pd.isna(valor):
        return ""

    documento = str(valor).strip()

    if documento.endswith(".0"):
        documento = documento[:-2]

    return documento


def leer_documentos_excel(archivo_excel):
    df = pd.read_excel(archivo_excel, dtype=str)

    if COLUMNA_DOCUMENTOS not in df.columns:
        columnas = ", ".join(str(col) for col in df.columns)
        raise ValueError(
            f"El Excel debe tener una columna llamada {COLUMNA_DOCUMENTOS}. "
            f"Columnas encontradas: {columnas}"
        )

    documentos = []
    vistos = set()

    for valor in df[COLUMNA_DOCUMENTOS]:
        documento = _normalizar_documento(valor)

        if not documento or documento in vistos:
            continue

        documentos.append(documento)
        vistos.add(documento)

    return documentos


def leer_documentos_texto(texto):
    documentos = []
    vistos = set()

    for valor in re.split(r"[\s,;]+", texto):
        documento = _normalizar_documento(valor)

        if not documento or documento in vistos:
            continue

        documentos.append(documento)
        vistos.add(documento)

    return documentos


def cruzar_documentos_lista(documentos, archivos):
    coincidencias = []
    sin_coincidencia = []

    archivos_por_nombre = [
        {
            **archivo,
            "nombre_normalizado": archivo["nombre"].lower(),
        }
        for archivo in archivos
    ]

    for documento in documentos:
        documento_normalizado = documento.lower()
        encontrados = [
            archivo for archivo in archivos_por_nombre
            if documento_normalizado in archivo["nombre_normalizado"]
        ]

        if not encontrados:
            sin_coincidencia.append(documento)
            continue

        for archivo in encontrados:
            coincidencias.append(
                {
                    "documento": documento,
                    "archivo": archivo["nombre"],
                    "carpeta": archivo["carpeta"],
                    "ruta": archivo["ruta"],
                    "extension": archivo["extension"],
                    "peso": archivo["peso"],
                    "tipo": "archivo",
                }
            )

    return {
        "documentos": documentos,
        "coincidencias": coincidencias,
        "sin_coincidencia": sin_coincidencia,
        "total_documentos": len(documentos),
        "total_coincidencias": len(coincidencias),
        "tipo": "archivos",
    }


def cruzar_documentos_archivos(archivo_excel, archivos):
    documentos = leer_documentos_excel(archivo_excel)
    return cruzar_documentos_lista(documentos, archivos)


def cruzar_documentos_texto(texto, archivos):
    documentos = leer_documentos_texto(texto)
    return cruzar_documentos_lista(documentos, archivos)


def cruzar_carpetas_texto(texto, carpetas):
    nombres = leer_documentos_texto(texto)
    coincidencias = []
    sin_coincidencia = []

    carpetas_normalizadas = [
        {
            "nombre": os.path.basename(carpeta),
            "ruta": carpeta,
            "nombre_normalizado": os.path.basename(carpeta).lower(),
        }
        for carpeta in carpetas
    ]

    for nombre in nombres:
        nombre_normalizado = nombre.lower()
        encontrados = [
            carpeta for carpeta in carpetas_normalizadas
            if nombre_normalizado in carpeta["nombre_normalizado"]
        ]

        if not encontrados:
            sin_coincidencia.append(nombre)
            continue

        for carpeta in encontrados:
            coincidencias.append(
                {
                    "documento": nombre,
                    "archivo": carpeta["nombre"],
                    "carpeta": os.path.dirname(carpeta["ruta"]),
                    "ruta": carpeta["ruta"],
                    "extension": "",
                    "peso": 0,
                    "tipo": "carpeta",
                }
            )

    return {
        "documentos": nombres,
        "coincidencias": coincidencias,
        "sin_coincidencia": sin_coincidencia,
        "total_documentos": len(nombres),
        "total_coincidencias": len(coincidencias),
        "tipo": "carpetas",
    }


def exportar_coincidencias_excel(resultado, ruta_destino):
    filas = resultado["coincidencias"]

    df = pd.DataFrame(
        filas,
        columns=["documento", "archivo", "carpeta", "ruta", "extension", "peso"],
    )

    df.rename(
        columns={
            "documento": "DOCUMENTO",
            "archivo": "ARCHIVO",
            "carpeta": "CARPETA",
            "ruta": "RUTA",
            "extension": "EXTENSION",
            "peso": "PESO",
        },
        inplace=True,
    )

    if resultado["sin_coincidencia"]:
        sin_match = pd.DataFrame(
            {"DOCUMENTO": resultado["sin_coincidencia"]}
        )

        with pd.ExcelWriter(ruta_destino, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Coincidencias", index=False)
            sin_match.to_excel(writer, sheet_name="Sin coincidencia", index=False)
    else:
        df.to_excel(ruta_destino, index=False)

    return os.path.abspath(ruta_destino)
