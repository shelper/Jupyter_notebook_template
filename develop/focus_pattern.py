#%%
import numpy as np
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
plt.ion()

#%%
def gen_focus_pattern(offset, efl, baseline, yb, ye, cycle_num, img_size):

    pix_size = 0.0055
    xb = (yb * baseline) / (yb - efl) - offset
    xe = (ye * baseline) / (ye - efl) - offset
    xb_pix = round(xb / pix_size)
    xe_pix = round(xe / pix_size)
    xs = np.linspace(xb_pix * pix_size, xe_pix * pix_size, img_size[1])
    ys = (offset + xs) * efl / ((offset + xs) - baseline)
    ys0 = np.linspace(ys[0], ys[-1], len(ys))

    mul = cycle_num * 2 * np.pi / (ys[-1] - ys[0])
    pattern = np.sin(ys * mul) + 1
    pattern =  np.tile(pattern, (img_size[0], 1))
    plt.imshow(pattern, cmap='gray')
    pattern_8bit = (pattern * 128).astype(np.uint8)
    Image.fromarray(pattern_8bit).save('focus_pattern.bmp', 'bmp')
# pattern = np.sin(ys0 * mul)
# plt.plot(pattern)
# plt.plot(ys)
# plt.plot(ys0)
# resampled_pattern = np.interp(ys, ys0, pattern)

#%%
yb = 15
ye = 50
cycle_num = ye - yb
offset, efl, baseline = 8, 5, 10
img_size = [500, 1500]
gen_focus_pattern(offset, efl, baseline, yb, ye, cycle_num, img_size)