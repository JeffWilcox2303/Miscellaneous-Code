import serial
import numpy as np
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
import pandas as pd
import datetime
import queue
import struct

ser = serial.Serial('COM5', 9600, timeout=0.001)

# reflow_length = 240 # seconds
# sample_period = 0.1 # seconds/sample
# n = int(reflow_length/sample_period) # samples

# data_points = deque(maxlen=n)

# profile = deque(maxlen=n)

# plt.ion()
# fig, ax = plt.subplots()
# line, = ax.plot([], [], 'b-')
# line1, = ax.plot([],[],'r-')

def serial_reader(port, q, stop_flag):
    """ Based on code from ChatGPT. Continuously read from serial port and push into queue. """
    buffer = b''
    batch = []
    while not stop_flag.is_set():
        try:
            line = port.read(port.in_waiting or 64)  # or port.read(n) if sending binary
            if line:
                buffer += line
                while len(buffer) >= 2:
                    sample = buffer[:2]
                    buffer = buffer[2:]
                    batch.append(sample)

                    if len(batch) >= 100:
                        q.put(b''.join(batch))
                        batch.clear()
        except serial.SerialException:
            break
    if batch:
        q.put(b''.join(batch))

# -------- Main plotting loop --------
# Modified from ChatGPT
def plotting_loop(q):
    plt.ion()
    fig, ax = plt.subplots()
    xs = []
    ys = []

    line, = ax.plot(xs, ys, "-")

    start = time.time()

    while True:
        # Try to get ALL data currently available
        while not q.empty():
            raw = q.get()
            try:
                value = float(27 - (struct.unpack('<H',raw)[0]*3.3/2**12 - 0.706)/0.0011721)
                xs.append(time.time() - start)
                ys.append(value)
            except ValueError:
                pass  # skip corrupted line

        # Update plot every ~50 ms
        line.set_xdata(xs)
        line.set_ydata(ys)
        ax.relim()
        ax.autoscale_view()

        plt.pause(0.05)

# def update_plot(frame):
#     if ser.in_waiting > 0:
#         temp = ser.readline().decode('utf-8').strip()
#         try:
#             value = float(temp)
#             # value = 27 - (int(temp)*3.3 - 0.706)/0.0011721
#             data_points.append(value)
            
#             x_data = list(range(len(data_points)))
#             y_data = list(data_points)

#             profile.append(30)
#             y1 = list(profile)

#             line.set_data(np.array(x_data)*0.05, list(y_data))
#             line1.set_data(np.array(x_data)*0.05, np.array(profile))
#             ax.relim()
#             ax.autoscale_view()
#         except ValueError:
#             print(f'Invalid data received: {temp}')
#     return line,

q = queue.Queue()

stop_flag = threading.Event()

t = threading.Thread(target=serial_reader, args=(ser,q,stop_flag))
t.daemon = True
t.start()

try:
    plotting_loop(q)
except KeyboardInterrupt:
    print("Stopping...")

stop_flag.set()
t.join()
ser.close()

# ani = FuncAnimation(fig, update_plot, interval=50, blit=False)
# plt.show()

# ser.close()
# data = {'Sample Time (s)': np.array(list(range(len(data_points))))*sample_period, 'Measured Temp (C)': np.array(data_points), 'Profile Temp (C)': np.array(profile)}
# df = pd.DataFrame(data)
# now = datetime.datetime.now()
# df.to_csv(f'temp_data_{now.date()}_{now.hour}h{now.minute}m{now.second}s.csv')