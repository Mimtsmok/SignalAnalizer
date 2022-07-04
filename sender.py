import socket
import time


UDP_IP = "localhost"
UDP_PORT = 4163

# byte_message = bytes("Hello, World!", "utf-8")
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

with open("fake_file.txt", "rb") as file:
    while True:
        if line := file.readline().strip():
            print(line)
            sock.sendto(line, (UDP_IP, UDP_PORT))
            time.sleep(0.5)
        else:
            file.seek(0)
