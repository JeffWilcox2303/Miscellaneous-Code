# Modified from ChatGPT
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np

app = QtCore.Application([])

win = pg.GraphicsLayoutWidget()
win.show()
plot = win.addPlot()
curve = plot.plot()

data = np.zeros(1000)

def update():
    global data
    data = np.roll(data, -1)
    data[-1] = np.random.normal()
    curve.setData(data)  # fast!
    
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(1)

app.exec()