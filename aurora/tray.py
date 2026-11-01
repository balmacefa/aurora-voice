"""Icono de bandeja del sistema con menú"""

import pystray
from PIL import Image, ImageDraw
import threading
from typing import Callable, Dict


class TrayIcon:
    """Icono de bandeja del sistema con menú de control"""
    
    def __init__(self, 
                 on_toggle: Callable,
                 on_language_change: Callable[[str], None],
                 on_config: Callable,
                 on_exit: Callable):
        self.on_toggle = on_toggle
        self.on_language_change = on_language_change
        self.on_config = on_config
        self.on_exit = on_exit
        
        self.icon: pystray.Icon = None
        self.thread: threading.Thread = None
        self.is_active = False
        
        # Idiomas disponibles
        self.languages = {
            'Español (España)': 'es-ES',
            'English (US)': 'en-US',
            'English (UK)': 'en-GB',
            'Français': 'fr-FR',
            'Deutsch': 'de-DE'
        }
    
    def _create_icon(self) -> Image.Image:
        """Crea un icono simple para la bandeja"""
        # Crear una imagen de 64x64
        image = Image.new('RGB', (64, 64), color='#2d2d2d')
        draw = ImageDraw.Draw(image)
        
        # Dibujar un micrófono simple
        # Base del micrófono
        draw.ellipse([22, 15, 42, 35], fill='#00ff00')
        # Cuerpo del micrófono
        draw.rectangle([28, 35, 36, 45], fill='#00ff00')
        # Base
        draw.rectangle([22, 45, 42, 48], fill='#00ff00')
        
        return image
    
    def _create_menu(self) -> pystray.Menu:
        """Crea el menú del icono de bandeja"""
        # Crear submenú de idiomas
        # NOTA: pystray invoca action(icon, item) si la funcion tiene 2 args
        # posicionales (incluso con defaults), lo que pisaba `lang=code`.
        # Usamos una fabrica que devuelve un callable sin argumentos.
        def make_action(lang):
            return lambda: self._on_language_selected(lang)

        language_items = [
            pystray.MenuItem(name, make_action(code))
            for name, code in self.languages.items()
        ]
        
        return pystray.Menu(
            pystray.MenuItem(
                'Activar/Desactivar dictado',
                lambda: self.on_toggle(),
                default=True
            ),
            pystray.MenuItem(
                'Idioma',
                pystray.Menu(*language_items)
            ),
            pystray.MenuItem(
                'Abrir configuración',
                lambda: self.on_config()
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                'Salir',
                lambda: self._on_exit_clicked()
            )
        )
    
    def _on_language_selected(self, language_code: str):
        """Handler para cambio de idioma"""
        self.on_language_change(language_code)
    
    def _on_exit_clicked(self):
        """Handler para salir"""
        try:
            self.on_exit()
        finally:
            if self.icon:
                self.icon.stop()
    
    def start(self):
        """Inicia el icono de bandeja en su propio thread"""
        if self.thread and self.thread.is_alive():
            return
        
        icon_image = self._create_icon()
        menu = self._create_menu()
        
        self.icon = pystray.Icon(
            'Aurora',
            icon_image,
            'Aurora - Dictado por voz',
            menu
        )
        
        # Ejecutar en thread dedicado
        self.thread = threading.Thread(target=self.icon.run, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Detiene el icono de bandeja"""
        if self.icon:
            self.icon.stop()
    
    def update_status(self, is_active: bool):
        """
        Actualiza el estado visual del icono.
        
        Args:
            is_active: True si el dictado está activo
        """
        self.is_active = is_active
        # Podríamos cambiar el icono aquí si quisiéramos
        # Por ahora solo guardamos el estado
