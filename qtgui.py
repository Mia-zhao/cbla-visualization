# GUI
import sys
import time

import math
import random
import numpy as np

import collections
from enum import Enum

from PyQt4.QtGui import *
from PyQt4.QtCore import *
import pyqtgraph as pg

from cbla_learner import Learner
import simpleTeensyComs

BUFFER_SIZE = 100
DATA = collections.deque([0.0]*BUFFER_SIZE, BUFFER_SIZE)
X = np.linspace(0, 10.0, BUFFER_SIZE)
Y = np.zeros(BUFFER_SIZE, dtype=np.float)

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

FONT_ARIAL = "Arial"
FONT_SIZE_TITLE = 12
FONT_SIZE_CONFIG = 11

State = Enum('State', 'ready running finshed')

numActs = 0
ActsList = []
numSens = 0
SensList = []
sensValues = []
actValues = []
teensyComms = None
destination = None 
origin = None

curve = None

class VisualApp(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()

        self.central_widget = QWidget()

        self.initUI()

    def initUI(self):
        self.central_layout = QGridLayout()
        
        self.topleft = self.menu_frame()
        self.topright = StackedContent()
        
        splitter1 = QSplitter(Qt.Horizontal)
        splitter1.addWidget(self.topleft)
        splitter1.addWidget(self.topright)
        splitter1.setStretchFactor(1, 10)
        
        self.bottom = BottomFrame(self)
        
        splitter2 = QSplitter(Qt.Vertical)
        splitter2.addWidget(splitter1)
        splitter2.addWidget(self.bottom)
        splitter2.setStretchFactor(0, 5)
        
        self.central_layout.addWidget(splitter2)

        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)
        
        self.statusBar().showMessage(MESSAGE_READY)
        
        self.setGeometry(100, 100, 1500, 900)
        self.setWindowTitle(APP_TITLE)
        self.show()

    def menu_frame(self):
        self.menu_frame = QFrame()
        self.init_menu()
        return self.menu_frame

    def init_menu(self):
        #self.setFrameShape(QFrame.StyledPanel)
        self.menu_frame.layout = QVBoxLayout()
    
        self.menu_frame.filter = QLineEdit('Type Key Word')
        
        self.menu_frame.menu_tree = QTreeView()
        
        self.menu_frame.menu_model = QStandardItemModel()
        self.menu_frame.menu_model.setHorizontalHeaderLabels([self.menu_frame.tr(MENU_HEADER)])
        self.addMenuItems(self.menu_frame.menu_model, MENU_ITEMS)
        self.menu_frame.menu_tree.setModel(self.menu_frame.menu_model)
        
        self.menu_frame.menu_tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.menu_frame.menu_tree.connect(self.menu_frame.menu_tree, SIGNAL('clicked(QModelIndex)'), self.openMenu)

        self.menu_frame.layout.addWidget(self.menu_frame.filter)
        self.menu_frame.layout.addWidget(self.menu_frame.menu_tree)
        self.menu_frame.setLayout(self.menu_frame.layout)

    def addMenuItems(self, parent, items):
        for name, children in items:
            item = QStandardItem(name)
            parent.appendRow(item)
            if children:
                self.addMenuItems(item, children)

    def openMenu(self, position):
        indexes = self.menu_frame.menu_tree.selectedIndexes()
        if (len(indexes) > 0):
            index = indexes[0]
            if (index.data() == MENU_CONFIG):
                self.topright.setCurrentIndex(0)
            elif (index.data() == MENU_SENS_ACT):
                self.topright.setCurrentIndex(1)
            elif (index.data() == MENU_SENS):
                self.topright.setCurrentIndex(2)
            elif (index.data() == MENU_ACT):
                self.topright.setCurrentIndex(3)
            elif (index.data() == MENU_CBLA):
                self.topright.setCurrentIndex(4)
            
class StackedContent(QStackedWidget):
    def __init__(self):
        super(QStackedWidget, self).__init__()
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
            "max_training_data_num": 500
        }
        self.init()

    def init(self):
        #content.setFrameShape(QFrame.StyledPanel)
        self.cbla = self.get_frame(MENU_CBLA)
        
        self.addWidget(self.config_frame())
        self.addWidget(self.get_frame(MENU_SENS_ACT))
        self.addWidget(self.get_frame(MENU_SENS))
        self.addWidget(self.get_frame(MENU_ACT))
        self.addWidget(self.cbla)

    def config_frame(self):
        frame = QWidget()
        layout = QFormLayout()
        
        title = QLabel()
        title.setText(MENU_CONFIG)
        title.setFont(QFont(FONT_ARIAL, FONT_SIZE_TITLE, QFont.Bold))
        
        learner_label = QLabel()
        learner_label.setText("Learner Configuration")
        learner_label.setFont(QFont(FONT_ARIAL, FONT_SIZE_TITLE - 1, QFont.Bold))
        
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
        
        self.exploring_reward_range = QLineEdit('(-0.03, 0.004)')
        self.exploring_reward_range.setFont(QFont(FONT_ARIAL, FONT_SIZE_CONFIG))
        
        expert_label = QLabel()
        expert_label.setText("Expert Configuration")
        expert_label.setFont(QFont(FONT_ARIAL, FONT_SIZE_TITLE - 1, QFont.Bold))
        
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
        
        layout.addRow(title)
        
        layout.addRow(learner_label)
        layout.addRow("Exploring Rate", exploring_rate)
        layout.addRow(self.adapt_exploring_rate)
        layout.addRow("Exploring Rate Range", self.exploring_rate_range)
        layout.addRow("Exploring Reward Range", self.exploring_reward_range)
        
        layout.addRow(expert_label)
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
        #config_ex_range.setEnabled(self.adapt_exploring_rate)
        #config_reward_range.setEnabled(self.adapt_exploring_rate)
        
        frame.setLayout(layout)
        return frame

    def adapt_exploring_rate_changed(self, checkbox):
        isAdapt = checkbox.isChecked()
        self.exploring_rate_range.setEnabled(isAdapt)
        self.exploring_reward_range.setEnabled(isAdapt)
        
        self.config["adapt_exploring_rate"] = isAdapt

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

    def get_frame(self, name):
        frame = QWidget()
        layout = QFormLayout()
        
        title = QLabel()
        title.setText(name)
        title.setFont(QFont(FONT_ARIAL, FONT_SIZE_TITLE, QFont.Bold))
        
        layout.addRow(title)
        frame.setLayout(layout)
        return frame


class BottomFrame(QFrame):
    def __init__(self, VisualApp):
        super(QFrame, self).__init__()
        self.status = State.ready
        self.app = VisualApp
        self.initUI()

    def initUI(self):
        #self.setFrameShape(QFrame.StyledPanel)
        self.layout = QVBoxLayout()
        
        self.log = QTextEdit()
        
        btn_layout = QHBoxLayout()
        
        self.btn_run = QPushButton("Run")
        self.btn_run.clicked.connect(self.run)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(QCoreApplication.instance().quit)
        
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.btn_run)
        btn_layout.addWidget(self.btn_cancel)
        
        self.layout.addWidget(self.log)
        self.layout.addLayout(btn_layout)
        
        self.setLayout(self.layout)

    def run(self):
        self.status = State.running
        self.log.setText("Running CBLA")
        execute_CBLA(self.app.topright.config, self.app)
        self.log.setText("Finished CBLA")
        
def execute_CBLA(config, app):
    new_plot = pg.PlotWidget(title="Learning Progress")
        
    new_plot.setLabel("bottom", text="Sample")
    new_plot.setLabel("left", text="Mean Error")
    #new_plot.setXRange(-10, 0)
    new_plot.setXRange(0, BUFFER_SIZE/10)
    new_plot.setYRange(-2, 5)
    
    new_plot.showGrid(x=True, y=True)
    #global curve
    curve = new_plot.plot(X, Y, pen=(255,0,0))
    
    cbla_layout = app.topright.cbla.layout()
    cbla_layout.addRow(new_plot)
    #new_plot.show()
    
    lrnr = Learner(tuple([0]*numSens),tuple([0]*numActs), 
        exploring_rate = config["exploring_rate"],
        exploring_rate_range = config["exploring_rate_range"],
        exploring_reward_range = config["exploring_reward_range"],
        adapt_exploring_rate = config["adapt_exploring_rate"],
        reward_smoothing = config["reward_smoothing"],
        split_threshold = config["split_threshold"],
         split_threshold_growth_rate = config["split_threshold_growth_rate"],
        split_lock_count_threshold = config["split_lock_count_threshold"],
        split_quality_threshold = config["split_quality_threshold"],
        split_quality_decay = config["split_quality_decay"],
        mean_error_threshold = config["mean_error_threshold"],
        mean_error = config["mean_error"],
        action_value = config["action_value"],
        learning_rate = config["learning_rate"],
        kga_delta = config["kga_delta"],
        kga_tau = config["kga_tau"],
        max_training_data_num = config["max_training_data_num"]
    )
    
    iterNum = 0
    actionValHist = []
    global numActs, numSens, SensList, sensValues, ActsList, actValues, teensyComms, destination, origin
    while iterNum < 50:


        # Act:  Update all the active actuators (do not act on the very first iteration,
        # until the sensors have been read
        if iterNum > 0:
            for i in range(0,len(ActsList)):
                simpleTeensyComs.Fade(teensyComms, destination, origin,ActsList[i].genByteStr(),
                                      int(actValues[i]),0)
                #print('Command Actuator ', i, 'to Value ', int(actValues[i]))

        #Sense:  Read all the sensors
        for i in range(0,len(SensList)):
            sensValues[i] = simpleTeensyComs.Read(teensyComms, destination,
                                                  origin,SensList[i].genByteStr(), 0)
            #print('Sensor ', i, 'Reads a Value of ',sensValues[i])

        #Learn:
        lrnr.learn(tuple(normalize_sens(sensValues,SensList)),tuple(actValues))

        #Select Next action to perform
        actValues = lrnr.select_action()

        numExperts = lrnr.expert.get_num_experts()
        #print("-------------------------------------------")
        #print("Reduced Mean Error " + str(lrnr.expert.rewards_history))
        #if iterNum == 10:
         #  Plots.PlotModel(list(lrnr.expert.training_data),
         #                  list(lrnr.expert.training_label),
          #                 lrnr.expert.predict_model.predict(list(lrnr.expert.training_data)))

        if numExperts > 1:
            print('Increased number of experts')
        #Report the action value and the number of experts currently in the system
        #print('Current max action value is ', lrnr.expert.get_largest_action_value())
        #print('Current number of experts is', lrnr.expert.get_num_experts())
        
        info = collections.defaultdict(dict)
        lrnr.expert.save_expert_info(info)
        DATA.append(info['mean_errors'][numExperts - 1])
        
        iterNum += 1

def normalize_sens(sensValues,SensList):
    normValues = []
    for i in range(0,len(SensList)):
        #for now, scale everything the same, this function can be extended to scale
        #separately based on the device type in the sensors list
        normValues.append(sensValues[i]/1023)

    return normValues

def update():
    Y[:] = DATA
    if(curve is not None):
        curve.setData(X, Y)
    
def main():
    import argparse

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('teensy_comport', type=str, help='The Teensy com port.')
    parser.add_argument('teensy_serial', type=int, help='The Teensy serial number - usually 6-7 digits.')
    parser.add_argument('comp_serial', type=int, help='The computers serial number for the purposes of simulation [22222]',
                       default=simpleTeensyComs.cbla_pc_id, nargs='?' )
    parser.add_argument('grasshopper_serial', type=int, help='The Grasshopper nodes serial number for the purposes of simulation [33333]',
                       default=simpleTeensyComs.udp_node_id, nargs='?' )

    args = parser.parse_args()

    global numActs, numSens, SensList, sensValues, ActsList, actValues, teensyComms, destination, origin
    #Initialize Comms
    # Initialize Comms and setup the teensy
    destination = args.teensy_serial #simpleTeensyComs.teensy_sernum
    origin = args.comp_serial
    Grasshopper = args.grasshopper_serial
    teensyComms = simpleTeensyComs.initializeComms(args.teensy_comport)
    
    numDevices = simpleTeensyComs.QueryNumDevices(teensyComms, destination, origin)
    print('The teensy has', numDevices, 'devices')
    devList = simpleTeensyComs.QueryIDs(teensyComms, destination, origin)
    
    
    for i in range(0,len(devList)):
        print(devList[i].pr())
        if devList[i].type%2 == 0:
            numSens += 1
            SensList.append(devList[i])
            sensValues.append(0)
        else:
            numActs += 1
            ActsList.append(devList[i])
            actValues.append(0)
    
    app = QApplication(sys.argv)
    w = VisualApp()

    timer = QTimer()
    timer.timeout.connect(update)
    timer.start(20)
    
    
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()