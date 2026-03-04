import os
import pandas as pd
from fpdf import FPDF
from pathlib import Path
import tempfile
from PIL import Image
import zipfile

# =====================
# CONFIGURACIÓN GLOBAL
# =====================
df_global = None
eron_a_procesar = []
logo_img = None
firma_img = None

FIRMA_WIDTH = 60
FIRMA_HEIGHT = 20
LINEA_ANCHO = 80
ESPACIO_VERTICAL_TEXTO = 15

REGIONAL_SIGNATURE_IMG_WIDTH = 60
REGIONAL_SIGNATURE_IMG_HEIGHT = 20

CARPETA_IMAGENES_REGIONALES = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'imagenes_regionales')
CARPETA_LOGO = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'logo')
NOMBRE_ARCHIVO_LOGO = 'logo.png'


# =====================
# FUNCIONES DE LÓGICA
# =====================

def cargar_imagen_firma(archivo):
    global firma_img
    if archivo is None:
        return None

    try:
        ext = os.path.splitext(archivo)[1].lower()
        if ext not in ['.png', '.jpg', '.jpeg']:
            raise ValueError("Formato de imagen de firma no soportado.")

        temp_dir = os.path.join(tempfile.gettempdir(), "firmas_temp")
        os.makedirs(temp_dir, exist_ok=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext, dir=temp_dir) as tmp:
            with open(archivo, 'rb') as f:
                tmp.write(f.read())
            tmp_path = tmp.name

        with Image.open(tmp_path) as img:
            img.verify()

        if firma_img and os.path.exists(firma_img):
            try:
                os.unlink(firma_img)
            except OSError:
                pass

        firma_img = tmp_path
        return tmp_path
    except Exception as e:
        print(f"Error al cargar imagen de firma: {str(e)}")
        return None


def cargar_logo_desde_ruta(ruta_carpeta, nombre_archivo):
    global logo_img
    ruta_completa = os.path.join(ruta_carpeta, nombre_archivo)

    if not os.path.exists(ruta_completa):
        print(f"Advertencia: No se encontró el logo en: '{ruta_completa}'")
        return None

    try:
        ext = os.path.splitext(nombre_archivo)[1].lower()
        if ext not in ['.png', '.jpg', '.jpeg']:
            return None

        temp_dir = os.path.join(tempfile.gettempdir(), "logos_temp")
        os.makedirs(temp_dir, exist_ok=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext, dir=temp_dir) as tmp:
            with open(ruta_completa, 'rb') as original:
                tmp.write(original.read())
            tmp_path = tmp.name

        with Image.open(tmp_path) as img:
            img.verify()

        if logo_img and os.path.exists(logo_img):
            try:
                os.unlink(logo_img)
            except OSError:
                pass

        logo_img = tmp_path
        return tmp_path
    except Exception as e:
        print(f"Error al cargar el logo: {str(e)}")
        return None


def cargar_imagen_por_nombre(nombre_imagen, carpeta_imagenes=None):
    if carpeta_imagenes is None:
        carpeta_imagenes = CARPETA_IMAGENES_REGIONALES
    if not nombre_imagen:
        return None

    try:
        nombre_imagen_limpio = nombre_imagen.strip()
        ruta_jpg = os.path.join(carpeta_imagenes, f"{nombre_imagen_limpio}.jpg")
        ruta_png = os.path.join(carpeta_imagenes, f"{nombre_imagen_limpio}.png")

        ruta_final = None
        ext = None

        if os.path.exists(ruta_jpg):
            ruta_final, ext = ruta_jpg, '.jpg'
        elif os.path.exists(ruta_png):
            ruta_final, ext = ruta_png, '.png'
        else:
            return None

        temp_dir = os.path.join(tempfile.gettempdir(), "regional_images_temp")
        os.makedirs(temp_dir, exist_ok=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext, dir=temp_dir) as tmp:
            with open(ruta_final, 'rb') as original:
                tmp.write(original.read())
            tmp_path = tmp.name

        with Image.open(tmp_path) as img:
            img.verify()

        return tmp_path
    except Exception as e:
        print(f"Error al cargar imagen de la regional '{nombre_imagen}': {str(e)}")
        return None


def crear_carpeta_base_salida(base_path):
    try:
        path = Path(base_path)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)
    except Exception as e:
        print(f"Error creando carpeta de salida: {str(e)}")
        temp_dir = os.path.join(tempfile.gettempdir(), "actas_generadas_fallback")
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir


def ajustar_texto(texto, max_width, pdf, font_size=8):
    if pd.isna(texto) or texto is None:
        return ""
    texto = str(texto)
    pdf.set_font("Arial", size=font_size)
    current_font_size = font_size
    while pdf.get_string_width(texto) > max_width - 2 and current_font_size > 6:
        current_font_size -= 0.5
        pdf.set_font("Arial", size=current_font_size)
    if pdf.get_string_width(texto) > max_width - 2:
        while pdf.get_string_width(texto + "...") > max_width - 2 and len(texto) > 3:
            texto = texto[:-1]
        texto = texto + "..."
    return texto


def formatear_texto_firma(texto):
    if pd.isna(texto) or texto is None:
        return ""
    texto = str(texto).strip().upper()
    texto = ' '.join(texto.split())
    return texto.replace(':', '').replace('  ', ' ')


def cargar_datos(ruta_archivo):
    """
    Carga el archivo Excel.
    Retorna (exito, mensaje, df_global, eron_a_procesar)
    """
    if not ruta_archivo or not os.path.exists(ruta_archivo):
        return False, "El archivo no existe o la ruta es incorrecta.", None, []

    try:
        ext = os.path.splitext(ruta_archivo)[1].lower()

        if ext not in ('.xlsx', '.xls'):
            return False, f"Formato '{ext}' no soportado. Sube un archivo Excel (.xlsx o .xls).", None, []

        df_main = pd.read_excel(ruta_archivo)

        try:
            df_erons_from_sheet = pd.read_excel(ruta_archivo, sheet_name='pdf')
        except ValueError:
            return False, "El archivo Excel no tiene la hoja 'pdf'. Asegúrate de que exista.", None, []

        required_cols = [
            'eron', 'regional', 'departamento', 'municipio', 'programa', 'periodo_reporte',
            'responsable1_nombre', 'responsable1_especialidad',
            'numero_pac', 'nombre_paciente'
        ] + [f'tratamiento{i}' for i in range(1, 6)] + [f'total{i}' for i in range(1, 6)]
        required_cols.extend(['responsable2_nombre', 'responsable2_cargo'])

        missing = [col for col in required_cols if col not in df_main.columns]
        if missing:
            return False, f"Faltan columnas requeridas: {', '.join(missing)}", None, []

        for col in df_main.columns:
            df_main[col] = df_main[col].astype(str).str.strip()

        df_main.replace('nan', '', inplace=True)
        df_main.replace('None', '', inplace=True)
        df_main['eron'] = df_main['eron'].astype(str).str.strip()
        df_main['regional'] = df_main['regional'].astype(str).str.strip()

        erons = []
        if not df_erons_from_sheet.empty and df_erons_from_sheet.shape[1] > 0:
            erons_brutos = df_erons_from_sheet.iloc[:, 0].dropna().astype(str).str.strip().unique().tolist()
            erons = sorted([e for e in erons_brutos if e])

        if not erons:
            mensaje = "Datos cargados. Sin ERONs especificados en la hoja 'pdf'."
        else:
            mensaje = f"Datos cargados correctamente. {len(erons)} ERONs encontrados en la hoja 'pdf'."

        return True, mensaje, df_main, erons

    except Exception as e:
        return False, f"Error general al cargar archivo: {str(e)}", None, []


def obtener_regional_por_eron(df, eron_nombre):
    if df is None:
        return None
    df_temp = df.copy()
    df_temp['eron'] = df_temp['eron'].astype(str).str.strip()
    regional = df_temp[df_temp['eron'] == eron_nombre]['regional'].unique()
    return regional[0] if len(regional) > 0 else None


def generar_todos_los_pdfs(df, erons, carpeta_salida):
    """
    Genera los PDFs para todos los ERONs.
    Retorna (exito, mensaje, ruta_zip)
    """
    if df is None:
        return False, "No hay datos cargados.", None
    if not erons:
        return False, "No hay ERONs para procesar.", None

    cargar_logo_desde_ruta(CARPETA_LOGO, NOMBRE_ARCHIVO_LOGO)

    output_folder = crear_carpeta_base_salida(carpeta_salida)
    zip_output_dir = os.path.join(tempfile.gettempdir(), "actas_zip_temp")
    os.makedirs(zip_output_dir, exist_ok=True)
    zip_filename = os.path.join(zip_output_dir, "Actas_ERON_Generadas.zip")

    pdf_paths = []
    generated_count = 0
    errors_count = 0

    for eron_seleccionado in erons:
        current_imagen_regional_path = None
        try:
            df_eron = df[df['eron'].astype(str).str.strip() == str(eron_seleccionado).strip()].copy()
            if df_eron.empty:
                errors_count += 1
                continue

            meta = df_eron.iloc[0]

            invalid_chars = '<>:"/\\|?*'
            eron_limpio = str(eron_seleccionado)
            for char in invalid_chars:
                eron_limpio = eron_limpio.replace(char, '_')
            eron_limpio = eron_limpio.strip()

            pdf_path = os.path.join(output_folder, f"acta_{eron_limpio}.pdf")
            pdf = FPDF(orientation='L', unit='mm', format='A4')
            pdf.add_page()
            pdf.set_margins(20, 20, 20)
            pdf.set_auto_page_break(auto=True, margin=20)

            LOGO_WIDTH, LOGO_HEIGHT = 30, 15

            if logo_img and os.path.exists(logo_img):
                pdf.image(logo_img, x=(pdf.w - LOGO_WIDTH) / 2, y=15, w=LOGO_WIDTH, h=LOGO_HEIGHT)
                pdf.ln(LOGO_HEIGHT + 10)
            else:
                pdf.ln(25)

            pdf.set_font("Arial", "B", 14)
            pdf.set_text_color(0, 51, 102)
            pdf.cell(0, 10, "SOPORTE DE ADMINISTRACIÓN DE MEDICAMENTOS POR ERON", 0, 1, "C")
            pdf.ln(5)

            pdf.set_font("Arial", "", 10)
            pdf.set_text_color(0, 0, 0)
            col_width = (pdf.w - 2 * pdf.l_margin) / 3
            campos = [
                ("PROGRAMA", "programa"), ("PERIODO", "periodo_reporte"), ("ERON", "eron"),
                ("REGIONAL", "regional"), ("DEPTO", "departamento"), ("MUNICIPIO", "municipio")
            ]

            for i in range(0, len(campos), 3):
                pdf.set_x(pdf.l_margin)
                for label, key in campos[i:i + 3]:
                    texto = ajustar_texto(meta.get(key, ''), col_width - 5, pdf, 10)
                    pdf.cell(col_width, 6, f"{label}: {texto}", 0, 0)
                pdf.ln()

            pdf.ln(10)

            widths = [15, 38] + [28, 10] * 5
            table_start_x = pdf.l_margin
            headers = ["ID", "PACIENTE"] + [f"TRAT {i}" for i in range(1, 6)] + ["TOTAL"] * 5

            pdf.set_x(table_start_x)
            pdf.set_font("Arial", "B", 9)
            pdf.set_fill_color(0, 51, 102)
            pdf.set_text_color(255, 255, 255)
            for w, h in zip(widths, headers):
                pdf.cell(w, 8, h, 1, 0, "C", fill=True)
            pdf.ln()

            pdf.set_font("Arial", "", 8)
            pdf.set_text_color(0, 0, 0)
            fill = False

            for _, row in df_eron.iterrows():
                if pdf.get_y() + 8 > pdf.h - 20:
                    pdf.add_page(orientation='L')
                    pdf.set_margins(20, 20, 20)
                    pdf.set_x(table_start_x)
                    pdf.set_font("Arial", "B", 9)
                    pdf.set_fill_color(0, 51, 102)
                    pdf.set_text_color(255, 255, 255)
                    for w, h in zip(widths, headers):
                        pdf.cell(w, 8, h, 1, 0, "C", fill=True)
                    pdf.ln()
                    pdf.set_font("Arial", "", 8)
                    pdf.set_text_color(0, 0, 0)
                    fill = False

                pdf.set_fill_color(240, 248, 255) if fill else pdf.set_fill_color(255, 255, 255)
                pdf.set_x(table_start_x)
                pdf.cell(widths[0], 8, ajustar_texto(row['numero_pac'], widths[0], pdf), 1, 0, "C", fill=fill)
                pdf.cell(widths[1], 8, ajustar_texto(row['nombre_paciente'], widths[1], pdf), 1, 0, "L", fill=fill)

                for i in range(1, 6):
                    ti = 2 + (i - 1) * 2
                    pdf.cell(widths[ti], 8, ajustar_texto(row.get(f'tratamiento{i}', ''), widths[ti], pdf), 1, 0, "L", fill=fill)
                    pdf.cell(widths[ti + 1], 8, ajustar_texto(row.get(f'total{i}', ''), widths[ti + 1], pdf), 1, 0, "C", fill=fill)

                pdf.ln()
                fill = not fill

            # Página de firma
            pdf.add_page(orientation='L')
            pdf.set_margins(20, 20, 20)
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 15, "RESPONSABILIDAD", 0, 1, "C")
            pdf.ln(40)

            col_width_firma = 120
            firma_x = (pdf.w - col_width_firma) / 2
            y_pos = pdf.get_y()

            regional_asociada = obtener_regional_por_eron(df, eron_seleccionado)
            if regional_asociada:
                current_imagen_regional_path = cargar_imagen_por_nombre(regional_asociada)

            if current_imagen_regional_path and os.path.exists(current_imagen_regional_path):
                img_x = firma_x + (col_width_firma - REGIONAL_SIGNATURE_IMG_WIDTH) / 2
                pdf.image(current_imagen_regional_path, x=img_x, y=y_pos, w=REGIONAL_SIGNATURE_IMG_WIDTH, h=REGIONAL_SIGNATURE_IMG_HEIGHT)
                pdf.ln(REGIONAL_SIGNATURE_IMG_HEIGHT + ESPACIO_VERTICAL_TEXTO)
            elif firma_img and os.path.exists(firma_img):
                img_x = firma_x + (col_width_firma - FIRMA_WIDTH) / 2
                pdf.image(firma_img, x=img_x, y=y_pos, w=FIRMA_WIDTH, h=FIRMA_HEIGHT)
                pdf.ln(FIRMA_HEIGHT + ESPACIO_VERTICAL_TEXTO)
            else:
                linea_x = firma_x + (col_width_firma - LINEA_ANCHO) / 2
                pdf.set_x(linea_x)
                pdf.cell(LINEA_ANCHO, 1, "_" * 40, 0, 1)
                pdf.ln(ESPACIO_VERTICAL_TEXTO)

            nombre_fmt = formatear_texto_firma(meta.get('responsable2_nombre', ''))
            cargo_fmt = formatear_texto_firma(meta.get('responsable2_cargo', ''))

            pdf.set_font("Arial", "B", 12)
            tw = pdf.get_string_width(nombre_fmt)
            pdf.set_x(firma_x + (col_width_firma - tw) / 2)
            pdf.cell(tw, 8, nombre_fmt, 0, 1, "L")

            pdf.set_font("Arial", "", 10)
            tw = pdf.get_string_width(cargo_fmt)
            pdf.set_x(firma_x + (col_width_firma - tw) / 2)
            pdf.cell(tw, 7, cargo_fmt, 0, 1, "L")

            pdf.output(pdf_path)
            pdf_paths.append(pdf_path)
            generated_count += 1

            if current_imagen_regional_path and os.path.exists(current_imagen_regional_path):
                try:
                    os.unlink(current_imagen_regional_path)
                except OSError:
                    pass

        except Exception as e:
            print(f"Error al generar PDF para ERON {eron_seleccionado}: {str(e)}")
            errors_count += 1

    if pdf_paths:
        with zipfile.ZipFile(zip_filename, 'w') as zf:
            for p in pdf_paths:
                zf.write(p, os.path.basename(p))

        mensaje = f"Proceso completado. {generated_count} PDF(s) generados."
        if errors_count > 0:
            mensaje += f" {errors_count} error(es) encontrados."
        return True, mensaje, zip_filename
    else:
        return False, "No se pudo generar ningún PDF. Revisa los datos y la hoja 'pdf'.", None


def limpiar_archivos_temporales():
    temp_dirs = [
        os.path.join(tempfile.gettempdir(), "firmas_temp"),
        os.path.join(tempfile.gettempdir(), "logos_temp"),
        os.path.join(tempfile.gettempdir(), "regional_images_temp"),
        os.path.join(tempfile.gettempdir(), "actas_zip_temp"),
    ]
    for d in temp_dirs:
        if os.path.exists(d) and os.path.isdir(d):
            try:
                for f in os.listdir(d):
                    os.unlink(os.path.join(d, f))
                os.rmdir(d)
            except OSError:
                pass