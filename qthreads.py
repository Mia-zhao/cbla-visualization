import datetime
import collections

import numpy as np

import threading

from PyQt4.QtCore import *
import pyqtgraph as pg

from cbla_learner import Learner

import simpleTeensyComs

import logging

STATUS_READY = "Ready"
STATUS_RUN = "Running"
STATUS_FINSH = "Finished"
STATUS_CONNECTION_FAIL = "Disconnected"
STATUS_CONNECTION_SUCCESS = "Connected"

TIME_FORMAT = "%Y-%m-%d-%H:%M:%S"

queue_dict = {}
QUEUE_SIZE = 100
devices = None
fade_commands = []

lock = threading.RLock()

MAX_CBLA_DATA_NUM = 50
x = np.linspace(0.0, 50.0, MAX_CBLA_DATA_NUM)
y1 = np.ones(MAX_CBLA_DATA_NUM, dtype=np.int)
y2 = np.zeros(MAX_CBLA_DATA_NUM, dtype=np.float)


# thread debugging
logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-10s) %(message)s',)

''' data object in queue '''
class DataObject(object):
    def __init__(self, byte_str, val):
        self.byte_str = byte_str
        self.val = val

''' represent CBLA internal states '''
#class CBLAStates(object):
    

''' 
    thread is started on connect to Teensy
    continuously send commands and receive data from Teensy
'''
class BackgroundThread(QThread):
    ''' define pyqt signals to communicate with other threads '''
    status = pyqtSignal(str)
    teensy_message = pyqtSignal(str)
    device_ready = pyqtSignal()
    disable_btn_connect = pyqtSignal()

    def __init__(self, main, com_port, com_serial, teensy_serial):
        super(BackgroundThread, self).__init__()
        self.com_port = com_port
        self.com_serial = com_serial
        self.teensy_serial = teensy_serial
        self.teensyComms = None

        main.connect_teensy.connect(self.connect_to_teensy)
        main.disconnect_teensy.connect(self.disconnect_from_teensy)

    def __del__(self):
        self.wait()

    @pyqtSlot()
    def connect_to_teensy(self):
        logging.debug("Connecting Teensy")
        if (self.teensyComms is None):
            try:
                self.teensyComms = simpleTeensyComs.initializeComms(self.com_port)
                self.status.emit(STATUS_CONNECTION_SUCCESS)
                time_stamp = datetime.datetime.now().strftime(TIME_FORMAT)
                msg = "{} Connected to port {}".format(time_stamp, self.com_port)
                self.teensy_message.emit(msg)
                self.disable_btn_connect.emit()
            except Exception as inst:
                self.status.emit(STATUS_CONNECTION_FAIL)
                time_stamp = datetime.datetime.now().strftime(TIME_FORMAT)
                desc = "{} Failed to open port {}\n{} {}".format(time_stamp, self.com_port, 
                    "".ljust(len(time_stamp)), inst.args[0])
                self.teensy_message.emit(desc)
        else:
            if (self.teensyComms.is_open == False):
                self.teensyComms.open()
                self.status.emit(STATUS_CONNECTION_SUCCESS)
                time_stamp = datetime.datetime.now().strftime(TIME_FORMAT)
                msg = "{} Reopened port {}".format(time_stamp, self.com_port)
                self.teensy_message.emit(msg)
                self.disable_btn_connect.emit()

    @pyqtSlot()
    def disconnect_from_teensy(self):
        logging.debug("disconnect signal triggered")
        if (self.teensyComms is not None and self.teensyComms.is_open):
            self.teensyComms.close()
            time_stamp = datetime.datetime.now().strftime(TIME_FORMAT)
            msg = "{} Disconnected from port {}".format(time_stamp, self.com_port)
            self.teensy_message.emit(msg)
            self.status.emit(STATUS_CONNECTION_FAIL)

    def run(self):
        global queue_dict, devices, fade_commands

        while(True):
            # sleep for 50 ms
            self.msleep(50)
            logging.debug("768")
            # sleep 500 ms if teensy connection is not established
            while(self.teensyComms is None):
                self.msleep(500)

            if (self.teensyComms.is_open and devices is None):
                self.get_devices()

            lock.acquire()
            if (len(fade_commands) > 0):
                for fade_command in fade_commands:
                    self.fade_value(fade_command[0], fade_command[1])
                fade_commands = []
            lock.release()

            if (self.teensyComms.is_open and devices is not None):
                for i in range(0,len(devices)):
                    dev = devices[i]
                    port = dev.port
                    if dev.type % 2 == 0:
                        byte_str = dev.genByteStr()
                        val = self.read_value(byte_str)
                        data = DataObject(byte_str, val)
                        lock.acquire()
                        if (byte_str in queue_dict):
                            if (len(queue_dict[byte_str]) == QUEUE_SIZE):
                                queue_dict[byte_str].pop(0)
                            queue_dict[byte_str].append(data)
                        else:
                            queue_dict[byte_str] = [data]
                        logging.debug("current queue size: {}, appending value: {}".format(len(queue_dict[byte_str]), val))
                        lock.release()

    # read sensor/actuator value given peripheral byte string             
    def read_value(self, peripheral_byte_str):
        try:
            logging.debug("reading {}".format(peripheral_byte_str))
            result = simpleTeensyComs.Read(self.teensyComms, self.teensy_serial, self.com_serial, peripheral_byte_str, 0)
            logging.debug("reading success with {}".format(result))
            return result
        except:
            return

    # set actuator value
    def fade_value(self, peripheral_byte_str, val):
        try:
            logging.debug("fading {} with {}".format(peripheral_byte_str, val))
            result = simpleTeensyComs.Fade(self.teensyComms, self.teensy_serial, self.com_serial, peripheral_byte_str, val, 0)
            logging.debug("fading success with {}".format(result))
            return result
        except:
            return

    # get the device list
    def get_devices(self):
        global devices
        devList = None
        try:
            devList = simpleTeensyComs.QueryIDs(self.teensyComms, self.teensy_serial, self.com_serial)
        except ConnectionError as err:
            time_stamp = datetime.datetime.now().strftime(TIME_FORMAT)
            desc = "{} {}".format(time_stamp, err.args[0])
            self.teensy_message.emit(desc)
            self.teensyComms.close()
        if (devList is not None):
            lock.acquire()
            devices = devList
            lock.release()
            self.device_ready.emit()

# performing background plots (plotting sensor/actuator values)
class SensorPlotThread(QThread):
    ''' define pyqt signals to communicate with other threads '''
    add_sensor = pyqtSignal(int, int, int, int, int, int, int)
    add_actuator = pyqtSignal(int, int, int, int, int, int)
    clear_sensor_actuator_list = pyqtSignal()
    update_tab_physical = pyqtSignal()
    update_sensor_plot = pyqtSignal(bytes, int)
    
    # main should be the main GUI
    def __init__(self, main, config={}):
        super(SensorPlotThread, self).__init__()
        self.config = config

    def __del__(self):
        self.wait()

    # continuously update sensor/actuator list
    def run(self):
        global devices, queue_dict

        while (True):
            # sleep for 100 ms
            self.msleep(100)

            # sleep 500 ms if device list is not ready
            while(devices is None):
                self.msleep(500)

            for key, vals in queue_dict.items():
                if (len(vals) > 0):
                    data = queue_dict[key][len(vals) - 1]
                    self.update_sensor_plot.emit(data.byte_str, data.val)
                    logging.debug("Updating sensor value: {}".format(data.val))

    @pyqtSlot()        
    def update_sensor_actuator_list(self):
        global devices
        peripherals = {0:{}}

        for i in range(0,len(devices)):
            dev = devices[i]
            port = dev.port
            if (port not in peripherals[0].keys()):
                peripherals[0][port] = {}
            peripherals[0][port][dev.address] = dev.type

        row = 0
        col = 0
        for n, ports in peripherals.items():
            node = n
            for p, a in ports.items():
                port = p
                num_sens = sum(t % 2 == 0 for t in a.values())
                num_acts = len(a.values()) - num_sens
                for addr, type in a.items():
                    if (type % 2 != 0):
                        self.add_actuator.emit(node, port, addr, type, row, col)
                        col = col + 1

                row = row + 1
                col = 0
                for addr, type in a.items():
                    if (type % 2 == 0):
                        self.add_sensor.emit(node, port, addr, type, row, col, int(num_acts/num_sens))
                        col = col + 1
                row = row + 1
                col = 0
        self.update_tab_physical.emit()

class CBLAThread(QThread):
    update_actuator_val = pyqtSignal(bytes, int)

    def __init__(self, main, config={}):
        super(CBLAThread, self).__init__()
        self.config = config

        main.run_cbla.connect(self.start)

    def __del__(self):
        self.wait()

    def run(self):
        global devices, queue_dict, fade_commands, x, y1, y2

        # sleep 500 ms if device list is not ready
        while(devices is None):
            self.msleep(500)

        numActs = 0
        ActsList = []
        numSens = 0
        SensList = []
        sensValues = []
        actValues = []

        for i in range(0,len(devices)):
            logging.debug(devices[i].pr())
            if devices[i].type%2 == 0:
                numSens += 1
                SensList.append(devices[i])
                sensValues.append(0)
            else:
                numActs += 1
                ActsList.append(devices[i])
                actValues.append(0)

        lrnr = Learner(tuple([0]*numSens),tuple([0]*numActs), **self.config)

        iterNum = 0
        expert_number = 1
        while (True):
            self.msleep(self.config['cycle_time'])
            if iterNum > 0:
                lock.acquire()
                for i in range(0,len(ActsList)):
                    self.update_actuator_val.emit(ActsList[i].genByteStr(), int(actValues[i]))
                    fade_command = (ActsList[i].genByteStr(), int(actValues[i]))
                    fade_commands.append(fade_command)
                    logging.debug("Command Actuator {} to Value {}".format(i, int(actValues[i])))
                lock.release()

            #Sense:  Read all the sensors
            lock.acquire()
            for i in range(0,len(SensList)):
                sens_byte_str = SensList[i].genByteStr()

                if (len(queue_dict[sens_byte_str]) > 0):
                    data = queue_dict[sens_byte_str][len(queue_dict[sens_byte_str]) - 1]
                    sensValues[i] = data.val
                    logging.debug("reading sensor {} value: {}".format(i, data.val))
            lock.release()

            #Learn:
            lrnr.learn(tuple(self.normalize_sens(sensValues,SensList)),tuple(actValues))

            #Select Next action to perform
            actValues = lrnr.select_action()

            numExperts = lrnr.expert.get_num_experts()

            reduced_mean_error = lrnr.expert.rewards_history

            if numExperts > 1:
                expert_number = expert_number + 1
                logging.debug("------------------------------")
                logging.debug("increased expert number")

            if (self.curves is not None and "plot_expert_number" in self.curves):
                y1 = np.append(y1[1:MAX_CBLA_DATA_NUM], expert_number)
                self.curves["plot_expert_number"].setData(x, y1)

            if (self.curves is not None and "plot_prediction_error" in self.curves):
                if (reduced_mean_error is not None):
                    y2 = np.append(y2[1:MAX_CBLA_DATA_NUM], reduced_mean_error)
                self.curves["plot_prediction_error"].setData(x, y2)
            #lock2.release()
            #Report the action value and the number of experts currently in the system
            #print('Current max action value is ', lrnr.expert.get_largest_action_value())
            #print('Current number of experts is', lrnr.expert.get_num_experts())

            iterNum += 1

    def normalize_sens(self, sensValues,SensList):
        normValues = []
        for i in range(0,len(SensList)):
            #for now, scale everything the same, this function can be extended to scale
            #separately based on the device type in the sensors list
            normValues.append(sensValues[i]/1023)

        return normValues