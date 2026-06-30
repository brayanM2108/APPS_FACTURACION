import pandas as pd
import numpy as np

from features.completar_rips.core.codigos_auxiliares import (
    TIPO_DOC_MAP,
    TIPOS_USUARIO_NOMBRE_A_CODIGO,
    SEXO_MAP,
    PAIS_RESIDENCIA,
    CODIGOS_MUNICIPIOS,
    ZONA_RESIDENCIA_MAP,
    PAIS_ORIGEN_MAP
)

def llenar_tipo_identificacion_desde_cruce(
        salida: pd.DataFrame,
        df_cruzado: pd.DataFrame
) -> pd.DataFrame:
    salida = salida.copy()
    tipo_raw = df_cruzado["TipoIdentificacion"].astype(str).str.strip()
    salida["Tipo identificación"] = tipo_raw.map(TIPO_DOC_MAP).fillna("CC")
    return salida

def llenar_numero_identificacion(salida: pd.DataFrame, df_filtrado: pd.DataFrame) -> pd.DataFrame:
    salida = salida.copy()
    salida["Número identificación"] = df_filtrado["NUMERO_IDENTIFICACION"].astype(str).str.strip()
    return salida

def llenar_tipo_usuario_por_nombre(salida: pd.DataFrame, df_filtrado: pd.DataFrame, nombre_tipo_usuario: str) -> pd.DataFrame:
    salida = salida.copy()
    nombre = str(nombre_tipo_usuario).strip()
    if nombre not in TIPOS_USUARIO_NOMBRE_A_CODIGO:
        raise ValueError(f"Nombre de tipo de usuario invalido: {nombre}")
    salida["Tipo de usuario"] = TIPOS_USUARIO_NOMBRE_A_CODIGO[nombre]
    return salida

def llenar_fecha_nacimiento_desde_cruce(
        salida: pd.DataFrame,
        df_cruzado: pd.DataFrame
) -> pd.DataFrame:
    salida = salida.copy()
    salida["Fecha de nacimiento"] = df_cruzado["FechaNacimiento"].astype(str).str.strip()
    return salida

def llenar_sexo_desde_cruce(
        salida: pd.DataFrame,
        df_cruzado: pd.DataFrame
) -> pd.DataFrame:
    salida = salida.copy()
    sexo_raw = df_cruzado["Genero"].astype(str).str.strip()
    salida["Sexo"] = sexo_raw.map(SEXO_MAP)

    if salida["Sexo"].isna().any():
        valores = sorted(set(sexo_raw[salida["Sexo"].isna()].tolist()))
        raise ValueError(f"Genero sin mapeo para Sexo: {valores}")

    return salida

def llenar_pais_residencia(salida: pd.DataFrame, df_filtrado: pd.DataFrame) -> pd.DataFrame:
    salida = salida.copy()
    salida["País residencia"] = PAIS_RESIDENCIA
    return salida

def llenar_municipio_residencia_aleatorio(
        salida: pd.DataFrame,
        df_filtrado: pd.DataFrame
) -> pd.DataFrame:

    salida = salida.copy()

    codigos = [str(c).zfill(5) for c in CODIGOS_MUNICIPIOS]

    n = len(df_filtrado)

    salida["Municipio residencia"] = np.random.choice(
        codigos,
        size=n,
        replace=True
    )

    return  salida

def llenar_zona_residencia(salida: pd.DataFrame, df_filtrado: pd.DataFrame) -> pd.DataFrame:
    salida["Zona residencia"] = ZONA_RESIDENCIA_MAP
    return salida

def llenar_incapacidad_desde_cruce(
        salida: pd.DataFrame,
        df_cruzado: pd.DataFrame
) -> pd.DataFrame:
    salida = salida.copy()
    raw = df_cruzado["TipoDiscapacidad"].astype(str).str.strip()
    salida["Incapacidad"] = raw.apply(lambda v: "NO" if v else "SI")
    return salida

def llenar_pais_origen_desde_cruce(
        salida: pd.DataFrame,
        df_cruzado: pd.DataFrame
) -> pd.DataFrame:
    salida = salida.copy()
    pais_raw = df_cruzado["Pais"].astype(str).str.strip()
    salida["País de origen"] = pais_raw.map(PAIS_ORIGEN_MAP).fillna("170")
    return salida




