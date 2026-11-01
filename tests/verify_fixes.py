"""Verifica las correcciones de bugs criticos en Aurora"""

import sys
import ctypes
import os

# Agregar el directorio padre al path para importar aurora
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_input_struct_size():
    """Verifica que INPUT tenga el tamano correcto (40 bytes en x64)"""
    from aurora.injector import INPUT
    
    size = ctypes.sizeof(INPUT)
    expected = 40 if sys.maxsize > 2**32 else 28
    
    if size == expected:
        print(f"[PASS] INPUT struct size: {size} bytes (expected {expected} for {'x64' if sys.maxsize > 2**32 else 'x86'})")
        return True
    else:
        print(f"[FAIL] INPUT struct size: {size} bytes (expected {expected} for {'x64' if sys.maxsize > 2**32 else 'x86'})")
        return False

def test_winrt_event_subscription():
    """Verifica que speech.py usa add/remove con tokens, no += / -="""
    import re
    
    speech_file = os.path.join(os.path.dirname(__file__), '..', 'aurora', 'speech.py')
    
    with open(speech_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar uso de += o -= para eventos (operadores invalidos)
    invalid_patterns = [
        r'\.result_generated\s*\+=',
        r'\.result_generated\s*-=',
        r'\.hypothesis_generated\s*\+=',
        r'\.hypothesis_generated\s*-=',
    ]
    
    found_invalid = False
    for pattern in invalid_patterns:
        if re.search(pattern, content):
            print(f"[FAIL] Encontrado patron invalido: {pattern}")
            found_invalid = True
    
    # Verificar uso correcto de add_ y remove_
    has_add_result = 'add_result_generated(' in content
    has_add_hyp = 'add_hypothesis_generated(' in content
    has_remove_result = 'remove_result_generated(' in content
    has_remove_hyp = 'remove_hypothesis_generated(' in content
    
    # Verificar tokens
    has_token_result = '_token_result' in content
    has_token_hyp = '_token_hyp' in content
    
    all_correct = (
        has_add_result and has_add_hyp and
        has_remove_result and has_remove_hyp and
        has_token_result and has_token_hyp and
        not found_invalid
    )
    
    if all_correct:
        print("[PASS] WinRT event subscription usa add/remove con tokens correctamente")
        return True
    else:
        print("[FAIL] WinRT event subscription incorrecta:")
        if not has_add_result: print("  - Falta add_result_generated")
        if not has_add_hyp: print("  - Falta add_hypothesis_generated")
        if not has_remove_result: print("  - Falta remove_result_generated")
        if not has_remove_hyp: print("  - Falta remove_hypothesis_generated")
        if not has_token_result: print("  - Falta _token_result")
        if not has_token_hyp: print("  - Falta _token_hyp")
        return False

def test_text_injector_instantiation():
    """Verifica que TextInjector se puede instanciar sin error"""
    try:
        from aurora.injector import TextInjector
        injector = TextInjector()
        print("[PASS] TextInjector se instancia correctamente")
        return True
    except Exception as e:
        print(f"[FAIL] Error al instanciar TextInjector: {e}")
        return False

def test_user32_configuration():
    """Verifica que user32 este configurado a nivel de modulo"""
    try:
        from aurora import injector
        
        # Verificar que user32 existe a nivel de modulo
        if not hasattr(injector, 'user32'):
            print("[FAIL] user32 no esta definido a nivel de modulo")
            return False
        
        # Verificar argtypes y restype
        user32 = injector.user32
        if not hasattr(user32.SendInput, 'argtypes'):
            print("[FAIL] SendInput.argtypes no esta configurado")
            return False
        
        if not hasattr(user32.SendInput, 'restype'):
            print("[FAIL] SendInput.restype no esta configurado")
            return False
        
        print("[PASS] user32 configurado correctamente a nivel de modulo")
        return True
    except Exception as e:
        print(f"[FAIL] Error verificando user32: {e}")
        return False

def main():
    """Ejecuta todas las verificaciones"""
    print("=== Verificacion de correcciones de bugs criticos ===\n")
    
    results = []
    
    # Test 1: Tamano de INPUT struct
    results.append(test_input_struct_size())
    print()
    
    # Test 2: Configuracion de user32
    results.append(test_user32_configuration())
    print()
    
    # Test 3: Eventos WinRT
    results.append(test_winrt_event_subscription())
    print()
    
    # Test 4: Instanciacion de TextInjector
    results.append(test_text_injector_instantiation())
    print()
    
    # Resumen
    total = len(results)
    passed = sum(results)
    
    print(f"=== Resumen: {passed}/{total} tests PASSED ===")
    
    return 0 if all(results) else 1

if __name__ == '__main__':
    sys.exit(main())
