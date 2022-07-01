import configparser
import tkinter as tk
from multiprocessing import Process
from queue import Queue
from threading import Thread
from tkinter.messagebox import showinfo
from tkinter.ttk import Button, Entry, Label

config = configparser.ConfigParser()
config.read("config.ini")

port = config["APP"]["PORT"]
sma_interval = config["APP"]["SMA_INTERVAL"]
buffer_size = config["APP"]["BUFFER_SIZE"]


def port_listener(q_out: Queue):
    while True:
        q_out.put(1)
    # while True:
    #     msg_received = sock.recv(65535)
    #     msg = msg_received.decode("UTF-8")
    #     db_val = re.search(DB_REGEX, msg)


def plotter(q_in: Queue):
    while True:
        if not q_in.empty():
            print(q_in.get())
    pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # Configure the root window
        self.title('Signal Analizer')
        self.geometry('720x480')

        # Port number
        self.port_label = Label(self, text='Порт: ')
        self.port_entry = Entry()
        self.port_entry.insert(0, port)
        self.port_label.grid(row=1, column=1)
        self.port_entry.grid(row=1, column=2)

        # SMA Interval
        self.sma_label = Label(self, text='Интервал скользящего среднего: ')
        self.sma_entry = Entry()
        self.sma_entry.insert(0, sma_interval)
        self.sma_label.grid(row=2, column=1)
        self.sma_entry.grid(row=2, column=2)

        # Buffer size for plotting
        self.buffer_label = Label(self, text='Количество точек на графике: ')
        self.buffer_entry = Entry()
        self.buffer_entry.insert(0, buffer_size)
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

    def run_button(self):
        q = Queue()
        # self.t1 = Thread(target=port_listener, args=(q, ))
        # self.t2 = Thread(target=plotter, args=(q, ))
        self.t1 = Process(target=port_listener, args=(q, ))
        self.t2 = Process(target=plotter, args=(q, ))
        self.t1.start()
        self.t2.start()
        showinfo(title='Information', message="Runned!")

    def save_button(self):
        config.set("APP", "PORT", self.port_entry.get())
        config.set("APP", "SMA_INTERVAL", self.sma_entry.get())
        config.set("APP", "BUFFER_SIZE", self.buffer_entry.get())

        with open("config.ini", "w") as config_file:
            config.write(config_file)

        showinfo(title="Information", message="Saved!")
    
    def on_closing(self):
        # TODO close threads
        print(self.t1)
        if self.t1:
            self.t1.kill()
            self.t2.kill()
        pass


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
