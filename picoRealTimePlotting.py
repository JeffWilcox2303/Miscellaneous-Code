import serial
import numpy as np
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
import pandas as pd
import datetime

ser = serial.Serial('COM5', 9600, timeout=0.001)

reflow_length = 240 # seconds
sample_period = 0.1 # seconds/sample
n = int(reflow_length/sample_period) # samples

data_points = deque(maxlen=n)

profile = deque(maxlen=n)

fig, ax = plt.subplots()
line, = ax.plot([], [], 'b-')
line1, = ax.plot([],[],'r-')

def update_plot(frame):
    if ser.in_waiting > 0:
        temp = ser.readline().decode('utf-8').strip()
        try:
            value = float(temp)
            # value = 27 - (int(temp)*3.3 - 0.706)/0.0011721
            data_points.append(value)
            
            x_data = list(range(len(data_points)))
            y_data = list(data_points)

            profile.append(30)
            y1 = list(profile)

            line.set_data(np.array(x_data)*0.05, list(y_data))
            line1.set_data(np.array(x_data)*0.05, np.array(profile))
            ax.relim()
            ax.autoscale_view()
        except ValueError:
            print(f'Invalid data received: {temp}')
    return line,

ani = FuncAnimation(fig, update_plot, interval=50, blit=False)
plt.show()

ser.close()
# data = {'Sample Time (s)': np.array(list(range(len(data_points))))*sample_period, 'Measured Temp (C)': np.array(data_points), 'Profile Temp (C)': np.array(profile)}
# df = pd.DataFrame(data)
# now = datetime.datetime.now()
# df.to_csv(f'temp_data_{now.date()}_{now.hour}h{now.minute}m{now.second}s.csv')