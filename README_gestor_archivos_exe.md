# Ejecutable Gestor de Archivos

Este ejecutable empaqueta la ventana moderna del gestor de archivos y sus dependencias de union de PDF.

## Requisitos
- Python instalado
- Dependencias del proyecto en `requirements.txt`
- PyInstaller

## Construccion
Ejecuta desde la raiz del proyecto:

```powershell
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --noconfirm gestor_archivos.spec
```

## Salida
El ejecutable se genera en `dist/gestor_archivos/gestor_archivos.exe`.

## Notas
- El Excel de auditoria se guarda en la misma carpeta del PDF unificado.
- El documento se toma del nombre antes del primer `_`.

