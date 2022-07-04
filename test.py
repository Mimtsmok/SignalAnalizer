import asyncio
import configparser
import os
import re
import socket
import tkinter as tk
import winsound
from queue import Queue
from tkinter.messagebox import showinfo
from tkinter.scrolledtext import ScrolledText
from tkinter.ttk import Button, Entry, Label

import matplotlib.pyplot as plt


class Listener:
    def __init__(self, port: int) -> None:
        # Search regex for dbs
        self.DB_REGEX = r"db=([\d-]+)\(([\d-]+),([\d-]+)\)"

        # Initialize socker for UDP (SOCK_DGRAM)
        self.sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        # Bind the socket to localhost on UDP_PORT
        self.sock.bind(('localhost', port))


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
        self.sma_interval = int(self.config["PLOTTER"]["SMA_INTERVAL"])
        self.buffer_size = int(self.config["PLOTTER"]["BUFFER_SIZE"])

        # Initialize buffer for operating between threads and proceses
        self.buffer = Queue()

        # Configure the root window
        self.title('Signal Analizer')
        self.geometry('720x480')
        self.state('zoomed')

        # Port number
        self.port_label = Label(self, text='Порт: ')
        self.port_entry = Entry()
        self.port_entry.insert(0, self.udp_port)
        self.port_label.pack()
        self.port_entry.pack()

        # SMA Interval
        self.sma_label = Label(self, text='Интервал скользящего среднего: ')
        self.sma_entry = Entry()
        self.sma_entry.insert(0, self.sma_interval)
        self.sma_label.pack()
        self.sma_entry.pack()

        # Buffer size for plotting
        self.buffer_label = Label(self, text='Количество точек на графике: ')
        self.buffer_entry = Entry()
        self.buffer_entry.insert(0, self.buffer_size)
        self.buffer_label.pack()
        self.buffer_entry.pack()

        # Run Button
        self.button_run = Button(self, text='Запустить')
        self.button_run['command'] = self.run_button
        self.button_run.pack()

        # Save Button
        self.button_save = Button(self, text='Сохранить настройки')
        self.button_save['command'] = self.save_button
        self.button_save.pack()

        # Stop Button
        self.button_stop = Button(self, text='Остановить')
        self.button_stop['command'] = self.stop_button
        self.button_stop.pack()

        # Scrolled text
        self.log_output = ScrolledText(self, width=720, height=640)
        self.log_output.pack(side='left')
        self.task = None

        # Initialize listener and plotter
        self.listener = None
        self.plotter = None

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

    async def listen_port(self):
        msg_received = self.listener.sock.recv(65535)
        msg = msg_received.decode("UTF-8")
        self.log_output.insert(tk.END, f"{msg}\n")
        self.log_output.see(tk.END)
        db_val = re.search(self.listener.DB_REGEX, msg)
        if db_val:
            self.buffer.put(int(db_val.group(1)))
        await asyncio.sleep(0)

    async def plot(self):
        if not self.buffer.empty():
            # Get lower x and set upper x
            x_lower = self.plotter.x.get()
            x_upper = x_lower + self.buffer_size - 1
            self.plotter.x.put(x_upper)

            # Get unactual value of db and put the new one
            self.plotter.db_sma.get()
            self.plotter.db_sma.put(self.buffer.get())

            # Count SMA
            avg_val = sum(self.plotter.db_sma.queue) / self.sma_interval

            # Get lower y and set upper y
            self.plotter.y.get()
            self.plotter.y.put(avg_val)

            # After initializing ques
            if x_upper > self.sma_interval:
                # Beep on condition
                if avg_val < 20:
                    self.beep(4, 941, 50)
                elif avg_val < 30:
                    self.beep(3, 852, 100)
                elif avg_val < 40:
                    self.beep(2, 770, 200)
                else:
                    self.beep(1, 697, 400)

                # Check min and max
                if avg_val > self.plotter.max:
                    self.plotter.max = avg_val
                if avg_val < self.plotter.min:
                    self.plotter.min = avg_val

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
        # Initialize parameters for listener
        self.udp_port = int(self.port_entry.get())

        # Initialize parameters for plotter
        self.sma_interval = int(self.sma_entry.get())
        self.buffer_size = int(self.buffer_entry.get())

        # Processes
        if not self.listener:
            self.listener = Listener(self.udp_port)
            self.plotter = Plotter(self.sma_interval, self.buffer_size)

        # Run proccesses
        self.task = self.loop.create_task(self.iteration())

    def save_button(self):
        self.config.set("LISTENER", "UDP_PORT", self.port_entry.get())
        self.config.set("PLOTTER", "SMA_INTERVAL", self.sma_entry.get())
        self.config.set("PLOTTER", "BUFFER_SIZE",
                        self.buffer_entry.get())

        with open("config.ini", "w") as config_file:
            self.config.write(config_file)

        showinfo(title="Information", message="Saved!")
    
    def stop_button(self):
        self.task.cancel()


asyncio.run(App().exec())
