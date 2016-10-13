import sys
import qtgui
from PyQt4.QtGui import *

app = QApplication([])

win = qtgui.VisualApp()

win.showMaximized()

sys.exit(app.exec_())