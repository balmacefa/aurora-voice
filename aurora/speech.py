"""Motor de reconocimiento de voz usando WinRT SpeechRecognizer"""

import asyncio
import threading
from typing import Callable, Optional
from aurora.errors import (
    MicrophonePermissionError,
    MicrophoneNotFoundError,
    LanguageNotInstalledError
)


class SpeechEngine:
    """
    Motor de reconocimiento de voz continuo usando WinRT.
    Corre un event loop asyncio en su propio thread.
    """
    
    def __init__(self):
        self.thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.recognizer = None
        self.session = None
        self._stop_event = threading.Event()
        self._running = False
        self._lock = threading.Lock()
        
        # Callbacks
        self.on_hypothesis: Optional[Callable[[str], None]] = None
        self.on_result: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
    
    def start(self, language: str, 
              on_hypothesis: Callable[[str], None],
              on_result: Callable[[str], None],
              on_error: Callable[[Exception], None]):
        """
        Inicia la sesión de reconocimiento continuo.
        
        Args:
            language: Código de idioma (ej. "es-ES", "en-US")
            on_hypothesis: Callback para resultados parciales
            on_result: Callback para resultados finales
            on_error: Callback para errores
        """
        with self._lock:
            if self._running:
                return
            
            self.on_hypothesis = on_hypothesis
            self.on_result = on_result
            self.on_error = on_error
            
            self._stop_event.clear()
            self._running = True
            
            # Iniciar thread con event loop (daemon=False para join limpio)
            self.thread = threading.Thread(
                target=self._run_async_loop,
                args=(language,),
                daemon=False
            )
            self.thread.start()
    
    def stop(self):
        """Detiene la sesión de reconocimiento"""
        with self._lock:
            if not self._running:
                return
            
            self._running = False
            self._stop_event.set()
        
        if self.thread:
            self.thread.join(timeout=2.0)
    
    def _run_async_loop(self, language: str):
        """Ejecuta el event loop asyncio en el thread dedicado"""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._setup_and_run(language))
        except Exception as e:
            if self.on_error:
                self.on_error(e)
        finally:
            if self.loop:
                # Cancelar tasks pendientes antes de cerrar
                try:
                    pending = asyncio.all_tasks(self.loop)
                    for task in pending:
                        task.cancel()
                    if pending:
                        self.loop.run_until_complete(
                            asyncio.gather(*pending, return_exceptions=True)
                        )
                except Exception:
                    pass  # Ignorar errores de cleanup
                
                self.loop.close()
    
    async def _setup_and_run(self, language: str):
        """Configura el recognizer y ejecuta la sesión continua"""
        try:
            # Importar WinRT (debe hacerse en el thread que tendrá el loop)
            from winrt.windows.media.speechrecognition import (
                SpeechRecognizer,
                SpeechRecognitionTopicConstraint,
                SpeechRecognitionScenario
            )
            from winrt.windows.globalization import Language
            
            # Crear recognizer con el idioma especificado
            lang = Language(language)
            self.recognizer = SpeechRecognizer(lang)
            
            # Agregar constraint de dictado
            constraint = SpeechRecognitionTopicConstraint(
                SpeechRecognitionScenario.DICTATION,
                "dictation"
            )
            self.recognizer.constraints.append(constraint)
            
            # Compilar constraints
            result = await self.recognizer.compile_constraints_async()
            
            # Verificar el resultado de la compilación
            # Soportar ambos casos: status.value o status directo
            status_code = result.status.value if hasattr(result.status, 'value') else result.status
            if status_code != 0:  # 0 = Success
                # Posible error: idioma no instalado
                if self.on_error:
                    self.on_error(LanguageNotInstalledError(
                        f"No se pudo compilar constraints para {language}. "
                        f"Status: {status_code}. "
                        f"Verifica que el idioma esté instalado en Windows."
                    ))
                return
            
            # Obtener la sesion de reconocimiento continuo
            self.session = self.recognizer.continuous_recognition_session
            
            # Suscribir eventos (la API real usa add_X -> token)
            self._token_result = self.session.add_result_generated(self._on_result_generated)
            self._token_hyp = self.session.add_hypothesis_generated(self._on_hypothesis_generated)
            
            # Iniciar reconocimiento continuo
            await self.session.start_async()
            
            # Esperar hasta que se senale stop
            while not self._stop_event.is_set():
                await asyncio.sleep(0.1)
            
            # Desuscribir eventos antes de detener (usando tokens)
            try:
                if self._token_result is not None:
                    self.session.remove_result_generated(self._token_result)
                    self._token_result = None
            except Exception as e:
                print(f"Error desuscribiendo result_generated: {e}")
            
            try:
                if self._token_hyp is not None:
                    self.session.remove_hypothesis_generated(self._token_hyp)
                    self._token_hyp = None
            except Exception as e:
                print(f"Error desuscribiendo hypothesis_generated: {e}")
            
            # Detener reconocimiento
            await self.session.stop_async()
            
        except PermissionError as e:
            if self.on_error:
                self.on_error(MicrophonePermissionError(
                    "No hay permisos de micrófono. Verifica la configuración de privacidad."
                ))
        except Exception as e:
            # Capturar otros errores (micrófono no disponible, etc.)
            error_msg = str(e).lower()
            if "microphone" in error_msg or "audio" in error_msg:
                if self.on_error:
                    self.on_error(MicrophoneNotFoundError(
                        f"Error de micrófono: {e}"
                    ))
            else:
                if self.on_error:
                    self.on_error(e)
    
    def _on_hypothesis_generated(self, session, args):
        """Handler para resultados parciales (hipótesis)"""
        try:
            # Snapshot local del callback para evitar race conditions
            cb = self.on_hypothesis
            if cb is None:
                return
            
            text = args.result.text
            if text:
                cb(text)
        except Exception as e:
            # No romper el thread de WinRT
            print(f"Error en hypothesis handler: {e}")
    
    def _on_result_generated(self, session, args):
        """Handler para resultados finales"""
        try:
            # Snapshot local del callback para evitar race conditions
            cb = self.on_result
            if cb is None:
                return
            
            # Soportar status con/sin .value
            status_code = args.result.status.value if hasattr(args.result.status, 'value') else args.result.status
            if status_code != 0:  # Solo procesar si status = Success
                return
            
            text = args.result.text
            if text:
                cb(text)
        except Exception as e:
            # No romper el thread de WinRT
            print(f"Error en result handler: {e}")
