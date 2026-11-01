"""Ventana overlay transparente para mostrar estado del dictado"""

import tkinter as tk
from tkinter import font


class OverlayWindow:
    """
    Ventana overlay sin borde, topmost, semitransparente.
    Se posiciona en la parte inferior-centro de la pantalla.
    """
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.visible = False
        
        # Configurar ventana
        self.root.overrideredirect(True)  # Sin borde
        self.root.attributes('-topmost', True)  # Siempre encima
        self.root.attributes('-alpha', 0.9)  # Semitransparente
        
        # Frame principal con fondo
        self.frame = tk.Frame(
            self.root,
            bg='#2d2d2d',
            padx=20,
            pady=15,
            relief=tk.RAISED,
            borderwidth=2
        )
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Label de estado
        self.state_label = tk.Label(
            self.frame,
            text="Escuchando...",
            fg='#00ff00',
            bg='#2d2d2d',
            font=font.Font(family='Segoe UI', size=10, weight='bold')
        )
        self.state_label.pack()
        
        # Label de texto parcial
        self.text_label = tk.Label(
            self.frame,
            text="",
            fg='#ffffff',
            bg='#2d2d2d',
            font=font.Font(family='Segoe UI', size=11),
            wraplength=600,
            justify=tk.LEFT
        )
        self.text_label.pack(pady=(5, 0))
        
        # Posicionar en la parte inferior-centro
        self._position_window()
        
        # Inicialmente oculta
        self.root.withdraw()
    
    def _position_window(self):
        """Posiciona la ventana en la parte inferior-centro de la pantalla"""
        self.root.update_idletasks()
        
        # Obtener dimensiones de la pantalla
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Obtener dimensiones de la ventana
        window_width = self.root.winfo_reqwidth()
        window_height = self.root.winfo_reqheight()
        
        # Calcular posición (centro horizontal, 100px desde abajo)
        x = (screen_width - window_width) // 2
        y = screen_height - window_height - 100
        
        self.root.geometry(f"+{x}+{y}")
    
    def show(self):
        """Muestra la ventana overlay"""
        if not self.visible:
            self.root.deiconify()
            self._position_window()
            self.visible = True
    
    def hide(self):
        """Oculta la ventana overlay"""
        if self.visible:
            self.root.withdraw()
            self.visible = False
    
    def update_text(self, partial: str):
        """
        Actualiza el texto parcial mostrado.
        
        Args:
            partial: Texto parcial del reconocimiento
        """
        self.text_label.config(text=partial)
        self._position_window()  # Reposicionar si cambió el tamaño
    
    def clear_text(self):
        """Limpia el texto parcial"""
        self.text_label.config(text="")
        self._position_window()
    
    def set_state(self, state: str, color: str = '#00ff00'):
        """
        Establece el estado mostrado.
        
        Args:
            state: Texto del estado (ej. "Escuchando...", "Error: ...")
            color: Color del texto de estado
        """
        self.state_label.config(text=state, fg=color)
        self._position_window()
