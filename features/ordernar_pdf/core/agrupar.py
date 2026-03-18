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

import pikepdf

_THREAD_WORKERS = min(16, (os.cpu_count() or 4) * 2)


def leer_paginas(path: str) -> int:
    """Devuelve el nº de páginas de un PDF, o -1 si falla."""
    try:
        with pikepdf.open(path) as pdf:
            return len(pdf.pages)
    except Exception:
        return -1


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
                n = fut.result()
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

    Callbacks:
      on_progress(archivos_procesados, total_archivos)
      on_done(total_archivos, total_paginas, segundos_transcurridos)
      on_error(excepcion)
    """
    total = len(paths)

    def worker():
        t_inicio = time.perf_counter()
        try:
            writer = pikepdf.Pdf.new()
            total_paginas = 0
            for i, path in enumerate(paths):
                try:
                    with pikepdf.open(path) as src:
                        writer.pages.extend(src.pages)
                        total_paginas += len(src.pages)
                except Exception:
                    pass  # archivo corrupto: se salta
                on_progress(i + 1, total)
            writer.save(destino)
            on_done(total, total_paginas, time.perf_counter() - t_inicio)
        except Exception as e:
            on_error(e)

    threading.Thread(target=worker, daemon=True).start()