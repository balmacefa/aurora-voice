import socket, json, sys
port = int(sys.argv[2]) if len(sys.argv) > 2 else 48123
try:
    cmd = json.loads(sys.argv[1])
    s = socket.create_connection(("127.0.0.1", port), timeout=6)
    s.sendall((json.dumps(cmd) + "\n").encode())
    print(s.recv(4096).decode().strip())
except Exception as e:
    print("IPC_ERR:", type(e).__name__, e)
