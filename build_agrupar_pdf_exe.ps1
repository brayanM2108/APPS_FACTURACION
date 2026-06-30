$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\Users\TECNICOESTADISTICO.P\PycharmProjects\APPS_FACTURACION"
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$EntryPoint = Join-Path $ProjectRoot "run_ordenar_pdf.py"

if (-not (Test-Path $PythonExe)) {
    throw "No se encontro Python en el entorno virtual: $PythonExe"
}

if (-not (Test-Path $EntryPoint)) {
    throw "No se encontro el entrypoint: $EntryPoint"
}

Push-Location $ProjectRoot
try {
    & $PythonExe -m pip install --upgrade pip pyinstaller
    & $PythonExe -m py_compile $EntryPoint

    & $PythonExe -m PyInstaller `
        --noconfirm `
        --clean `
        --windowed `
        --onefile `
        --name AgruparPDF `
        --paths $ProjectRoot `
        --collect-all pikepdf `
        --collect-submodules PIL `
        --collect-submodules pypdf `
        $EntryPoint

    $exePath = Join-Path $ProjectRoot "dist\AgruparPDF.exe"
    if (Test-Path $exePath) {
        Write-Host "EXE generado correctamente en: $exePath"
    } else {
        throw "La compilacion termino, pero no se encontro el EXE esperado en $exePath"
    }
}
finally {
    Pop-Location
}

