"""Aurora - Auto-update desde GitHub Releases (solo stdlib)."""

import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

OWNER = "balmacefa"
REPO = "aurora-voice"
ASSET_NAME = "Aurora-Portable.exe"
API_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/latest"
USER_AGENT = "Aurora-Updater"


class UpdateError(Exception):
    pass


# ---------------------------------------------------------------- versiones
def parse_version(v) -> tuple:
    """'v0.1.1' / '0.1.1' -> (0, 1, 1). Ignora sufijos (-beta, +build)."""
    s = str(v or "").strip().lstrip("vV")
    m = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?", s)
    if not m:
        raise ValueError(f"version invalida: {v!r}")
    return tuple(int(x) if x else 0 for x in m.groups())


def is_newer(remote, local) -> bool:
    try:
        return parse_version(remote) > parse_version(local)
    except ValueError:
        return False


def current_version() -> str:
    from aurora import __version__
    return __version__


# ------------------------------------------------------------------- GitHub
def get_latest_release(timeout=10):
    """Devuelve dict {tag, version, url, name, notes} o None si no hay releases.

    Lanza UpdateError en errores de red/HTTP distintos de 404.
    """
    req = urllib.request.Request(API_URL, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise UpdateError(f"GitHub respondio HTTP {e.code}") from e
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        raise UpdateError(f"Error de red consultando GitHub: {e}") from e
    except ValueError as e:
        raise UpdateError(f"Respuesta de GitHub invalida: {e}") from e

    tag = data.get("tag_name") or ""
    url = None
    for a in data.get("assets") or []:
        if a.get("name") == ASSET_NAME:
            url = a.get("browser_download_url")
            break
    return {
        "tag": tag,
        "version": tag.lstrip("vV"),
        "url": url,
        "name": data.get("name") or tag,
        "notes": data.get("body") or "",
    }


def check_for_update() -> dict:
    cur = current_version()
    res = {"available": False, "current": cur, "latest": None, "url": None, "notes": ""}
    try:
        rel = get_latest_release()
    except UpdateError as e:
        res["error"] = str(e)
        return res
    if rel is None:
        res["message"] = "No hay releases publicadas"
        return res
    res["latest"] = rel["version"]
    res["url"] = rel["url"]
    res["notes"] = rel["notes"]
    if is_newer(rel["version"], cur):
        if rel["url"]:
            res["available"] = True
        else:
            res["error"] = f"La release {rel['tag']} no tiene el asset {ASSET_NAME}"
    return res


# ----------------------------------------------------------------- descarga
def download(url, dest_path, timeout=60, progress=None):
    """Descarga url a dest_path en streaming. progress(done_bytes, total_bytes|None)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    dest_path = Path(dest_path)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r, open(dest_path, "wb") as f:
            total = r.headers.get("Content-Length")
            total = int(total) if total and total.isdigit() else None
            done = 0
            while True:
                chunk = r.read(64 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if progress:
                    progress(done, total)
        if total is not None and done != total:
            raise UpdateError(f"Descarga incompleta ({done}/{total} bytes)")
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        try:
            dest_path.unlink()
        except OSError:
            pass
        raise UpdateError(f"Error descargando: {e}") from e
    return str(dest_path)


# ------------------------------------------------------------------ update
# Helper en PowerShell (mas robusto que .bat en modo onefile/windowed sin
# consola): espera a que el proceso muera, reemplaza el exe y RELANZA con
# Start-Process (hereda la window-station interactiva -> la GUI arranca).
_PS = r"""$ErrorActionPreference = 'SilentlyContinue'
$targetPid = __PID__
$new = '__NEW__'
$exe = '__EXE__'
try { Wait-Process -Id $targetPid -Timeout 30 } catch {}
$ok = $false
for ($i = 0; $i -lt 20; $i++) {
  try { Move-Item -LiteralPath $new -Destination $exe -Force -ErrorAction Stop; $ok = $true; break }
  catch { Start-Sleep -Milliseconds 600 }
}
if ($ok) { Start-Process -FilePath $exe -WorkingDirectory (Split-Path -Parent $exe) }
Remove-Item -LiteralPath $MyInvocation.MyCommand.Path -Force
"""


def apply_update(dry_run=False, url=None) -> dict:
    """Reemplaza el exe actual por el de la ultima release. Solo si frozen."""
    if not getattr(sys, "frozen", False):
        return {"ok": False, "reason": "solo en build portable (frozen)"}

    if url is None:
        info = check_for_update()
        if info.get("error"):
            return {"ok": False, "reason": info["error"]}
        if not info["available"]:
            return {"ok": False, "reason": "no hay actualizacion disponible"}
        url = info["url"]

    exe_path = Path(sys.executable)
    new_path = exe_path.with_name(exe_path.name + ".new")
    try:
        download(url, new_path)
    except UpdateError as e:
        return {"ok": False, "reason": str(e)}

    bat_path = Path(tempfile.gettempdir()) / f"aurora_update_{os.getpid()}.ps1"
    try:
        script = (_PS.replace("__PID__", str(os.getpid()))
                     .replace("__NEW__", str(new_path))
                     .replace("__EXE__", str(exe_path)))
        bat_path.write_text(script, encoding="utf-8", newline="\r\n")
    except OSError as e:
        return {"ok": False, "reason": f"No se pudo crear el helper: {e}"}

    result = {"ok": True, "dry_run": bool(dry_run), "new_exe": str(new_path),
              "bat": str(bat_path), "exe": str(exe_path)}
    if dry_run:
        return result

    try:
        # NO usar DETACHED_PROCESS: desvincula de la window-station interactiva
        # y el exe relanzado no podria crear la GUI (tkinter).
        flags = (getattr(subprocess, "CREATE_NO_WINDOW", 0)
                 | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
        subprocess.Popen(["powershell.exe", "-NoProfile", "-ExecutionPolicy",
                          "Bypass", "-WindowStyle", "Hidden", "-File", str(bat_path)],
                         creationflags=flags, stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         close_fds=True)
    except OSError as e:
        return {"ok": False, "reason": f"No se pudo lanzar el helper: {e}"}
    print("Actualizando Aurora, reiniciando...", flush=True)
    os._exit(0)


def check_and_apply(dry_run=False) -> dict:
    info = check_for_update()
    if info.get("error"):
        print(f"No se pudo comprobar actualizaciones: {info['error']}")
        return {"ok": False, "updated": False, **info}
    if not info["available"]:
        print(f"Aurora {info['current']} esta al dia.")
        return {"ok": True, "updated": False, **info}
    print(f"Nueva version {info['latest']} (actual {info['current']}).")
    res = apply_update(dry_run=dry_run, url=info["url"])
    return {"ok": res.get("ok", False), "updated": bool(res.get("ok") and not dry_run),
            "apply": res, **info}
