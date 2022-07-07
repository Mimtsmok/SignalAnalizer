import socket
import time


UDP_IP = input("HOST: ") # 10.191.99.84
UDP_PORT = int(input("PORT: ")) # 4163

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

with open("fake_file.txt", "rb") as file:
    while True:
        if line := file.readline().strip():
            print(line)
            sock.sendto(line, (UDP_IP, UDP_PORT))
            time.sleep(0.5)
        else:
            file.seek(0)
