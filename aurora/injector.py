"""Inyección de texto mediante SendInput Unicode"""

import ctypes
import time
import sys
from ctypes import wintypes


# Constantes de Windows
INPUT_KEYBOARD = 1
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_KEYUP = 0x0002
VK_RETURN = 0x0D

# Definir ULONG_PTR segun la arquitectura (correcto para x64)
if sys.maxsize > 2**32:
    ULONG_PTR = ctypes.c_uint64  # 64-bit
else:
    ULONG_PTR = ctypes.c_ulong   # 32-bit

# Estructuras de Windows
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR)
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD)
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR)
    ]

class INPUT(ctypes.Structure):
    class _I(ctypes.Union):
        _fields_ = [
            ("ki", KEYBDINPUT),
            ("mi", MOUSEINPUT),
            ("hi", HARDWAREINPUT)
        ]
    
    _anonymous_ = ("_i",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("_i", _I)
    ]

# Configurar user32 a nivel de módulo
user32 = ctypes.WinDLL('user32', use_last_error=True)
user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
user32.SendInput.restype = wintypes.UINT


class TextInjector:
    """Inyecta texto en el campo con foco usando SendInput Unicode"""
    
    @staticmethod
    def inject_text(text: str, delay_ms: int = 0):
        """
        Inyecta texto carácter por carácter con SendInput Unicode.
        Maneja correctamente caracteres fuera del BMP mediante surrogates.
        Mapea '\n' a VK_RETURN (virtual key), ignora '\r'.
        
        Args:
            text: Texto a inyectar
            delay_ms: Delay opcional entre caracteres en milisegundos
        """
        if not text:
            return
        
        for char in text:
            # Ignorar \r
            if char == '\r':
                continue
            
            events = []
            
            # Mapear \n a VK_RETURN (virtual key)
            if char == '\n':
                # Key down
                input_down = INPUT()
                input_down.type = INPUT_KEYBOARD
                input_down.ki.wVk = VK_RETURN
                input_down.ki.wScan = 0
                input_down.ki.dwFlags = 0
                input_down.ki.time = 0
                input_down.ki.dwExtraInfo = 0
                events.append(input_down)
                
                # Key up
                input_up = INPUT()
                input_up.type = INPUT_KEYBOARD
                input_up.ki.wVk = VK_RETURN
                input_up.ki.wScan = 0
                input_up.ki.dwFlags = KEYEVENTF_KEYUP
                input_up.ki.time = 0
                input_up.ki.dwExtraInfo = 0
                events.append(input_up)
            else:
                # Obtener el código Unicode
                code_point = ord(char)
                
                # Para caracteres fuera del BMP (> 0xFFFF), Windows espera surrogates
                if code_point > 0xFFFF:
                    # Calcular surrogates UTF-16
                    code_point -= 0x10000
                    high_surrogate = 0xD800 + (code_point >> 10)
                    low_surrogate = 0xDC00 + (code_point & 0x3FF)
                    chars_to_send = [high_surrogate, low_surrogate]
                else:
                    chars_to_send = [code_point]
                
                for char_code in chars_to_send:
                    # Key down
                    input_down = INPUT()
                    input_down.type = INPUT_KEYBOARD
                    input_down.ki.wVk = 0
                    input_down.ki.wScan = char_code
                    input_down.ki.dwFlags = KEYEVENTF_UNICODE
                    input_down.ki.time = 0
                    input_down.ki.dwExtraInfo = 0
                    events.append(input_down)
                    
                    # Key up
                    input_up = INPUT()
                    input_up.type = INPUT_KEYBOARD
                    input_up.ki.wVk = 0
                    input_up.ki.wScan = char_code
                    input_up.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
                    input_up.ki.time = 0
                    input_up.ki.dwExtraInfo = 0
                    events.append(input_up)
            
            # Enviar todos los eventos del carácter atómicamente
            if events:
                n = len(events)
                inputs_array = (INPUT * n)(*events)
                result = user32.SendInput(n, inputs_array, ctypes.sizeof(INPUT))
                if result != n:
                    raise ctypes.WinError(ctypes.get_last_error())
            
            # Delay opcional entre caracteres
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
