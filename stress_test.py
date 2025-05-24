#!/usr/bin/env python3
import os, time, json
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import base64
import socket

SERVER_ADDR = ("127.0.0.1", 7777)
DELIM = "\r\n\r\n"

def send_command(command):
    with socket.socket() as s:
        s.connect(SERVER_ADDR)
        s.sendall((command + DELIM).encode())
        buff = ""
        while DELIM not in buff:
            data = s.recv(1024*1024)
            if not data:
                break
            buff += data.decode()
    return json.loads(buff.split(DELIM)[0])

def client_list():
    resp = send_command("LIST")
    if resp.get("status") == "OK":
        return resp["files"]
    return []

def client_upload(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
    b64data = base64.b64encode(data).decode()
    filename = os.path.basename(filepath)
    resp = send_command(f"UPLOAD {filename} {b64data}")
    return resp.get("status") == "OK"

def client_download(filename):
    resp = send_command(f"GET {filename}")
    if resp.get("status") == "OK":
        data = base64.b64decode(resp["file_data"])
        with open(f"download_{filename}", "wb") as f:
            f.write(data)
        return True, len(data)
    return False, 0

# Generate dummy file if not exists
def prepare_file(size_mb):
    fname = f"dummy_{size_mb}MB.bin"
    if not os.path.exists(fname):
        with open(fname, "wb") as f:
            f.write(os.urandom(size_mb * 1024 * 1024))
    return fname

def worker_task(_op, fname):
    start = time.time()
    if _op == "upload":
        success = client_upload(fname)
        bytes_transferred = os.path.getsize(fname) if success else 0
    else:
        success, bytes_transferred = client_download(fname)
    elapsed = time.time() - start
    return {"success": success, "time": elapsed, "bytes": bytes_transferred}

def main():
    operation = os.getenv("STRESS_OP", "download")  # "download" or "upload"
    file_size = int(os.getenv("FILE_SIZE_MB", "10"))
    pool_type = os.getenv("CLIENT_POOL_TYPE", "thread")  # "thread" or "process"
    client_count = int(os.getenv("CLIENT_POOL", "1"))

    fname = prepare_file(file_size)

    Executor = ThreadPoolExecutor if pool_type == "thread" else ProcessPoolExecutor

    with Executor(max_workers=client_count) as executor:
        results = list(executor.map(lambda _: worker_task(operation, fname), range(client_count)))

    total_time = sum(r["time"] for r in results)
    total_bytes = sum(r["bytes"] for r in results)
    success_count = sum(1 for r in results if r["success"])
    fail_count = client_count - success_count

    output = {
        "clients": client_count,
        "pool_type": pool_type,
        "operation": operation,
        "file_size_MB": file_size,
        "total_duration_sec": round(total_time, 3),
        "throughput_Bps": int(total_bytes / total_time) if total_time > 0 else 0,
        "successes": success_count,
        "failures": fail_count,
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()