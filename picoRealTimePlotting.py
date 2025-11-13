import serial
import numpy as np
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque

ser = serial.Serial('COM5', 9600, timeout=0.001)

data_points = deque(maxlen=100)

fig, ax = plt.subplots()
line, = ax.plot([], [], 'b-')

def update_plot(frame):
    if ser.in_waiting > 0:
        temp = ser.readline().decode('utf-8').strip()
        try:
            value = float(temp)
            # value = 27 - (int(temp)*3.3 - 0.706)/0.0011721
            data_points.append(value)
            
            x_data = list(range(len(data_points)))
            y_data = list(data_points)

            line.set_data(list(x_data), list(y_data))
            ax.relim()
            ax.autoscale_view()
        except ValueError:
            print(f'Invalid data received: {temp}')
    return line,

ani = FuncAnimation(fig, update_plot, interval=1, blit=False)
plt.show()

ser.close()