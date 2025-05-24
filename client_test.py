import socket, json

SERVER_ADDR = ("127.0.0.1", 7777)
DELIM = "\r\n\r\n"

def send_command(cmd):
    with socket.socket() as s:
        s.connect(SERVER_ADDR)
        s.sendall((cmd + DELIM).encode())
        buff = ""
        while DELIM not in buff:
            data = s.recv(1024*1024)
            if not data:
                break
            buff += data.decode()
    return json.loads(buff.split(DELIM)[0])

# Test LIST command
print(send_command("LIST"))
