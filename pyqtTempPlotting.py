# Modified from ChatGPT
import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QThread, pyqtSignal
import pyqtgraph as pg
import numpy as np
import time


# -----------------------------
# Serial Reader Thread
# -----------------------------
class SerialThread(QThread):
    data_received = pyqtSignal(int)

    def __init__(self, port, baud=115200):
        super().__init__()
        self.port = port
        self.baud = baud
        self.running = True

    def run(self):
        ser = serial.Serial(self.port, self.baud, timeout=1)
        while self.running:
            try:
                line = ser.readline().decode("utf-8").strip()
                if line:
                    value = int(line)
                    self.data_received.emit(value)
            except:
                pass
        ser.close()

    def stop(self):
        self.running = False


# -----------------------------
# Main Window with Plot
# -----------------------------
class MainWindow(QMainWindow):
    def __init__(self, port):
        super().__init__()
        self.setWindowTitle("RP2040 Real-Time Plot")
        self.window = 10

        # PyQtGraph setup
        self.plot_widget = pg.PlotWidget()
        self.setCentralWidget(self.plot_widget)

        # Axis labels
        self.plot_widget.setLabel('left', 'Temperature', units='C')
        self.plot_widget.setLabel('bottom', 'Time', units='s')
        self.plot_widget.setTitle('Real Time Temperature Plotting')

        self.t0 = time.monotonic()

        self.time_data = []   # Will hold timestamps
        self.value_data = []  # Will hold values
        self.max_points = 1000
        self.curve = self.plot_widget.plot()

        # Serial thread
        self.thread = SerialThread(port)
        self.thread.data_received.connect(self.update_plot)
        self.thread.start()

    def update_plot(self, value):
        # Determine time elapsed since window created
        t = time.monotonic() - self.t0

        # Append data
        self.time_data.append(t)
        self.value_data.append(float(27 - (value*3.3/2**12 - 0.706)/0.0011721))

        # # Shift data left, append new value
        # self.data[:-1] = self.data[1:]
        # self.data[-1] = float(27 - (value*3.3/2**12 - 0.706)/0.0011721)
        # if len(self.time_data) > self.max_points:
        #     self.time_data = self.time_data[-self.max_points:]
        #     self.value_data = self.value_data[-self.max_points:]
        while self.time_data and (t - self.time_data[0] > self.window):
            self.time_data.pop(0)
            self.value_data.pop(0)
        self.curve.setData(self.time_data, self.value_data)

    def closeEvent(self, event):
        self.thread.stop()
        self.thread.wait()
        event.accept()


# -----------------------------
# Application Entry
# -----------------------------
def find_rp2040_port():
    for p in serial.tools.list_ports.comports():
        if "RP2040" in p.description or "Pico" in p.description:
            return p.device
    return None


if __name__ == "__main__":
    port = find_rp2040_port()
    if not port:
        # print("RP2040 not found. Plug it in and check dmesg / Device Manager.")
        print("RP2040 not found. Defaulting to COM5")
        port = "COM5"
        # sys.exit(1)

    app = QApplication(sys.argv)
    win = MainWindow(port)
    win.show()
    sys.exit(app.exec_())