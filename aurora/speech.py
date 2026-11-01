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
        
        # Tokens de suscripcion WinRT
        self._token_result = None
        self._token_hyp = None
        
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
            
            # Evento propio por sesion: un thread viejo que no termino en el
            # join no debe ver el reinicio de la sesion nueva.
            self._stop_event = threading.Event()
            self._running = True
            
            # Iniciar thread con event loop (daemon=False para join limpio)
            self.thread = threading.Thread(
                target=self._run_async_loop,
                args=(language, self._stop_event),
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
        
        t = self.thread
        if t and t is not threading.current_thread():
            t.join(timeout=2.0)

    def _run_async_loop(self, language: str, stop_event: threading.Event):
        """Ejecuta el event loop asyncio en el thread dedicado"""
        loop = asyncio.new_event_loop()
        self.loop = loop
        try:
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._setup_and_run(language, stop_event))
        except Exception as e:
            cb = self.on_error
            if cb:
                cb(self._map_error(e, language))
        finally:
            # Cancelar tasks pendientes antes de cerrar
            try:
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                if pending:
                    loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
            except Exception:
                pass  # Ignorar errores de cleanup
            loop.close()

            # Cerrar recognizer (IClosable) - local a esta sesion
            rec, self.recognizer = self.recognizer, None
            self.session = None
            try:
                if rec is not None and hasattr(rec, 'close'):
                    rec.close()
            except Exception:
                pass  # Ignorar errores de cierre

            # Si el thread termino solo (error), permitir un nuevo start()
            with self._lock:
                if self._stop_event is stop_event:
                    self._running = False

    @staticmethod
    def _map_error(e: Exception, language: str) -> Exception:
        """Traduce excepciones WinRT/HRESULT a errores propios de Aurora"""
        if isinstance(e, (MicrophonePermissionError, MicrophoneNotFoundError,
                          LanguageNotInstalledError)):
            return e
        # HRESULT en OSError.winerror o en args[0]
        code = getattr(e, 'winerror', None)
        if code is None and e.args and isinstance(e.args[0], int):
            code = e.args[0]
        code = (code or 0) & 0xFFFFFFFF
        msg = str(e).lower()
        if isinstance(e, PermissionError) or code in (0x80070005, 0x80045509):
            # E_ACCESSDENIED / politica de privacidad de voz no aceptada
            return MicrophonePermissionError(
                "No hay permisos de micrófono o el reconocimiento de voz en línea "
                "está desactivado. Revisa Configuración > Privacidad > Voz y Micrófono."
            )
        if code in (0x8004503A, 0x80045508) or "not supported" in msg or "language" in msg:
            return LanguageNotInstalledError(
                f"El idioma {language} no está disponible para reconocimiento de voz."
            )
        if code in (0x8007001F, 0x80070490, 0xC00D3704) or "microphone" in msg or "audio" in msg:
            return MicrophoneNotFoundError(f"Error de micrófono: {e}")
        return e
    
    async def _setup_and_run(self, language: str, stop_event: threading.Event):
        """Configura el recognizer y ejecuta la sesión continua"""
        completed = threading.Event()
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
            token_completed = self.session.add_completed(
                lambda s, a: completed.set()
            )

            # Por defecto la sesion se cierra tras ~5s de silencio: ampliarlo
            try:
                from datetime import timedelta
                self.session.auto_stop_silence_timeout = timedelta(hours=1)
            except Exception:
                pass  # Se compensa reiniciando en 'completed'

            # Iniciar reconocimiento continuo
            await self.session.start_async()

            # Esperar hasta que se senale stop
            while not stop_event.is_set():
                if completed.is_set():
                    # La sesion se cerro sola (timeout, etc.): reiniciar
                    completed.clear()
                    try:
                        await self.session.start_async()
                    except Exception:
                        if stop_event.is_set():
                            break
                        raise
                await asyncio.sleep(0.1)

            try:
                self.session.remove_completed(token_completed)
            except Exception:
                pass
            
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
            try:
                await self.session.stop_async()
            except Exception as e:
                print(f"Error deteniendo sesion: {e}")

        except Exception as e:
            # Permisos de microfono, idioma no instalado, mic ausente, etc.
            if self.on_error:
                self.on_error(self._map_error(e, language))
    
    def _on_hypothesis_generated(self, session, args):
        """Handler para resultados parciales (hipotesis)"""
        # Verificar stop al inicio para evitar despachar resultados obsoletos
        if self._stop_event.is_set() or not self._running:
            return
        
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
        # Verificar stop al inicio para evitar despachar resultados obsoletos
        if self._stop_event.is_set() or not self._running:
            return
        
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
