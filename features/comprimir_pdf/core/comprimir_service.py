"""
features/comprimir_pdf/core/comprimir_service.py
Logica de negocio para comprimir PDFs.
Sin dependencias de tkinter.

Niveles de compresion (afectan calidad de imagenes embebidas):
  BAJO   -> calidad 85  (perdida minima, poco ahorro)
  MEDIO  -> calidad 60  (equilibrio recomendado)
  ALTO   -> calidad 35  (maximo ahorro, notable en fotos)
"""
import io
import logging
import os
import threading
from typing import Callable

import pikepdf
from pikepdf import Pdf, PdfImage
from PIL import Image

logger = logging.getLogger(__name__)

NIVELES: dict[str, int] = {
    "Bajo":  85,
    "Medio": 60,
    "Alto":  35,
}

# Umbral por defecto en bytes (300 MB)
UMBRAL_DEFECTO = 300 * 1024 * 1024


def tamaño_bytes(path: str) -> int:
    """Devuelve el tamano del archivo en bytes, o 0 si no existe."""
    try:
        return os.path.getsize(path)
    except OSError:
        logger.exception("No se pudo obtener tamano de archivo: %s", path)
        return 0


def es_pesado(path: str, umbral_bytes: int = UMBRAL_DEFECTO) -> bool:
    return tamaño_bytes(path) >= umbral_bytes


def _comprimir_imagen_pil(img: Image.Image, calidad: int) -> bytes | None:
    """
    Recodifica una imagen PIL ya decodificada a JPEG con la calidad indicada.
    Devuelve None si el resultado no es más pequeño que el original estimado,
    o si la imagen no es compatible con JPEG (ej. paleta con transparencia).
    """
    try:
        # JPEG no soporta transparencia ni paletas con alpha
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")
        elif img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=calidad, optimize=True)
        return buf.getvalue()
    except Exception:
        logger.debug("No se pudo recodificar imagen a JPEG", exc_info=True)
        return None


def comprimir_pdf(
        origen: str,
        destino: str,
        nivel: str,
        on_progress: Callable[[int, int], None],
        on_done: Callable[[int, int, float], None],   # (bytes_antes, bytes_despues, segundos)
        on_error: Callable[[Exception], None],
) -> None:
    """
    Comprime `origen` y guarda el resultado en `destino`.
    Corre en un hilo daemon; usa callbacks para comunicarse con la UI.

    on_progress(paginas_procesadas, total_paginas)
    on_done(bytes_antes, bytes_despues, segundos)
    on_error(excepcion)

    Estrategia de compresion:
      1. Por cada imagen en cada pagina se obtiene un objeto PIL via
         PdfImage.as_pil_image() — esto cubre JPEG, PNG, CCITT, JBIG2,
         indexed color y cualquier formato que pikepdf sepa decodificar.
      2. Se recodifica a JPEG con la calidad del nivel elegido.
      3. Solo se sustituye si el JPEG resultante pesa menos que la imagen
         original (evita agrandar imagenes ya bien comprimidas).
      4. Imagenes con canal alpha se convierten a RGB antes de recodificar.
      5. Al guardar se activa compress_streams y object_stream_mode para
         comprimir tambien el texto y la estructura del PDF.
    """
    calidad = NIVELES.get(nivel, NIVELES["Medio"])

    def _safe_progress(actual: int, total: int) -> None:
        try:
            on_progress(actual, total)
        except Exception:
            logger.exception("Error en callback on_progress(%s, %s)", actual, total)

    def _safe_done(bytes_antes: int, bytes_despues: int, segundos: float) -> None:
        try:
            on_done(bytes_antes, bytes_despues, segundos)
        except Exception:
            logger.exception(
                "Error en callback on_done(%s, %s, %.3f)",
                bytes_antes, bytes_despues, segundos,
            )

    def _safe_error(exc: Exception) -> None:
        try:
            on_error(exc)
        except Exception:
            logger.exception("Error en callback on_error")
        logger.exception("Fallo en compresion de PDF", exc_info=exc)

    def worker() -> None:
        import time
        t0 = time.perf_counter()
        stats = {
            "paginas": 0,
            "imagenes_total": 0,
            "imagenes_reemplazadas": 0,
            "imagenes_omitidas_sin_ganancia": 0,
            "imagenes_no_procesables": 0,
        }

        try:
            logger.info(
                "Inicia compresion PDF: origen=%s destino=%s nivel=%s calidad=%s",
                origen, destino, nivel, calidad,
            )
            bytes_antes = tamaño_bytes(origen)

            with Pdf.open(origen) as pdf:
                total = len(pdf.pages)
                stats["paginas"] = total
                logger.info("PDF cargado. Paginas detectadas: %s", total)

                for i, page in enumerate(pdf.pages):
                    for name, obj in page.images.items():
                        stats["imagenes_total"] += 1
                        try:
                            pdfimg = PdfImage(obj)

                            # Tamaño original del stream para comparar despues
                            tam_original = len(obj.read_raw_bytes())

                            # ── Punto clave del fix ───────────────────────────
                            # as_pil_image() decodifica cualquier formato que
                            # pikepdf entienda (JPEG, PNG, CCITT, JBIG2, etc.)
                            # sin que PIL tenga que identificar el formato raw.
                            img_pil = pdfimg.as_pil_image()
                            # ─────────────────────────────────────────────────

                            comprimido = _comprimir_imagen_pil(img_pil, calidad)

                            if comprimido is None:
                                stats["imagenes_no_procesables"] += 1
                                continue

                            if len(comprimido) >= tam_original:
                                # El JPEG saldria mas grande: no vale la pena
                                stats["imagenes_omitidas_sin_ganancia"] += 1
                                continue

                            obj.write(
                                comprimido,
                                filter=pikepdf.Name("/DCTDecode"),
                            )
                            stats["imagenes_reemplazadas"] += 1

                        except Exception:
                            stats["imagenes_no_procesables"] += 1
                            logger.debug(
                                "Imagen no procesada en pagina=%s nombre=%s",
                                i + 1, str(name),
                                exc_info=True,
                                )

                    _safe_progress(i + 1, total)

                # Guardar con compresion de streams activada
                pdf.save(
                    destino,
                    compress_streams=True,
                    object_stream_mode=pikepdf.ObjectStreamMode.generate,
                )

            segundos = time.perf_counter() - t0
            bytes_despues = tamaño_bytes(destino)

            logger.info(
                "Compresion finalizada en %.2fs | tamano: %s -> %s bytes | "
                "imagenes: total=%s reemplazadas=%s omitidas=%s no_procesables=%s",
                segundos,
                bytes_antes, bytes_despues,
                stats["imagenes_total"],
                stats["imagenes_reemplazadas"],
                stats["imagenes_omitidas_sin_ganancia"],
                stats["imagenes_no_procesables"],
            )

            _safe_done(bytes_antes, bytes_despues, segundos)

        except Exception as e:
            _safe_error(e)

    threading.Thread(
        target=worker, daemon=True, name="pdf-compression-worker"
    ).start()


def _fmt_bytes(n: int) -> str:
    """Formatea bytes en KB / MB legibles."""
    if n >= 1_048_576:
        return f"{n / 1_048_576:.1f} MB"
    return f"{n / 1024:.0f} KB"


def resumen_compresion(bytes_antes: int, bytes_despues: int) -> str:
    ahorro = bytes_antes - bytes_despues
    pct = ahorro / bytes_antes * 100 if bytes_antes else 0
    return (
        f"{_fmt_bytes(bytes_antes)} -> {_fmt_bytes(bytes_despues)}  "
        f"(ahorro: {_fmt_bytes(ahorro)}, {pct:.1f}%)"
    )