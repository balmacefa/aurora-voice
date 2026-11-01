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