# GUI
import sys
import time

import math
import random
import numpy as np

import collections

from PyQt4.QtGui import *
from PyQt4.QtCore import *
import pyqtgraph as pg

BUFFER_SIZE = 100
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
FONT_SIZE_LABEL = 11

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
        
        self.bottom = BottomFrame()
        
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
        self.init()

    def init(self):
        #content.setFrameShape(QFrame.StyledPanel)
        self.addWidget(self.config_frame())
        self.addWidget(self.get_frame(MENU_SENS_ACT))
        self.addWidget(self.get_frame(MENU_SENS))
        self.addWidget(self.get_frame(MENU_ACT)) 
        self.addWidget(self.get_frame(MENU_CBLA))

    def config_frame(self):
        frame = QWidget()
        layout = QFormLayout()
        
        title = QLabel()
        title.setText(MENU_CONFIG)
        title.setFont(QFont(FONT_ARIAL, FONT_SIZE_TITLE, QFont.Bold))
        
        config_er = QLineEdit('0.3')
        config_er.setValidator(QDoubleValidator())
        config_er.setMaxLength(6)
        config_er.setFont(QFont(FONT_ARIAL, FONT_SIZE_LABEL))
        #config_er.textEdited.connect(self.setExploringRate)
    
        config_ex_range = QLineEdit('(0.4, 0.01)')
        config_ex_range.setFont(QFont(FONT_ARIAL, FONT_SIZE_LABEL))
    
        config_reward_range = QLineEdit('(-0.03, 0.004)')
        config_reward_range.setFont(QFont(FONT_ARIAL, FONT_SIZE_LABEL))
    
        config_split_thres = QLineEdit('40')
        config_split_thres.setFont(QFont(FONT_ARIAL, FONT_SIZE_LABEL))
    
        config_mean_err_thres = QLineEdit('0.0')
        config_mean_err_thres.setFont(QFont(FONT_ARIAL, FONT_SIZE_LABEL))
    
        config_learning_rate = QLineEdit('0.25')
        config_learning_rate.setFont(QFont(FONT_ARIAL, FONT_SIZE_LABEL))
    
        config_kga_delta = QLineEdit('10')
        config_kga_delta.setFont(QFont(FONT_ARIAL, FONT_SIZE_LABEL))
    
        config_kga_tau = QLineEdit('30')
        config_kga_tau.setFont(QFont(FONT_ARIAL, FONT_SIZE_LABEL))
    
        checkbox = QCheckBox("Adapt Exploring Rate")
        checkbox.setChecked(False)
        #checkbox.stateChanged.connect(lambda:self.setAdapt(self.checkbox))
    
        layout.addRow(title)
        layout.addRow("Exploring Rate", config_er)
        layout.addRow("Exploring Rate Range", config_ex_range)
        layout.addRow("Reward Range", config_reward_range)
        layout.addRow(checkbox)
        layout.addRow("Split Threshold", config_split_thres)
        layout.addRow("Mean Error Threshold", config_mean_err_thres)
        layout.addRow("Learning Rate", config_learning_rate)
        layout.addRow("KGA Delta", config_kga_delta)
        layout.addRow("KGA Tau", config_kga_tau)
        
        #config_ex_range.setEnabled(self.adapt_exploring_rate)
        #config_reward_range.setEnabled(self.adapt_exploring_rate)
        
        frame.setLayout(layout)
        return frame
    
        #setGeometry(300, 300, 800, 600)
        #setWindowTitle("CBLA Run")
        #show()

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
    def __init__(self):
        super(QFrame, self).__init__()
        self.initUI()

    def initUI(self):
        #self.setFrameShape(QFrame.StyledPanel)
        self.layout = QVBoxLayout()
        
        self.log = QTextEdit()
        
        btn_layout = QHBoxLayout()
        
        self.btn_run = QPushButton("Run")
        self.btn_cancel = QPushButton("Cancel")
        
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.btn_run)
        btn_layout.addWidget(self.btn_cancel)
        
        self.layout.addWidget(self.log)
        self.layout.addLayout(btn_layout)
        
        self.setLayout(self.layout)

def main():
    app = QApplication(sys.argv)
    w = VisualApp()

    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()