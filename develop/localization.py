from scipy import signal
import numpy as np
import matplotlib.pyplot as plt
# gaussian beam with 250 beam width
nmu, nsigma = 0, 4
width = 201
s = signal.general_gaussian(width, p=1, sig=100/2.355) * 128

r = np.ndarray(10000)
for i in range(10000):
# loop 1000 times 
    noise = np.random.normal(nmu, nsigma, width)
    sp_noise = np.sin(np.random.uniform(0, 2*np.pi, width))/2 + 0.5
    sig = s * sp_noise + noise
    plt.figure(), plt.plot(sig)
    wc = np.sum(np.arange(width)  * sig) / sig.sum()
    r[i] = wc - width // 2

plt.figure()
plt.hist(r)
plt.show()