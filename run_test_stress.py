#!/usr/bin/env python3
import os
import subprocess
import time
import signal
import json
import csv
import sys

# -- Konfigurasi eksperimen --
SERVER_SCRIPTS = {
    "thread":   "multithread_pool.py",
    "process":  "multiprocess_pool.py"
}
SERVER_WORKERS_OPTIONS = [1, 5, 50]       # opsi jumlah worker server
CLIENT_WORKERS_OPTIONS = [1, 5, 50]       # opsi jumlah client pool
OPERATIONS = ["download", "upload"]
FILE_SIZES_MB = [10, 50, 100]
OUTPUT_CSV = "stress_test_results.csv"

PYTHON_CMD = sys.executable  # python interpreter yang dipakai saat ini

def start_server(mode, workers):
    env = os.environ.copy()
    env["WORKER_LIMIT"] = str(workers)
    print(f"Starting server {mode} with {workers} workers...")
    return subprocess.Popen(
        [PYTHON_CMD, SERVER_SCRIPTS[mode]],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

def run_stress_test(operation, size_mb, client_workers):
    env = os.environ.copy()
    env.update({
        "STRESS_OP": operation,
        "FILE_SIZE_MB": str(size_mb),
        "CLIENT_POOL_TYPE": "thread",  # client pool selalu thread, bisa ubah jika perlu
        "CLIENT_POOL": str(client_workers),
    })
    print(f"Running stress test: {operation}, {size_mb}MB, clients={client_workers}...")
    result = subprocess.run(
        [PYTHON_CMD, "stress_test.py"],
        capture_output=True,
        env=env,
        text=True,
        timeout=600  # timeout 10 menit per run, bisa diubah
    )
    if result.returncode != 0:
        raise RuntimeError(f"Stress test failed: {result.stderr.strip()}")
    return json.loads(result.stdout)

def kill_process(proc):
    if proc.poll() is None:  # proses masih jalan
        try:
            # cross platform terminate
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            proc.kill()

def main():
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "No", "Server Model", "Server Workers", "Operation", "File Size MB",
            "Client Workers", "Total Time (s)", "Throughput (Bps)", 
            "Success Clients", "Failed Clients", "Success Server Workers", "Failed Server Workers"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        counter = 1
        for mode in SERVER_SCRIPTS.keys():
            for sw in SERVER_WORKERS_OPTIONS:
                server_proc = start_server(mode, sw)
                # Tunggu server siap (idealnya cek port, ini pakai sleep)
                time.sleep(3)
                
                success_server_workers = 0
                fail_server_workers = 0
                
                for op in OPERATIONS:
                    for size in FILE_SIZES_MB:
                        for cw in CLIENT_WORKERS_OPTIONS:
                            try:
                                result = run_stress_test(op, size, cw)
                            except Exception as e:
                                print(f"Error running stress test: {e}")
                                continue

                            # Menambahkan hitung sukses dan gagal pada server
                            if result.get("successes", 0) > 0:
                                success_server_workers += 1
                            else:
                                fail_server_workers += 1

                            writer.writerow({
                                "No": counter,
                                "Server Model": mode,
                                "Server Workers": sw,
                                "Operation": op,
                                "File Size MB": size,
                                "Client Workers": cw,
                                "Total Time (s)": result.get("total_duration_sec", 0),
                                "Throughput (Bps)": result.get("throughput_Bps", 0),
                                "Success Clients": result.get("successes", 0),
                                "Failed Clients": result.get("failures", 0),
                                "Success Server Workers": success_server_workers,
                                "Failed Server Workers": fail_server_workers
                            })
                            csvfile.flush()
                            print(f"Run {counter} done.")
                            counter += 1

                print(f"Stopping server {mode} with {sw} workers...")
                kill_process(server_proc)
                time.sleep(1)

    print(f"All done{OUTPUT_CSV}")

if __name__ == "__main__":
    main()
