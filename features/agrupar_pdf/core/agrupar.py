"""
features/ordernar_pdf/core.py
Lógica de negocio: carga de metadatos y unión de PDFs.
Sin dependencias de tkinter.
"""
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable
import logging

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


def _abrir_pdf(path: str) -> pikepdf.Pdf | None:
    """
    Abre un PDF con pikepdf. Si el xref está corrupto intenta
    reconstruirlo copiando las páginas vía pypdf como fallback.
    Devuelve un pikepdf.Pdf listo para usar, o None si es irrecuperable.
    """
    try:
        return pikepdf.open(path)
    except pikepdf.PdfError as e:
        logger.warning("pikepdf no pudo abrir %s (%s) — intentando recuperación con pypdf", path, e)
        try:
            import io
            from pypdf import PdfReader, PdfWriter

            reader = PdfReader(path, strict=False)
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)

            buf = io.BytesIO()
            writer.write(buf)
            buf.seek(0)
            return pikepdf.open(buf)
        except Exception:
            logger.exception("Recuperación fallida para %s — se omitirá", path)
            return None
    except Exception:
        logger.exception("Error inesperado al abrir %s — se omitirá", path)
        return None


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
        on_done: Callable[[int, int, float], None],
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
      on_done(total_archivos, total_paginas, segundos_transcurridos)
      on_error(excepcion)
    """
    total = len(paths)

    def worker():
        t_inicio = time.perf_counter()
        try:
            logger.debug("Iniciando unión de %d PDFs en %s", total, destino)
            writer = pikepdf.Pdf.new()
            total_paginas = 0
            omitidos = 0

            for i, path in enumerate(paths):
                pdf = _abrir_pdf(path)
                if pdf is None:
                    logger.warning("Archivo omitido en la unión: %s", path)
                    omitidos += 1
                else:
                    try:
                        writer.pages.extend(pdf.pages)
                        total_paginas += len(pdf.pages)
                    except Exception:
                        logger.exception("Error al copiar páginas de %s — se omitirá", path)
                        omitidos += 1
                    finally:
                        pdf.close()

                on_progress(i + 1, total)

            writer.save(destino)
            logger.debug(
                "PDF guardado en %s (archivos=%d omitidos=%d paginas=%d)",
                destino, total, omitidos, total_paginas,
            )
            on_done(total, total_paginas, time.perf_counter() - t_inicio)

        except Exception as e:
            logger.exception("Error durante la unión de PDFs: %s", e)
            on_error(e)

    threading.Thread(target=worker, daemon=True).start()