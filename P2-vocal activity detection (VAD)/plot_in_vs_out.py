
import numpy as np
from scipy.io import wavfile
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
plt.rcParams['figure.dpi'] = 200

samplerate_in, data_in = wavfile.read('in.wav')
samplerate_out, data_out = wavfile.read('out.wav')


red_patch = mpatches.Patch(color='red', label='Input file', linewidth=0.2)
blue_patch = mpatches.Patch(color='blue', label='Output file', linewidth=0.2)
fig, axs = plt.subplots(2)

axs[0].plot(data_in, 'r--', linewidth=0.2)
axs[0].set_ylabel("amplitude")
axs[1].plot( data_out, 'b-', linewidth=0.2)
fig.suptitle("Input and output (cancelled silences)")
plt.xlabel("time (s)")
plt.ylabel("amplitude")
plt.legend(handles=[red_patch, blue_patch])
plt.show()