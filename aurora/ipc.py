# INTEGRACION (anadir dentro de App.run(), justo despues de crear/iniciar el tray):
#     from aurora.ipc import start_control_server; start_control_server(self)
"""Servidor de control local (headless) para Aurora.

TCP en 127.0.0.1:AURORA_IPC_PORT (default 48123). Protocolo: una peticion JSON
por linea, una respuesta JSON por linea. Comandos: status, start, stop, toggle,
set_language, quit.
"""
import json
import os
import socket
import threading

DEFAULT_PORT = 48123
_TK_TIMEOUT = 10.0


def _port() -> int:
    try:
        return int(os.environ.get("AURORA_IPC_PORT", DEFAULT_PORT))
    except ValueError:
        return DEFAULT_PORT


def _version() -> str:
    try:
        from aurora import __version__
        return __version__
    except Exception:
        return "unknown"


class ControlServer:
    def __init__(self, app, port: int = None):
        self.app = app
        self.port = port or _port()
        self._sock = None
        self._thread = None
        self._stopping = False

    # ---- ciclo de vida -------------------------------------------------
    def start(self) -> bool:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("127.0.0.1", self.port))
            s.listen(5)
        except OSError as e:
            print(f"[ipc] No se pudo abrir 127.0.0.1:{self.port}: {e}")
            return False
        self._sock = s
        self._thread = threading.Thread(target=self._serve, name="aurora-ipc", daemon=True)
        self._thread.start()
        print(f"[ipc] Control escuchando en 127.0.0.1:{self.port}")
        return True

    def stop(self):
        self._stopping = True
        try:
            if self._sock:
                self._sock.close()
        except OSError:
            pass

    def _serve(self):
        while not self._stopping:
            try:
                conn, _ = self._sock.accept()
            except OSError:
                break
            threading.Thread(target=self._client, args=(conn,), daemon=True).start()

    def _client(self, conn):
        try:
            conn.settimeout(30)
            with conn, conn.makefile("rwb") as f:
                for raw in f:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        req = json.loads(raw.decode("utf-8"))
                        if not isinstance(req, dict):
                            raise ValueError("la peticion debe ser un objeto JSON")
                        resp = self.handle(req)
                    except Exception as e:
                        resp = {"ok": False, "error": f"{type(e).__name__}: {e}"}
                    f.write((json.dumps(resp, ensure_ascii=False) + "\n").encode("utf-8"))
                    f.flush()
        except OSError:
            pass

    # ---- ejecucion en thread de tkinter --------------------------------
    def _run_tk(self, fn):
        """Ejecuta fn en el thread de tkinter y espera; devuelve su resultado."""
        root = getattr(self.app, "root", None)
        if root is None:
            return fn()
        done = threading.Event()
        box = {}

        def wrapper():
            try:
                box["r"] = fn()
            except Exception as e:
                box["e"] = e
            finally:
                done.set()

        root.after(0, wrapper)
        if not done.wait(_TK_TIMEOUT):
            raise TimeoutError("timeout esperando al thread de tkinter")
        if "e" in box:
            raise box["e"]
        return box.get("r")

    def _status(self) -> dict:
        return {
            "ok": True,
            "is_dictating": bool(self.app.is_dictating),
            "language": self.app.config.language,
            "version": _version(),
        }

    # ---- comandos ------------------------------------------------------
    def handle(self, req: dict) -> dict:
        cmd = req.get("cmd")
        app = self.app
        if cmd == "status":
            return self._status()
        if cmd == "start":
            self._run_tk(app._start_dictation)
            return self._status()
        if cmd == "stop":
            self._run_tk(app._stop_dictation)
            return self._status()
        if cmd == "toggle":
            self._run_tk(app.toggle_dictation)
            return self._status()
        if cmd == "set_language":
            lang = req.get("language")
            if not isinstance(lang, str) or not lang:
                return {"ok": False, "error": "falta 'language'"}

            def apply():
                handler = getattr(app, "_on_language_change", None)
                if handler:  # detiene/reinicia el dictado si estaba activo
                    handler(lang)
                else:
                    app.config.language = lang

            self._run_tk(apply)
            return self._status()
        if cmd == "quit":
            root = getattr(app, "root", None)
            if root is not None:
                # no esperar: la app se cierra
                root.after(0, self._do_quit)
            else:
                self._do_quit()
            return {"ok": True, "quitting": True}
        return {"ok": False, "error": f"comando desconocido: {cmd!r}"}

    def _do_quit(self):
        app = self.app
        try:
            on_exit = getattr(app, "_on_exit", None)
            if on_exit:
                on_exit()
        except Exception as e:
            print(f"[ipc] error en _on_exit: {e}")
        try:
            if getattr(app, "tray", None):
                app.tray.stop()
        except Exception:
            pass
        try:
            if app.root:
                app.root.quit()
                app.root.destroy()
        except Exception:
            pass
        self.stop()
        # Garantiza el cierre aun si quedan threads no-daemon.
        threading.Timer(2.0, lambda: os._exit(0)).start()


def start_control_server(app):
    """Arranca el servidor de control en un thread daemon y lo devuelve."""
    server = ControlServer(app)
    server.start()  # si el puerto esta ocupado, loguea y la app sigue
    return server
