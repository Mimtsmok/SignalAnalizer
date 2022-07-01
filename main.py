import re
import socket
import winsound
from queue import Queue

import matplotlib.pyplot as plt

# Set Frequency To 2500 Hertz
frequency = 5500
# Set Duration To 100 ms == 0.1 second
duration = 100  

def beep():
    winsound.Beep(697, 400)

def double_beep():
    winsound.Beep(770, 200)
    winsound.Beep(770, 200)

def triple_beep():
    winsound.Beep(852, 100)
    winsound.Beep(852, 100)
    winsound.Beep(852, 100)

def quadro_beep():
    winsound.Beep(941, 50)
    winsound.Beep(941, 50)
    winsound.Beep(941, 50)
    winsound.Beep(941, 50)


DB_REGEX = r"db=([\d-]+)\(([\d-]+),([\d-]+)\)"
AVG_INTERVAL = 10
BUFFER = 50



UDP_IP = "localhost"
UDP_PORT = 4163 #65432

sock = socket.socket(
    socket.AF_INET,
    socket.SOCK_DGRAM
)

sock.bind((UDP_IP, UDP_PORT))

max = 0
min = 100

dbs = Queue(AVG_INTERVAL)
x = Queue(BUFFER)
y = Queue(BUFFER)

for i in range(AVG_INTERVAL):
    dbs.put(0)

for i in range(BUFFER):
    x.put(0)
    y.put(0)

plt.figure(figsize=(12, 6))
plt.ylim([20, 50])
# plt.show()

i = -1

print("Hello!")

while True:
    msg_received = sock.recv(65535)
    if msg_received.decode("UTF-8") == "":
        break
    else:
        msg = msg_received.decode("UTF-8")
        print(msg)
        db_val = re.search(DB_REGEX, msg)
        if db_val:
            i += 1
            x_lower = x.get()
            x.put(i)
            dbs.get()
            dbs.put(int(db_val.group(1)))
            avg_val = sum(dbs.queue) / AVG_INTERVAL
            y.get()
            y.put(avg_val)

            if avg_val > max:
                max = avg_val
            elif avg_val < min and i > AVG_INTERVAL:
                min = avg_val

            plt.cla()
            plt.xlim([x_lower, i])
            plt.axhline(y=max, color='r', linestyle='-')
            plt.axhline(y=min, color='g', linestyle='-')
            plt.plot(x.queue, y.queue)
            plt.pause(0.3)

            if avg_val < 20:
                quadro_beep()
            elif avg_val < 30:
                triple_beep()
            elif avg_val < 40:
                double_beep()
            else:
                beep()
