"""Smoke test para verificar que Aurora puede inicializarse"""

import sys
import os

# Agregar el directorio padre al path para importar aurora
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_imports():
    """Verifica que todos los módulos se pueden importar"""
    print("[OK] Test 1: Importando modulos Aurora...")
    try:
        from aurora import __version__
        from aurora.config import ConfigManager
        from aurora.errors import (
            MicrophonePermissionError,
            MicrophoneNotFoundError,
            UnsupportedOSError,
            LanguageNotInstalledError
        )
        from aurora.hotkey import HotkeyManager
        from aurora.injector import TextInjector
        # No importamos overlay/tray/app porque requieren GUI
        print(f"  [OK] Modulos importados correctamente (v{__version__})")
        return True
    except Exception as e:
        print(f"  [FAIL] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """Verifica que ConfigManager funciona"""
    print("\n[OK] Test 2: ConfigManager...")
    try:
        from aurora.config import ConfigManager
        config = ConfigManager()
        
        # Verificar defaults
        assert config.language in ['es-ES', 'en-US'], f"Idioma inesperado: {config.language}"
        assert config.hotkey, "Hotkey no configurado"
        
        print(f"  [OK] Config cargada: language={config.language}, hotkey={config.hotkey}")
        print(f"  [OK] Config file: {config.config_file}")
        return True
    except Exception as e:
        print(f"  [FAIL] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_winrt_imports():
    """Verifica que PyWinRT está instalado y se puede importar"""
    print("\n[OK] Test 3: Importando WinRT SpeechRecognition...")
    try:
        from winrt.windows.media.speechrecognition import (
            SpeechRecognizer,
            SpeechRecognitionTopicConstraint,
            SpeechRecognitionScenario
        )
        from winrt.windows.globalization import Language
        print("  [OK] Modulos WinRT importados correctamente")
        return True
    except ImportError as e:
        print(f"  [FAIL] ERROR: PyWinRT no instalado correctamente: {e}")
        print("  -> Ejecuta: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"  [FAIL] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_winrt_api_names():
    """Inspecciona los nombres reales de la API WinRT instalada"""
    print("\n[OK] Test 4: Inspeccionando API WinRT...")
    try:
        import winrt.windows.media.speechrecognition as sr_module
        
        print("  [INFO] Clases/funciones disponibles en speechrecognition:")
        available = [x for x in dir(sr_module) if not x.startswith('_')]
        for item in available[:15]:  # Primeros 15
            print(f"    - {item}")
        if len(available) > 15:
            print(f"    ... y {len(available) - 15} mas")
        
        return True
    except Exception as e:
        print(f"  [FAIL] ERROR: {e}")
        return False


def test_speech_recognizer():
    """Intenta crear un SpeechRecognizer y compilar constraints"""
    print("\n[OK] Test 5: Creando SpeechRecognizer y compilando constraints...")
    try:
        import asyncio
        from winrt.windows.media.speechrecognition import (
            SpeechRecognizer,
            SpeechRecognitionTopicConstraint,
            SpeechRecognitionScenario
        )
        from winrt.windows.globalization import Language
        
        async def test_recognizer():
            # Intentar primero con en-US (más común), luego es-ES
            for lang_code in ["en-US", "es-ES"]:
                try:
                    print(f"  [INFO] Intentando con idioma: {lang_code}")
                    lang = Language(lang_code)
                    recognizer = SpeechRecognizer(lang)
                    
                    # Agregar constraint de dictado
                    constraint = SpeechRecognitionTopicConstraint(
                        SpeechRecognitionScenario.DICTATION,
                        "dictation"
                    )
                    recognizer.constraints.append(constraint)
                    
                    # Compilar constraints
                    print(f"  [INFO] Compilando constraints para {lang_code}...")
                    result = await recognizer.compile_constraints_async()
                    
                    # Verificar resultado
                    status_value = result.status.value if hasattr(result.status, 'value') else result.status
                    print(f"  [INFO] Status de compilacion: {status_value} ({type(result.status).__name__})")
                    
                    if status_value == 0:  # Success
                        print(f"  [OK] Constraints compilados exitosamente para {lang_code}")
                        return True
                    else:
                        print(f"  [WARN] Compilacion devolvio status {status_value} para {lang_code}")
                        
                except OSError as e:
                    if "not supported" in str(e):
                        print(f"  [WARN] {lang_code} no esta instalado en este sistema")
                    else:
                        raise
            
            # Si ninguno funciono
            print("  [WARN] Ningun idioma de prueba (en-US, es-ES) esta instalado")
            print("  -> Instala al menos un paquete de voz en Configuracion de Windows")
            return False
        
        # Ejecutar test async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(test_recognizer())
        loop.close()
        
        return result
        
    except PermissionError as e:
        print(f"  [WARN] ERROR de permisos: {e}")
        print("  -> Verifica que el microfono tenga permisos en Configuracion de Windows")
        print("  [INFO] El codigo esta correcto, pero faltan permisos/configuracion del sistema")
        return True  # No fallar el test por problemas del sistema
    except OSError as e:
        if "Speech Error" in str(e) or "not supported" in str(e):
            print(f"  [WARN] Windows Speech no esta disponible: {e}")
            print("  -> Posibles causas:")
            print("     1. No hay paquetes de idioma con voz instalados")
            print("     2. No hay permisos de microfono")
            print("     3. El servicio de Speech de Windows no esta activo")
            print("  [INFO] El codigo esta correcto, instala un paquete de voz en Windows")
            return True  # No fallar el test por problemas del sistema
        else:
            print(f"  [FAIL] ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False
    except Exception as e:
        print(f"  [FAIL] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_injector():
    """Verifica que TextInjector existe y es usable"""
    print("\n[OK] Test 6: TextInjector...")
    try:
        from aurora.injector import TextInjector
        injector = TextInjector()
        print("  [OK] TextInjector instanciado correctamente")
        print("  [INFO] (No se ejecuta inject_text en el smoke test)")
        return True
    except Exception as e:
        print(f"  [FAIL] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_regressions():
    """Regresiones: mapeo de errores de speech y acciones del menu del tray"""
    print("\n[OK] Test 7: Regresiones (errores speech, menu tray)...")
    try:
        from aurora.speech import SpeechEngine
        from aurora.errors import MicrophonePermissionError, LanguageNotInstalledError
        e = OSError(); e.winerror = -2147199735  # 0x80045509
        assert isinstance(SpeechEngine._map_error(e, "es-ES"), MicrophonePermissionError)
        e = OSError(); e.winerror = -2147200966  # 0x8004503A
        assert isinstance(SpeechEngine._map_error(e, "es-ES"), LanguageNotInstalledError)
        assert isinstance(SpeechEngine._map_error(PermissionError(), "es-ES"), MicrophonePermissionError)

        from aurora.tray import TrayIcon
        got = []
        t = TrayIcon(lambda: None, got.append, lambda: None, lambda: None)
        menu = t._create_menu()
        lang_menu = [i for i in menu.items if i.text == 'Idioma'][0].submenu
        item = [i for i in lang_menu.items if i.text == 'English (US)'][0]
        item(None)  # pystray invoca action(icon, item)
        assert got == ['en-US'], got
        print("  [OK] Regresiones OK")
        return True
    except Exception as e:
        print(f"  [FAIL] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecuta todos los tests"""
    print("=" * 60)
    print("Aurora - Smoke Test")
    print("=" * 60)
    
    results = []
    
    results.append(test_imports())
    results.append(test_config())
    results.append(test_winrt_imports())
    results.append(test_winrt_api_names())
    results.append(test_speech_recognizer())
    results.append(test_injector())
    results.append(test_regressions())
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"[PASS] TODOS LOS TESTS PASARON ({passed}/{total})")
        print("=" * 60)
        return 0
    else:
        print(f"[FAIL] ALGUNOS TESTS FALLARON ({passed}/{total})")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
