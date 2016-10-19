import sys

import qtgui
from PyQt4.QtGui import *
from PyQt4.QtCore import *

def main():
    
    app = QApplication([])

    win = qtgui.VisualApp()

    win.showMaximized()  
    

    sys.exit(app.exec_())

if __name__=='__main__':
    main()

