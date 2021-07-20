import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['figure.dpi'] = 150
plt.rcParams.update({'font.size': 9})

lp = np.loadtxt('lp_2_3.txt')
lpcc = np.loadtxt('lpcc_2_3.txt')
mfcc = np.loadtxt('mfcc_2_3.txt')
fig, axs = plt.subplots(3, ncols=1)
fig.suptitle("2nd vs 3rd coefficients", y=1.02)

lp_2 = lp[:, 0]
lp_3 = lp[:, 1]

lpcc_2 = lpcc[:, 0]
lpcc_3 = lpcc[:, 1]

mfcc_2 = mfcc[:, 0]
mfcc_3 = mfcc[:, 1]

plt.tight_layout()

axs[0].scatter(lp_2, lp_3, label="Lp", color='blue', s=1)
axs[1].scatter(lpcc_2,lpcc_3, label="Lpcc", color='red',  s=1)
axs[2].scatter(mfcc_2,mfcc_3, label="Mfcc",color='green', s=1)

for i in range(3):
    axs[i].set_ylabel("3rd coefficient")
    axs[i].set_xlabel("2nd coefficient")
    axs[i].legend(loc='upper right', prop={'size': 6})

plt.show()