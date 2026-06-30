from dataclasses import dataclass
from pathlib import Path
import pandas as pd

from features.completar_rips.core.codigos_auxiliares import COLUMNAS_SALIDA
from features.completar_rips.core.completar_hoja_transaccion import llenar_factura
from features.completar_rips.core.procesar_archivos import leer_informe, cargar_base_csv, leer_base_ppl
from features.completar_rips.core.completar_hoja_usuarios import (
    llenar_numero_identificacion,
    llenar_tipo_usuario_por_nombre,
    llenar_tipo_identificacion_desde_cruce,
    llenar_sexo_desde_cruce,
    llenar_zona_residencia,
    llenar_incapacidad_desde_cruce,
    llenar_pais_residencia,
    llenar_municipio_residencia_aleatorio,
    llenar_fecha_nacimiento_desde_cruce,
    llenar_pais_origen_desde_cruce
)

from features.completar_rips.core.completar_hoja_consultas import (
    llenar_codigo_prestador,
    llenar_fecha_y_hora,
    llenar_modalidad_tecnologia_salud,
    llenar_grupo_servicios,
    llenar_servicio_por_convenio,
    llenar_finalidad_tecnologia_por_convenio,
    llenar_tipo_id_profesional,
    llenar_numero_id_profesional_aleatorio,
    llenar_valor_servicio,
    llenar_concepto_recaudo,
    llenar_valor_pago_moderador,
    llenar_causa_externa_por_convenio,
    llenar_diagnostico_principal_por_convenio,
    llenar_tipo_diagnostico_principal,
    llenar_autorizacion_desde_ppl,
    llenar_codigo,
    filtrar_por_factura
)

@dataclass
class CompletarRipsConfig:
    informe_path: Path
    base_csv_path: Path
    output_path: Path
    numero_factura: int
    tipo_usuario: str
    modalidad_tecnologia: str
    grupo_servicios: str
    modo_diagnostico: str
    base_ppl_path: Path | None = None


class CompletarRipsService:
    def __init__(self, config: CompletarRipsConfig):
        self.config = config

    def ejecutar(self) -> Path:
        df_informe = leer_informe(str(self.config.informe_path))
        df_filtrado = filtrar_por_factura(df_informe, self.config.numero_factura).reset_index(drop=True)

        df_filtrado["NUMERO_IDENTIFICACION"] = (
            df_filtrado["NUMERO_IDENTIFICACION"].astype(str).str.strip()
        )

        # Eliminar duplicados por número de identificación
        df_filtrado = (
            df_filtrado
            .drop_duplicates(subset=["NUMERO_IDENTIFICACION"], keep="first")
            .reset_index(drop=True)
        )

        df_base = cargar_base_csv(str(self.config.base_csv_path))
        df_base["NumeroIdentificacion"] = df_base["NumeroIdentificacion"].astype(str).str.strip()

        df_cruzado = df_filtrado.merge(
            df_base,
            left_on="NUMERO_IDENTIFICACION",
            right_on="NumeroIdentificacion",
            how="left",
        ).reset_index(drop=True)

        df_cruce_ppl = None
        if self.config.modo_diagnostico == "PPL":
            if not self.config.base_ppl_path:
                raise ValueError("Se requiere base PPL para modo PPL.")
            df_ppl = leer_base_ppl(str(self.config.base_ppl_path))
            df_ppl.columns = df_ppl.columns.str.strip()
            df_ppl["IDENTIFICACIÓN"] = df_ppl["IDENTIFICACIÓN"].astype(str).str.strip()

            df_cruce_ppl = df_filtrado.merge(
                df_ppl,
                left_on="NUMERO_IDENTIFICACION",
                right_on="IDENTIFICACIÓN",
                how="left",
            )

        salida = pd.DataFrame(index=df_filtrado.index, columns=COLUMNAS_SALIDA)

        salida = llenar_factura(salida, df_filtrado)
        salida = llenar_numero_identificacion(salida, df_filtrado)
        salida = llenar_tipo_usuario_por_nombre(salida, df_filtrado, self.config.tipo_usuario)
        salida = llenar_codigo_prestador(salida, df_filtrado)
        salida = llenar_fecha_y_hora(salida, df_filtrado)
        salida = llenar_modalidad_tecnologia_salud(salida, df_filtrado, self.config.modalidad_tecnologia)
        salida = llenar_grupo_servicios(salida, df_filtrado, self.config.grupo_servicios)
        salida = llenar_servicio_por_convenio(salida, df_filtrado)
        salida = llenar_finalidad_tecnologia_por_convenio(salida, df_filtrado)
        salida = llenar_tipo_id_profesional(salida, df_filtrado)
        salida = llenar_numero_id_profesional_aleatorio(salida, df_filtrado)
        salida = llenar_valor_servicio(salida, df_filtrado)
        salida = llenar_concepto_recaudo(salida, df_filtrado)
        salida = llenar_valor_pago_moderador(salida, df_filtrado)
        salida = llenar_codigo(salida, df_filtrado)
        salida = llenar_causa_externa_por_convenio(salida, df_filtrado)
        salida = llenar_diagnostico_principal_por_convenio(
            salida,
            df_filtrado,
            modo_diagnostico=self.config.modo_diagnostico,
            df_cruce_ppl=df_cruce_ppl,
        )
        salida = llenar_tipo_diagnostico_principal(salida, df_filtrado)
        salida = llenar_tipo_identificacion_desde_cruce(salida, df_cruzado)
        salida = llenar_sexo_desde_cruce(salida, df_cruzado)
        salida = llenar_fecha_nacimiento_desde_cruce(salida, df_cruzado)
        salida = llenar_pais_residencia(salida, df_filtrado)
        salida = llenar_pais_origen_desde_cruce(salida, df_cruzado)
        salida = llenar_municipio_residencia_aleatorio(salida, df_filtrado)
        salida = llenar_incapacidad_desde_cruce(salida, df_cruzado)
        salida = llenar_zona_residencia(salida, df_filtrado)

        if df_cruce_ppl is not None:
            salida = llenar_autorizacion_desde_ppl(salida, df_cruce_ppl)

        salida = salida[COLUMNAS_SALIDA]
        salida.to_excel(self.config.output_path, index=False)
        return self.config.output_path