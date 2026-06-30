import pandas as pd
from pathlib import Path

informe = Path(r"C:\Users\TECNICOESTADISTICO.P\Downloads\COMPLETAR RIPS PPL\Informe De Facturacion (6).xlsx")
ppl = Path(r"C:\Users\TECNICOESTADISTICO.P\Downloads\COMPLETAR RIPS PPL\PPL ABRIL .xlsx")
numero_factura = "15488"

df_informe = pd.read_excel(informe, sheet_name="Informe De Facturacion", header=2, engine="openpyxl")
df_filtrado = df_informe[df_informe["NRO_FACTURACLI"].astype(str).str.strip() == str(numero_factura).strip()].copy()
df_filtrado["NUMERO_IDENTIFICACION"] = df_filtrado["NUMERO_IDENTIFICACION"].astype(str).str.strip()

df_ppl = pd.read_excel(ppl, sheet_name="BASE", header=0, engine="openpyxl")
df_ppl.columns = df_ppl.columns.map(lambda c: str(c).strip())
if "IDENTIFICACIÓN" in df_ppl.columns:
    df_ppl["IDENTIFICACIÓN"] = df_ppl["IDENTIFICACIÓN"].astype(str).str.strip()

# Merge
if "IDENTIFICACIÓN" in df_ppl.columns:
    df_cruce = df_filtrado.merge(df_ppl, left_on="NUMERO_IDENTIFICACION", right_on="IDENTIFICACIÓN", how="left")
else:
    df_cruce = None

print("Filas filtradas:", len(df_filtrado))
print("Columnas PPL con 'CIE':", [c for c in df_ppl.columns if "CIE" in c])
print("Existe IDENTIFICACIÓN:", "IDENTIFICACIÓN" in df_ppl.columns)
print("Existe CODIGO CIE 10-1:", "CODIGO CIE 10-1" in df_ppl.columns)

if df_cruce is not None:
    print("Matches identificacion:", df_cruce["IDENTIFICACIÓN"].notna().sum())
    if "CODIGO CIE 10-1" in df_cruce.columns:
        print("Nulos CODIGO CIE 10-1:", df_cruce["CODIGO CIE 10-1"].isna().sum())
        print("Primeros valores CODIGO CIE 10-1:", df_cruce["CODIGO CIE 10-1"].head(5).tolist())