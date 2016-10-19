import sys

import qtgui
from PyQt4.QtGui import *
from PyQt4.QtCore import *

def main():
    
    app = QApplication([])

    win = qtgui.VisualApp()

    win.showMaximized()  
    
    win.bottom.btn_cancel.clicked.connect(app.quit)

    sys.exit(app.exec_())

if __name__=='__main__':
    main()

