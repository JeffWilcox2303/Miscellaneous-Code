import numpy as np
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt

data = pd.read_csv('Solder Toaster Temperature Measurements - Broil Setting.csv')

# The first 84 samples (or 14 minutes) are used as the temperature deltas get close to 0 and are less helpful near steady state
T = np.array(data['Temperature (C)'])

### Explanation of temperature derivative
# 0.2 is used as a fudge factor to account for some values not changing across a timestep
# If a smaller value is used, then the natural log of a smaller number is lower,
# so the curve is pulled downwards. If a larger number is used, the curve is skewed upwards.
# 0.2 was somewhat arbitrarily chosen and has better results than 0.1 or 0.2
# Regardless, using logarithms with differentials is difficult and requires some abnormal handling
dT = [(T[i+1] - T[i] + 0.2)/10 for i in range(84)]
Y = np.log(np.abs(dT))

t = np.array(data['Time (s)'])
time = t[:84]

Psi = np.ndarray((2,84))
Psi[0,:] = time
Psi[1,:] = [1 for _ in range(84)]
Psi = Psi.T

theta = np.linalg.solve(np.matmul(Psi.T,Psi), np.matmul(Psi.T,Y.T))
tau = -1/theta[0]
Ti = T[0] # C
Tf = tau*np.exp(theta[1])+Ti
print(f'Tf = {Tf}')
print(f'Tau = {tau}')
calcY = Tf - (Tf-Ti)*np.exp(-t/tau)

P = 500 # W
R = (Tf-Ti)/P
print(f'R = {R} C/W')

plt.plot(t,T,label='Measured')
plt.plot(t,calcY,label='Fit')
plt.ylabel('Temperature (C)')
plt.xlabel('Time (s)')
plt.title('Measured vs Fit Temperature Curve, Broil Setting')
plt.text(500,125,'T = Tf - (Tf - Ti)*exp(-t/tau)')
plt.text(500,100,f'Tau = {tau} s')
plt.text(500,75,f'Tf = {Tf} C')
plt.text(500,50,f'R = {R} C/W')
plt.legend()
plt.savefig('BroilerSolderOven.png')
plt.show()
