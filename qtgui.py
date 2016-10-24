import collections
import numpy as np
import pyqtgraph as pg

import qthreads

from PyQt4.QtGui import *
from PyQt4.QtCore import *

APP_TITLE = "CBLA Visualization"
PLOT_TITLE = "CBLA Plots"

MENU_CONFIG = "Configurations"

FONT_ARIAL = "Arial"
FONT_SIZE_TITLE = 12
FONT_SIZE_CONFIG = 11
FONT_SIZE_SUBTITLE = 11

MAX_SENSOR_DATA_NUM = 100
INIT_ACTUATOR_VAL = 30

COLOR_ACTIVE = QColor("black")
COLOR_INACTIVE = QColor("red")

class VisualApp(QMainWindow):
    ''' define pyqt signals to communicate with other threads '''
    # signals to notify teensy connect/disconnect (emitted on button clicks)
    connect_teensy = pyqtSignal()
    disconnect_teensy = pyqtSignal()
    run_cbla = pyqtSignal()

    def __init__(self):
        super(VisualApp, self).__init__()

        # initialize UI
        self.initUI()

        self.bgthread = qthreads.BackgroundThread(self)

        self.sensorPlot = qthreads.SensorPlotThread(self)

        self.cblathread = qthreads.CBLAThread(self)

        # message signal at log widget
        self.bgthread.teensy_message.connect(self.message)

        # update main window status
        self.bgthread.status.connect(self.update_status)

        # disable connect button
        self.bgthread.disable_btn_connect.connect(self.disable_btn_connect)

        # update device list when devices are detected
        self.bgthread.device_ready.connect(self.sensorPlot.update_sensor_actuator_list)

        # clear sensor/actuator list
        self.sensorPlot.clear_sensor_actuator_list.connect(self.clear_sensor_actuator_list)

        # update handle sensor/actuator widget
        self.sensorPlot.add_sensor.connect(self.add_sensor)
        self.sensorPlot.add_actuator.connect(self.add_actuator)

        # update sensor/actuator layout
        self.sensorPlot.update_tab_physical.connect(self.update_tab_physical)

        # update sensor plot
        self.sensorPlot.update_sensor_plot.connect(self.update_sensor_plot)

        # update actuator slider
        self.cblathread.update_actuator_val.connect(self.update_actuator_slider)

        self.bgthread.start()

        self.sensorPlot.start()

    def initUI(self):
        self.central_widget = QWidget()
        self.central_layout = QGridLayout()

        self.topleft = QScrollArea()
        self.topleft.setWidget(Configuration(self))
        self.topleft.setMinimumWidth(self.topleft.widget().sizeHint().width() + 50)

        self.topright = SensorActuator(self)

        self.splitter1 = QSplitter(Qt.Horizontal, parent=self)
        self.splitter1.addWidget(self.topleft)
        self.splitter1.addWidget(self.topright)
        self.splitter1.setStretchFactor(1, 2)
        
        handle = self.splitter1.handle(1)
        button_splitter = QToolButton(handle)
        button_splitter.setArrowType(Qt.LeftArrow)
        button_splitter.clicked.connect(self.handle_splitter)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(button_splitter)
        handle.setLayout(layout)

        self.bottom = Bottom(self)

        splitter2 = QSplitter(Qt.Vertical, parent=self)
        splitter2.addWidget(self.splitter1)
        splitter2.addWidget(self.bottom)
        splitter2.setStretchFactor(0, 10)

        self.central_layout.addWidget(splitter2)

        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

        self.update_status(qthreads.STATUS_READY)

        self.setWindowTitle(APP_TITLE)

        self.setAttribute(Qt.WA_DeleteOnClose)

    # collapse/expand configuration panel
    def handle_splitter(self):
        if (not all(self.splitter1.sizes())):
            self.splitter1.setSizes([1, 1])
        else:
            self.splitter1.setSizes([0, 1])

    # adding log message to log text box
    def message(self, desc):
        self.bottom.log.append(desc)

    # update status at status bar
    def update_status(self, status):
        self.statusBar().showMessage(status)

    # disable connect button
    def disable_btn_connect(self):
        self.bottom.btn_connect.setEnabled(False)

    # clear all actuators and sensors
    def clear_sensor_actuator_list(self):
        self.topright.actuators = []
        self.topright.sensors = []

    # update actuator/sensor tab
    def update_tab_physical(self):
        self.topright.tab_physical.setWidget(self.topright.tab_physical_content)

    # add sensor to layout
    def add_sensor(self, node, port, addr, type, row, col, colspan):
        layout = self.topright.tab_physical_content.layout()
        sensor = Sensor(node, port, addr, type, self.topright.tab_physical)
        layout.addWidget(sensor, row, col, 1, colspan)

        self.topright.sensors.append(sensor)

    # add actuator to layout
    def add_actuator(self, node, port, addr, type, row, col):
        layout = self.topright.tab_physical_content.layout()
        actuator = Actuator(node, port, addr, type, self.topright.tab_physical)
        layout.addWidget(actuator, row, col)

        self.topright.actuators.append(actuator)

    # update value of actuator slider
    def update_actuator_slider(self, byte_str, val):
        for actuator in self.topright.actuators:
            if (actuator.byte_str == byte_str):
                actuator.slider.setValue(val)

    # update value of sensor plot
    def update_sensor_plot(self, byte_str, val):
        for sensor in self.topright.sensors:
            if (sensor.byte_str == byte_str):
                sensor.data.append(val)
                sensor.y[:] = sensor.data
                if(sensor.curve is not None):
                    sensor.curve.setData(sensor.x, sensor.y)

class Configuration(QWidget):
    def __init__(self, main=None):
        super(Configuration, self).__init__()
        self.init_config_widget()
        self.main = main

    def init_config_widget(self):
        layout = QFormLayout()

        title = QLabel(MENU_CONFIG)
        title.setFont(QFont(FONT_ARIAL, FONT_SIZE_TITLE, QFont.Bold))

        label_connection = QLabel("Connection")
        label_connection.setFont(QFont(FONT_ARIAL, FONT_SIZE_SUBTITLE, QFont.Bold))

        com_port = QLineEdit(str(qthreads.config['com_port']))
        com_port.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        com_port.textEdited.connect(self.com_port_changed)

        serial_number = QLineEdit(str(qthreads.config['serial_number']))
        serial_number.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        serial_number.textEdited.connect(self.serial_number_changed)

        label_learner = QLabel("Learner Configuration")
        label_learner.setFont(QFont(FONT_ARIAL, FONT_SIZE_SUBTITLE, QFont.Bold))

        exploring_rate = QLineEdit(str(qthreads.config['exploring_rate']))
        exploring_rate.setValidator(QDoubleValidator())
        exploring_rate.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        exploring_rate.textEdited.connect(self.exploring_rate_changed)

        self.adapt_exploring_rate = QCheckBox(str(qthreads.config['adapt_exploring_rate']))
        self.adapt_exploring_rate.setChecked(False)
        self.adapt_exploring_rate.stateChanged.connect(lambda:self.adapt_exploring_rate_changed(self.adapt_exploring_rate))
        self.adapt_exploring_rate.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))

        self.exploring_rate_range = QLineEdit(str(qthreads.config['exploring_rate_range']))
        self.exploring_rate_range.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        self.exploring_rate_range.textEdited.connect(self.exploring_rate_range_changed)

        self.exploring_reward_range = QLineEdit(str(qthreads.config['exploring_reward_range']))
        self.exploring_reward_range.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        self.exploring_reward_range.textEdited.connect(self.exploring_reward_range_changed)

        label_expert = QLabel("Expert Configuration")
        label_expert.setFont(QFont(FONT_ARIAL, FONT_SIZE_SUBTITLE, QFont.Bold))

        reward_smoothing = QLineEdit(str(qthreads.config['reward_smoothing']))
        reward_smoothing.setValidator(QDoubleValidator())
        reward_smoothing.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        reward_smoothing.textEdited.connect(self.reward_smoothing_changed)

        split_threshold = QLineEdit(str(qthreads.config['split_threshold']))
        split_threshold.setValidator(QDoubleValidator())
        split_threshold.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        split_threshold.textEdited.connect(self.split_threshold_changed)

        split_threshold_growth_rate = QLineEdit(str(qthreads.config['split_threshold_growth_rate']))
        split_threshold_growth_rate.setValidator(QDoubleValidator())
        split_threshold_growth_rate.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        split_threshold_growth_rate.textEdited.connect(self.split_threshold_growth_rate_changed)

        split_lock_count_threshold = QLineEdit(str(qthreads.config['split_lock_count_threshold']))
        split_lock_count_threshold.setValidator(QDoubleValidator())
        split_lock_count_threshold.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        split_lock_count_threshold.textEdited.connect(self.split_lock_count_threshold_changed)

        split_quality_threshold = QLineEdit(str(qthreads.config['split_quality_threshold']))
        split_quality_threshold.setValidator(QDoubleValidator())
        split_quality_threshold.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        split_quality_threshold.textEdited.connect(self.split_quality_threshold_changed)

        split_quality_decay = QLineEdit(str(qthreads.config['split_quality_decay']))
        split_quality_decay.setValidator(QDoubleValidator())
        split_quality_decay.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        split_quality_decay.textEdited.connect(self.split_quality_decay_changed)

        mean_error_threshold = QLineEdit(str(qthreads.config['mean_error_threshold']))
        mean_error_threshold.setValidator(QDoubleValidator())
        mean_error_threshold.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        mean_error_threshold.textEdited.connect(self.mean_error_threshold_changed)

        mean_error = QLineEdit(str(qthreads.config['mean_error']))
        mean_error.setValidator(QDoubleValidator())
        mean_error.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        mean_error.textEdited.connect(self.mean_error_changed)

        action_value = QLineEdit(str(qthreads.config['action_value']))
        action_value.setValidator(QDoubleValidator())
        action_value.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        action_value.textEdited.connect(self.action_value_changed)

        learning_rate = QLineEdit(str(qthreads.config['learning_rate']))
        learning_rate.setValidator(QDoubleValidator())
        learning_rate.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        learning_rate.textEdited.connect(self.learning_rate_changed)

        kga_delta = QLineEdit(str(qthreads.config['kga_delta']))
        kga_delta.setValidator(QDoubleValidator())
        kga_delta.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        kga_delta.textEdited.connect(self.kga_delta_changed)

        kga_tau = QLineEdit(str(qthreads.config['kga_tau']))
        kga_tau.setValidator(QDoubleValidator())
        kga_tau.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        kga_tau.textEdited.connect(self.kga_tau_changed)

        max_training_data_num = QLineEdit(str(qthreads.config['max_training_data_num']))
        max_training_data_num.setValidator(QDoubleValidator())
        max_training_data_num.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        max_training_data_num.textEdited.connect(self.max_training_data_num_changed)

        self.exploring_rate_range.setEnabled(False)
        self.exploring_reward_range.setEnabled(False)

        label_execution = QLabel("Execution Parameter")
        label_execution.setFont(QFont(FONT_ARIAL, FONT_SIZE_SUBTITLE, QFont.Bold))

        cycle_time = QLineEdit(str(qthreads.config['cycle_time']))
        cycle_time.setValidator(QDoubleValidator())
        cycle_time.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        cycle_time.textEdited.connect(self.cycle_time_changed)

        label_cbla_plot = QLabel("CBLA Plot")
        label_cbla_plot.setFont(QFont(FONT_ARIAL, FONT_SIZE_SUBTITLE, QFont.Bold))

        plot_prediction_error = QCheckBox("Learning Progress")
        plot_prediction_error.setChecked(qthreads.CBLAPlots.plot_prediction_error in qthreads.cbla_plots)
        plot_prediction_error.stateChanged.connect(lambda:self.plot_prediction_error_changed(plot_prediction_error))

        plot_expert_number = QCheckBox("Expert Number")
        plot_expert_number.setChecked(qthreads.CBLAPlots.plot_expert_number in qthreads.cbla_plots)
        plot_expert_number.stateChanged.connect(lambda:self.plot_expert_number_changed(plot_expert_number))
        
        plot_max_action_value = QCheckBox("Max Action Value")
        plot_max_action_value.setChecked(qthreads.CBLAPlots.plot_max_action_value in qthreads.cbla_plots)
        plot_max_action_value.stateChanged.connect(lambda:self.plot_max_action_value_changed(plot_max_action_value))

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
        layout.addRow("Cycle Time (ms)", cycle_time)

        layout.addRow(label_cbla_plot)
        layout.addRow(plot_prediction_error)
        layout.addRow(plot_expert_number)
        layout.addRow(plot_max_action_value)

        self.setLayout(layout)

    def com_port_changed(self, val):
        qthreads.config['com_port'] = val

    def serial_number_changed(self, val):
        qthreads.config['serial_number'] = val

    def adapt_exploring_rate_changed(self, checkbox):
        isAdapt = checkbox.isChecked()
        self.exploring_rate_range.setEnabled(isAdapt)
        self.exploring_reward_range.setEnabled(isAdapt)

        qthreads.config['adapt_exploring_rate'] = isAdapt

    def exploring_rate_range_changed(self, val):
        valRange = val.replace("(", "").replace(")", "").split(",")
        if (len(valRange) > 1):
            minVal = float(valRange[0].replace(" ", ""))
            maxVal = float(valRange[1].replace(" ", ""))
            qthreads.config['exploring_rate_range'] = (minVal, maxVal)

    def exploring_reward_range_changed(self, val):
        valRange = val.replace("(", "").replace(")", "").split(",")
        if (len(valRange) > 1):
            minVal = float(valRange[0].replace(" ", ""))
            maxVal = float(valRange[1].replace(" ", ""))
            qthreads.config['exploring_reward_range'] = (minVal, maxVal)

    def exploring_rate_changed(self, val):
        qthreads.config['exploring_rate'] = val

    def reward_smoothing_changed(self, val):
        qthreads.config['reward_smoothing'] = val

    def split_threshold_changed(self, val):
        qthreads.config['split_threshold'] = val

    def split_threshold_growth_rate_changed(self, val):
        qthreads.config['split_threshold_growth_rate'] = val

    def split_quality_threshold_changed(self, val):
        qthreads.config['split_quality_threshold'] = val

    def split_lock_count_threshold_changed(self, val):
        qthreads.config['split_lock_count_threshold'] = val

    def split_quality_decay_changed(self, val):
        qthreads.config['split_quality_decay'] = val

    def mean_error_threshold_changed(self, val):
        qthreads.config['mean_error_threshold'] = val

    def mean_error_changed(self, val):
        qthreads.config['mean_error'] = val

    def action_value_changed(self, val):
        qthreads.config['action_value'] = val

    def learning_rate_changed(self, val):
        qthreads.config['learning_rate'] = val

    def kga_delta_changed(self, val):
        qthreads.config['kga_delta'] = val

    def kga_tau_changed(self, val):
        qthreads.config['kga_tau'] = val

    def max_training_data_num_changed(self, val):
        qthreads.config['max_training_data_num'] = val

    def cycle_time_changed(self, val):
        qthreads.config['cycle_time'] = val

    def plot_prediction_error_changed(self, checkbox):
        plot_prediction_error = checkbox.isChecked()
        if (plot_prediction_error and qthreads.CBLAPlots.plot_prediction_error not in qthreads.cbla_plots):
            qthreads.cbla_plots.append(qthreads.CBLAPlots.plot_prediction_error)
        elif (plot_prediction_error == False and qthreads.CBLAPlots.plot_prediction_error in qthreads.cbla_plots):
            qthreads.cbla_plots.remove(qthreads.CBLAPlots.plot_prediction_error)

    def plot_expert_number_changed(self, checkbox):
        plot_expert_number = checkbox.isChecked()
        if (plot_expert_number and qthreads.CBLAPlots.plot_expert_number not in qthreads.cbla_plots):
            qthreads.cbla_plots.append(qthreads.CBLAPlots.plot_expert_number)
        elif (plot_expert_number == False and qthreads.CBLAPlots.plot_expert_number in qthreads.cbla_plots):
            qthreads.cbla_plots.remove(qthreads.CBLAPlots.plot_expert_number)

    def plot_max_action_value_changed(self, checkbox):
        plot_max_action_value = checkbox.isChecked()
        if (plot_max_action_value and qthreads.CBLAPlots.plot_expert_number not in qthreads.cbla_plots):
            qthreads.cbla_plots.append(qthreads.CBLAPlots.plot_expert_number)
        elif (plot_max_action_value == False and qthreads.CBLAPlots.plot_expert_number in qthreads.cbla_plots):
            qthreads.cbla_plots.remove(qthreads.CBLAPlots.plot_max_action_value)

class SensorActuator(QWidget):
    def __init__(self, main=None):
        super(SensorActuator, self).__init__()
        self.init_sensor_actuator_widget()
        self.actuators = []
        self.sensors = []
        self.main = main

    def init_sensor_actuator_widget(self):
        layout = QVBoxLayout()

        label_sens_act = QLabel("Sensors and Actuators")
        label_sens_act.setFont(QFont(FONT_ARIAL, FONT_SIZE_TITLE, QFont.Bold))

        tab_widget = QTabWidget(self)

        self.tab_physical = QScrollArea()
        self.tab_physical_content = QWidget()
        self.tab_physical_content.setLayout(QGridLayout())

        self.tab_virtual = QScrollArea(tab_widget) 
        tab_virtual_content = VirtualBehavior()
        self.tab_virtual.setWidget(tab_virtual_content)

        tab_widget.addTab(self.tab_physical, "Physical")
        tab_widget.addTab(self.tab_virtual, "Virtual")

        layout.addWidget(label_sens_act)
        layout.addWidget(tab_widget)

        self.setLayout(layout)

    def clear_list(self):
        self.actuators = []
        self.sensors = []

    def clear_layout(self):
        layout = self.tab_physical.widget().layout()
        while (layout.count() > 0):
            child = layout.takeAt(0)
            if (child.widget() is not None):
                child.widget().deleteLater()
            elif (child.layout() is not None):
                clear_layout(child.layout())

class VirtualBehavior(QWidget):
    def __init__(self, parent=None):
        super(VirtualBehavior, self).__init__(parent)
        pass

class Sensor(QWidget):
    def __init__(self, node, port, addr, type, parent=None):
        super(Sensor, self).__init__(parent)

        self.node = node
        self.port = port
        self.addr = addr
        self.type = type

        self.byte_str = self.addr.to_bytes(1,byteorder='big') + self.type.to_bytes(1,byteorder='big') + \
            self.port.to_bytes(1,byteorder='big')

        self.curve = None
        self.x = np.linspace(0.0, 10.0, MAX_SENSOR_DATA_NUM)
        self.y = np.zeros(MAX_SENSOR_DATA_NUM, dtype=np.float)
        self.data = collections.deque([0.0]*MAX_SENSOR_DATA_NUM, MAX_SENSOR_DATA_NUM)

        self.init_sensor_widget()

    def init_sensor_widget(self):
        layout = QVBoxLayout()

        self.subwidget = QWidget()
        sublayout = QGridLayout()

        self.toggleButton = QToolButton()
        self.toggleButton.setStyleSheet("QToolButton {border: none}")
        self.toggleButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggleButton.setArrowType(Qt.RightArrow)
        self.toggleButton.setText("Hide")
        self.toggleButton.setCheckable(True)
        self.toggleButton.setChecked(True)
        self.toggleButton.clicked.connect(self.hide_show_sensor)

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

        layout.addWidget(self.toggleButton)

        sublayout.addWidget(label_node, 0, 0)
        sublayout.addWidget(label_port, 0, 1)
        sublayout.addWidget(label_addr, 0, 2)
        sublayout.addWidget(plot, 1, 0, 1, 3)
        self.subwidget.setLayout(sublayout)

        layout.addWidget(self.subwidget)

        self.setLayout(layout)

    def hide_show_sensor(self, checked):
        if (checked):
            arrow = Qt.RightArrow
            self.subwidget.show()
            text = "Hide"
        else:
            arrow = Qt.DownArrow
            self.subwidget.hide()
            text = "Show"
        self.toggleButton.setArrowType(arrow)
        self.toggleButton.setText(text)

class Actuator(QWidget):
    def __init__(self, node, port, addr, type, parent = None):
        super(Actuator, self).__init__(parent)

        self.node = node
        self.port = port
        self.addr = addr
        self.type = type

        self.byte_str = self.addr.to_bytes(1,byteorder='big') + self.type.to_bytes(1,byteorder='big') + \
            self.port.to_bytes(1,byteorder='big')

        self.init_actuator_widget()

    # make the actuator widget clickable
    # use this function to activate/inactivate actuator
    def mousePressEvent(self, event):
        palette = self.palette()
        if (self.palette().color(QPalette.Foreground).name() == COLOR_ACTIVE.name()):
            palette.setColor(self.foregroundRole(), COLOR_INACTIVE)
        else:
            palette.setColor(self.foregroundRole(), COLOR_ACTIVE)
        self.setPalette(palette)

        if (self.palette().color(QPalette.Foreground).name() == COLOR_ACTIVE.name()):
            if (self.byte_str in qthreads.devices_inactive):
                qthreads.devices_inactive.remove(self.byte_str)
        if (self.palette().color(QPalette.Foreground).name() == COLOR_INACTIVE.name()):
            if (self.byte_str not in qthreads.devices_inactive):
                qthreads.devices_inactive.append(self.byte_str)
        print(qthreads.devices_inactive)

    def init_actuator_widget(self):
        layout = QVBoxLayout()

        self.toggleButton = QToolButton()
        self.toggleButton.setStyleSheet("QToolButton {border: none}")
        self.toggleButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggleButton.setArrowType(Qt.RightArrow)
        self.toggleButton.setText("Hide")
        self.toggleButton.setCheckable(True)
        self.toggleButton.setChecked(True)
        self.toggleButton.clicked.connect(self.hide_show_actuator)

        self.subwidget = QWidget()
        sublayout = QGridLayout()

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

        layout.addWidget(self.toggleButton)

        sublayout.addWidget(label_node, 0, 0)
        sublayout.addWidget(label_port, 0, 1)
        sublayout.addWidget(label_addr, 0, 2)
        sublayout.addWidget(self.label_value, 1, 0)
        sublayout.addWidget(self.slider, 1, 1, 1, 3)
        self.subwidget.setLayout(sublayout)

        layout.addWidget(self.subwidget)

        self.setLayout(layout)

        default_palette = self.palette()
        default_palette.setColor(self.foregroundRole(), COLOR_ACTIVE)
        self.setPalette(default_palette)

    def hide_show_actuator(self, checked):
        if (checked):
            arrow = Qt.RightArrow
            self.subwidget.show()
            text = "Hide"
        else:
            arrow = Qt.DownArrow
            self.subwidget.hide()
            text = "Show"
        self.toggleButton.setArrowType(arrow)
        self.toggleButton.setText(text)

    def slider_value_changed(self):
        self.label_value.setText("{}".format(self.slider.value()))

class Bottom(QWidget):
    def __init__(self, main=None):
        super(Bottom, self).__init__()
        self.main = main
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()

        self.log = QTextEdit()
        self.log.setReadOnly(True)

        btn_layout = QHBoxLayout()

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self.clear)

        self.btn_connect = QPushButton("Connect")
        self.btn_connect.clicked.connect(self.connect)

        self.btn_disconnect = QPushButton("Disconnect")
        self.btn_disconnect.clicked.connect(self.disconnect)

        self.btn_run = QPushButton("Run")
        self.btn_run.clicked.connect(self.run)

        self.btn_cancel = QPushButton("Cancel")

        btn_layout.addWidget(self.btn_clear)
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.btn_connect)
        btn_layout.addWidget(self.btn_disconnect)
        btn_layout.addWidget(self.btn_run)
        btn_layout.addWidget(self.btn_cancel)

        self.layout.addWidget(self.log)
        self.layout.addLayout(btn_layout)

        self.setLayout(self.layout)

    def disconnect(self):
        self.main.disconnect_teensy.emit()
        self.btn_connect.setEnabled(True)

    def clear(self):
        self.log.clear()

    def connect(self):
        self.main.connect_teensy.emit()

    def run(self):
        self.btn_run.setEnabled(False)
        self.main.run_cbla.emit()

        self.main.cblathread.dock_widget = QDockWidget(PLOT_TITLE)
        self.main.cblathread.curves = {}
        if (len(qthreads.cbla_plots) > 0):
            self.main.cblathread.plot_window = pg.GraphicsWindow()
            self.main.cblathread.dock_widget.setWidget(self.main.cblathread.plot_window)
            self.main.addDockWidget(Qt.RightDockWidgetArea, self.main.cblathread.dock_widget)
        for plot in qthreads.cbla_plots:
            title = None
            if (plot == "plot_expert_number"):
                title = "Number of Experts"
            elif (plot == "plot_prediction_error"):
                title = "Learning Progress"
            graph = self.main.cblathread.plot_window.addPlot(title=title)
            graph.enableAutoRange('xy', True)
            self.main.cblathread.curves[plot] = graph.plot()
