# CODIGO PARA TRANSPONER LOS MEDICAMENTOS FINAL
import pandas as pd
import os


def cargar_archivo_excel(archivo):
    """Carga el archivo Excel con manejo robusto de columnas"""
    try:
        # Cargar el archivo manteniendo los nombres originales
        df = pd.read_excel(archivo)

        # Mostrar todas las columnas disponibles para referencia
        print("\nColumnas disponibles en el archivo:")
        print(df.columns.tolist())

        # Mapeo flexible de columnas requeridas
        mapeo_columnas = {
            'NUMERO DE IDENTIFICACION': None,
            'NOMBRE PACIENTE': None,
            'ERON': None,
            'REGIONAL': None,
            'MEDICAMENTO': None,
            'CANTIDAD TOTAL': None
        }

        # Buscar coincidencias para cada columna requerida
        for col in df.columns:
            col_lower = str(col).lower()

            if 'numeropac' in col_lower or 'identif' in col_lower or 'idpac' in col_lower:
                mapeo_columnas['NUMERO DE IDENTIFICACION'] = col
            elif 'nombrepac' in col_lower or 'paciente' in col_lower:
                mapeo_columnas['NOMBRE PACIENTE'] = col
            elif 'eron' in col_lower:
                mapeo_columnas['ERON'] = col
            elif 'regional' in col_lower:
                mapeo_columnas['REGIONAL'] = col
            elif 'medicamento' in col_lower:
                mapeo_columnas['MEDICAMENTO'] = col
            elif 'cantidadtotal' in col_lower or 'cantidad total' in col_lower or 'dosis' in col_lower:
                mapeo_columnas['CANTIDAD TOTAL'] = col

        # Verificar que todas las columnas requeridas se encontraron
        faltantes = [k for k, v in mapeo_columnas.items() if v is None]
        if faltantes:
            print("\nERROR: No se encontraron las siguientes columnas:")
            for col in faltantes:
                print(f"- {col}")
            return None

        print("\nColumnas mapeadas correctamente:")
        for estandar, original in mapeo_columnas.items():
            print(f"{estandar} <- {original}")

        # Renombrar columnas y seleccionar solo las necesarias
        df = df.rename(columns={v: k for k, v in mapeo_columnas.items()})
        return df[list(mapeo_columnas.keys())]

    except Exception as e:
        print(f"\nError al cargar el archivo: {str(e)}")
        return None


def transformar_datos(df):
    """Transforma los datos de vertical a horizontal"""
    try:
        # Eliminar filas con datos críticos faltantes
        df = df.dropna(subset=['NUMERO DE IDENTIFICACION', 'NOMBRE PACIENTE'])

        # Agrupar por paciente
        resultados = []
        for (id_paciente, nombre), group in df.groupby(['NUMERO DE IDENTIFICACION', 'NOMBRE PACIENTE']):
            registro = {
                'NUMERO DE IDENTIFICACION': id_paciente,
                'NOMBRE PACIENTE': nombre,
                'ERON': group['ERON'].iloc[0] if 'ERON' in group.columns else '',
                'REGIONAL': group['REGIONAL'].iloc[0] if 'REGIONAL' in group.columns else ''
            }

            # Agregar medicamentos y cantidades como pares
            for i, (_, fila) in enumerate(group.iterrows(), 1):
                registro[f'MEDICAMENTO_{i}'] = fila['MEDICAMENTO']
                registro[f'CANTIDAD_TOTAL_{i}'] = fila.get('CANTIDAD TOTAL', '')

            resultados.append(registro)

        return pd.DataFrame(resultados)

    except Exception as e:
        print(f"\nError durante la transformación: {str(e)}")
        return None


def eliminar_duplicados_por_identificacion(df):
    """Elimina duplicados conservando solo el primer registro por número de identificación"""
    return df.drop_duplicates(subset='NUMERO DE IDENTIFICACION', keep='first')


def procesar_archivo(archivo_entrada):
    """
    Función principal que orquesta todo el proceso.
    Recibe la ruta del archivo y retorna (exito, mensaje, ruta_salida)
    """
    if not os.path.exists(archivo_entrada):
        return False, "El archivo no existe o la ruta es incorrecta.", None

    df = cargar_archivo_excel(archivo_entrada)
    if df is None:
        return False, "No se pudo cargar el archivo. Verifica las columnas.", None

    df_transformado = transformar_datos(df)
    if df_transformado is None:
        return False, "Error durante la transformación de datos.", None

    df_transformado = eliminar_duplicados_por_identificacion(df_transformado)

    # Guardar en la misma carpeta del archivo de entrada
    carpeta = os.path.dirname(archivo_entrada)
    nombre_base = os.path.splitext(os.path.basename(archivo_entrada))[0]
    archivo_salida = os.path.join(carpeta, f"{nombre_base}_transformado.xlsx")
    df_transformado.to_excel(archivo_salida, index=False)

    max_med = max([int(col.split('_')[-1]) for col in df_transformado.columns if 'MEDICAMENTO_' in col] or [0])
    mensaje = (
        f"Transformación completada exitosamente.\n\n"
        f"Pacientes procesados: {len(df_transformado)}\n"
        f"Máximo medicamentos por paciente: {max_med}\n\n"
        f"Archivo guardado en:\n{archivo_salida}"
    )

    return True, mensaje, archivo_salida