# Testing Manual - Aurora

Checklist de pruebas manuales según criterios de aceptación.

## ✅ Pre-requisitos

- [ ] Windows 11 (o Win10 build 22000+)
- [ ] Python 3.12.10 instalado
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Micrófono conectado y configurado
- [ ] Permisos de micrófono habilitados en Windows
- [ ] Privilegios de administrador para hotkey global

## 🧪 Tests funcionales

### 1. Instalación y arranque

- [ ] `smoke_test.py` pasa todos los checks
- [ ] Aurora arranca sin errores con `run_aurora.bat`
- [ ] Icono aparece en la bandeja del sistema
- [ ] No hay ventanas visibles al inicio (overlay oculto)

### 2. Dictado básico - Español

- [ ] Presionar `Ctrl+Alt+H` muestra el overlay
- [ ] El overlay dice "Escuchando..." en verde
- [ ] Dictar una frase de al menos 10 palabras
- [ ] El texto parcial aparece en tiempo real en el overlay
- [ ] Al terminar de hablar (pausa), el texto final se inyecta en Notepad
- [ ] El overlay limpia el texto parcial tras la inyección
- [ ] Presionar `Ctrl+Alt+H` nuevamente oculta el overlay y detiene el dictado

**Frase de prueba:**
> "Buenos días, esta es una prueba del sistema de dictado por voz de Aurora para Windows once"

### 3. Dictado básico - Inglés

- [ ] Cambiar idioma a `en-US` desde el menú de bandeja
- [ ] Activar dictado con `Ctrl+Alt+H`
- [ ] Dictar una frase en inglés de al menos 10 palabras
- [ ] El texto se inyecta correctamente

**Frase de prueba:**
> "Hello world, this is a voice dictation test for the Aurora application running on Windows eleven"

### 4. Inyección en múltiples aplicaciones

Probar que el texto se inyecta correctamente en:

- [ ] Notepad (notepad.exe)
- [ ] Google Chrome / Edge (campo de búsqueda, input de formulario)
- [ ] VS Code (editor de texto)
- [ ] Microsoft Word / WordPad
- [ ] Discord / Teams (campo de chat)

### 5. Cambio de idioma

- [ ] El menú de bandeja muestra lista de idiomas
- [ ] Seleccionar `en-US` actualiza la configuración
- [ ] Si el dictado estaba activo, se reinicia con el nuevo idioma
- [ ] El cambio persiste (verificar `%APPDATA%\Aurora\config.json`)
- [ ] Probar dictar en el nuevo idioma

### 6. Cambio de hotkey

- [ ] Editar `%APPDATA%\Aurora\config.json` manualmente
- [ ] Cambiar `"hotkey": "ctrl+shift+d"`
- [ ] Reiniciar Aurora
- [ ] Verificar que `Ctrl+Shift+D` ahora activa/desactiva el dictado
- [ ] Verificar que `Ctrl+Alt+H` ya no funciona

### 7. Sesión continua

- [ ] Activar dictado
- [ ] Dictar una frase, esperar que se inyecte
- [ ] SIN desactivar el dictado, dictar otra frase
- [ ] Ambas frases se inyectan correctamente
- [ ] El overlay permanece visible entre inyecciones

### 8. Overlay - Estados visuales

- [ ] Estado "Escuchando..." es verde
- [ ] El texto parcial aparece debajo del estado
- [ ] El overlay se reposiciona si el texto crece
- [ ] El overlay está siempre encima (topmost)
- [ ] El overlay es semitransparente

### 9. Manejo de errores - Idioma no instalado

- [ ] Editar config.json: `"language": "ja-JP"` (japonés, probablemente no instalado)
- [ ] Reiniciar Aurora y activar dictado
- [ ] El overlay muestra error: "Idioma no instalado: ja-JP"
- [ ] El dictado se detiene automáticamente
- [ ] Cambiar de vuelta a `es-ES` y verificar que funciona

### 10. Manejo de errores - Permisos de micrófono

- [ ] Ir a `Configuración` → `Privacidad` → `Micrófono`
- [ ] Deshabilitar "Permitir que las apps de escritorio accedan al micrófono"
- [ ] Activar dictado en Aurora
- [ ] Se muestra un error de permisos
- [ ] Rehabilitar permisos y verificar que funciona

### 11. Manejo de errores - Micrófono desconectado

- [ ] Desconectar el micrófono físicamente (o deshabilitarlo en Configuración)
- [ ] Activar dictado
- [ ] Se muestra un error de micrófono no encontrado
- [ ] Reconectar micrófono y verificar que funciona

### 12. Tray icon - Menú

- [ ] Click derecho en el icono de bandeja
- [ ] Verificar opciones: Activar/Desactivar, Idioma (submenú), Config, Salir
- [ ] "Activar/Desactivar dictado" togglea el dictado correctamente
- [ ] "Abrir configuración" abre `config.json` en el editor por defecto
- [ ] "Salir" cierra Aurora completamente

### 13. Caracteres Unicode especiales

Dictar frases con:

- [ ] Acentos: "José López está comiendo paté en París"
- [ ] Eñes: "El niño pequeño sueña con España"
- [ ] Símbolos: "Pregunta: ¿cómo estás? Exclamación: ¡bien!"
- [ ] Números: "uno dos tres cuatro cinco seis siete ocho nueve diez"

### 14. Rendimiento

- [ ] Activar dictado y dictar durante 2-3 minutos continuos
- [ ] El overlay no se congela
- [ ] No hay lag perceptible entre hablar y ver el texto parcial
- [ ] No hay fugas de memoria evidentes (verificar Task Manager)

### 15. Cierre limpio

- [ ] Activar dictado
- [ ] Cerrar Aurora desde el menú de bandeja
- [ ] El dictado se detiene
- [ ] El icono desaparece de la bandeja
- [ ] No quedan procesos python.exe colgados (Task Manager)

## 📊 Criterios de aceptación generales

- ✅ Latencia de hipótesis < 500ms
- ✅ Precisión de reconocimiento comparable a Win+H nativo
- ✅ Overlay no interfiere con el trabajo (se puede ignorar)
- ✅ Funciona en aplicaciones estándar de Windows
- ✅ No crashes durante uso normal
- ✅ Configuración persiste entre sesiones

## 🐛 Bugs conocidos (si los hay)

*Lista aquí cualquier bug encontrado durante el testing:*

- (ninguno reportado aún)

## 📝 Notas

- El smoke test NO requiere micrófono activo, solo verifica la instalación
- Algunos tests requieren tener instalados paquetes de voz adicionales en Windows
- La elevación a admin es necesaria para que keyboard lib registre hotkeys globales sin restricciones
