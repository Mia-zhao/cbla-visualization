from datetime import datetime
import random
import time
from serial.tools import list_ports

import simpleTeensyComs
from pymongo import MongoClient

import numpy as np

import math

import matplotlib
matplotlib.use('TkAgg')

from numpy import arange, sin, pi
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.backend_bases import key_press_handler

import matplotlib.pyplot as plt
import matplotlib.animation as animation

from matplotlib.figure import Figure
import argparse
import time
import math

import sys
if sys.version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk

NUM_LED_PER_DEVICE = 3
NUM_DEVICE = 6

SLEEP_LENGTH = 1
MAX_DATA_POINTS = 100

parser = argparse.ArgumentParser(description='Start a simple logging process using random outputs and logging the inputs.')
parser.add_argument('--teensy', dest='teensy', type=str, help='The Teensy serial numbers.', nargs='+')
parser.add_argument('comp_serial', type=int, help='The computers serial number for the purposes of simulation [22222]',
                   default=simpleTeensyComs.cbla_pc_id, nargs='?' )
parser.add_argument('grasshopper_serial', type=int, help='The Grasshopper nodes serial number for the purposes of simulation [33333]',
                   default=simpleTeensyComs.udp_node_id, nargs='?' )

args = parser.parse_args()

class DevicePage(tk.Frame):
    def __init__(self, deviceNum, master=None):
        super().__init__(master)
        self.pack()

        self.deviceNum = deviceNum
        if (deviceNum == 1):
            self.p = Proximity(args)
        else:
            self.p = None

        self.data = [0] * MAX_DATA_POINTS
        self.is_running = False
        self.figure, self.ax = plt.subplots()        
        self.ax.set_ylim(0, 4000)
        self.line, = self.ax.plot(range(MAX_DATA_POINTS), self.data)
        self.act_vals = []
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

        self.led_labels = [tk.Label(left) for i in range(0, NUM_LED_PER_DEVICE)]
        self.led_sliders = [tk.Scale(left) for i in range(0, NUM_LED_PER_DEVICE)]
        self.var_labels = [tk.Label(left) for i in range(0, NUM_LED_PER_DEVICE)]
        self.var = [tk.DoubleVar() for i in range(0, NUM_LED_PER_DEVICE)]
        for i in range(0, NUM_LED_PER_DEVICE):
            led_label = self.led_labels[i]
            led_label["text"] = "LED " + str(i + 1)
            led_label["font"] = ("Arial", "13")
            led_label.pack(expand=True, fill="both", side="top")

            led_slider = self.led_sliders[i]
            led_slider["orient"] = "horizontal"
            led_slider["from_"] = 0
            led_slider["to"] = 255
            led_slider.pack(expand=True, fill="both", side="top")

            var_label = self.var_labels[i]
            var_label["text"] = "Current Actuator Value: " + str(self.var[i].get())
            var_label["font"] = ("Arial", "12", "bold")
            var_label.pack(expand=True, fill="both", side="top")

        btn_send = tk.Button(left)
        btn_send["text"] = "send"
        btn_send["font"] = ("Arial", "12")
        btn_send["command"] = self.send_command
        btn_send.pack(expand=True, side="top")
        return left

    def send_command(self):
        for i in range(0, NUM_LED_PER_DEVICE):
            self.act_vals[i] = self.var[i].get()
        if (self.p is not None):
            self.simple_logger_loop(self.act_vals)

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
        start = datetime.now()
        val = self.p.simple_logger_loop()
        end = datetime.now()
        self.p.loop_count += 1
        for i in range(0, len(self.var_labels)):
            self.var_labels[i]["text"] = "Current Actuator Value: " + str(val[2+i])
        print('Looped %d times...Loop took %s' %(self.p.loop_count, str(end-start)))
        self.data.append(val[1])
        self.line.set_ydata(self.data)  # update the data
        return self.line,
 
    def init(self):
        return self.line,

    def run(self):
        if (self.is_running == False):
            self.is_running = True
            self.lift()
            ani = animation.FuncAnimation(self.figure, self.animate, interval=10, blit=False, init_func=self.init)
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

class Proximity:
    def __init__(self, args):
        self.serials = []
        self.origin = -1
        self.teensyComs = []
        self.actuators = {}
        self.sensors = {}
        self.db = None
        self.loop_count = 0
        self.simple_logger_setup(args)

    def simple_logger_setup(self, args):
        print(args)

        # Unpack the input arguments
        self.serials = args.teensy
        self.origin = args.comp_serial
        Grasshopper = args.grasshopper_serial
        # A Dict of the communications in the form of SERIAL_NUMBER: CONNECTION
        print( self.map_ports(self.serials) )
        portmap = self.map_ports(self.serials)
        self.teensyComms = dict([(sn, simpleTeensyComs.initializeComms(portmap[sn])) for sn in portmap])

        for sn in self.teensyComms:
            # Set up the Teensy communications
            numDevices = simpleTeensyComs.QueryNumDevices(self.teensyComms[sn], sn, self.origin)
            print('The teensy has', numDevices, 'devices')
            devices = simpleTeensyComs.QueryIDs(self.teensyComms[sn], sn, self.origin)

            self.sensors[sn] = {}
            self.actuators[sn] = {}

            for i in range(len(devices)):
                print(devices[i].pr())
                if devices[i].type%2 == 0:
                    self.sensors[sn][devices[i]] = 0
                else:
                    self.actuators[sn][devices[i]] = 0
        # Set up the database
        client = MongoClient()
        self.db = client.USBStressTest

    def map_ports(self, serials):
        '''Map ports to serial number listings

        :type serials: List of serial numbers
        :return: Dictionary of port mappings {serialNumber:port}
        
        :todo: Is this cross-platform friendly?
        '''
        port_mapping = {}
        for port, pname, desc in list_ports.comports():
            if desc.split()[0] == 'USB':
                snr = desc.split()[2].split('=')[1][:-1]
                
                port_mapping[int(snr)] = port
                
        return port_mapping

    def shutdown(self):
        for sn in self.teensyComms:
            for self.actuator in self.actuators[sn]:
                simpleTeensyComs.Fade(self.teensyComms[sn], sn, self.origin, self.actuator.genByteStr(), 0, 0)

    def simple_logger_loop(self, act_vals = None):
        values = []
        readings = []

        for sn in self.teensyComms:

            for sensor in self.sensors[sn]:
                self.sensors[sn][sensor] = simpleTeensyComs.Read(self.teensyComms[sn], sn, self.origin, sensor.genByteStr(), 0)

                self.db.readings.insert_one({
                    'datetime': datetime.now(),
                    'teensy_serial': sn,
                    'address': sensor.address,
                    'type': sensor.type,
                    'port': sensor.port,
                    'value': self.sensors[sn][sensor],
                })

                readings.append(self.sensors[sn][sensor])
        
        print('Sens: ' + str(readings))

        act_val = 0
        if readings[0] > 1500:
            act_val = int(10 + 0.01 * readings[0])
        for sn in self.teensyComms:
            print("................")
            print(self.actuators[sn])
            for actuator in self.actuators[sn]:
                self.actuators[sn][actuator] = act_val
                if (act_vals is not None and len(act_vals) == 0 and act_val == 0):
                    self.actuators[sn][actuator] = act_vals[0]
                simpleTeensyComs.Fade(self.teensyComms[sn], sn, self.origin, actuator.genByteStr(), int(self.actuators[sn][actuator]),0)

                self.db.readings.insert_one({
                    'datetime': datetime.now(),
                    'teensy_serial': sn,
                    'address': actuator.address,
                    'type': actuator.type,
                    'port': actuator.port,
                    'value': self.actuators[sn][actuator],
                })

                values.append(self.actuators[sn][actuator])

        print('Acts: ' + str(values))
        return [self.loop_count, readings[0]] + values
    
    def port_serial_type(self, port_serial_string):
        serial, port = port_serial_string.split(',')
        serial = int(serial)
        
        return (serial, port,)

    def get_distance(self, val):
        volt = val * 0.0048828125
        return 65 * math.pow(volt, -1.10)
 
root = tk.Tk()
main = MainPage(root)
main.pack(side="top", fill="both", expand=True)
root.wm_geometry("400x400")
root.mainloop()