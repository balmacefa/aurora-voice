```markdown
# Empaquetado de Aurora

Este directorio contiene los archivos necesarios para empaquetar la aplicación Aurora en un ejecutable de Windows usando PyInstaller.

## Cómo construir el ejecutable

1.  **Abre PowerShell** en el directorio raíz del proyecto (donde se encuentra `main.py`).
2.  **Navega al directorio `packaging/`**:
    ```powershell
    cd packaging
    ```
3.  **Ejecuta el script de construcción**:
    ```powershell
    .\build.ps1
    ```
    Este script realizará las siguientes acciones:
    *   Creará un entorno virtual local (`.venv`) si no existe.
    *   Instalará las dependencias de `requirements.txt` en el entorno virtual.
    *   Instalará PyInstaller.
    *   Ejecutará PyInstaller usando `Aurora.spec` para crear el ejecutable.

## Dónde encontrar el ejecutable

Una vez que el script `build.ps1` haya finalizado, el ejecutable de Aurora se encontrará en:

`dist/Aurora/Aurora.exe`

Este será un directorio completo (onedir) que contendrá todos los archivos necesarios para ejecutar la aplicación.

## Nota Importante: Hotkey Global

La funcionalidad de hotkey global de Aurora (usando la librería `keyboard`) puede requerir que la aplicación se ejecute con **permisos de administrador** para funcionar correctamente en algunas configuraciones de Windows.
```
## Portable

Version de un solo archivo (onefile) que no requiere instalacion.

Construir (desde la raiz del proyecto):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File packaging\build-portable.ps1
```

Resultado en `dist\portable\`: `Aurora-Portable.exe` y el archivo vacio `Aurora.portable`.

Uso: copia ambos archivos a la misma carpeta (p. ej. un USB) y ejecuta `Aurora-Portable.exe`.
El marcador `Aurora.portable` junto al exe activa el modo portable: la configuracion se guarda en `data\` junto al exe.

Prioridad de resolucion del directorio de datos:

1. Variable `AURORA_DATA_DIR` (ruta explicita).
2. Variable `AURORA_PORTABLE=1` -> `<carpeta del exe>\data` (o `.\data` desde el cwd si no es exe).
3. Exe con marcador `Aurora.portable` en su carpeta -> `<carpeta del exe>\data`.
4. `%APPDATA%\Aurora` (por defecto).

Si el directorio elegido en 1-3 no se puede crear o escribir, se usa `%APPDATA%\Aurora`.

Nota: el hotkey global (libreria `keyboard`) puede requerir ejecutar como Administrador.
