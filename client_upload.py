from client_test import send_command

filename = "dummy_10MB.bin"
with open(filename, "rb") as f:
    data = f.read()

import base64
b64data = base64.b64encode(data).decode()
resp = send_command(f"UPLOAD {filename} {b64data}")
print(resp)
