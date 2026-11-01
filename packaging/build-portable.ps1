# Build del ejecutable Aurora PORTABLE (onefile, windowed). Ejecutar DESDE LA RAIZ del proyecto:
#   powershell -NoProfile -ExecutionPolicy Bypass -File packaging\build-portable.ps1
# Resultado: dist\portable\Aurora-Portable.exe + dist\portable\Aurora.portable (marcador)
$ErrorActionPreference = 'Stop'
$py = "C:\Users\fabia\AppData\Local\Programs\Python\Python312\python.exe"

Write-Host "Construyendo portable con PyInstaller (onefile)..."
& $py -m PyInstaller --noconfirm --clean --windowed --onefile --name Aurora-Portable `
    --distpath dist\portable --workpath build/pyi-portable --specpath build `
    --paths . `
    --collect-all winrt --collect-submodules winrt `
    --hidden-import keyboard --hidden-import pystray --hidden-import PIL `
    main.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller fallo con codigo $LASTEXITCODE" }

$exe = Join-Path $PWD "dist\portable\Aurora-Portable.exe"
if (-not (Test-Path $exe)) { throw "No se genero $exe" }
New-Item -ItemType File -Force -Path (Join-Path $PWD "dist\portable\Aurora.portable") | Out-Null

Write-Host "============================================================"
Write-Host "  Ejecutable portable: $exe"
Write-Host "  Marcador: dist\portable\Aurora.portable (datos en .\data junto al exe)"
Write-Host "  Nota: el hotkey global requiere ejecutar como Administrador."
Write-Host "============================================================"
