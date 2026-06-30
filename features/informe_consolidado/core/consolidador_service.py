import os
import traceback
from datetime import datetime
import warnings

import pandas as pd
from pandas.errors import SettingWithCopyWarning


warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)
warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)


def limpiar_a_float(valor):
    try:
        return float(str(valor).replace(".", "").replace(",", "."))
    except Exception:
        return None


def ejecutar_consolidacion(
    factura_electronica_path,
    facturado_path,
    facturacion_informe_path,
    consolidado_path,
    salida_path,
    meses_a_eliminar=None,
    on_progress=None,
    on_log=None,
    log_path=None,
):
    if log_path is None:
        log_path = os.path.join(os.path.dirname(salida_path), "log_errores_consolidado.txt")

    def registrar(mensaje, es_error=False):
        marca = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefijo = "ERROR" if es_error else "INFO"
        linea = f"[{marca}] [{prefijo}] {mensaje}"

        try:
            with open(log_path, "a", encoding="utf-8") as archivo_log:
                archivo_log.write(linea + "\n")
        except Exception:
            pass

        if on_log:
            on_log(linea)

    def progreso(valor, mensaje):
        if on_progress:
            on_progress(valor, mensaje)

    try:
        with open(log_path, "w", encoding="utf-8") as archivo_log:
            archivo_log.write("Inicio de consolidacion\n")

        if meses_a_eliminar is None:
            meses_a_eliminar = [
                "NOVIEMBRE_2025", "DICIEMBRE_2025", "ENERO_2026", "FEBRERO_2026", "MARZO_2026", "ABRIL_2026"
            ]
        meses_a_eliminar = [str(m).strip().upper() for m in meses_a_eliminar if str(m).strip()]
        registrar(f"Meses a eliminar aplicados: {', '.join(meses_a_eliminar) if meses_a_eliminar else 'Ninguno'}")

        progreso(5, "Leyendo facturacion electronica")
        FacturaEle = factura_electronica_path
        dfFactuEle = pd.read_csv(FacturaEle, converters={"Prefijo12": limpiar_a_float})
        dfFactuEle.drop(columns=["Prefijo7"], inplace=True)
        nuevos_nombres = [
            "IDENTIFICACION", "PREFIJO", "FACTURA", "FECHA LEGALIZACION", "FECHA FACTURA", "CUFE",
            "TIPO IDENTIFICACION", "PACIENTE", "VALOR PACIENTE", "VALOR TERCERO", "NIT", "EPS",
            "CONVENIO", "USUARIO", "Estado", "RADICADO PANACEA", "FECHA RADICADO", "RADICADO EXTERNO",
        ]
        dfFactuEle.columns = nuevos_nombres
        dfFactuEle["RADICADO EXTERNO"] = pd.to_numeric(dfFactuEle["RADICADO EXTERNO"], errors="coerce").astype("Int64")
        dfFactuEle["RADICADO EXTERNO"] = pd.to_numeric(dfFactuEle["RADICADO EXTERNO"])
        dfFactuEle["FECHA LEGALIZACION"] = pd.to_datetime(
            dfFactuEle["FECHA LEGALIZACION"], format="mixed", dayfirst=True, errors="coerce"
        )
        dfFactuEle["FECHA FACTURA"] = pd.to_datetime(dfFactuEle["FECHA FACTURA"], dayfirst=True, errors="coerce")
        dfFactuEle["FECHA RADICADO"] = pd.to_datetime(
            dfFactuEle["FECHA RADICADO"], format="mixed", dayfirst=True, errors="coerce"
        )
        df_activos = dfFactuEle[dfFactuEle["Estado"].str.strip().str.lower() == "activo"]
        df_anulados = dfFactuEle[dfFactuEle["Estado"].str.strip().str.lower() == "anulado"]

        progreso(20, "Leyendo archivo facturado")
        Facturado = facturado_path
        dffacturadoActivo = pd.read_excel(Facturado, sheet_name="FACTURADO")
        dffacturadoActivo["Llave"] = dffacturadoActivo["MES"].astype(str) + "_" + dffacturadoActivo["AÑO"].astype(str)
        dffacturadoActivo["Llave"] = dffacturadoActivo["Llave"].str.upper().str.strip()
        dffactuActivoFiltrado = dffacturadoActivo[~dffacturadoActivo["Llave"].isin(meses_a_eliminar)]
        nuevos_nombres_F = [
            "PREFIJO", "FACTURA", "FECHA LEGALIZACION", "FECHA FACTURA", "CUFE",
            "TIPO IDENTIFICACION", "IDENTIFICACION", "PACIENTE", "VALOR PACIENTE", "VALOR TERCERO", "NIT", "EPS",
            "CONVENIO", "USUARIO", "Estado", "RADICADO PANACEA", "FECHA RADICADO", "RADICADO EXTERNO", "MES", "AÑO", "LLAVE",
        ]
        dffactuActivoFiltrado.columns = nuevos_nombres_F
        dffactuActivoFiltrado["RADICADO EXTERNO"] = pd.to_numeric(
            dffactuActivoFiltrado["RADICADO EXTERNO"], errors="coerce"
        ).astype("Int64")
        dffactuActivoFiltrado["RADICADO EXTERNO"] = pd.to_numeric(dffactuActivoFiltrado["RADICADO EXTERNO"])
        dffactuActivoFiltrado["FECHA LEGALIZACION"] = pd.to_datetime(
            dffactuActivoFiltrado["FECHA LEGALIZACION"], format="mixed", dayfirst=True, errors="coerce"
        )
        dffactuActivoFiltrado["FECHA FACTURA"] = pd.to_datetime(
            dffactuActivoFiltrado["FECHA FACTURA"], dayfirst=True, errors="coerce"
        )
        dffactuActivoFiltrado["FECHA RADICADO"] = pd.to_datetime(dffactuActivoFiltrado["FECHA RADICADO"])
        dfFacturadoActivoFinal = pd.concat([dffactuActivoFiltrado, df_activos], axis=0, join="inner", ignore_index=True)
        df_facturas_real = dfFacturadoActivoFinal.groupby("FACTURA", as_index=False)["VALOR TERCERO"].sum()

        dffacturadoNulo = pd.read_excel(Facturado, sheet_name="ANULADO")
        dffacturadoNulo["Llave"] = dffacturadoNulo["MES"].astype(str) + "_" + dffacturadoNulo["AÑO"].astype(str)
        dffacturadoNulo["Llave"] = dffacturadoNulo["Llave"].str.upper().str.strip()
        dffacturadoNuloFiltrado = dffacturadoNulo[~dffacturadoNulo["Llave"].isin(meses_a_eliminar)]
        nuevos_nombres_N = [
            "PREFIJO", "FACTURA", "FECHA LEGALIZACION", "FECHA FACTURA", "CUFE",
            "TIPO IDENTIFICACION", "IDENTIFICACION", "PACIENTE", "VALOR PACIENTE", "VALOR TERCERO F", "NIT", "EPS",
            "CONVENIO", "USUARIO", "Estado", "RADICADO PANACEA", "FECHA RADICADO", "RADICADO EXTERNO", "MES", "AÑO", "LLAVE",
        ]
        dffacturadoNuloFiltrado.columns = nuevos_nombres_N
        dffacturadoNuloFiltrado["RADICADO EXTERNO"] = pd.to_numeric(
            dffacturadoNuloFiltrado["RADICADO EXTERNO"], errors="coerce"
        ).astype("Int64")
        dffacturadoNuloFiltrado["RADICADO EXTERNO"] = pd.to_numeric(dffacturadoNuloFiltrado["RADICADO EXTERNO"])
        dffacturadoNuloFiltrado["FECHA LEGALIZACION"] = pd.to_datetime(
            dffacturadoNuloFiltrado["FECHA LEGALIZACION"], format="mixed", dayfirst=True, errors="coerce"
        )
        dffacturadoNuloFiltrado["FECHA FACTURA"] = pd.to_datetime(
            dffacturadoNuloFiltrado["FECHA FACTURA"], dayfirst=True, errors="coerce"
        )
        dffacturadoNuloFiltrado["FECHA RADICADO"] = pd.to_datetime(dffacturadoNuloFiltrado["FECHA RADICADO"])
        dffacturadoNuloFiltradoFinal = pd.concat([dffacturadoNuloFiltrado, df_anulados], axis=0, join="inner", ignore_index=True)
        total = df_facturas_real["VALOR TERCERO"].sum()
        registrar(f"Total valor tercero real: {total}")

        progreso(35, "Cruzando con facturacion informe")
        facturacioninfo = facturacion_informe_path
        dffacturacioninfo = pd.read_excel(facturacioninfo)
        facturacioninfoRespaldo = pd.read_excel(facturacioninfo)
        dffacturacioninfo["FechaLegalizacion"] = pd.to_datetime(dffacturacioninfo["FechaLegalizacion"])
        dffacturacioninfo["FECHA_FACTURA"] = pd.to_datetime(dffacturacioninfo["FECHA_FACTURA"])
        nueva_columna = dffacturacioninfo["TotalLegalizacion"] - dffacturacioninfo["VALOR_RECAUDO_PACIENTE"]
        dffacturacioninfo.insert(7, "VALOR TERCERO F", nueva_columna)

        consolidado = consolidado_path
        consulta_hojas = pd.ExcelFile(consolidado)
        registrar(f"Hojas en consolidado: {consulta_hojas.sheet_names}")
        dfConsolidado = pd.read_excel(consolidado, sheet_name="BASE")
        df_no_legalizado = dffacturacioninfo[~dffacturacioninfo["NRO_LEGALIACION"].isin(dfConsolidado["NRO_LEGALIACION"])]
        df_no_facturas = df_no_legalizado[~df_no_legalizado["NRO_FACTURACLI"].isin(dfConsolidado["NRO_FACTURACLI"])]
        final_consolidar = df_no_facturas[~df_no_facturas["NRO_FACTURACLI"].isin(dffacturadoNuloFiltradoFinal["FACTURA"])]
        df_cambio_estado = dffacturadoNuloFiltradoFinal[
            dffacturadoNuloFiltradoFinal["FACTURA"].isin(dfConsolidado["NRO_FACTURACLI"])
        ]
        final_consolidar["VALOR TERCERO F"] = final_consolidar["VALOR TERCERO F"].apply(lambda x: 0 if x < 0 else x)
        final_consolidar_comp = final_consolidar.groupby("NRO_FACTURACLI", as_index=False)["VALOR TERCERO F"].sum()
        final_consolidar_comp = final_consolidar_comp.rename(columns={"NRO_FACTURACLI": "FACTURA"})

        df_facturas_real_comp = df_facturas_real[df_facturas_real["FACTURA"].isin(final_consolidar_comp["FACTURA"])]
        df_comparado = pd.merge(
            df_facturas_real_comp,
            final_consolidar_comp,
            on="FACTURA",
            suffixes=("_facturas_real", "_final_consolidar_comp"),
            how="outer",
        )
        df_comparado[["VALOR TERCERO", "VALOR TERCERO F"]] = df_comparado[["VALOR TERCERO", "VALOR TERCERO F"]].fillna(0)
        df_comparado["DIFERENCIA"] = df_comparado["VALOR TERCERO"] - df_comparado["VALOR TERCERO F"]
        valores_diferentes_de_cero = (df_comparado["DIFERENCIA"] != 0).sum().sum()
        registrar(f"Total de valores diferentes de 0: {valores_diferentes_de_cero}")

        progreso(50, "Ajustando diferencias - pasada 1")
        for _, row in df_comparado.iterrows():
            factura = row["FACTURA"]
            valor_tercero = row["DIFERENCIA"]

            if valor_tercero > 1:
                registrar(f"Factura {factura} con valor positivo: reemplazando desde respaldo")
                final_consolidar = final_consolidar[final_consolidar["NRO_FACTURACLI"] != factura]
                filas_respaldo = facturacioninfoRespaldo[facturacioninfoRespaldo["NRO_FACTURACLI"] == factura]
                nueva_columna = filas_respaldo["TotalLegalizacion"] - filas_respaldo["VALOR_RECAUDO_PACIENTE"]
                filas_respaldo.insert(7, "VALOR TERCERO F", nueva_columna)
                filas_respaldo["VALOR TERCERO F"] = filas_respaldo["VALOR TERCERO F"].apply(lambda x: 0 if x < 0 else x)
                final_consolidar = pd.concat([final_consolidar, filas_respaldo], ignore_index=True)
                df_factura = final_consolidar[final_consolidar["NRO_FACTURACLI"] == factura]
                duplicados = df_factura.duplicated(
                    subset=["NRO_LEGALIACION", "VALOR TERCERO F", "CODIGO_ALTERNO"], keep="first"
                )
                indices_a_eliminar = df_factura[duplicados].index
                final_consolidar = final_consolidar.drop(index=indices_a_eliminar)
            elif valor_tercero < 0:
                registrar(f"Factura {factura} con valor negativo: eliminando duplicados")
                df_factura = final_consolidar[final_consolidar["NRO_FACTURACLI"] == factura]
                duplicados_completos = df_factura.duplicated(
                    subset=["NRO_LEGALIACION", "VALOR TERCERO F", "CODIGO_ALTERNO"], keep="first"
                )
                duplicados_parciales = df_factura.duplicated(
                    subset=["NRO_LEGALIACION", "VALOR TERCERO F"], keep="first"
                )
                solo_parciales = duplicados_parciales & ~duplicados_completos
                indices_a_eliminar = df_factura[duplicados_completos].index
                if not indices_a_eliminar.empty:
                    registrar(f"Se eliminaran {len(indices_a_eliminar)} duplicados exactos")
                if solo_parciales.any():
                    registrar(f"{solo_parciales.sum()} posibles duplicados con codigo alterno distinto")
                final_consolidar = final_consolidar.drop(index=indices_a_eliminar)

        progreso(65, "Ajustando diferencias - pasada 2")
        df_facturas_real_comp = df_facturas_real[df_facturas_real["FACTURA"].isin(final_consolidar_comp["FACTURA"])]
        df_comparado = pd.merge(
            df_facturas_real_comp,
            final_consolidar_comp,
            on="FACTURA",
            suffixes=("_facturas_real", "_final_consolidar_comp"),
            how="outer",
        )
        df_comparado[["VALOR TERCERO", "VALOR TERCERO F"]] = df_comparado[["VALOR TERCERO", "VALOR TERCERO F"]].fillna(0)
        df_comparado["DIFERENCIA"] = df_comparado["VALOR TERCERO"] - df_comparado["VALOR TERCERO F"]
        valores_diferentes_de_cero = (df_comparado["DIFERENCIA"] != 0).sum().sum()
        registrar(f"Total de valores diferentes de 0: {valores_diferentes_de_cero}")

        for _, row in df_comparado.iterrows():
            factura = row["FACTURA"]
            valor_tercero = row["DIFERENCIA"]

            if valor_tercero > 1:
                registrar(f"Factura {factura} con valor positivo: reemplazando desde respaldo")
                final_consolidar = final_consolidar[final_consolidar["NRO_FACTURACLI"] != factura]
                filas_respaldo = facturacioninfoRespaldo[facturacioninfoRespaldo["NRO_FACTURACLI"] == factura]
                nueva_columna = filas_respaldo["TotalLegalizacion"] - filas_respaldo["VALOR_RECAUDO_PACIENTE"]
                filas_respaldo.insert(7, "VALOR TERCERO F", nueva_columna)
                filas_respaldo["VALOR TERCERO F"] = filas_respaldo["VALOR TERCERO F"].apply(lambda x: 0 if x < 0 else x)
                final_consolidar = pd.concat([final_consolidar, filas_respaldo], ignore_index=True)
                df_factura = final_consolidar[final_consolidar["NRO_FACTURACLI"] == factura]
                duplicados = df_factura.duplicated(
                    subset=["NRO_LEGALIACION", "VALOR TERCERO F", "CODIGO_ALTERNO"], keep="first"
                )
                indices_a_eliminar = df_factura[duplicados].index
                final_consolidar = final_consolidar.drop(index=indices_a_eliminar)
            elif valor_tercero < 0:
                registrar(f"Factura {factura} con valor negativo: eliminando duplicados")
                df_factura = final_consolidar[final_consolidar["NRO_FACTURACLI"] == factura]
                duplicados_completos = df_factura.duplicated(
                    subset=["NRO_LEGALIACION", "VALOR TERCERO F", "CODIGO_ALTERNO"], keep=False
                )
                duplicados_parciales = df_factura.duplicated(
                    subset=["NRO_LEGALIACION", "VALOR TERCERO F"], keep=False
                )
                solo_parciales = duplicados_parciales & ~duplicados_completos
                indices_a_eliminar = df_factura[duplicados_completos].index
                if not indices_a_eliminar.empty:
                    registrar(f"Se eliminaran {len(indices_a_eliminar)} duplicados exactos")
                if solo_parciales.any():
                    registrar(f"{solo_parciales.sum()} posibles duplicados con codigo alterno distinto")
                final_consolidar = final_consolidar.drop(index=indices_a_eliminar)

        progreso(80, "Ajustando diferencias - pasada 3")
        final_consolidar_comp = final_consolidar.groupby("NRO_FACTURACLI", as_index=False)["VALOR TERCERO F"].sum()
        final_consolidar_comp = final_consolidar_comp.rename(columns={"NRO_FACTURACLI": "FACTURA"})
        df_facturas_real_comp = df_facturas_real[df_facturas_real["FACTURA"].isin(final_consolidar_comp["FACTURA"])]
        df_comparado = pd.merge(
            df_facturas_real_comp,
            final_consolidar_comp,
            on="FACTURA",
            suffixes=("_facturas_real", "_final_consolidar_comp"),
            how="outer",
        )
        df_comparado[["VALOR TERCERO", "VALOR TERCERO F"]] = df_comparado[["VALOR TERCERO", "VALOR TERCERO F"]].fillna(0)
        df_comparado["DIFERENCIA"] = df_comparado["VALOR TERCERO"] - df_comparado["VALOR TERCERO F"]
        valores_diferentes_de_cero = (df_comparado["DIFERENCIA"] != 0).sum().sum()
        registrar(f"Total de valores diferentes de 0: {valores_diferentes_de_cero}")

        for _, row in df_comparado.iterrows():
            factura = row["FACTURA"]
            valor_tercero = row["DIFERENCIA"]

            if valor_tercero > 1:
                registrar(f"Factura {factura} con valor positivo: reemplazando desde respaldo")
                final_consolidar = final_consolidar[final_consolidar["NRO_FACTURACLI"] != factura]
                filas_respaldo = facturacioninfoRespaldo[facturacioninfoRespaldo["NRO_FACTURACLI"] == factura]
                nueva_columna = filas_respaldo["TotalLegalizacion"] - filas_respaldo["VALOR_RECAUDO_PACIENTE"]
                filas_respaldo.insert(7, "VALOR TERCERO F", nueva_columna)
                filas_respaldo["VALOR TERCERO F"] = filas_respaldo["VALOR TERCERO F"].apply(lambda x: 0 if x < 0 else x)
                final_consolidar = pd.concat([final_consolidar, filas_respaldo], ignore_index=True)
                df_factura = final_consolidar[final_consolidar["NRO_FACTURACLI"] == factura]
                duplicados = df_factura.duplicated(
                    subset=["NRO_LEGALIACION", "VALOR TERCERO F", "CODIGO_ALTERNO"], keep="first"
                )
                indices_a_eliminar = df_factura[duplicados].index
                final_consolidar = final_consolidar.drop(index=indices_a_eliminar)
            elif valor_tercero < 0:
                registrar(f"Factura {factura} con valor negativo: eliminando duplicados")
                df_factura = final_consolidar[final_consolidar["NRO_FACTURACLI"] == factura]
                duplicados = df_factura.duplicated(
                    subset=["NRO_LEGALIACION", "VALOR TERCERO F"], keep="first"
                )
                indices_a_eliminar = df_factura[duplicados].index
                final_consolidar = final_consolidar.drop(index=indices_a_eliminar)

        progreso(95, "Guardando archivo de salida")
        with pd.ExcelWriter(salida_path) as writer:
            final_consolidar.to_excel(writer, sheet_name="PEND_CONSOLIDAR", index=False)
            df_cambio_estado.to_excel(writer, sheet_name="CAMBIO_ESTADO", index=False)

        progreso(100, "Proceso finalizado")
        registrar(f"Archivo generado: {salida_path}")
        return True, f"Proceso completado. Archivo generado en: {salida_path}", salida_path, log_path

    except Exception as exc:
        registrar(f"Fallo en consolidacion: {exc}", es_error=True)
        registrar(traceback.format_exc(), es_error=True)
        progreso(100, "Proceso finalizado con error")
        return False, f"Error durante la consolidacion: {exc}", None, log_path

