"""
features/ordernar_pdf/core.py
Lógica de negocio: carga de metadatos y unión de PDFs.
Sin dependencias de tkinter.
"""
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from typing import Callable, Any
import logging
import tempfile
import pandas as pd

import pikepdf
from pypdf import PdfReader

logger = logging.getLogger(__name__)

_THREAD_WORKERS = min(16, (os.cpu_count() or 4) * 2)


def leer_paginas(path: str) -> int:
    """
    Devuelve el nº de páginas de un PDF, o -1 si falla.
    Intenta primero con pikepdf; si el xref está corrupto,
    usa pypdf como fallback (más tolerante con archivos malformados).
    """
    try:
        with pikepdf.open(path) as pdf:
            return len(pdf.pages)
    except pikepdf.PdfError as e:
        logger.warning("pikepdf no pudo leer %s (%s) — intentando con pypdf", path, e)
        try:
            reader = PdfReader(path, strict=False)
            return len(reader.pages)
        except Exception:
            logger.exception("pypdf tampoco pudo leer páginas de: %s", path)
            return -1
    except Exception:
        logger.exception("Error inesperado al leer páginas del PDF: %s", path)
        return -1


@contextmanager
def _abrir_pdf(path: str):
    """
    Abre un PDF con pikepdf. Si el xref está corrupto intenta
    reconstruirlo copiando las páginas vía pypdf como fallback.
    Devuelve un contexto (pdf, recuperado) que garantiza el cierre del PDF.
    """
    pdf = None
    temp_path = None
    try:
        try:
            pdf = pikepdf.open(path)
            yield pdf, False
        except pikepdf.PdfError as e:
            logger.warning("pikepdf no pudo abrir %s (%s) — intentando recuperación con pypdf", path, e)
            try:
                from pypdf import PdfReader, PdfWriter

                reader = PdfReader(path, strict=False)
                writer = PdfWriter()
                for page in reader.pages:
                    writer.add_page(page)

                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    temp_path = tmp.name
                writer.write(temp_path)
                pdf = pikepdf.open(temp_path)
                logger.info("Recuperacion exitosa con pypdf: %s", path)
                yield pdf, True
            except Exception:
                logger.exception("Recuperación fallida para %s — se omitirá", path)
                yield None, False
        except Exception:
            logger.exception("Error inesperado al abrir %s — se omitirá", path)
            yield None, False
    finally:
        if pdf is not None:
            try:
                pdf.close()
            except Exception:
                pass
        if temp_path:
            try:
                os.remove(temp_path)
            except Exception:
                pass


def _documento_desde_nombre(nombre: str) -> str:
    base = os.path.splitext(os.path.basename(nombre))[0]
    if "_" in base:
        return base.split("_", 1)[0]
    return base


def exportar_auditoria_unificacion(auditoria: list[dict[str, Any]], destino_pdf: str) -> str:
    base = os.path.splitext(os.path.basename(destino_pdf))[0]
    ruta_excel = os.path.join(os.path.dirname(destino_pdf), f"{base}_auditoria.xlsx")
    columnas = [
        "DOCUMENTO",
        "ARCHIVO",
        "RUTA",
        "PAGINA_INICIO",
        "PAGINA_FIN",
        "PAGINAS",
        "DESTINO",
    ]
    df = pd.DataFrame(auditoria or [], columns=columnas)
    df.to_excel(ruta_excel, index=False)
    return os.path.abspath(ruta_excel)


def _unir_pdfs_sync(
        paths: list[str],
        destino: str,
        on_progress: Callable[[int, int], None] | None = None,
) -> tuple[int, list[str], list[str], dict[str, int], list[dict[str, Any]]]:
    """
    Une PDFs de forma síncrona y devuelve métricas del proceso.
    """
    writer = pikepdf.Pdf.new()
    total_paginas = 0
    omitidos: list[str] = []
    recuperados: list[str] = []
    paginas_recuperados: dict[str, int] = {}
    auditoria: list[dict[str, Any]] = []

    total_archivos = len(paths)

    for index, path in enumerate(paths, start=1):
        with _abrir_pdf(path) as resultado:
            pdf, recuperado = resultado
            if pdf is None:
                logger.warning("Archivo omitido en la unión: %s", path)
                omitidos.append(path)
                if on_progress:
                    on_progress(index, total_archivos)
                continue
            try:
                if recuperado:
                    recuperados.append(path)
                    pagina_inicial = total_paginas + 1
                pagina_inicio = total_paginas + 1
                num_paginas = len(pdf.pages)
                writer.pages.extend(pdf.pages)
                total_paginas += num_paginas
                if recuperado:
                    paginas_recuperados[path] = pagina_inicial
                pagina_fin = pagina_inicio + num_paginas - 1 if num_paginas > 0 else pagina_inicio
                auditoria.append(
                    {
                        "DOCUMENTO": _documento_desde_nombre(path),
                        "ARCHIVO": os.path.basename(path),
                        "RUTA": path,
                        "PAGINA_INICIO": pagina_inicio,
                        "PAGINA_FIN": pagina_fin,
                        "PAGINAS": num_paginas,
                        "DESTINO": destino,
                    }
                )
            except Exception:
                logger.exception("Error al copiar páginas de %s — se omitirá", path)
                omitidos.append(path)

        if on_progress:
            on_progress(index, total_archivos)

    if os.path.exists(destino):
        try:
            os.remove(destino)
        except Exception as remove_exc:
            raise RuntimeError(f"No se pudo sobrescribir el destino: {destino}") from remove_exc
    writer.save(destino, deterministic_id=True)
    logger.debug(
        "PDF guardado en %s (archivos=%d omitidos=%d paginas=%d)",
        destino, len(paths), len(omitidos), total_paginas,
    )
    return total_paginas, omitidos, recuperados, paginas_recuperados, auditoria


def cargar_metadatos_async(
        paths: list[str],
        cache: dict[str, int],
        on_progress: Callable[[str, int], None],
        on_done: Callable[[], None],
) -> None:
    """
    Lee el nº de páginas de cada path en paralelo (hilo daemon).

    Callbacks (se llaman desde el hilo worker, usar .after() en la UI):
      on_progress(path, n_paginas)  — por cada archivo terminado
      on_done()                     — cuando terminan todos
    """
    nuevos = [p for p in paths if p not in cache]
    if not nuevos:
        on_done()
        return

    def worker():
        with ThreadPoolExecutor(max_workers=_THREAD_WORKERS) as ex:
            futures = {ex.submit(leer_paginas, p): p for p in nuevos}
            for fut in as_completed(futures):
                path = futures[fut]
                try:
                    n = fut.result()
                except Exception as e:
                    logger.exception("Excepción en el future al leer %s: %s", path, e)
                    n = -1
                cache[path] = n
                on_progress(path, n)
        on_done()

    threading.Thread(target=worker, daemon=True).start()


def unir_pdfs(
        paths: list[str],
        destino: str,
        on_progress: Callable[[int, int], None],
        on_done: Callable[[int, int, list[str], list[str], dict[str, int], list[dict[str, Any]], float], None],
        on_error: Callable[[Exception], None],
) -> None:
    """
    Une los PDFs de `paths` en `destino` usando pikepdf (streaming).
    Corre en un hilo daemon para no bloquear la UI.

    Para archivos con xref corrupto intenta recuperarlos vía pypdf
    antes de omitirlos, de modo que el lote completo se procese
    siempre que sea posible.

    Callbacks:
      on_progress(archivos_procesados, total_archivos)
      on_done(total_archivos, total_paginas, omitidos, recuperados, paginas_recuperados, auditoria, segundos_transcurridos)
      on_error(excepcion)
    """
    total = len(paths)

    def worker():
        t_inicio = time.perf_counter()
        try:
            logger.debug("Iniciando unión de %d PDFs en %s", total, destino)
            total_paginas, omitidos, recuperados, paginas_recuperados, auditoria = _unir_pdfs_sync(
                paths,
                destino,
                on_progress=on_progress,
            )
            if recuperados:
                logger.info("Recuperados con pypdf (%d): %s", len(recuperados), "; ".join(recuperados))
            else:
                logger.info("Recuperados con pypdf: ninguno")
            if omitidos:
                logger.info("Archivos omitidos (%d): %s", len(omitidos), "; ".join(omitidos))
            else:
                logger.info("Archivos omitidos: ninguno")
            on_done(
                total,
                total_paginas,
                omitidos,
                recuperados,
                paginas_recuperados,
                auditoria,
                time.perf_counter() - t_inicio,
            )

        except Exception as e:
            logger.exception("Error durante la unión de PDFs: %s", e)
            on_error(e)

    threading.Thread(target=worker, daemon=True).start()

def unir_pdfs_por_carpeta(
        root_dir: str,
        output_dir: str,
        on_progress,
        on_done,
        on_error,
) -> None:
    """
    Une PDFs por cada subcarpeta de primer nivel dentro de `root_dir`.

    Los PDFs resultantes se guardan en `output_dir`
    usando el nombre de cada subcarpeta.
    """

    def worker():
        t_inicio = time.perf_counter()

        try:
            os.makedirs(output_dir, exist_ok=True)

            subdirs = [e.path for e in os.scandir(root_dir) if e.is_dir()]

            total = len(subdirs)
            pdfs_generados = 0
            total_paginas = 0

            carpetas_sin_pdfs: list[str] = []
            omitidos_por_carpeta: dict[str, list[str]] = {}
            recuperados_por_carpeta: dict[str, list[str]] = {}

            for i, carpeta in enumerate(subdirs):
                nombre_carpeta = os.path.basename(carpeta)

                destino = os.path.join(
                    output_dir,
                    f"{nombre_carpeta}.pdf"
                )

                pdfs = [
                    os.path.join(carpeta, f)
                    for f in os.listdir(carpeta)
                    if f.lower().endswith(".pdf")
                       and os.path.isfile(os.path.join(carpeta, f))
                ]

                if not pdfs:
                    carpetas_sin_pdfs.append(carpeta)
                    on_progress(i + 1, total, carpeta, destino)
                    continue

                total_pag, omitidos, recuperados, _paginas_recuperados, _ = (
                    _unir_pdfs_sync(pdfs, destino)
                )

                total_paginas += total_pag
                pdfs_generados += 1

                if omitidos:
                    omitidos_por_carpeta[carpeta] = omitidos

                if recuperados:
                    recuperados_por_carpeta[carpeta] = recuperados

                on_progress(i + 1, total, carpeta, destino)

            on_done(
                total,
                pdfs_generados,
                total_paginas,
                carpetas_sin_pdfs,
                omitidos_por_carpeta,
                recuperados_por_carpeta,
                time.perf_counter() - t_inicio,
                )

        except Exception as e:
            logger.exception("Error durante la unión por carpeta: %s", e)
            on_error(e)

    threading.Thread(target=worker, daemon=True).start()
