import pandas as pd

def llenar_factura(salida: pd.DataFrame, df_filtrado: pd.DataFrame) -> pd.DataFrame:
    prefijo = df_filtrado["PREFIJO_FACT"].astype(str).str.strip()
    numero = df_filtrado["NRO_FACTURACLI"].astype(str).str.strip()
    salida = salida.copy()
    salida["Factura"] = prefijo + numero
    return salida