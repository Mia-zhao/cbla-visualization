import matplotlib
matplotlib.use('TkAgg')

from numpy import arange, sin, pi
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.backend_bases import key_press_handler

import matplotlib.pyplot as plt
import matplotlib.animation as animation

from matplotlib.figure import Figure

import time
import math

import sys
if sys.version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk

NUM_LED_PER_DEVICE = 3
NUM_DEVICE = 6
MAX_DATA_POINTS = 100

class DevicePage(tk.Frame):
    def __init__(self, deviceNum, master=None):
        super().__init__(master)
        self.pack()

        self.deviceNum = deviceNum

        self.data = [0] * MAX_DATA_POINTS
        self.is_running = False
        self.figure, self.ax = plt.subplots()        
        self.ax.set_ylim(-1, 1)
        self.line, = self.ax.plot(range(MAX_DATA_POINTS), self.data)

        self.create_widgets()

    def create_widgets(self):
        self.left = self.create_led_widgets()
        self.right = self.create_canvas()

    def create_led_widgets(self):
        left = tk.Frame(self)
        left.pack(expand=True, fill="both", side="left")

        device_label = tk.Label(left)
        device_label["text"] = text="Device " + str(self.deviceNum)
        device_label["font"] = ("Arial", "16", "bold")
        device_label.pack(side="top", expand=True, fill="both")

        for i in range(0, NUM_LED_PER_DEVICE):
            led_label = tk.Label(left)
            led_label["text"] = "LED " + str(i + 1)
            led_label["font"] = ("Arial", "13")
            led_label.pack(expand=True, fill="both", side="top")

            led_slider = tk.Scale(left)
            led_slider["orient"] = "horizontal"
            led_slider["from_"] = 0
            led_slider["to"] = 255
            led_slider.pack(expand=True, fill="both", side="top")

            #val_label = tk.Label(left)
            #val_label["text"] = "Current Value: " + str(self.var[i].get())

        btn_send = tk.Button(left)
        btn_send["text"] = "send"
        btn_send["font"] = ("Arial", "12")
        btn_send.pack(expand=True, side="top")
        return left

    def create_canvas(self):
        right = tk.Frame(self)
        right.pack(side="right")

        canvas_label = tk.Label(right)
        canvas_label["text"] = "Sensor Reading"
        canvas_label["font"] = ("Arial", "16")
        canvas_label.pack(expand=True, fill="both", side="top")

        self.canvas = FigureCanvasTkAgg(self.figure, master=right)

        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
        return right

    def get_data1(self):
        ts = time.time()
        return math.sin(ts * 16)

    def animate(self, i):
        self.data.pop(0)
        self.data.append(self.get_data1())
        self.line.set_ydata(self.data)  # update the data
        return self.line,
 
    def init(self):
        return self.line,

    def run(self):
        if (self.is_running == False):
            self.is_running = True
            self.lift()
            ani = animation.FuncAnimation(self.figure, self.animate, interval=30, blit=False, init_func=self.init)
            self.canvas.show()
        else:
            self.lift()

class MainPage(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)

        self.pages = []
        for i in range(0, NUM_DEVICE):
            page = DevicePage(i + 1, self)
            self.pages.append(page)

        buttonframe = tk.Frame(self)
        container = tk.Frame(self)
        buttonframe.pack(side="top", fill="x", expand=False)
        container.pack(side="top", fill="both", expand=True)

        for page in self.pages:
            page.place(in_=container, x=0, y=0, relwidth=1, relheight=1)

        for i in range(0, len(self.pages)):
            b = tk.Button(buttonframe)
            b["text"] = "Device Page " + str(i + 1)
            b["command"] = self.pages[i].run
            b.pack(side="left")

root = tk.Tk()
main = MainPage(root)
main.pack(side="top", fill="both", expand=True)
root.wm_geometry("400x400")
root.mainloop()