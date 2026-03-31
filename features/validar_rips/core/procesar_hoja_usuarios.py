from typing import Any, Callable, Dict, List, Set

import pandas as pd
from openpyxl.workbook.workbook import Workbook


class ProcesadorHojaUsuarios:
    def __init__(
            self,
            get_target_headers: Callable[[Any, int], Dict[str, int]],
            find_target_col: Callable[[Dict[str, int], str], int | None],
            resolve_source_column: Callable[[List[str], str], str | None],
            to_clean_text: Callable[[Any], str],
            normalize_tipo_documento: Callable[[Any], str],
            normalize_tipo_usuario: Callable[[Any], str],
            normalize_fecha_yyyy_mm_dd: Callable[[Any], str],
            normalize_sexo: Callable[[Any], str],
            normalize_country_or_municipio_code: Callable[[Any], str],
            normalize_zona: Callable[[Any], str],
            normalize_incapacidad: Callable[[Any], str],
            validate_usuario_row: Callable[[Dict[str, Any]], None],
    ):
        self._get_target_headers = get_target_headers
        self._find_target_col = find_target_col
        self._resolve_source_column = resolve_source_column
        self._to_clean_text = to_clean_text
        self._normalize_tipo_documento = normalize_tipo_documento
        self._normalize_tipo_usuario = normalize_tipo_usuario
        self._normalize_fecha_yyyy_mm_dd = normalize_fecha_yyyy_mm_dd
        self._normalize_sexo = normalize_sexo
        self._normalize_country_or_municipio_code = normalize_country_or_municipio_code
        self._normalize_zona = normalize_zona
        self._normalize_incapacidad = normalize_incapacidad
        self._validate_usuario_row = validate_usuario_row

    def ejecutar(
            self,
            df_source: pd.DataFrame,
            wb: Workbook,
            config: Dict[str, Any],
            num_documento_id_obligado: str,
    ) -> Set[str]:
        ws = wb[str(config["usuarios_sheet"])]
        headers = self._get_target_headers(ws, int(config["usuarios_header_row"]))

        required_cols = [
            "tipoDocumentoIdentificacion",
            "numDocumentoIdentificacion",
            "num_DocumentoIdObligado",
            "tipoUsuario",
            "fechaNacimiento",
            "codSexo",
            "codPaisResidencia",
            "codMunicipioResidencia",
            "codZonaTerritorialResidencia",
            "incapacidad",
            "codPaisOrigen",
            "consecutivo",
        ]

        target_cols: Dict[str, int] = {}
        for col_name in required_cols:
            col_idx = self._find_target_col(headers, col_name)
            if col_idx is None:
                raise ValueError(f"No se encontro la columna destino '{col_name}' en hoja usuarios.")
            target_cols[col_name] = col_idx

        source_mapping = {
            "tipoDocumentoIdentificacion": "Tipo identificación",
            "numDocumentoIdentificacion": "Número identificación",
            "tipoUsuario": "Tipo de usuario",
            "fechaNacimiento": "Fecha de nacimiento",
            "codSexo": "Sexo",
            "codPaisResidencia": "País residencia",
            "codMunicipioResidencia": "Municipio residencia",
            "codZonaTerritorialResidencia": "Zona residencia",
            "incapacidad": "Incapacidad",
            "codPaisOrigen": "País de origen",
        }

        resolved: Dict[str, str] = {}
        for target_field, source_name in source_mapping.items():
            src_col = self._resolve_source_column(df_source.columns.tolist(), source_name)
            if not src_col:
                raise ValueError(f"No se pudo mapear columna origen '{source_name}' para '{target_field}'.")
            resolved[target_field] = src_col

        errors: List[str] = []
        usuarios_ids: Set[str] = set()
        seen_num_doc: Set[str] = set()
        row_out = int(config["usuarios_start_row"])
        next_consecutivo = 1

        for row_num_excel, (_, src_row) in enumerate(df_source.iterrows(), start=2):
            out = {
                "tipoDocumentoIdentificacion": self._normalize_tipo_documento(
                    src_row[resolved["tipoDocumentoIdentificacion"]]
                ),
                "numDocumentoIdentificacion": self._to_clean_text(src_row[resolved["numDocumentoIdentificacion"]]),
                "num_DocumentoIdObligado": self._to_clean_text(num_documento_id_obligado),
                "tipoUsuario": self._normalize_tipo_usuario(src_row[resolved["tipoUsuario"]]),
                "fechaNacimiento": self._normalize_fecha_yyyy_mm_dd(src_row[resolved["fechaNacimiento"]]),
                "codSexo": self._normalize_sexo(src_row[resolved["codSexo"]]),
                "codPaisResidencia": self._normalize_country_or_municipio_code(src_row[resolved["codPaisResidencia"]]),
                "codMunicipioResidencia": self._normalize_country_or_municipio_code(src_row[resolved["codMunicipioResidencia"]]),
                "codZonaTerritorialResidencia": self._normalize_zona(src_row[resolved["codZonaTerritorialResidencia"]]),
                "incapacidad": self._normalize_incapacidad(src_row[resolved["incapacidad"]]),
                "codPaisOrigen": self._normalize_country_or_municipio_code(src_row[resolved["codPaisOrigen"]]),
                "consecutivo": next_consecutivo,
            }

            if out["numDocumentoIdentificacion"] in seen_num_doc:
                continue

            try:
                self._validate_usuario_row(out)
            except ValueError as e:
                errors.append(f"Fila origen {row_num_excel}: {e}")
                continue

            for field in required_cols:
                value_to_write = out.get(field, "")
                if field == "consecutivo" and str(value_to_write).strip() != "":
                    value_to_write = int(value_to_write)

                cell = ws.cell(row=row_out, column=target_cols[field], value=value_to_write)
                if field == "consecutivo":
                    cell.number_format = "0"

            seen_num_doc.add(out["numDocumentoIdentificacion"])
            usuarios_ids.add(out["numDocumentoIdentificacion"])
            row_out += 1
            next_consecutivo += 1

        if errors:
            msg = "\n".join(errors[:50])
            raise ValueError(
                "Se encontraron filas invalidas en 'usuarios'.\n"
                f"Total errores: {len(errors)}\n"
                f"Primeros errores:\n{msg}"
            )

        return usuarios_ids
