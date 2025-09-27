import numpy as np
import matplotlib.pyplot as plt

R = 100 # Ohms
C = 1e-9 # Farads
tau = R*C
f = 915e6 # Hertz
T = 1/f # Seconds
t = np.linspace(0,1000*T,10001)
v0 = 1 # Volts

v_lin = v0*(1-t/tau)
v_lin = [np.max([0,v]) for v in v_lin]
v_exp = v0*np.exp(-t/tau)
v_cos = v0*np.cos(2*np.pi*f*t)
plt.plot(t,v_lin,label='Linear')
plt.plot(t,v_exp,label='Exponential')
# plt.plot(t,v_cos,'-',label='Cosine')
plt.legend()
plt.title('Diode Decay Plot')
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')
plt.show()
plt.savefig('diode_plot.png')