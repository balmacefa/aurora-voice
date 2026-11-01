"""Gestión de configuración de Aurora"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any


def _appdata_dir() -> Path:
    return Path(os.getenv('APPDATA') or Path.home()) / 'Aurora'


def _is_writable_dir(path: Path) -> bool:
    """Comprueba que se puede crear el directorio y escribir en él."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / '.aurora_write_test'
        probe.write_text('ok', encoding='utf-8')
        probe.unlink()
        return True
    except Exception:
        return False


def _resolve_data_dir() -> Path:
    """Resuelve el directorio de datos.

    Prioridad: AURORA_DATA_DIR > AURORA_PORTABLE=1 > marcador Aurora.portable
    junto al exe (frozen) > %APPDATA%\\Aurora. Si a/b/c no son escribibles,
    se usa %APPDATA%\\Aurora.
    """
    frozen = getattr(sys, 'frozen', False)
    exe_dir = Path(sys.executable).parent if frozen else None

    candidate = None
    env_dir = os.getenv('AURORA_DATA_DIR')
    if env_dir:
        candidate = Path(env_dir)
    elif os.getenv('AURORA_PORTABLE') == '1':
        candidate = (exe_dir if frozen else Path.cwd()) / 'data'
    elif frozen and (exe_dir / 'Aurora.portable').exists():
        candidate = exe_dir / 'data'

    if candidate is not None and _is_writable_dir(candidate):
        return candidate
    return _appdata_dir()


class ConfigManager:
    """Gestiona la configuración de Aurora en %APPDATA%"""
    
    DEFAULT_CONFIG = {
        "language": "es-ES",
        "hotkey": "ctrl+alt+h"
    }
    
    def __init__(self):
        self.config_dir = _resolve_data_dir()
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
