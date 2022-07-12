import re
from queue import Queue
from socket import AF_INET, IPPROTO_UDP, SOCK_DGRAM, socket
from winsound import Beep

import matplotlib.pyplot as plt


def beep(num: int, freq: int, dur: int) -> None:
    for i in range(num):
        Beep(freq, dur)


def auto_beep(min_val, avg_value, range) -> None:
    # Beep on condition
    if avg_value <= min_val:
        beep(4, 941, 50)
    elif avg_value < min_val + range:
        beep(3, 852, 100)
    elif avg_value < min_val + 2 * range:
        beep(2, 770, 200)
    elif avg_value < min_val + 3 * range:
        beep(1, 697, 400)
    else:
        beep(1, 697, 800)


# Constants
DB_REGEX = r"db=([\d-]+)\(([\d-]+),([\d-]+)\)"
# Inputs
UDP_PORT = 4163  # int(input("PORT: "))
AVG_INTERVAL = 10  # int(input("AVG_INTERVAL: "))
BUFFER = 50  # int(input("BUFFER: "))

plt.figure(figsize=(2, 4))

try:
    # Connection
    UDP_IP = ""

    sock = socket(
        AF_INET,
        SOCK_DGRAM,
        IPPROTO_UDP
    )

    sock.bind((UDP_IP, UDP_PORT))

    # Plot settings
    max = 0
    min = 100

    dbs = Queue(AVG_INTERVAL)
    x = Queue(BUFFER)
    y = Queue(BUFFER)

    for i in range(AVG_INTERVAL):
        dbs.put(0)

    for i in range(BUFFER):
        x.put(i - BUFFER + 1)
        y.put(0)

    while True:
        raw_data, addr = sock.recvfrom(65535)
        try:
            # Print
            decoded_data = raw_data[28:].decode("UTF-8")

            # Compute
            db_val = re.search(DB_REGEX, decoded_data)
            if db_val:
                # X
                x_lower = x.get()
                x_higher = x_lower + BUFFER - 1
                x.put(x_higher)

                # SMA
                dbs.get()
                dbs.put(int(db_val.group(1)))
                avg_val = sum(dbs.queue) / AVG_INTERVAL

                # Y
                y.get()
                y.put(avg_val)

                # # Plot
                plt.cla()
                # plt.grid()
                # plt.xlim([-0.2, 0.2])
                plt.ylim([0, max+5])
                plt.bar(0, avg_val, 2)
                plt.axhline(y=min, color='r', linestyle='--')
                plt.axhline(y=max, color='r', linestyle='--')
                # plt.axhline(y=avg_val, color = 'b', linestyle = '-')

                plt.draw()
                plt.pause(0.01)

                # if x_higher > AVG_INTERVAL:
                if x_higher > AVG_INTERVAL:
                    # Check min and max
                    if avg_val > max:
                        max = avg_val
                    if avg_val < min:
                        min = avg_val

                    auto_beep(min, avg_val, 10)

        except UnicodeDecodeError as ex_dec:
            pass

except Exception as ex:
    print(ex)

input("Press Enter to continue...")
