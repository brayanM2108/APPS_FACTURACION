import pandas as pd
import numpy as np
from features.completar_rips.core.codigos_auxiliares import (
    TIPO_ID_PROFESIONAL,
    CODIGO_PRESTADOR,
    CONCEPTO_RECAUDO,
    VALOR_PAGO_MODERADOR,
    TIPO_DIAGNOSTICO_PRINCIPAL,
    DOCUMENTOS_PROFESIONALES,
    COLUMNAS_SALIDA,
    TIPOS_MODALIDAD_ATENCION_A_CODIGO,
    GRUPO_SERVICIOS_NOMBRE_A_CODIGO,
    SERVICIO_POR_CONVENIO,
    FINALIDAD_POR_CONVENIO,
    CAUSA_EXTERNA_POR_CONVENIO,
    DIAGNOSTICO_PRINCIPAL_POR_CONVENIO,
)


def crear_plantilla_salida() -> pd.DataFrame:
    return pd.DataFrame(columns=COLUMNAS_SALIDA)

def filtrar_por_factura(df: pd.DataFrame, numero_factura: int) -> pd.DataFrame:
    serie = df["NRO_FACTURACLI"].astype(str).str.strip()
    filtrado = df[serie == str(numero_factura).strip()]

    if filtrado.empty:
        raise ValueError(f"No se encontró el número de factura: {numero_factura}")

    return filtrado


def llenar_codigo_prestador(salida: pd.DataFrame, df_filtrado: pd.DataFrame) -> pd.DataFrame:
    salida = salida.copy()
    salida["Código Prestador"] = CODIGO_PRESTADOR
    return salida

def llenar_fecha_y_hora(salida: pd.DataFrame, df_filtrado: pd.DataFrame) -> pd.DataFrame:
    salida = salida.copy()
    salida["Fecha y hora"] = df_filtrado["FechaLegalizacion"].astype(str).str.strip()
    return salida

def llenar_modalidad_tecnologia_salud(
        salida: pd.DataFrame,
        df_filtrado: pd.DataFrame,
        nombre_modalidad: str
) -> pd.DataFrame:
    salida = salida.copy()
    nombre = str(nombre_modalidad).strip()
    if nombre not in TIPOS_MODALIDAD_ATENCION_A_CODIGO:
        raise ValueError(f"Modalidad de atencion invalida: {nombre}")
    salida["Modalidad tecnología salud"] = TIPOS_MODALIDAD_ATENCION_A_CODIGO[nombre]
    return salida

def llenar_grupo_servicios(
        salida: pd.DataFrame,
        df_filtrado: pd.DataFrame,
        nombre_grupo: str
) -> pd.DataFrame:
    salida = salida.copy()
    nombre = str(nombre_grupo).strip()
    if nombre not in GRUPO_SERVICIOS_NOMBRE_A_CODIGO:
        raise ValueError(f"Grupo de servicios invalido: {nombre}")
    salida["Grupo servicios"] = GRUPO_SERVICIOS_NOMBRE_A_CODIGO[nombre]
    return salida



def llenar_servicio_por_convenio(salida: pd.DataFrame, df_filtrado: pd.DataFrame) -> pd.DataFrame:
    salida = salida.copy()
    convenio = df_filtrado["CONVENIO"].astype(str).str.strip()
    salida["Servicio"] = convenio.map(SERVICIO_POR_CONVENIO)

    if salida["Servicio"].isna().any():
        valores = sorted(set(convenio[salida["Servicio"].isna()].tolist()))
        raise ValueError(f"CONVENIO sin mapeo para Servicio: {valores}")

    return salida

def llenar_finalidad_tecnologia_por_convenio(
        salida: pd.DataFrame,
        df_filtrado: pd.DataFrame
) -> pd.DataFrame:
    salida = salida.copy()
    convenio = df_filtrado["CONVENIO"].astype(str).str.strip()
    salida["Finalidad tecnología"] = convenio.map(FINALIDAD_POR_CONVENIO)

    if salida["Finalidad tecnología"].isna().any():
        valores = sorted(set(convenio[salida["Finalidad tecnología"].isna()].tolist()))
        raise ValueError(f"CONVENIO sin mapeo para Finalidad tecnología: {valores}")

    return salida

def llenar_tipo_id_profesional(salida: pd.DataFrame, df_filtrado: pd.DataFrame) -> pd.DataFrame:
    salida = salida.copy()
    salida["Tipo ID profesional"] = TIPO_ID_PROFESIONAL
    return salida

def llenar_numero_id_profesional_aleatorio(
        salida: pd.DataFrame,
        df_filtrado: pd.DataFrame
) -> pd.DataFrame:
    salida = salida.copy()
    n = len(df_filtrado)
    salida["Número ID profesional"] = np.random.choice(DOCUMENTOS_PROFESIONALES, size=n, replace=True)
    return salida

def llenar_valor_servicio(salida: pd.DataFrame, df_filtrado: pd.DataFrame) -> pd.DataFrame:
    salida = salida.copy()
    salida["Valor servicio"] = df_filtrado["ValorUnitario"]
    return salida

def llenar_concepto_recaudo(salida: pd.DataFrame, df_filtrado: pd.DataFrame) -> pd.DataFrame:
    salida = salida.copy()
    salida["Concepto recaudo"] = CONCEPTO_RECAUDO
    return salida


def llenar_valor_pago_moderador(salida: pd.DataFrame, df_filtrado: pd.DataFrame) -> pd.DataFrame:
    salida = salida.copy()
    salida["Valor pago moderador"] = VALOR_PAGO_MODERADOR
    return salida

def llenar_codigo(salida: pd.DataFrame, df_filtrado: pd.DataFrame) -> pd.DataFrame:
    salida = salida.copy()
    salida["Código"] = df_filtrado["CODIGO_ALTERNO"].astype(str).str.strip()
    return salida



def llenar_causa_externa_por_convenio(
        salida: pd.DataFrame,
        df_filtrado: pd.DataFrame
) -> pd.DataFrame:
    salida = salida.copy()
    convenio = df_filtrado["CONVENIO"].astype(str).str.strip()
    salida["Causa externa"] = convenio.map(CAUSA_EXTERNA_POR_CONVENIO)

    if salida["Causa externa"].isna().any():
        valores = sorted(set(convenio[salida["Causa externa"].isna()].tolist()))
        raise ValueError(f"CONVENIO sin mapeo para Causa externa: {valores}")

    return salida

def llenar_diagnostico_principal_por_convenio(
        salida: pd.DataFrame,
        df_filtrado: pd.DataFrame,
        modo_diagnostico: str,
        df_cruce_ppl: pd.DataFrame | None = None
) -> pd.DataFrame:
    salida = salida.copy()

    if modo_diagnostico == "FOMAG":
        salida["Código Diagnóstico principal"] = DIAGNOSTICO_PRINCIPAL_POR_CONVENIO

    elif modo_diagnostico == "PPL":
        if df_cruce_ppl is None:
            raise ValueError("Se requiere df_cruce_ppl para modo PPL.")
        salida["Código Diagnóstico principal"] = df_cruce_ppl["CODIGO CIE 10-1"] = df_cruce_ppl["CODIGO CIE 10-1"].astype(str).str.strip()

    else:
        raise ValueError(f"Modo diagnostico invalido: {modo_diagnostico}")

    return salida

def llenar_tipo_diagnostico_principal(salida: pd.DataFrame, df_filtrado: pd.DataFrame) -> pd.DataFrame:
    salida = salida.copy()
    salida["Tipo diagnóstico principal"] = TIPO_DIAGNOSTICO_PRINCIPAL
    return salida


def llenar_autorizacion_desde_ppl(
        salida: pd.DataFrame,
        df_cruce_ppl: pd.DataFrame
) -> pd.DataFrame:
    salida = salida.copy()
    salida["Autorización"] = df_cruce_ppl["AUTORIZACION"].astype(str).str.strip()
    return salida

