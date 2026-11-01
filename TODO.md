# TODO — Aurora (handoff para el próximo agente)

> Lee primero `docs/RE-WinH-Dictation.md` (cómo funciona Win+H) y `docs/TESTING.md`
> (checklist de aceptación). El MVP está construido y con QA multi-modelo cerrado.
> Smoke test: `python tests/smoke_test.py` (6/6). Verificación de fixes:
> `python tests/verify_fixes.py` (4/4). Python: `C:\Users\fabia\AppData\Local\Programs\Python\Python312\python.exe`.

## 🔴 BLOQUEANTE DE SISTEMA (no es bug de código) — hacer primero
El motor on-device de `Windows.Media.SpeechRecognition` devuelve
`WinError -2147199584 (Internal Speech Error)` porque faltan datos de voz en el equipo.
Para que Aurora reconozca audio:
1. Config → Hora e idioma → Idioma y región → (idioma) → Opciones → instalar paquete de **Voz**.
2. Config → Privacidad y seguridad → Micrófono → permitir que **apps de escritorio** accedan al micrófono.
3. Verificar que hay dispositivo de entrada activo (Config → Sistema → Sonido → Entrada).
4. Re-ejecutar `python tests/smoke_test.py`: el Test 5 (SpeechRecognizer) debe pasar SIN el WARN.

## ⏳ VALIDACIÓN EN VIVO (tras el bloqueante)
- [ ] Ejecutar `run_aurora.bat` como Administrador (el hotkey global `keyboard` lo requiere).
- [ ] Probar el ciclo completo con `Ctrl+Alt+H`: dictar frase ≥10 palabras en es-ES y en-US,
      ver el parcial en el overlay, y que el texto final se inyecte en **Notepad, Chrome y VS Code**
      (ver checklist en `docs/TESTING.md`).
- [ ] Confirmar que `\n` dictado produce Enter real (fix VK_RETURN en `aurora/injector.py`).
- [ ] Verificar que al reiniciar el dictado varias veces NO hay callbacks duplicados
      (fix de tokens add_/remove_* en `aurora/speech.py`).

## 🧪 DEUDA DE PRUEBAS
- [ ] `inject_text()` no tiene test automatizado end-to-end (el smoke test no lo ejecuta).
      Añadir un test que inyecte en un Notepad lanzado de prueba y lea el resultado (pywinauto/UIA),
      o al menos un test que arme el array de `INPUT` y valide `cbSize`/flags sin enviar.
- [ ] Revisar artefactos de workstreams extra sin integrar: `aurora/ipc.py`, `tools/aurora_mcp.py`,
      `packaging/` y `.agents_prompts/`. Decidir si se integran al MVP o se archivan.

## 🚧 PENDIENTES DE ROBUSTEZ (de la revisión multi-modelo, prioridad media)
- [ ] `aurora/speech.py`: distinguir denegación de micrófono (`OSError` winerror `-2147024891`
      / E_ACCESSDENIED) y mapearla a `MicrophonePermissionError` en vez del `except Exception` genérico.
- [ ] `aurora/speech.py`: reemplazar el polling `asyncio.sleep(0.1)` por un `asyncio.Event`
      señalizado con `loop.call_soon_threadsafe` para parar sin latencia.
- [ ] `aurora/hotkey.py` / `aurora/app.py`: si el registro del hotkey falla (sin admin),
      mostrar notificación de bandeja (hoy solo hace print).
- [ ] `aurora/overlay.py`: evitar reposicionar la ventana en cada `update_text()` (flicker);
      reposicionar solo si cambia el tamaño.

## 🎁 STRETCH (post-MVP, ver PRD)
- [ ] Empaquetado con PyInstaller (`packaging/Aurora.spec`, `packaging/build.ps1`) → ejecutable standalone.
- [ ] Comandos de edición por voz ("nueva línea", "borrar última palabra").
- [ ] Paridad TSF para inyección (hoy usamos SendInput Unicode; Win+H usa Text Services Framework).

## 📌 Estado actual (para contexto)
- RE de Win+H completo; MVP multi-thread (tkinter + asyncio WinRT + keyboard) funcional a nivel de código.
- 2 rondas de QA: 9 bugs reales cerrados. 2 eran críticos que rompían el producto
  (`sizeof(INPUT)` x64 = 32→40; eventos WinRT con tokens add_/remove_* en vez de `+=/-=`).
