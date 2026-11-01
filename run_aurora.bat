@echo off
REM Aurora - Launcher con intento de elevación a admin

echo Aurora - Dictado por voz para Windows 11
echo.

REM Verificar si ya tenemos privilegios de admin
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Ejecutando con privilegios de administrador...
    goto :run
)

echo NOTA: Para que el hotkey global funcione correctamente, se recomienda
echo ejecutar con privilegios de administrador.
echo.
echo Intentando elevar a administrador...
echo Si aparece el UAC, acepta para mejores resultados.
echo.

REM Intentar elevar (esto abrirá una nueva ventana con admin)
powershell -Command "Start-Process cmd -ArgumentList '/c cd /d %~dp0 && %~dp0run_aurora.bat' -Verb RunAs"
exit

:run
REM Ejecutar Aurora
"C:\Users\fabia\AppData\Local\Programs\Python\Python312\python.exe" "%~dp0main.py"
pause
