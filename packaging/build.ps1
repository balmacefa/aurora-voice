# Build del ejecutable Aurora (onedir, windowed). Ejecutar DESDE LA RAIZ del proyecto:
#   powershell -NoProfile -ExecutionPolicy Bypass -File packaging\build.ps1
# Resultado: dist\Aurora\Aurora.exe
$ErrorActionPreference = 'Stop'
$py = "C:\Users\fabia\AppData\Local\Programs\Python\Python312\python.exe"

Write-Host "Instalando dependencias en el Python objetivo..."
& $py -m pip install -r requirements.txt
& $py -m pip install pyinstaller

Write-Host "Construyendo con PyInstaller (collect-all winrt es clave)..."
& $py -m PyInstaller --noconfirm --clean --windowed --onedir --name Aurora `
    --distpath dist --workpath build/pyi --specpath build `
    --paths . `
    --collect-all winrt --collect-submodules winrt `
    --hidden-import keyboard --hidden-import pystray --hidden-import PIL `
    main.py

Write-Host "============================================================"
Write-Host "  Ejecutable: $PWD\dist\Aurora\Aurora.exe"
Write-Host "  Nota: el hotkey global requiere ejecutar como Administrador."
Write-Host "============================================================"
