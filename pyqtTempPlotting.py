# Modified from ChatGPT
import csv
import sys
import serial
import serial.tools.list_ports
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QThread, pyqtSignal
import pyqtgraph as pg
import numpy as np
import time
from collections import deque


# -----------------------------
# Serial Reader Thread
# -----------------------------
class SerialThread(QThread):
    data_received = pyqtSignal(float, int)
    send_request = QtCore.pyqtSignal(str)

    def __init__(self, port, baud=115200):
        super().__init__()
        self.port = port
        self.baud = baud
        self.running = True
        self.t0 = time.monotonic()
        self.ser = serial.Serial(self.port, self.baud, timeout=0.1,write_timeout=0.1)
        self.send_request.connect(self.send)

    def run(self):
        if self.ser:
            while self.running:
                try:
                    line = self.ser.readline().decode("utf-8").strip()
                    if line:
                        value = int(line)
                        t = time.monotonic() - self.t0
                        self.data_received.emit(t, value)
                except:
                    pass
            self.ser.close()

    @QtCore.pyqtSlot(str)
    def send(self, message):
        if self.ser and self.ser.is_open:
            try:
                self.ser.write((message + "\n").encode())
            except serial.SerialTimeoutException:
                print("Write timeout - device not reading yet")

    def stop(self):
        self.running = False


# -----------------------------
# Main Window with Plot
# -----------------------------
class MainWindow(QMainWindow):
    def __init__(self, port):
        super().__init__()
        self.setWindowTitle("RP2040 Real-Time Plot")
        self.window1 = 10 # seconds
        self.window2 = 240 # seconds

        self.history_time = []
        self.history_values = []

        self.window1_time = deque()
        self.window1_values = deque()

        self.window2_time = deque()
        self.window2_values = deque()

        # PyQtGraph setup
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        self.setCentralWidget(widget)

        # 10-second window
        self.plot_window1 = pg.PlotWidget(title="Last 10 Seconds")
        self.curve_window1 = self.plot_window1.plot([], [])

        # 240-second window
        self.plot_window2 = pg.PlotWidget(title="Last 240 Seconds")
        self.curve_window2 = self.plot_window2.plot([], [])

        # Save button
        self.save_button = QtWidgets.QPushButton("Save CSV")
        self.save_button .clicked.connect(self.save_csv)

        # Send button
        self.send_button = QtWidgets.QPushButton("Send Command")
        self.send_button.clicked.connect(self.send_command)

        layout.addWidget(self.send_button)
        layout.addWidget(self.plot_window1)
        layout.addWidget(self.plot_window2)
        layout.addWidget(self.save_button)

        # Axis labels
        self.plot_window1.setLabel('left', 'Temperature', units='C')
        self.plot_window1.setLabel('bottom', 'Time', units='s')
        self.plot_window2.setLabel('left', 'Temperature', units='C')
        self.plot_window2.setLabel('bottom', 'Time', units='s')

        # Serial thread
        self.thread = SerialThread(port)
        self.thread.data_received.connect(self.on_data)
        self.thread.start()

        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.update_plots)
        self.update_timer.start(33)

    def on_data(self, t, value):
        # Append data
        self.history_time.append(t)
        self.history_values.append(float(27 - (value*3.3/2**12 - 0.706)/0.0011721))

        self.window1_time.append(t)
        self.window1_values.append(float(27 - (value*3.3/2**12 - 0.706)/0.0011721))
        while self.window1_time and (t - self.window1_time[0] > self.window1):
            self.window1_time.popleft()
            self.window1_values.popleft()

        self.window2_time.append(t)
        self.window2_values.append(float(27 - (value*3.3/2**12 - 0.706)/0.0011721))
        while self.window2_time and (t - self.window2_time[0] > self.window2):
            self.window2_time.popleft()
            self.window2_values.popleft()


    def update_plots(self):
        if self.history_time:
            self.curve_window1.setData(self.window1_time, self.window1_values)
            self.curve_window2.setData(self.window2_time, self.window2_values)

    def save_csv(self):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if not filename:
            return
        
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["time","value"])
            for t,v in zip(self.history_time, self.history_values):
                writer.writerow([t,v])
        
        QtWidgets.QMessageBox.information(self, "Saved", "Data saved to CSV.")

    def send_command(self):
        self.thread.send_request.emit("START")

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