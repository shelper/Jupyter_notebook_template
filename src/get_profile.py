import matplotlib.pyplot as plt
import numpy as np
import cv2
import glob
import scipy.signal as signal

width = 40


files = glob.glob('../data/20170222/*.bmp')
files0 = files[::2]
files1 = files[1::2]
for f0, f1 in zip(files0, files1):
    tmpfile = f0 + '.png'
    im0 = cv2.imread(f0, 0).astype('float')
    im1 = cv2.imread(f1, 0).astype('float')
    line_img = im1-im0
    line_img = line_img[:-1, :]
    line_center = np.argmax(line_img.mean(axis=1))
    line_img = line_img[line_center - width: line_center + width, :]
    line_img -= line_img.min()
    line_img = line_img.astype(np.uint8)

    # plt.imshow(line_img, cmap='hot')
    # plt.gcf().set_size_inches(9,2)
    # plt.gcf().tight_layout()
    # plt.savefig(tmpfile)
    # plt.close()


    # smooth and thresholding the image
    # TODO test if thresh => smooth => thresh works better in despeckle
    tmpfile = f0 + 'filtered.png'
    line_img = cv2.GaussianBlur(line_img, ksize=(0, 0), sigmaX=3, sigmaY=1.5)
    line_img[line_img <30] = 0
    # plt.imshow(line_img, vmax=100, cmap='hot')
    # plt.gcf().set_size_inches((9, 2))
    # plt.gcf().tight_layout()
    # plt.savefig(tmpfile)
    # plt.close()

    # setup a slider window to find the center of the line at each column
    # tmpfile = 'profile.png'
    tmpfile = f1 + 'profile.png'
    h, w = line_img.shape
    profile = np.zeros(w)
    d_n = np.arange(h)
    for i in range(1, w):
        col = line_img[:, i]
        if sum(d_n * col) < 1000:
            profile[i] = profile[i-1]
        else:
            profile[i] = sum(d_n * col) / col.sum()

    profile = profile.mean() - profile
    plt.plot(profile, label=os.path.basename(f0))
    plt.legend()
    plt.savefig(tmpfile)
    plt.close()

    # profile2 = signal.savgol_filter(profile, 51, 3)
    # plt.plot(profile2)

    # plt.gcf().set_size_inches((8, 2))
    # plt.gcf().tight_layout()
    # plt.savefig(tmpfile)
    # plt.close()
