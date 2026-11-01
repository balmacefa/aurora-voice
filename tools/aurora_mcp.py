# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=1.2.0,<2"]
# ///
"""Servidor MCP para controlar Aurora sin UI (via aurora/ipc.py)."""
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("aurora")

AURORA_HOME = os.environ.get("AURORA_HOME") or str(Path(__file__).resolve().parent.parent)
AURORA_PY = os.environ.get(
    "AURORA_PY", r"C:\Users\fabia\AppData\Local\Programs\Python\Python312\python.exe"
)
AURORA_IPC_PORT = int(os.environ.get("AURORA_IPC_PORT", "48123"))

_proc = None  # ultimo proceso lanzado por aurora_launch


def _send(cmd_dict: dict, timeout: float = 5) -> dict:
    try:
        with socket.create_connection(("127.0.0.1", AURORA_IPC_PORT), timeout=timeout) as s:
            s.settimeout(timeout)
            s.sendall((json.dumps(cmd_dict) + "\n").encode("utf-8"))
            buf = b""
            while b"\n" not in buf:
                chunk = s.recv(4096)
                if not chunk:
                    break
                buf += chunk
        line = buf.split(b"\n", 1)[0].strip()
        if not line:
            return {"ok": False, "stdout": "", "stderr": "Respuesta vacia de Aurora"}
        data = json.loads(line.decode("utf-8"))
        return {"ok": bool(data.get("ok")), "stdout": line.decode("utf-8"), "stderr": "", "data": data}
    except ConnectionRefusedError:
        return {"ok": False, "stdout": "", "stderr": "Aurora no esta corriendo; usa aurora_launch"}
    except socket.timeout:
        return {"ok": False, "stdout": "", "stderr": f"Timeout ({timeout}s) esperando a Aurora"}
    except (OSError, ValueError) as e:
        return {"ok": False, "stdout": "", "stderr": f"{type(e).__name__}: {e}"}


@mcp.tool()
def aurora_launch() -> dict:
    """Lanza la app Aurora (main.py) en segundo plano, sin ventana de consola."""
    global _proc
    if _send({"cmd": "status"}, timeout=1).get("ok"):
        return {"ok": True, "stdout": "Aurora ya esta corriendo", "stderr": ""}
    flags = 0
    if sys.platform == "win32":
        flags = (subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                 | subprocess.CREATE_NO_WINDOW)
    try:
        _proc = subprocess.Popen(
            [AURORA_PY, "main.py"], cwd=AURORA_HOME, creationflags=flags,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            close_fds=True,
        )
    except OSError as e:
        return {"ok": False, "stdout": "", "stderr": f"No se pudo lanzar: {e}"}
    return {"ok": True, "stdout": f"Lanzado pid={_proc.pid}", "stderr": "", "pid": _proc.pid}


@mcp.tool()
def aurora_status() -> dict:
    """Estado de Aurora: is_dictating, language, version."""
    return _send({"cmd": "status"})


@mcp.tool()
def aurora_start() -> dict:
    """Inicia el dictado."""
    return _send({"cmd": "start"})


@mcp.tool()
def aurora_stop() -> dict:
    """Detiene el dictado."""
    return _send({"cmd": "stop"})


@mcp.tool()
def aurora_toggle() -> dict:
    """Alterna el dictado."""
    return _send({"cmd": "toggle"})


@mcp.tool()
def aurora_set_language(language: str) -> dict:
    """Cambia el idioma de dictado (p.ej. 'es-ES', 'en-US')."""
    return _send({"cmd": "set_language", "language": language})


@mcp.tool()
def aurora_quit() -> dict:
    """Cierra Aurora; si sigue viva tras el quit, termina el proceso lanzado."""
    import time
    res = _send({"cmd": "quit"})
    if not res.get("ok") and "no esta corriendo" in res.get("stderr", ""):
        return res
    time.sleep(3)
    if _send({"cmd": "status"}, timeout=1).get("ok"):
        if _proc is not None and _proc.poll() is None:
            _proc.terminate()
            res["stderr"] = (res.get("stderr", "") + " Proceso terminado a la fuerza").strip()
        else:
            res["stderr"] = (res.get("stderr", "") + " Aurora sigue respondiendo y no fue lanzada por este servidor").strip()
            res["ok"] = False
    return res


def _run_main_flags(flags: list, timeout: float) -> dict:
    """Ejecuta main.py con flags (modo dev) y devuelve stdout parseado si es JSON."""
    cf = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    try:
        p = subprocess.run([AURORA_PY, "main.py", *flags], cwd=AURORA_HOME,
                           capture_output=True, text=True, timeout=timeout,
                           creationflags=cf)
    except subprocess.TimeoutExpired:
        return {"ok": False, "stdout": "", "stderr": f"Timeout ({timeout}s)"}
    except OSError as e:
        return {"ok": False, "stdout": "", "stderr": f"{type(e).__name__}: {e}"}
    out = p.stdout.strip()
    res = {"ok": p.returncode == 0, "stdout": out, "stderr": p.stderr.strip()}
    for line in reversed(out.splitlines()):
        try:
            res["result"] = json.loads(line)
            break
        except ValueError:
            continue
    return res


@mcp.tool()
def aurora_check_update() -> dict:
    """Comprueba si hay una version nueva en GitHub Releases (no descarga)."""
    return _run_main_flags(["--check-update"], timeout=30)


@mcp.tool()
def aurora_update(dry_run: bool = False) -> dict:
    """Actualiza Aurora desde GitHub Releases. dry_run=True solo descarga/prepara.
    Nota: en modo dev (no exe portable) no reemplaza nada."""
    flags = ["--update"] + (["--dry-run"] if dry_run else [])
    return _run_main_flags(flags, timeout=180)


if __name__ == "__main__":
    mcp.run()
