"""Gestión de hotkeys globales"""

import keyboard
import threading
from typing import Callable, Optional


class HotkeyManager:
    """Gestiona el registro de hotkeys globales usando keyboard lib"""
    
    def __init__(self):
        self.current_combo: Optional[str] = None
        self.callback: Optional[Callable] = None
        self._running = False
    
    def start(self, combo: str, callback: Callable) -> bool:
        """
        Registra un hotkey global.
        
        Args:
            combo: Combinación de teclas (ej. "ctrl+alt+h")
            callback: Función a llamar cuando se presione el hotkey
        
        Returns:
            True si el hotkey se registró correctamente, False en caso de error
        """
        if self._running:
            self.stop()
        
        self.current_combo = combo
        self.callback = callback
        
        try:
            keyboard.add_hotkey(combo, callback)
            self._running = True
            return True
        except Exception as e:
            print(f"Error registrando hotkey {combo}: {e}")
            self._running = False
            return False
    
    def stop(self):
        """Desregistra el hotkey actual"""
        if self._running and self.current_combo:
            try:
                keyboard.remove_hotkey(self.current_combo)
            except Exception as e:
                print(f"Error removiendo hotkey: {e}")
        
        self._running = False
        self.current_combo = None
        self.callback = None
    
    def rebind(self, new_combo: str) -> bool:
        """
        Cambia la combinación de teclas manteniendo el mismo callback.
        Registra el nuevo antes de desregistrar el anterior para evitar ventana sin hotkey.
        
        Args:
            new_combo: Nueva combinación de teclas
        
        Returns:
            True si el rebind fue exitoso, False en caso de error
        """
        if not self.callback:
            return False
        
        callback = self.callback
        old_combo = self.current_combo
        
        # Intentar registrar el nuevo hotkey primero
        try:
            keyboard.add_hotkey(new_combo, callback)
            # Si fue exitoso, desregistrar el anterior
            if old_combo and self._running:
                try:
                    keyboard.remove_hotkey(old_combo)
                except Exception as e:
                    print(f"Advertencia al remover hotkey anterior: {e}")
            
            self.current_combo = new_combo
            self._running = True
            return True
            
        except Exception as e:
            print(f"Error en rebind a {new_combo}: {e}")
            # Si falla el nuevo, asegurar que el anterior siga activo
            # (ya debería estar registrado, no hacemos nada)
            return False
