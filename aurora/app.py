"""Aplicación principal Aurora - Orquestador"""

import platform
import queue
import tkinter as tk
import os
import subprocess
from typing import Optional

from aurora.config import ConfigManager
from aurora.errors import UnsupportedOSError, LanguageNotInstalledError
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
        hotkey_registered = self.hotkey.start(self.config.hotkey, self.toggle_dictation)
        if not hotkey_registered:
            error_msg = (
                f"\n[ADVERTENCIA] No se pudo registrar el hotkey '{self.config.hotkey}'.\n"
                f"Probablemente Aurora necesita ejecutarse como Administrador.\n"
                f"Los hotkeys globales requieren permisos elevados en Windows.\n"
            )
            print(error_msg)
            # Intentar notificar en tray si ya est
en iniciado
            # (pero el tray se inicia despu
es, as
i que solo print por ahora)
        
        # Crear icono de bandeja
        self.tray = TrayIcon(
            on_toggle=self.toggle_dictation,
            on_language_change=self._on_language_change,
            on_config=self._open_config,
            on_exit=self._on_exit
        )
        self.tray.start()
        
        # Iniciar consumer de mensajes
        self._check_message_queue()
        
        # Entrar en mainloop de tkinter
        self.root.mainloop()
    
    def toggle_dictation(self):
        """Activa/desactiva el dictado"""
        if self.is_dictating:
            self._stop_dictation()
        else:
            self._start_dictation()
    
    def _start_dictation(self):
        """Inicia la sesión de dictado"""
        if self.is_dictating:
            return
        
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
    
    def _stop_dictation(self):
        """Detiene la sesión de dictado"""
        if not self.is_dictating:
            return
        
        self.is_dictating = False
        
        # Detener motor de voz
        self.speech.stop()
        
        # Ocultar overlay
        self.overlay.hide()
        
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
                
                if msg_type == 'hypothesis':
                    # Actualizar texto parcial en overlay
                    self.current_partial = data
                    self.overlay.update_text(data)
                
                elif msg_type == 'result':
                    # Resultado final: inyectar texto
                    if data:
                        self.injector.inject_text(data)
                    # Limpiar parcial
                    self.current_partial = ""
                    self.overlay.clear_text()
                    self.overlay.set_state("Escuchando...", "#00ff00")
                
                elif msg_type == 'error':
                    # Mostrar error en overlay
                    error = data
                    if isinstance(error, LanguageNotInstalledError):
                        msg = f"Idioma no instalado: {self.config.language}"
                    else:
                        msg = f"Error: {type(error).__name__}"
                    
                    self.overlay.set_state(msg, "#ff0000")
                    self.overlay.clear_text()
                    
                    # Detener dictado tras error
                    self._stop_dictation()
        
        except queue.Empty:
            pass
        
        # Re-programar para dentro de 100ms
        if self.root:
            self.root.after(100, self._check_message_queue)
    
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
        """Handler para salir de la aplicación"""
        # Detener dictado si está activo
        if self.is_dictating:
            self._stop_dictation()
        
        # Detener motor de voz y esperar con timeout
        if self.speech:
            self.speech.stop()
            if self.speech.thread and self.speech.thread.is_alive():
                self.speech.thread.join(timeout=3.0)
        
        # Drenar cola de mensajes pendientes antes de cerrar
        try:
            while True:
                msg_type, data = self.message_queue.get_nowait()
                # Procesar especialmente 'result' para inyectar texto pendiente
                if msg_type == 'result' and data:
                    self.injector.inject_text(data)
        except queue.Empty:
            pass
        
        # Detener hotkey
        if self.hotkey:
            self.hotkey.stop()
        
        # Cerrar ventana tkinter
        if self.root:
            self.root.quit()
