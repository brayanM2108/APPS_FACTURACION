import os
import shutil
import pandas as pd
from tqdm import tqdm


def listar_archivos(carpeta):
    """Lista todos los archivos en una carpeta y sus subcarpetas"""
    archivos = []
    for root, _, files in os.walk(carpeta):
        for file in files:
            archivos.append(os.path.join(root, file))
    return archivos


def crear_tabla_edicion(directorio):
    """Crea un archivo Excel con el plan de movimiento de archivos"""
    archivos = listar_archivos(directorio)

    if not archivos:
        return False, "No se encontraron archivos en la carpeta.", None

    df = pd.DataFrame({
        'Archivo_origen': archivos,
        'Nuevo_nombre': [os.path.basename(a) for a in archivos],
        'Nueva_ruta': ['' for _ in archivos],
        'Accion': ['mover' for _ in archivos],
        'Carpeta_1': ['' for _ in archivos],
        'Carpeta_2': ['' for _ in archivos],
        'Carpeta_3': ['' for _ in archivos],
        'Carpeta_4': ['' for _ in archivos],
        'Carpeta_5': ['' for _ in archivos],
    })

    archivo_excel = os.path.join(directorio, 'plan_de_movimiento.xlsx')
    df.to_excel(archivo_excel, index=False)

    return True, f"Plan de movimiento guardado en:\n{archivo_excel}", archivo_excel


def aplicar_cambios(tabla_path, carpeta_base, simular=False):
    """Aplica los cambios definidos en el Excel (mover/copiar/eliminar archivos)"""
    try:
        df = pd.read_excel(tabla_path)
    except Exception as e:
        return False, f"Error al leer el archivo Excel: {str(e)}", []

    errores = []

    # Validar columnas requeridas
    columnas_requeridas = {'Archivo_origen', 'Nuevo_nombre', 'Nueva_ruta', 'Accion',
                           'Carpeta_1', 'Carpeta_2', 'Carpeta_3', 'Carpeta_4', 'Carpeta_5'}

    if not columnas_requeridas.issubset(df.columns):
        return False, "El archivo Excel no contiene las columnas necesarias.", []

    # Procesar cada fila
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Procesando archivos"):
        try:
            origen = row['Archivo_origen']
            nuevo_nombre = row['Nuevo_nombre']
            nueva_ruta = row['Nueva_ruta']
            accion = str(row['Accion']).strip().lower()

            # Validar que el archivo origen existe
            if not os.path.exists(origen):
                errores.append(f"Archivo no encontrado: {origen}")
                continue

            # Construir ruta de destino
            destino_dir = carpeta_base

            # Agregar nueva_ruta si está definida
            if pd.notna(nueva_ruta) and nueva_ruta.strip():
                destino_dir = os.path.join(destino_dir, nueva_ruta.strip())

            # Agregar subcarpetas si están definidas
            for col in ['Carpeta_1', 'Carpeta_2', 'Carpeta_3', 'Carpeta_4', 'Carpeta_5']:
                if pd.notna(row[col]) and str(row[col]).strip():
                    destino_dir = os.path.join(destino_dir, str(row[col]).strip())

            destino_final = os.path.join(destino_dir, nuevo_nombre)

            # Validar que el destino no existe (excepto para eliminar)
            if accion != "eliminar" and os.path.exists(destino_final):
                errores.append(f"Ya existe el archivo destino: {destino_final}")
                continue

            # Ejecutar acción
            if simular:
                print(f"[SIMULACIÓN] {accion.upper()} de {origen} → {destino_final}")
            else:
                # Crear directorio destino si no existe
                if accion in ["mover", "copiar"]:
                    os.makedirs(destino_dir, exist_ok=True)

                # Ejecutar la operación
                if accion == "mover":
                    shutil.move(origen, destino_final)
                elif accion == "copiar":
                    shutil.copy2(origen, destino_final)
                elif accion == "eliminar":
                    os.remove(origen)
                else:
                    errores.append(f"Acción inválida en fila {idx + 2}: {accion}")

        except Exception as e:
            errores.append(f"Error en fila {idx + 2}: {str(e)}")

    # Generar reporte de errores
    if errores:
        log_path = os.path.join(os.path.dirname(tabla_path), 'log_errores.txt')
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"Total de errores: {len(errores)}\n")
            f.write("=" * 50 + "\n\n")
            for error in errores:
                f.write(error + '\n')

        return False, f"Se encontraron {len(errores)} errores.\nRevisa: {log_path}", log_path
    else:
        return True, "Todos los archivos se procesaron correctamente.", None
