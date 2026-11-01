# Aurora 🎙️

**Dictado por voz para Windows 11** - Una alternativa equivalente a Win+H usando la misma API pública de Windows.

## 🌟 Características

- ✅ Reconocimiento de voz continuo on-device (sin enviar datos a la nube)
- ✅ Soporte multi-idioma (español, inglés, francés, alemán, etc.)
- ✅ Overlay visual con feedback en tiempo real
- ✅ Hotkey global configurable (por defecto: `Ctrl+Alt+H`)
- ✅ Inyección de texto Unicode en cualquier aplicación
- ✅ Icono de bandeja con menú de control

## 📋 Requisitos

- **Windows 11** (o Windows 10 build 22000+)
- **Python 3.12.10** instalado en `C:\Users\fabia\AppData\Local\Programs\Python\Python312\python.exe`
- **Micrófono** conectado y configurado
- **Permisos de micrófono** habilitados para aplicaciones de escritorio
- **Privilegios de administrador** (recomendado para hotkey global)
- **Paquetes de idioma** instalados en Windows para los idiomas que quieras usar

## 🚀 Instalación

1. **Instalar dependencias:**
   ```bash
   cd C:\Users\fabia\Desktop\Aurora
   "C:\Users\fabia\AppData\Local\Programs\Python\Python312\python.exe" -m pip install -r requirements.txt
   ```

2. **Verificar instalación:**
   ```bash
   "C:\Users\fabia\AppData\Local\Programs\Python\Python312\python.exe" tests/smoke_test.py
   ```

## 🎯 Uso

### Ejecutar Aurora

**Opción 1 - Launcher con elevación (recomendado):**
```bash
run_aurora.bat
```

**Opción 2 - Directamente con Python:**
```bash
"C:\Users\fabia\AppData\Local\Programs\Python\Python312\python.exe" main.py
```

### Controles

- **Activar/Desactivar dictado:** `Ctrl+Alt+H` (configurable)
- **Icono de bandeja:** Click derecho para acceder al menú
  - Activar/Desactivar dictado
  - Cambiar idioma
  - Abrir configuración
  - Salir

### Flujo de trabajo

1. Presiona `Ctrl+Alt+H` para iniciar el dictado
2. Habla normalmente - verás el texto parcial en el overlay
3. El texto final se inyecta automáticamente en el campo con foco
4. Presiona `Ctrl+Alt+H` nuevamente para detener

## ⚙️ Configuración

El archivo de configuración se guarda en:
```
%APPDATA%\Aurora\config.json
```

### Opciones disponibles:

```json
{
  "language": "es-ES",
  "hotkey": "ctrl+alt+h"
}
```

- **language:** Código de idioma para reconocimiento (ej. `es-ES`, `en-US`, `fr-FR`)
- **hotkey:** Combinación de teclas global (formatos válidos: `ctrl+alt+h`, `ctrl+shift+d`, etc.)

**Nota:** Puedes abrir el archivo de configuración desde el menú de la bandeja.

## 🌍 Idiomas soportados

Aurora soporta cualquier idioma que tengas instalado en Windows. Los más comunes:

- 🇪🇸 Español (España): `es-ES`
- 🇲🇽 Español (México): `es-MX`
- 🇺🇸 English (US): `en-US`
- 🇬🇧 English (UK): `en-GB`
- 🇫🇷 Français: `fr-FR`
- 🇩🇪 Deutsch: `de-DE`

**Para agregar un idioma:**
1. Ve a `Configuración de Windows` → `Hora e idioma` → `Idioma y región`
2. Agrega el idioma deseado
3. Instala el paquete de voz para ese idioma
4. Selecciona el idioma en el menú de Aurora

## 🐛 Solución de problemas

### "Error: Idioma no instalado"

- Verifica que el idioma esté instalado en Windows
- Ve a `Configuración` → `Hora e idioma` → `Voz`
- Descarga el paquete de voz para tu idioma

### "Error: No hay permisos de micrófono"

- Ve a `Configuración` → `Privacidad y seguridad` → `Micrófono`
- Habilita "Permitir que las aplicaciones de escritorio accedan al micrófono"

### "Error: Micrófono no encontrado"

- Verifica que tu micrófono esté conectado y configurado como dispositivo predeterminado
- Ve a `Configuración` → `Sistema` → `Sonido` → `Entrada`

### El hotkey no funciona

- Ejecuta Aurora con privilegios de administrador (usa `run_aurora.bat`)
- Verifica que la combinación no esté siendo usada por otra aplicación
- Prueba cambiar el hotkey en la configuración

### El texto no se inyecta

- Asegúrate de que la aplicación de destino tenga un campo de texto con foco
- Algunas aplicaciones con privilegios elevados pueden bloquear la inyección
- Prueba ejecutar Aurora como administrador

## 🏗️ Arquitectura técnica

Aurora usa el mismo mecanismo que Win+H:

- **API:** `Windows.Media.SpeechRecognition.SpeechRecognizer` (WinRT)
- **Constraint:** `SpeechRecognitionTopicConstraint` con escenario `Dictation`
- **Procesamiento:** On-device, sin envío de datos a la nube
- **Eventos:** `HypothesisGenerated` (parcial) y `ResultGenerated` (final)
- **Inyección:** `SendInput` con `KEYEVENTF_UNICODE` para soporte completo Unicode

## 📝 Notas

- **Win+H vs Ctrl+Alt+H:** Aurora usa `Ctrl+Alt+H` por defecto porque Windows reserva `Win+H` para su Voice Typing nativo. Puedes cambiar la combinación en la configuración.
- **Privacidad:** Todo el reconocimiento se hace on-device. No se envían datos a servidores externos.
- **Rendimiento:** El uso de CPU/RAM es similar al de Win+H nativo de Windows.

## 📄 Licencia

Proyecto de demostración educativa.

---

**Desarrollado con ❤️ para Windows 11**
