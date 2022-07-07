import asyncio
import configparser
import os
import re
import select
import tkinter as tk
import winsound
from queue import Queue
from socket import AF_INET, IPPROTO_UDP, SOCK_RAW, socket
from tkinter.messagebox import showinfo
from tkinter.scrolledtext import ScrolledText
from tkinter.ttk import Button, Entry, Label
from tkinter import BooleanVar
from tk_tools import Gauge

import matplotlib.pyplot as plt


class Listener:
    def __init__(self, port: int) -> None:
        # Search regex for dbs
        self.DB_REGEX = r"db=([\d-]+)\(([\d-]+),([\d-]+)\)"

        # Initialize socker for UDP (SOCK_DGRAM)
        self.sock = socket(
            AF_INET,
            SOCK_RAW,
            IPPROTO_UDP
        )

        # Bind the socket to localhost on UDP_PORT
        self.sock.bind(("", port))
        self.sock.setblocking(0)


class Plotter:
    def __init__(self, sma_interval: int, buffer_size: int) -> None:
        # Initialize max and min values
        self.max = 0
        self.min = 100

        # Initialize x, y and SMA
        self.db_sma = Queue(sma_interval)
        self.x = Queue(buffer_size)
        self.y = Queue(buffer_size)

        for i in range(sma_interval):
            self.db_sma.put(0)

        for i in range(buffer_size):
            self.x.put(i - buffer_size + 1)
            self.y.put(0)


class App:
    async def exec(self):
        self.window = Window(asyncio.get_event_loop())
        await self.window.show()


class Window(tk.Tk):
    def __init__(self, loop):
        super().__init__()
        self.loop = loop

        # Initialization of paremeters
        # Read configs drom file
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")

        # Initialize parameters for listener
        self.udp_port = int(self.config["LISTENER"]["UDP_PORT"])

        # Initialize parameters for plotter
        self.beep_interval = int(self.config["PLOTTER"]["BEEP_INTERVAL"])
        self.sma_interval = int(self.config["PLOTTER"]["SMA_INTERVAL"])
        self.buffer_size = int(self.config["PLOTTER"]["BUFFER_SIZE"])

        # Initialize buffer for operating between threads and proceses
        self.buffer = Queue()

        # Configure the root window
        self.title('Signal Analizer')
        self.geometry('720x640')
        self.option_add('*font', '16')
        # self.state('zoomed')

        # Port number
        self.port_label = Label(self, text='Порт: ')
        self.port_entry = Entry()
        self.port_entry.insert(0, self.udp_port)
        self.port_label.grid(row=1, column=1)
        self.port_entry.grid(row=1, column=2)

        # Beep interval
        self.beep_label = Label(self, text='Разнесение звука: ')
        self.beep_entry = Entry()
        self.beep_entry.insert(0, self.beep_interval)
        self.beep_label.grid(row=2, column=1)
        self.beep_entry.grid(row=2, column=2)

        # SMA Interval
        self.sma_label = Label(self, text='Интервал скользящего среднего: ')
        self.sma_entry = Entry()
        self.sma_entry.insert(0, self.sma_interval)
        self.sma_label.grid(row=3, column=1)
        self.sma_entry.grid(row=3, column=2)

        # Buffer size for plotting
        self.buffer_label = Label(self, text='Количество точек на графике: ')
        self.buffer_entry = Entry()
        self.buffer_entry.insert(0, self.buffer_size)
        self.buffer_label.grid(row=4, column=1)
        self.buffer_entry.grid(row=4, column=2)

        # Run Button
        self.button_run = Button(self, text='Запустить')
        self.button_run['command'] = self.run_button
        self.button_run.grid(row=5, column=1)

        # Save Button
        self.button_save = Button(self, text='Сохранить настройки')
        self.button_save['command'] = self.save_button
        self.button_save.grid(row=5, column=2)

        # Stop Button
        self.button_stop = Button(self, text='Остановить')
        self.button_stop['command'] = self.stop_button
        self.button_stop.grid(row=5, column=3)

        # Checkboxes
        self.debug = BooleanVar()
        self.debug_checkbox = tk.Checkbutton(
            self, text='Debug', variable=self.debug)
        self.debug_checkbox.grid(row=6, column=1)

        # Min/Current/Max display
        self.min_label = Label(self, text='Минимум: 100, дБ')
        self.current_label = Label(self, text='Текущее: 0, дБ')
        self.max_label = Label(self, text='Максимум: 0, дБ')
        self.min_label.grid(row=7, column=1)
        self.current_label.grid(row=7, column=2)
        self.max_label.grid(row=7, column=3)

        # Gauge
        self.gauge = Gauge(self, max_value=100.0, divisions=20,
                           red=100, red_low=0, yellow=0, yellow_low=100,
                           width=720, height=480, label='DB', unit='дБ')
        self.gauge.grid(row=8, column=1, columnspan=3)
        self.gauge.set_value(0)

        # Scrolled text
        self.log_output = ScrolledText(self)
        # self.log_output.pack(side='left')
        self.task = None

    async def show(self):
        while True:
            try:
                self.winfo_toplevel().update()
                await asyncio.sleep(.1)
            except Exception as ex:
                os._exit(0)

    @staticmethod
    def beep(num: int, freq: int, dur: int) -> None:
        for i in range(num):
            winsound.Beep(freq, dur)

    def auto_beep(self, min_val: int, avg_value: int, range: int) -> None:
        # Beep on condition
        if avg_value <= min_val:
            self.beep(4, 941, 50)
        elif avg_value < min_val + range:
            self.beep(3, 852, 100)
        elif avg_value < min_val + 2 * range:
            self.beep(2, 770, 200)
        elif avg_value < min_val + 3 * range:
            self.beep(1, 697, 400)
        else:
            self.beep(1, 697, 800)

    async def listen_port(self):
        # On ready to read return socket, timeout = 2 s
        ready = select.select([self.listener.sock], [], [], 0.01)
        if ready[0]:
            # Read data
            raw_data, _ = self.listener.sock.recvfrom(65535)
            try:
                # Decode data
                decoded_data = raw_data[28:].decode("UTF-8")

                if self.debug.get():
                    self.log_output.insert(tk.END, f"{decoded_data}\n")
                    self.log_output.see(tk.END)

                # Find desired value
                db_val = re.search(self.listener.DB_REGEX, decoded_data)

                if db_val:
                    self.buffer.put(int(db_val.group(1)))

            # If can't decode - pass
            except UnicodeDecodeError as ex:
                pass

        await asyncio.sleep(0)

    async def plot(self):
        if not self.buffer.empty():
            # Get lower x and set upper x
            x_lower = self.plotter.x.get()
            x_upper = x_lower + self.buffer_size
            self.plotter.x.put(x_upper)

            # Get unactual value of db and put the new one
            self.plotter.db_sma.get()
            self.plotter.db_sma.put(self.buffer.get())

            # Count SMA
            avg_val = sum(self.plotter.db_sma.queue) / self.sma_interval
            self.current_label.config(text=f"Текущее: {avg_val}, дБ")
            self.gauge.set_value(avg_val)

            # After initializing ques
            if x_upper > self.sma_interval:
                # Beep on condition
                self.auto_beep(self.plotter.min, avg_val, 10)

                # Check min and max
                if avg_val > self.plotter.max:
                    self.plotter.max = avg_val
                    self.gauge._yellow = (avg_val // 5 * 6 - 1) / 100
                    self.max_label.config(
                        text=f"Максимум: {self.plotter.max}, дБ")
                if avg_val < self.plotter.min:
                    self.plotter.min = avg_val
                    self.gauge._yellow_low = (avg_val // 5 * 5) / 100
                    self.min_label.config(
                        text=f"Минимум: {self.plotter.min}, дБ")

                if self.debug.get():
                    # Get lower y and set upper y
                    self.plotter.y.get()
                    self.plotter.y.put(avg_val)

                    # Replot graph
                    plt.cla()
                    plt.grid()
                    plt.xlim([x_lower + 1, x_upper + 1])
                    plt.axhline(y=self.plotter.max, color='r', linestyle='-')
                    plt.axhline(y=self.plotter.min, color='g', linestyle='-')
                    plt.plot(self.plotter.x.queue, self.plotter.y.queue)
                    plt.tight_layout()
                    plt.pause(0.01)

        await asyncio.sleep(0)

    async def iteration(self):
        while True:
            await self.listen_port()
            await self.plot()

    def run_button(self):
        if self.debug.get():
            self.geometry('720x940')
            self.log_output.grid(row=9, column=1, columnspan=3)
        else:
            self.geometry('720x640')
            self.log_output.grid_forget()
        # Initialize parameters for listener
        self.udp_port = int(self.port_entry.get())

        # Initialize parameters for plotter
        self.beep_interval = int(self.beep_entry.get())
        self.sma_interval = int(self.sma_entry.get())
        self.buffer_size = int(self.buffer_entry.get())

        # Processes
        # if not self.listener:
        self.listener = Listener(self.udp_port)
        self.plotter = Plotter(self.sma_interval, self.buffer_size)

        # Run proccesses
        self.task = self.loop.create_task(self.iteration())

    def save_button(self):
        self.config.set("LISTENER", "UDP_PORT", self.port_entry.get())
        self.config.set("PLOTTER", "BEEP_INTERVAL", self.beep_interval.get())
        self.config.set("PLOTTER", "SMA_INTERVAL", self.sma_entry.get())
        self.config.set("PLOTTER", "BUFFER_SIZE",
                        self.buffer_entry.get())

        with open("config.ini", "w") as config_file:
            self.config.write(config_file)

        showinfo(title="Information", message="Saved!")

    def stop_button(self):
        self.task.cancel()
        self.listener.sock.detach()
        self.listener.sock.close()
        plt.close()
        self.log_output.insert(tk.END, "=============== ENDED ===============")


asyncio.run(App().exec())
