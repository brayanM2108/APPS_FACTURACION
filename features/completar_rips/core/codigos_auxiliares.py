TIPO_ID_PROFESIONAL = "CC"

CODIGO_PRESTADOR = "110011908701"

CONCEPTO_RECAUDO = "05"

VALOR_PAGO_MODERADOR = 0

TIPO_DIAGNOSTICO_PRINCIPAL = "03"

PAIS_RESIDENCIA = "170"

PAIS_ORIGEN_MAP = {
    "Colombia": "170",
    "Venezuela": "862",
}

ZONA_RESIDENCIA_MAP = "02"

SEXO_MAP = {
    "Masculino": "M",
    "Femenino": "F",
    "Indeterminado": "I",
}

TIPO_DOC_MAP = {
    "Cédula de ciudadanía": "CC",
    "Cédula de extranjería": "CE",
    "Pasaporte" : "PA",
    "Salvoconducto" : "SC",
    "Permiso especial de permanencia" : "PE",
    "Registro civil": "RC",
    "Tarjeta de identidad": "TI",
    "Adulto sin identificación": "AS",
    "Menor sin identificación": "MS",
    "DOCUMENTO EXTRANJERO": "DE",
    "Número de identificación tributaria NIT" : "NIT",
    "Permiso protencion temporal": "PT"

}


DOCUMENTOS_PROFESIONALES = [
    "1192724621",
    "1002416634",
    "1115076344",
    "1115072772",
    "1015440838",
    "1130618101",
    "1000856043",
    "1000115666",
    "1031175730",
    "1003809064",
    "1070949510",
    "1019143550",
    "1069758825",
    "1000860177",
    "80920937",
    "1057574954",
    "1000066542",
    "1001173868",
    "1120365516",
    "52860796",
]

COLUMNAS_SALIDA = [

    "Factura",
    "Tipo identificación",
    "Número identificación",
    "Tipo de usuario",
    "Fecha de nacimiento",
    "Sexo",
    "País residencia",
    "Municipio residencia",
    "Zona residencia",
    "País de origen",
    "Incapacidad",
    "Fecha y hora",
    "Autorización",
    "Código Prestador",
    "Modalidad tecnología salud",
    "Grupo servicios",
    "Servicio",
    "Finalidad tecnología",
    "Tipo ID profesional",
    "Número ID profesional",
    "Valor servicio",
    "Concepto recaudo",
    "Valor pago moderador",
    "Factura pago moderador",
    "Código",
    "Descripción",
    "Causa externa",
    "Código Diagnóstico principal",
    "Tipo diagnóstico principal",
]

TIPOS_USUARIO_NOMBRE_A_CODIGO = {
    "Contributivo cotizante": "01",
    "Contributivo beneficiario": "02",
    "Contributivo adicional": "03",
    "Subsidiado": "04",
    "No afiliado": "05",
    "Especial o Excepcion cotizante": "06",
    "Especial o Excepcion beneficiario": "07",
    "Personas privadas de la libertad a cargo del Fondo Nacional de Salud": "08",
    "Tomador / Amparado ARL": "09",
    "Tomador / Amparado SOAT": "10",
    "Tomador / Amparado Planes  voluntarios de salud": "11",
    "Particular": "12",
    "Especial o Exepcion no cotizante Ley 352 de 1997": "13",
}

TIPOS_MODALIDAD_ATENCION_A_CODIGO = {
    "Intramural": "01",
    "Extramural unidad móvil" : "02",
    "Extramural domiciliaria": "03",
    "Extramural jornada de salud": "04",
    "Telemedicina interactiva": "06",
    "Telemedicina no interactiva": "07",
    "Telemedicina telexperticia": "08",
    "Telemedicina telemonitoreo": "09",
}

GRUPO_SERVICIOS_NOMBRE_A_CODIGO = {
    "Consulta externa": "01",
    "Apoyo diagnóstico y complementación terapéutica": "02",
    "Internación": "03",
    "Quirúrgico": "04",
    "Atención inmediata": "05",
}

CODIGOS_MUNICIPIOS = {
    "11001",
    "05001",
    "08001",
    "76001",
    "15001",
    "68001",
    "25019",
    "25035",
    "25040",
    "25053",
    "25086",
    "25095",
    "25099",
    "25120",
    "25123",
    "25126",
    "25148",
    "25151",
    "25154",
    "25168",
    "25175",
    "25178",
    "25181",
    "25183",
    "25200",
    "25214",
    "25224",
    "25245",
    "25258",
    "25260",
    "25269",
    "25279",
    "25281",
    "25286",
    "25288",
    "25290",
    "25293",
    "25295",
    "25297",
    "25299",
    "25307",
    "25312",
    "25317",
    "25320",
    "25322",
    "25324",
    "25326",
    "25328",
    "25335",
    "25339",
    "25368",
    "25372",
    "25377",
    "25386",
    "25394",
    "25398",
    "25402",
    "25407",
    "25426",
    "25430",
    "25436",
    "25438",
    "25473",
    "25483",
    "25486",
    "25488",
    "25489",
    "25491",
    "25506",
    "25513",
    "25518",
    "25524",
    "25530",
    "25535",
    "25572",
    "25580",
    "25592",
    "25594",
    "25596",
    "25599",
    "25612"
}


SERVICIO_POR_CONVENIO = {
    "Patrimonio Autonomo Fondo Atención Salud PPL 2024": "345",
    "FONDO NACIONAL DE PRESTACIONES SOCIALES DEL": "344",
}

FINALIDAD_POR_CONVENIO = {
    "Patrimonio Autonomo Fondo Atención Salud PPL 2024": "44",
    "FONDO NACIONAL DE PRESTACIONES SOCIALES DEL": "11",
}

CAUSA_EXTERNA_POR_CONVENIO = {
    "Patrimonio Autonomo Fondo Atención Salud PPL 2024": "38",
    "FONDO NACIONAL DE PRESTACIONES SOCIALES DEL": "40",
}

DIAGNOSTICO_PRINCIPAL_POR_CONVENIO = "Z719"

MODO_DIAGNOSTICO = ""

usecols = [
    "NumeroIdentificacion",
    "TipoIdentificacion",
    "Genero",
    "FechaNacimiento",
    "TipoDiscapacidad",
    "Pais",
    "Departamento",
    "Ciudad",
]

dtypes = {
    "NumeroIdentificacion": "string",
    "TipoIdentificacion": "string",
    "Genero": "string",
    "FechaNacimiento": "string",
    "TipoDiscapacidad": "string",
    "Pais": "string",
    "Departamento": "string",
    "Ciudad": "string",
}

usecols = [
    "dtl1",  # NumeroIdentificacion
    "dtl2",  # TipoIdentificacion
    "dtl4",  # Genero
    "dtl5",  # FechaNacimiento
    "dtl19", # TipoDiscapacidad
    "dtl29", # Pais
    "dtl30", # Departamento
    "dtl31", # Ciudad
]

dtypes = {col: "string" for col in usecols}