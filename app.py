import configparser
import re
import tkinter as tk
import winsound
from multiprocessing import Process
from multiprocessing import Queue as mpq
from queue import Queue
from socket import AF_INET, IPPROTO_UDP, SOCK_RAW, socket
from tkinter.messagebox import showinfo
from tkinter.ttk import Button, Entry, Label

import matplotlib.pyplot as plt


def beep(num: int, freq: int, dur: int) -> None:
    for i in range(num):
        winsound.Beep(freq, dur)


def listen_port(buffer: Queue, port: int):
    # Search regex for dbs
    DB_REGEX = r"db=([\d-]+)\(([\d-]+),([\d-]+)\)"

    # Initialize socker for UDP (SOCK_DGRAM)
    sock = socket(
        AF_INET,
        SOCK_RAW,
        IPPROTO_UDP
    )

    # Bind the socket to localhost on UDP_PORT
    sock.bind(("", port))

    # Start listen
    while True:

        raw_data, _ = sock.recvfrom(65535)

        try:
            decoded_data = raw_data[28:].decode("UTF-8")
            print(decoded_data)

            db_val = re.search(DB_REGEX, decoded_data)

            if db_val:
                buffer.put(int(db_val.group(1)))

        except UnicodeDecodeError as ex:
            print(ex)
            


def plot(buffer: Queue, sma_interval: int, buffer_size: int):
    # Initialize max and min values
    max = 0
    min = 100

    db_sma = Queue(sma_interval)
    x = Queue(buffer_size)
    y = Queue(buffer_size)

    for i in range(sma_interval):
        db_sma.put(0)

    for i in range(buffer_size):
        x.put(i - buffer_size)
        y.put(0)

    while True:
        if not buffer.empty():
            # Get lower x and set upper x
            x_lower = x.get()
            x_upper = x_lower + buffer_size - 1
            x.put(x_upper)

            # Get unactual value of db and put the new one
            db_sma.get()
            db_sma.put(buffer.get())

            # Count SMA
            avg_val = sum(db_sma.queue) / sma_interval

            # Get lower y and set upper y
            y.get()
            y.put(avg_val)

            # After initializing ques
            if x_upper > sma_interval:
                # Beep on condition
                if avg_val < 20:
                    beep(4, 941, 50)
                elif avg_val < 30:
                    beep(3, 852, 100)
                elif avg_val < 40:
                    beep(2, 770, 200)
                else:
                    beep(1, 697, 400)

                # Check min and max
                if avg_val > max:
                    max = avg_val
                elif avg_val < min:
                    min = avg_val
            
            # Replot graph
            plt.cla()
            plt.grid()
            plt.xlim([x_lower, x_upper])
            plt.axhline(y=max, color='r', linestyle='-')
            plt.axhline(y=min, color='g', linestyle='-')
            plt.plot(x.queue, y.queue)
            plt.pause(0.3)


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # Initialization of paremeters
        # Read configs drom file
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")

        # Initialize parameters for listener
        self.udp_port = int(self.config["LISTENER"]["UDP_PORT"])

        # Initialize parameters for plotter
        self.sma_interval = int(self.config["PLOTTER"]["SMA_INTERVAL"])
        self.buffer_size = int(self.config["PLOTTER"]["BUFFER_SIZE"])

        # Initialize buffer for operating between threads and proceses
        self.buffer = mpq()

        # Configure the root window
        self.title('Signal Analizer')
        self.geometry('720x480')

        # Port number
        self.port_label = Label(self, text='Порт: ')
        self.port_entry = Entry()
        self.port_entry.insert(0, self.udp_port)
        self.port_label.grid(row=1, column=1)
        self.port_entry.grid(row=1, column=2)

        # SMA Interval
        self.sma_label = Label(self, text='Интервал скользящего среднего: ')
        self.sma_entry = Entry()
        self.sma_entry.insert(0, self.sma_interval)
        self.sma_label.grid(row=2, column=1)
        self.sma_entry.grid(row=2, column=2)

        # Buffer size for plotting
        self.buffer_label = Label(self, text='Количество точек на графике: ')
        self.buffer_entry = Entry()
        self.buffer_entry.insert(0, self.buffer_size)
        self.buffer_label.grid(row=3, column=1)
        self.buffer_entry.grid(row=3, column=2)

        # Run Button
        self.button = Button(self, text='Запустить')
        self.button['command'] = self.run_button
        self.button.grid(row=4, column=1)

        # Save Button
        self.button = Button(self, text='Сохранить настройки')
        self.button['command'] = self.save_button
        self.button.grid(row=4, column=2)

        # Processes
        self.listener = None
        self.plotter = None

    def run_button(self):
        # Initialize parameters for listener
        self.udp_port = int(self.port_entry.get())

        # Initialize parameters for plotter
        self.sma_interval = int(self.sma_entry.get())
        self.buffer_size = int(self.buffer_entry.get())

        # Run proccesses
        self.listener = Process(
            target=listen_port, args=(self.buffer, self.udp_port))
        self.plotter = Process(target=plot, args=(
            self.buffer, self.sma_interval, self.buffer_size))
        self.listener.start()
        self.plotter.start()

    def save_button(self):
        self.config.set("LISTENER", "UDP_PORT", self.port_entry.get())
        self.config.set("PLOTTER", "SMA_INTERVAL", self.sma_entry.get())
        self.config.set("PLOTTER", "BUFFER_SIZE",
                        self.buffer_entry.get())

        with open("config.ini", "w") as config_file:
            self.config.write(config_file)

        showinfo(title="Information", message="Saved!")

    def on_closing(self):
        if self.listener:
            self.listener.terminate()
            self.plotter.terminate()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
