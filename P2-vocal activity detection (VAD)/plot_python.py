import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

data = np.loadtxt('out.txt')
x = data[:, 0]
power = data[:, 1]
z = data[:, 2]
a = data[:, 3]

data_mean = np.array(power).mean()
res = "{0:0.2f}".format(data_mean)
data_mean = np.full(power.size, data_mean)

red_patch = mpatches.Patch(color='red', label='Power from out.txt file bb :D')
blue_patch = mpatches.Patch(color='blue', label='mean value ='+str(res)+"dB")

plt.plot(power, 'r--', data_mean, 'b-')
plt.title("Power ")
plt.xlabel("over time (**)")
plt.ylabel("power axis (dB)")
plt.legend(handles=[red_patch, blue_patch])
plt.show()
