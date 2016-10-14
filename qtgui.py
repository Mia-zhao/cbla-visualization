import numpy as np
import collections

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import pyqtgraph as pg
from enum import Enum

APP_TITLE = "CBLA Visualization"

MENU_HEADER = "Menu"
MENU_CONFIG = "Configurations"
MENU_SENS_ACT = "Sensors/Actuators"
MENU_SENS = "Sensors"
MENU_ACT = "Actuators"
MENU_CBLA = "CBLA"
MENU_ITEMS = [
    (MENU_CONFIG, []),
    (MENU_SENS_ACT, [
        (MENU_SENS, []), 
        (MENU_ACT, [])]),
    (MENU_CBLA, [])]

MESSAGE_READY = "Ready"
MESSAGE_RUN = "Running"
MESSAGE_FINISH = "Finished"

FONT_ARIAL = "Arial"
FONT_SIZE_TITLE = 12
FONT_SIZE_CONFIG = 11
FONT_SIZE_SUBTITLE = 11

MAX_SENSOR_DATA_NUM = 100
INIT_ACTUATOR_VAL = 30

Peripheral = Enum('Peripheral', 'actuator sensor')

class VisualApp(QMainWindow):
    def __init__(self):
        super(VisualApp, self).__init__()
        self.initUI()

    def initUI(self):
        self.central_widget = QWidget()
        self.central_layout = QGridLayout()
        
        self.topleft = QScrollArea()
        self.topleft.setWidget(Configuration(self))
        self.topright = SensorActuator(parent=self)
        
        splitter1 = QSplitter(Qt.Horizontal, parent=self)
        splitter1.addWidget(self.topleft)
        splitter1.addWidget(self.topright)
        splitter1.setStretchFactor(1, 2)
        
        self.bottom = Bottom(self)
        
        splitter2 = QSplitter(Qt.Vertical, parent=self)
        splitter2.addWidget(splitter1)
        splitter2.addWidget(self.bottom)
        splitter2.setStretchFactor(0, 10)
        
        self.central_layout.addWidget(splitter2)

        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)
        
        self.statusBar().showMessage(MESSAGE_READY)
        
        self.setWindowTitle(APP_TITLE)
        
        self.setAttribute(Qt.WA_DeleteOnClose)

class Configuration(QWidget):
    def __init__(self, parent=None):
        super(Configuration, self).__init__(parent)
        self.config = {
            "exploring_rate": 0.1,
            "exploring_rate_range": (0.4, 0.01),
            "exploring_reward_range": (-0.03, 0.004),
            "adapt_exploring_rate": False,
            "reward_smoothing": 1,
            "split_threshold": 40,
            "split_threshold_growth_rate": 1.0,
            "split_lock_count_threshold": 1,
            "split_quality_threshold": 0.0,
            "split_quality_decay": 1.0,
            "mean_error_threshold": 0.0,
            "mean_error": 1.0,
            "action_value": 0.0,
            "learning_rate": 0.25,
            "kga_delta": 10,
            "kga_tau": 30,
            "max_training_data_num": 500,
            "cycle_time": 0.8,
            "serial_number": 141960,
            "COM port": 'COM 7'
        }
        self.init_config_widget()

    def init_config_widget(self):
        layout = QFormLayout()
        
        title = QLabel(MENU_CONFIG)
        title.setFont(QFont(FONT_ARIAL, FONT_SIZE_TITLE, QFont.Bold))
        
        label_connection = QLabel("Connection")
        label_connection.setFont(QFont(FONT_ARIAL, FONT_SIZE_SUBTITLE, QFont.Bold))
        
        com_port = QLineEdit('COM 7')
        com_port.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        com_port.textEdited.connect(self.com_port_changed)
        
        serial_number = QLineEdit('141960')
        serial_number.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        serial_number.textEdited.connect(self.serial_number_changed)
        
        label_learner = QLabel("Learner Configuration")
        label_learner.setFont(QFont(FONT_ARIAL, FONT_SIZE_SUBTITLE, QFont.Bold))
        
        exploring_rate = QLineEdit('0.3')
        exploring_rate.setValidator(QDoubleValidator())
        exploring_rate.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        exploring_rate.textEdited.connect(self.exploring_rate_changed)

        self.adapt_exploring_rate = QCheckBox("Adapt Exploring Rate")
        self.adapt_exploring_rate.setChecked(False)
        self.adapt_exploring_rate.stateChanged.connect(lambda:self.adapt_exploring_rate_changed(self.adapt_exploring_rate))
        self.adapt_exploring_rate.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        
        self.exploring_rate_range = QLineEdit('(0.4, 0.01)')
        self.exploring_rate_range.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        self.exploring_rate_range.textEdited.connect(self.exploring_rate_range_changed)
        
        self.exploring_reward_range = QLineEdit('(-0.03, 0.004)')
        self.exploring_reward_range.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        self.exploring_reward_range.textEdited.connect(self.exploring_reward_range_changed)
        
        label_expert = QLabel("Expert Configuration")
        label_expert.setFont(QFont(FONT_ARIAL, FONT_SIZE_SUBTITLE, QFont.Bold))
        
        reward_smoothing = QLineEdit('1')
        reward_smoothing.setValidator(QDoubleValidator())
        reward_smoothing.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        reward_smoothing.textEdited.connect(self.reward_smoothing_changed)
        
        split_threshold = QLineEdit('40')
        split_threshold.setValidator(QDoubleValidator())
        split_threshold.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        split_threshold.textEdited.connect(self.split_threshold_changed)
        
        split_threshold_growth_rate = QLineEdit('1')
        split_threshold_growth_rate.setValidator(QDoubleValidator())
        split_threshold_growth_rate.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        split_threshold_growth_rate.textEdited.connect(self.split_threshold_growth_rate_changed)
        
        split_lock_count_threshold = QLineEdit('1')
        split_lock_count_threshold.setValidator(QDoubleValidator())
        split_lock_count_threshold.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        split_lock_count_threshold.textEdited.connect(self.split_lock_count_threshold_changed)
        
        split_quality_threshold = QLineEdit('0')
        split_quality_threshold.setValidator(QDoubleValidator())
        split_quality_threshold.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        split_quality_threshold.textEdited.connect(self.split_quality_threshold_changed)
        
        split_quality_decay = QLineEdit('1')
        split_quality_decay.setValidator(QDoubleValidator())
        split_quality_decay.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        split_quality_decay.textEdited.connect(self.split_quality_decay_changed)
        
        mean_error_threshold = QLineEdit('0')
        mean_error_threshold.setValidator(QDoubleValidator())
        mean_error_threshold.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        mean_error_threshold.textEdited.connect(self.mean_error_threshold_changed)
        
        mean_error = QLineEdit('1')
        mean_error.setValidator(QDoubleValidator())
        mean_error.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        mean_error.textEdited.connect(self.mean_error_changed)
        
        action_value = QLineEdit('0')
        action_value.setValidator(QDoubleValidator())
        action_value.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        action_value.textEdited.connect(self.action_value_changed)
        
        learning_rate = QLineEdit('0.25')
        learning_rate.setValidator(QDoubleValidator())
        learning_rate.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        learning_rate.textEdited.connect(self.learning_rate_changed)
        
        kga_delta = QLineEdit('10')
        kga_delta.setValidator(QDoubleValidator())
        kga_delta.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        kga_delta.textEdited.connect(self.kga_delta_changed)
        
        kga_tau = QLineEdit('30')
        kga_tau.setValidator(QDoubleValidator())
        kga_tau.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        kga_tau.textEdited.connect(self.kga_tau_changed)
        
        max_training_data_num = QLineEdit('500')
        max_training_data_num.setValidator(QDoubleValidator())
        max_training_data_num.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        max_training_data_num.textEdited.connect(self.max_training_data_num_changed)
        
        self.exploring_rate_range.setEnabled(False)
        self.exploring_reward_range.setEnabled(False)
        
        label_execution = QLabel("Execution Parameter")
        label_execution.setFont(QFont(FONT_ARIAL, FONT_SIZE_SUBTITLE, QFont.Bold))
        
        cycle_time = QLineEdit('0.8')
        cycle_time.setValidator(QDoubleValidator())
        cycle_time.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        cycle_time.textEdited.connect(self.cycle_time_changed)
        
        layout.addRow(title)
        
        layout.addRow(label_connection)
        layout.addRow("COM Port", com_port)
        layout.addRow("Teensy Serial Number", serial_number)
        
        layout.addRow(label_learner)
        layout.addRow("Exploring Rate", exploring_rate)
        layout.addRow(self.adapt_exploring_rate)
        layout.addRow("Exploring Rate Range", self.exploring_rate_range)
        layout.addRow("Exploring Reward Range", self.exploring_reward_range)
        
        layout.addRow(label_expert)
        layout.addRow("Reward Smoothing", reward_smoothing)
        layout.addRow("Split Threshold", split_threshold)
        layout.addRow("split Threshold Growth Rate", split_threshold_growth_rate)
        layout.addRow("Split Lock Count Threshold", split_lock_count_threshold)
        layout.addRow("Split Quality Threshold", split_quality_threshold)
        layout.addRow("Split Quality Decay", split_quality_decay)
        layout.addRow("Mean Error Threshold", mean_error_threshold)
        layout.addRow("Mean Error", mean_error)
        layout.addRow("Action Value", action_value)
        layout.addRow("Learning Rate", learning_rate)
        layout.addRow("KGA Delta", kga_delta)
        layout.addRow("KGA TAU", kga_tau)
        layout.addRow("Max Training Data Num", max_training_data_num)
        
        layout.addRow(label_execution)
        layout.addRow("Cycle Time", cycle_time)
        
        self.setLayout(layout)

    def com_port_changed(self, val):
        self.config["com_port"] = val

    def serial_number_changed(self, val):
        self.config["serial_number"] = val

    def adapt_exploring_rate_changed(self, checkbox):
        isAdapt = checkbox.isChecked()
        self.exploring_rate_range.setEnabled(isAdapt)
        self.exploring_reward_range.setEnabled(isAdapt)
        
        self.config["adapt_exploring_rate"] = isAdapt

    def exploring_rate_range_changed(self, val):
        valRange = val.replace("(", "").replace(")", "").split(",")
        if (len(valRange) > 1):
            minVal = float(valRange[0].replace(" ", ""))
            maxVal = float(valRange[1].replace(" ", ""))
            self.config["exploring_rate_range"] = (minVal, maxVal)

    def exploring_reward_range_changed(self, val):
        valRange = val.replace("(", "").replace(")", "").split(",")
        if (len(valRange) > 1):
            minVal = float(valRange[0].replace(" ", ""))
            maxVal = float(valRange[1].replace(" ", ""))
            self.config["exploring_reward_range"] = (minVal, maxVal)

    def exploring_rate_changed(self, val):
        self.config["exploring_rate"] = val
        
    def reward_smoothing_changed(self, val):
        self.config["reward_smoothing"] = val

    def split_threshold_changed(self, val):
        self.config["split_threshold"] = val

    def split_threshold_growth_rate_changed(self, val):
        self.config["split_threshold_growth_rate"] = val

    def split_quality_threshold_changed(self, val):
        self.config["split_quality_threshold"] = val

    def split_lock_count_threshold_changed(self, val):
        self.config["split_lock_count_threshold"] = val
        
    def split_quality_decay_changed(self, val):
        self.config["split_quality_decay"] = val

    def mean_error_threshold_changed(self, val):
        self.config["mean_error_threshold"] = val

    def mean_error_changed(self, val):
        self.config["mean_error"] = val
        
    def action_value_changed(self, val):
        self.config["action_value"] = val

    def learning_rate_changed(self, val):
        self.config["learning_rate"] = val

    def kga_delta_changed(self, val):
        self.config["kga_delta"] = val

    def kga_tau_changed(self, val):
        self.config["kga_tau"] = val

    def max_training_data_num_changed(self, val):
        self.config["max_training_data_num"] = val

    def cycle_time_changed(self, val):
        self.config["cycle_time"] = val

class SensorActuator(QWidget):
    def __init__(self, parent=None):
        super(SensorActuator, self).__init__(parent)
        self.init_sensor_actuator_widget()

    def init_sensor_actuator_widget(self):
        layout = QVBoxLayout()
        
        label_sens_act = QLabel("Sensors and Actuators")
        label_sens_act.setFont(QFont(FONT_ARIAL, FONT_SIZE_TITLE, QFont.Bold))
        
        tab_widget = QTabWidget(self)
        
        self.tab_physical = QWidget(tab_widget)
        self.tab_virtual = VirtualBehavior(tab_widget)
        
        tab_widget.addTab(self.tab_physical, "Physical")
        tab_widget.addTab(self.tab_virtual, "Virtual")
        
        self.init_physical_tab()
        self.init_virtual_tab()
        
        layout.addWidget(label_sens_act)
        layout.addWidget(tab_widget)
        
        self.setLayout(layout)

    def add_sensor_actuator(self, peripheral_map):
        layout = QGridLayout()
        
        row = 0
        column = 0
        if peripheral_map is not None:
            for n, ports in peripheral_map.items():
                node = n
                for p, a in ports.items():
                    port = p
                    num_acts = sum(t == Peripheral.actuator for t in a.values())
                    num_sens = sum(t == Peripheral.sensor for t in a.values())
                    for addr, type in a.items():
                        if (type == Peripheral.actuator):
                            act = Actuator(node, port, addr, self.tab_physical)
                            layout.addWidget(act, row, column)
                            column = column + 1
                    
                    row = row + 1
                    column = 0
                    for addr, type in a.items():
                        if (type == Peripheral.sensor):
                            sens = Sensor(node, port, addr, self.tab_physical)
                            layout.addWidget(sens, row, column, 1, int(num_acts / num_sens))
                            column = column + 1
                    column = 0
        
        self.tab_physical.setLayout(layout)

    def init_physical_tab(self):
        pass
        

    def init_virtual_tab(self):
        pass

class VirtualBehavior(QWidget):
    def __init__(self, parent=None):
        super(VirtualBehavior, self).__init__(parent)
        pass

class Sensor(QWidget):
    def __init__(self, node, port, addr, parent=None):
        super(Sensor, self).__init__(parent)
        
        self.node = node
        self.port = port
        self.addr = addr
        
        self.curve = None
        self.x = np.linspace(0.0, 10.0, MAX_SENSOR_DATA_NUM)
        self.y = np.zeros(MAX_SENSOR_DATA_NUM, dtype=np.float)
        self.data = collections.deque([0.0]*MAX_SENSOR_DATA_NUM, MAX_SENSOR_DATA_NUM)
        
        self.init_sensor_widget()

    def init_sensor_widget(self):
        layout = QGridLayout()
        
        label_node = QLabel("Node: {}".format(self.node))
        label_node.setFont(QFont(FONT_ARIAL, FONT_SIZE_SUBTITLE, QFont.Bold))
        
        label_port = QLabel("Port: {}".format(self.port))
        label_port.setFont(QFont(FONT_ARIAL, FONT_SIZE_SUBTITLE, QFont.Bold))
        
        label_addr = QLabel("Address: {}".format(self.addr))
        label_addr.setFont(QFont(FONT_ARIAL, FONT_SIZE_SUBTITLE, QFont.Bold))
        
        plot = pg.PlotWidget(title="Sensor Reading")
        
        plot.setLabel("bottom", text="Sample")
        plot.setLabel("left", text="Sensor Value")
        plot.setXRange(0, 10)
        plot.setYRange(0, 5000)
        
        plot.showGrid(x=True, y=True)
        
        self.curve = plot.plot(self.x, self.y, pen=(255,0,0))
        
        layout.addWidget(label_node, 0, 0)
        layout.addWidget(label_port, 0, 1)
        layout.addWidget(label_addr, 0, 2)
        layout.addWidget(plot, 1, 0, 1, 3)
        
        #self.setStyleSheet('Sensor{border: 2px solid black;}')
        
        self.setLayout(layout)

class Actuator(QWidget):
    def __init__(self, node, port, addr, parent = None):
        super(Actuator, self).__init__(parent)
        
        self.node = node
        self.port = port
        self.addr = addr
        
        self.init_actuator_widget()

    def init_actuator_widget(self):
        layout = QGridLayout()
        
        label_node = QLabel("Node: {}".format(self.node))
        label_node.setFont(QFont(FONT_ARIAL, FONT_SIZE_SUBTITLE, QFont.Bold))
        
        label_port = QLabel("Port: {}".format(self.port))
        label_port.setFont(QFont(FONT_ARIAL, FONT_SIZE_SUBTITLE, QFont.Bold))
        
        label_addr = QLabel("Address: {}".format(self.addr))
        label_addr.setFont(QFont(FONT_ARIAL, FONT_SIZE_SUBTITLE, QFont.Bold))
        
        self.label_value = QLabel("{}".format(INIT_ACTUATOR_VAL))
        self.label_value.setFont(QFont(FONT_ARIAL, FONT_SIZE_SUBTITLE, QFont.Bold))
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(255)
        self.slider.setValue(INIT_ACTUATOR_VAL)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.valueChanged.connect(self.slider_value_changed)
        self.slider.setTickInterval(5)
        
        layout.addWidget(label_node, 0, 0)
        layout.addWidget(label_port, 0, 1)
        layout.addWidget(label_addr, 0, 2)
        layout.addWidget(self.label_value, 1, 0)
        layout.addWidget(self.slider, 1, 1, 1, 3)
        
        self.setLayout(layout)

    def slider_value_changed(self):
        self.label_value.setText("{}".format(self.slider.value()))

class Bottom(QWidget):
    def __init__(self, parent=None):
        super(Bottom, self).__init__(parent)
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        
        self.log = QTextEdit()
        
        btn_layout = QHBoxLayout()
        
        self.btn_run = QPushButton("Run")
        self.btn_run.clicked.connect(self.run)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.cancel)
        
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.btn_run)
        btn_layout.addWidget(self.btn_cancel)
        
        self.layout.addWidget(self.log)
        self.layout.addLayout(btn_layout)
        
        self.setLayout(self.layout)

    def run(self):
        pass

    def cancel(self):
        pass