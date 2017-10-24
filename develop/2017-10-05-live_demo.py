import serial
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter, medfilt

from tiretread import *

# plt.ioff()

acq_port = 'COM10'
baudrate = 115200

# configurations that used in the treads detection algorithm
# raw image params
thresh = 50.0
pix_num, pix_size = 1000, 0.0055
# system params
baseline, sensor2baseline_offset, d0 = 10.067, 1.25, 5.549

# tread params
win_size, edge_size, edge_expand = 30, 10, 5
min_tread_width, max_tread_width, max_treads_num, treads_num = 20, 80, 8, 4
min_treads_score = 0.5

# profile smoothing params for Savitzky–Golay smoothing 
spike_size, filt_size, fit_order = 2, 11, 3

with serial.Serial() as rser:
    rser.baudrate = baudrate
    rser.port = acq_port
    rser.open()
    if rser.is_open:
        rser.write(b'd')

    while True:
        trigger_measurement =  input("Enter to trigger acquisition, enter 'b' to exit: ")
        if trigger_measurement == 'b':
            break
        else:
            rser.timeout = 2
        rser.write(b'r')
        
        img = np.fromstring(rser.readall(), dtype='uint8')
        size = len(img)
        print(size)
        if size > pix_num:
            offset = size - size // pix_num * pix_num
            img = img[offset:].reshape(size // pix_num, pix_num)
            img = img.astype(np.float32)
            plt.imshow(img, vmin=0, vmax=255);plt.show()
            # print(img.shape)
            # img = img[:2000,:]
            img -= img.min()
            img *= 255 / img.max()
            img[img < thresh] = 0

            profile = get_profile(img, spike_size, filt_size, fit_order)
            profile_diff = profile[:-edge_size] - profile[edge_size:]

            treads_edge = find_treads(profile_diff, edge_size, win_size, max_treads_num, min_tread_width, max_tread_width)
            treads = calibrate_treads(profile, treads_edge, pix_size, edge_expand, 
                                        baseline, d0, sensor2baseline_offset)
            treads_depth = - treads.min(axis=1)

            idx_peaks_dips = treads_edge - [0, edge_size]
            treads_score = get_treads_score(profile_diff, treads_depth, idx_peaks_dips)
            picked_treads_idx = (treads_score.argsort())[-treads_num:]
            picked_treads_idx = picked_treads_idx[treads_score[picked_treads_idx] > min_treads_score]
            picked_treads = treads[picked_treads_idx]
            picked_treads_depth = treads_depth[picked_treads_idx]
            picked_treads_score = treads_score[picked_treads_idx]
            picked_treads_edge = treads_edge[picked_treads_idx]

            resized_img = np.flipud(img[:, int(profile.min()):int(profile.max())].T)
            plt.figure()
            plt.subplot(311)
            plt.imshow(resized_img, aspect=0.1 * resized_img.shape[1]/resized_img.shape[0])

            plt.subplot(312)
            plt.plot(profile)
            for (s, e) in treads_edge:
                plt.axvline(x=s, color='r')
                plt.axvline(x=e, color='r')
            for (s, e) in picked_treads_edge:
                plt.axvline(x=s, color='g')
                plt.axvline(x=e, color='g')
                plt.xlim(0, len(profile))
                
            plt.subplot(313)
            if len(treads):
                plt.plot(picked_treads.T)
                plt.legend(picked_treads_depth)
            # plt.show()

        else:
            print("No data read in before time out")
    else:
        print("cannot open the data COM port, check port #")

