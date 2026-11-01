"""Aplicación principal Aurora - Orquestador"""

import platform
import queue
import tkinter as tk
import os
import subprocess
import time
from typing import Optional

from aurora.config import ConfigManager
from aurora.errors import (
    UnsupportedOSError, LanguageNotInstalledError,
    MicrophonePermissionError, MicrophoneNotFoundError,
)
from aurora.hotkey import HotkeyManager
from aurora.injector import TextInjector
from aurora.overlay import OverlayWindow
from aurora.speech import SpeechEngine
from aurora.tray import TrayIcon


class App:
    """Aplicación principal que orquesta todos los componentes"""
    
    def __init__(self):
        # Verificar OS
        self._check_os()
        
        # Configuración
        self.config = ConfigManager()
        
        # Queue para comunicación thread-safe speech -> UI
        self.message_queue: queue.Queue = queue.Queue()
        
        # Estado
        self.is_dictating = False
        self.current_partial = ""
        self._exiting = False
        self._hide_after_id = None
        self._last_toggle = 0.0

        # Componentes (se inicializan en run)
        self.root: Optional[tk.Tk] = None
        self.overlay: Optional[OverlayWindow] = None
        self.speech: Optional[SpeechEngine] = None
        self.hotkey: Optional[HotkeyManager] = None
        self.tray: Optional[TrayIcon] = None
        self.injector = TextInjector()
    
    def _check_os(self):
        """Verifica que estemos en Windows 11"""
        if platform.system() != 'Windows':
            raise UnsupportedOSError("Aurora solo funciona en Windows")
        
        # Windows 11 = version 10.0 build >= 22000
        version = platform.version()
        try:
            build = int(version.split('.')[-1])
            if build < 22000:
                print("ADVERTENCIA: Aurora está diseñado para Windows 11. "
                      "Puede funcionar en Windows 10 pero no está garantizado.")
        except:
            pass  # No podemos verificar, continuamos
    
    def run(self):
        """Punto de entrada principal de la aplicación"""
        # Crear ventana principal (tkinter debe estar en el thread principal)
        self.root = tk.Tk()
        self.root.title("Aurora")
        
        # Crear overlay
        self.overlay = OverlayWindow(self.root)
        
        # Crear motor de voz
        self.speech = SpeechEngine()
        
        # Crear gestor de hotkeys
        self.hotkey = HotkeyManager()
        hotkey_registered = self.hotkey.start(self.config.hotkey, self._request_toggle)
        if not hotkey_registered:
            error_msg = (
                f"\n[ADVERTENCIA] No se pudo registrar el hotkey '{self.config.hotkey}'.\n"
                f"Probablemente Aurora necesita ejecutarse como Administrador.\n"
                f"Los hotkeys globales requieren permisos elevados en Windows.\n"
            )
            print(error_msg)
            # Intentar notificar en tray si ya esta iniciado
            # (pero el tray se inicia despues, asi que solo print por ahora)
        
        # Crear icono de bandeja
        self.tray = TrayIcon(
            on_toggle=self._request_toggle,
            on_language_change=lambda lang: self._post('language', lang),
            on_config=self._open_config,
            on_exit=lambda: self._post('exit', None)
        )
        self.tray.start()
        
        # Servidor de control local (IPC) para manejar Aurora sin UI (MCP/CLI)
        try:
            from aurora.ipc import start_control_server
            self._control_server = start_control_server(self)
        except Exception as _e:
            print(f"[aviso] servidor de control no disponible: {_e}")
        
        # Iniciar consumer de mensajes
        self._check_message_queue()
        
        # Entrar en mainloop de tkinter
        try:
            self.root.mainloop()
        finally:
            self._cleanup()

    def _cleanup(self):
        """Libera recursos al salir (idempotente, thread principal)"""
        self._exiting = True
        self._shutdown()
        if self.tray:
            try:
                self.tray.stop()
            except Exception:
                pass
        if self.root:
            try:
                self.root.destroy()
            except Exception:
                pass
            self.root = None

    def _post(self, kind: str, data):
        """Encola un comando para ejecutarse en el thread de tkinter"""
        self.message_queue.put((kind, data))

    def _request_toggle(self):
        """Llamado desde hotkey/tray (otros threads): delega al thread de UI"""
        now = time.monotonic()
        if now - self._last_toggle < 0.3:  # anti-rebote (auto-repeat de teclas)
            return
        self._last_toggle = now
        self._post('toggle', None)
    
    def toggle_dictation(self):
        """Activa/desactiva el dictado"""
        if self.is_dictating:
            self._stop_dictation()
        else:
            self._start_dictation()
    
    def _start_dictation(self):
        """Inicia la sesion de dictado"""
        if self.is_dictating:
            return
        
        self._cancel_hide()
        self.is_dictating = True
        self.current_partial = ""

        # Mostrar overlay
        self.overlay.set_state("Escuchando...", "#00ff00")
        self.overlay.clear_text()
        self.overlay.show()
        
        # Actualizar tray
        self.tray.update_status(True)
        
        # Iniciar motor de voz
        self.speech.start(
            language=self.config.language,
            on_hypothesis=self._on_hypothesis,
            on_result=self._on_result,
            on_error=self._on_error
        )
    
    def _cancel_hide(self):
        if self._hide_after_id is not None and self.root:
            try:
                self.root.after_cancel(self._hide_after_id)
            except Exception:
                pass
        self._hide_after_id = None

    def _hide_error(self):
        self._hide_after_id = None
        if not self.is_dictating:
            self.overlay.hide()

    def _stop_dictation(self, hide: bool = True):
        """Detiene la sesion de dictado"""
        if not self.is_dictating:
            return

        self.is_dictating = False

        # Detener motor de voz
        self.speech.stop()

        # Ocultar overlay (tras un error, dejar visible el mensaje unos segundos)
        if hide:
            self.overlay.hide()
        elif self.root:
            self._hide_after_id = self.root.after(3000, self._hide_error)
        
        # Actualizar tray
        self.tray.update_status(False)
    
    def _on_hypothesis(self, text: str):
        """
        Callback para resultados parciales.
        Se ejecuta en el thread del motor de voz, por eso usa la queue.
        """
        self.message_queue.put(('hypothesis', text))
    
    def _on_result(self, text: str):
        """
        Callback para resultados finales.
        Se ejecuta en el thread del motor de voz, por eso usa la queue.
        """
        self.message_queue.put(('result', text))
    
    def _on_error(self, error: Exception):
        """
        Callback para errores.
        Se ejecuta en el thread del motor de voz, por eso usa la queue.
        """
        self.message_queue.put(('error', error))
    
    def _check_message_queue(self):
        """
        Consume mensajes de la queue y actualiza la UI.
        Se ejecuta en el thread principal (tkinter).
        """
        try:
            while True:
                msg_type, data = self.message_queue.get_nowait()
                
                try:
                    self._handle_message(msg_type, data)
                except Exception as e:
                    print(f"Error procesando mensaje '{msg_type}': {e}")
                if self._exiting:
                    return

        except queue.Empty:
            pass

        # Re-programar para dentro de 100ms
        if self.root and not self._exiting:
            self.root.after(100, self._check_message_queue)

    def _handle_message(self, msg_type, data):
        """Procesa un mensaje en el thread de tkinter"""
        if msg_type == 'toggle':
            self.toggle_dictation()

        elif msg_type == 'language':
            self._on_language_change(data)

        elif msg_type == 'exit':
            self._on_exit()

        elif msg_type == 'hypothesis':
            if not self.is_dictating:
                return  # parcial obsoleto de una sesion ya detenida
            self.current_partial = data
            self.overlay.update_text(data)

        elif msg_type == 'result':
            # Resultado final: inyectar texto (tambien si llega justo tras parar)
            if data:
                self.injector.inject_text(data)
            self.current_partial = ""
            if self.is_dictating:
                self.overlay.clear_text()
                self.overlay.set_state("Escuchando...", "#00ff00")

        elif msg_type == 'error':
            if not self.is_dictating:
                return  # error de una sesion anterior
            error = data
            if isinstance(error, LanguageNotInstalledError):
                msg = f"Idioma no instalado: {self.config.language}"
            elif isinstance(error, MicrophonePermissionError):
                msg = "Sin permiso de micrófono / voz"
            elif isinstance(error, MicrophoneNotFoundError):
                msg = "Micrófono no disponible"
            else:
                msg = f"Error: {type(error).__name__}"
            print(f"Error de dictado: {error!r}")

            self.overlay.set_state(msg, "#ff0000")
            self.overlay.clear_text()

            # Detener dictado tras error, dejando el mensaje visible unos segundos
            self._stop_dictation(hide=False)
    
    def _on_language_change(self, language_code: str):
        """Handler para cambio de idioma desde el menú"""
        was_active = self.is_dictating
        
        # Si estaba dictando, detener
        if was_active:
            self._stop_dictation()
        
        # Cambiar idioma
        self.config.language = language_code
        
        # Si estaba activo, reiniciar
        if was_active:
            self._start_dictation()
    
    def _open_config(self):
        """Abre el archivo de configuración con el editor por defecto"""
        config_path = self.config.config_file
        try:
            os.startfile(str(config_path))
        except Exception as e:
            print(f"Error abriendo config: {e}")
    
    def _on_exit(self):
        """Salir de la aplicación (se ejecuta en el thread de tkinter)"""
        self._exiting = True
        self._shutdown()
        if self.root:
            self.root.quit()

    def _shutdown(self):
        """Detiene dictado, motor de voz y hotkey (idempotente)"""
        self._cancel_hide()
        if self.is_dictating:
            self._stop_dictation()

        # Detener motor de voz y esperar con timeout
        if self.speech:
            self.speech.stop()
            t = self.speech.thread
            if t and t.is_alive():
                t.join(timeout=3.0)

        # Drenar cola: inyectar solo resultados finales pendientes
        try:
            while True:
                msg_type, data = self.message_queue.get_nowait()
                if msg_type == 'result' and data:
                    try:
                        self.injector.inject_text(data)
                    except Exception as e:
                        print(f"Error inyectando texto: {e}")
        except queue.Empty:
            pass

        # Desregistrar hotkey
        if self.hotkey:
            self.hotkey.stop()
            self.hotkey = None
