from typing import Any, Callable, Dict

import pandas as pd
from openpyxl.workbook.workbook import Workbook


class ProcesadorHojaTransaccion:
    def __init__(
            self,
            get_target_headers: Callable[[Any, int], Dict[str, int]],
            find_target_col: Callable[[Dict[str, int], str], int | None],
            resolve_source_column: Callable[[list[str], str], str | None],
            to_clean_text: Callable[[Any], str],
            validate_transaccion: Callable[[Dict[str, Any]], None],
    ):
        self._get_target_headers = get_target_headers
        self._find_target_col = find_target_col
        self._resolve_source_column = resolve_source_column
        self._to_clean_text = to_clean_text
        self._validate_transaccion = validate_transaccion

    def ejecutar(self, df_source: pd.DataFrame, wb: Workbook, config: Dict[str, Any]) -> str:
        ws = wb[str(config["transaccion_sheet"])]
        headers = self._get_target_headers(ws, int(config["transaccion_header_row"]))

        required_cols = ["numDocumentoIdObligado", "numFactura", "tipoNota", "numNota"]
        target_cols: Dict[str, int] = {}
        for col_name in required_cols:
            col_idx = self._find_target_col(headers, col_name)
            if col_idx is None:
                raise ValueError(f"No se encontro la columna destino '{col_name}' en hoja transaccion.")
            target_cols[col_name] = col_idx

        if df_source.empty:
            raise ValueError("La hoja de informacion no tiene filas para transaccion.")

        factura_col = self._resolve_source_column(df_source.columns.tolist(), "Factura")
        if not factura_col:
            raise ValueError("No se pudo mapear columna origen 'Factura' para transaccion.")

        first_row = df_source.iloc[0]
        out = {
            "numDocumentoIdObligado": str(config["num_documento_id_obligado"]),
            "numFactura": self._to_clean_text(first_row[factura_col]),
            "tipoNota": "NA",
            "numNota": "",
        }

        self._validate_transaccion(out)

        row_out = int(config["transaccion_start_row"])
        for field, col_idx in target_cols.items():
            ws.cell(row=row_out, column=col_idx, value=out.get(field, ""))

        return out["numDocumentoIdObligado"]
