#!/usr/bin/env python3
import os, base64, logging, socket, json
from concurrent.futures import ThreadPoolExecutor

PORT = 7777
DATA_DIR = "server_storage"
WORKER_LIMIT = int(os.getenv("WORKER_LIMIT", 5))
DELIM = b"\r\n\r\n"

os.makedirs(DATA_DIR, exist_ok=True)

def handle_client_conn(conn):
    try:
        buffer = b""
        while DELIM not in buffer:
            chunk = conn.recv(1024*1024)  # 1MB chunks
            if not chunk:
                break
            buffer += chunk
        raw_request = buffer.split(DELIM)[0].decode()
        parts = raw_request.split(" ", 2)
        cmd = parts[0]

        if cmd == "LIST":
            files = os.listdir(DATA_DIR)
            resp = {"status": "OK", "files": files}
        elif cmd == "UPLOAD":
            filename, b64data = parts[1], parts[2]
            data = base64.b64decode(b64data)
            with open(os.path.join(DATA_DIR, filename), "wb") as f:
                f.write(data)
            resp = {"status": "OK", "message": "Upload succeeded"}
        elif cmd == "GET":
            filename = parts[1]
            with open(os.path.join(DATA_DIR, filename), "rb") as f:
                data = base64.b64encode(f.read()).decode()
            resp = {"status": "OK", "file_data": data}
        else:
            resp = {"status": "ERROR", "message": "Unknown command"}
    except Exception as e:
        logging.exception(e)
        resp = {"status": "ERROR", "message": str(e)}

    conn.sendall(json.dumps(resp).encode() + DELIM)
    conn.close()

def main():
    logging.basicConfig(level=logging.INFO)
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", PORT))
    srv.listen()
    logging.info(f"[ThreadPool] Listening on port {PORT} with {WORKER_LIMIT} workers")

    with ThreadPoolExecutor(max_workers=WORKER_LIMIT) as pool:
        while True:
            conn, _ = srv.accept()
            pool.submit(handle_client_conn, conn)

if __name__ == "__main__":
    main()