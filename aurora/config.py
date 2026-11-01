"""Gestión de configuración de Aurora"""

import json
import os
from pathlib import Path
from typing import Dict, Any


class ConfigManager:
    """Gestiona la configuración de Aurora en %APPDATA%"""
    
    DEFAULT_CONFIG = {
        "language": "es-ES",
        "hotkey": "ctrl+alt+h"
    }
    
    def __init__(self):
        self.config_dir = Path(os.getenv('APPDATA')) / 'Aurora'
        self.config_file = self.config_dir / 'config.json'
        self.config: Dict[str, Any] = {}
        self._ensure_config_dir()
        self.load()
    
    def _ensure_config_dir(self):
        """Crea el directorio de configuración si no existe"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load(self) -> Dict[str, Any]:
        """Carga la configuración desde el archivo JSON"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                # Asegurar que existen las claves por defecto
                for key, value in self.DEFAULT_CONFIG.items():
                    if key not in self.config:
                        self.config[key] = value
            except (json.JSONDecodeError, IOError) as e:
                # Guardar backup antes de caer a defaults
                backup_path = self.config_file.with_suffix('.json.bak')
                try:
                    import shutil
                    shutil.copy2(self.config_file, backup_path)
                    print(f"Config corrupto guardado en {backup_path}")
                except Exception:
                    pass
                print(f"Error cargando config: {e}, usando defaults")
                self.config = self.DEFAULT_CONFIG.copy()
        else:
            self.config = self.DEFAULT_CONFIG.copy()
            self.save()
        return self.config
    
    def save(self):
        """Guarda la configuración en el archivo JSON (escritura atómica)"""
        import tempfile
        try:
            # Escribir a archivo temporal en el mismo directorio
            temp_fd, temp_path = tempfile.mkstemp(
                dir=self.config_dir,
                prefix='.config_',
                suffix='.tmp',
                text=True
            )
            try:
                with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
                # Reemplazar atómicamente
                os.replace(temp_path, self.config_file)
            except Exception:
                # Limpiar el temporal si algo falla
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
                raise
        except IOError as e:
            print(f"Error guardando config: {e}")
    
    def get(self, key: str, default=None) -> Any:
        """Obtiene un valor de configuración"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Establece un valor de configuración y guarda"""
        self.config[key] = value
        self.save()
    
    @property
    def language(self) -> str:
        return self.get('language', 'es-ES')
    
    @language.setter
    def language(self, value: str):
        self.set('language', value)
    
    @property
    def hotkey(self) -> str:
        return self.get('hotkey', 'ctrl+alt+h')
    
    @hotkey.setter
    def hotkey(self, value: str):
        self.set('hotkey', value)
