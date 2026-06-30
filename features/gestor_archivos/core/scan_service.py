import os
import threading
from queue import Queue


def _worker(queue, resultados, lock):
    while True:
        carpeta = queue.get()

        if carpeta is None:
            queue.task_done()
            break

        try:
            with os.scandir(carpeta) as entries:
                for entry in entries:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            queue.put(entry.path)
                        elif entry.is_file(follow_symlinks=False):
                            stat = entry.stat(follow_symlinks=False)
                            archivo = {
                                "nombre": entry.name,
                                "ruta": entry.path,
                                "extension": os.path.splitext(entry.name)[1].lower(),
                                "peso": stat.st_size,
                                "carpeta": os.path.dirname(entry.path),
                            }

                            with lock:
                                resultados.append(archivo)
                    except Exception:
                        pass
        except Exception:
            pass
        finally:
            queue.task_done()


def escanear_carpeta(carpeta_base, workers=8):
    queue = Queue()
    resultados = []
    lock = threading.Lock()
    workers = max(1, int(workers))

    queue.put(carpeta_base)

    threads = []

    for _ in range(workers):
        thread = threading.Thread(
            target=_worker,
            args=(queue, resultados, lock),
            daemon=True,
        )
        thread.start()
        threads.append(thread)

    queue.join()

    for _ in threads:
        queue.put(None)

    queue.join()

    for thread in threads:
        thread.join()

    return resultados
