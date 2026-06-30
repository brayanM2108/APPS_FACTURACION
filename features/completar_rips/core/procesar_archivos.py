import pandas as pd

from features.completar_rips.core.codigos_auxiliares import usecols, dtypes


def leer_informe(path_excel: str) -> pd.DataFrame:
    return pd.read_excel(
        path_excel,
        sheet_name="Informe De Facturacion",
        header=2, 
        engine="openpyxl"
    )

def leer_base_ppl(path_excel: str) -> pd.DataFrame:
    return pd.read_excel(
        path_excel,
        sheet_name="BASE",
        header= 0,
        engine="openpyxl"
    )

def cargar_base_csv(path_csv: str) -> pd.DataFrame:
    df = pd.read_csv(path_csv, usecols=usecols, dtype=dtypes)
    return df.rename(columns={
        "dtl1": "NumeroIdentificacion",
        "dtl2": "TipoIdentificacion",
        "dtl4": "Genero",
        "dtl5": "FechaNacimiento",
        "dtl19": "TipoDiscapacidad",
        "dtl29": "Pais",
        "dtl30": "Departamento",
        "dtl31": "Ciudad",
    })

