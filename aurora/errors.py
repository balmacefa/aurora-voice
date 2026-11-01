"""Excepciones específicas de Aurora"""


class AuroraError(Exception):
    """Excepción base para errores de Aurora"""
    pass


class MicrophonePermissionError(AuroraError):
    """El usuario no ha concedido permisos de micrófono"""
    pass


class MicrophoneNotFoundError(AuroraError):
    """No se encontró un micrófono disponible"""
    pass


class UnsupportedOSError(AuroraError):
    """Sistema operativo no soportado"""
    pass


class LanguageNotInstalledError(AuroraError):
    """El idioma de reconocimiento no está instalado en Windows"""
    pass
