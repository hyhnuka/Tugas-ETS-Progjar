from client_test import send_command
import base64

filename = "dummy_10MB.bin"
resp = send_command(f"GET {filename}")

if resp.get("status") == "OK":
    data = base64.b64decode(resp["file_data"])
    with open(f"download_{filename}", "wb") as f:
        f.write(data)
    print(f"Download berhasil, ukuran file {len(data)} bytes")
else:
    print("Download gagal:", resp)
