
from tkinter import constants, filedialog, Button, Frame, Tk, Entry, Scale, Label, StringVar, ttk, IntVar, Checkbutton, messagebox, Checkbutton
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
plt.ion()

from PIL import Image
from tiretread import *

# raw image params
thresh = 40.0
pix_num, pix_size = 1500, 0.0055
baseline, sensor2baseline_offset, d0 = 10.067, -0.45, 5.549

# tread params
win_size, edge_size, edge_expand = 30, 10, 5
min_tread_width, max_tread_width, max_treads_num, treads_num = 20, 80, 8, 4
min_treads_score = 0.5

# profile smoothing params for Savitzky–Golay smoothing 
spike_size, filt_size, fit_order = 2, 11, 3
    

class FileDialog(Frame):
    def __init__(self, root):
        self.img_file = StringVar()

        Frame.__init__(self, root)
        pack_opt = {'fill': constants.BOTH, 'padx': 10, 'pady': 5}

        Label(self, text="Load Image").pack(side=constants.TOP, fill=constants.X)
        Entry(self, textvariable=self.img_file).pack(side=constants.TOP, fill=constants.X)
        self.img_file.set('0011.bmp')

        self.offset = Scale(self, from_=-1, to=1, resolution=0.01, orient=constants.HORIZONTAL)
        self.offset.bind("<ButtonRelease-1>", self.find_treads)
        self.offset.pack()

        # self.pullfrom = os.path.abspath('./')
        Button(self, text='FindTreads', relief=constants.GROOVE, 
               font=('sans', '10', 'bold'), command=self.find_treads).pack(**pack_opt)
        

    def find_treads(self, event):
        sensor2baseline_offset = self.offset.get()
        # print(sensor2baseline_offset)
        img = np.array(Image.open(self.img_file.get()))
        plt.figure('RawData')
        plt.imshow(img, vmin=0, vmax=255)

        
        profile = get_profile(img, thresh, spike_size, filt_size, fit_order)
        profile_diff = profile[:-edge_size] - profile[edge_size:]

        treads_edge = find_treads(profile_diff, edge_size, win_size, max_treads_num, min_tread_width, max_tread_width)
        treads = calibrate_treads(profile, treads_edge, pix_size, edge_expand, 
                                    baseline, d0, sensor2baseline_offset)
        treads_depth = - treads.min(axis=1)
        # print(treads_depth)

        idx_peaks_dips = treads_edge - [0, edge_size]
        treads_score = get_treads_score(profile_diff, treads_depth, idx_peaks_dips)
        picked_treads_idx = (treads_score.argsort())[-treads_num:]
        picked_treads_idx = picked_treads_idx[treads_score[picked_treads_idx] > min_treads_score]
        picked_treads_idx.sort()

        picked_treads = treads[picked_treads_idx]
        picked_treads_depth = treads_depth[picked_treads_idx]
        # picked_treads_score = treads_score[picked_treads_idx]
        picked_treads_edge = treads_edge[picked_treads_idx]

        tread_legend = []
        for i, depth in zip(picked_treads_idx, picked_treads_depth):
            depth = int(round(depth / 25.4 * 32))
            tread_legend.append('{0:d} : {1:d}/32'.format(i, depth))

        plt.figure('Treads')
        # resized_img = np.flipud(img[:, int(profile.min()):int(profile.max())].T)
        # plt.subplot(311)
        # plt.imshow(resized_img, aspect=0.1 * resized_img.shape[1]/resized_img.shape[0])

        plt.subplot(211)
        plt.cla()
        plt.plot(profile)
        for (s, e) in treads_edge:
            plt.axvline(x=s, color='r')
            plt.axvline(x=e, color='r')
        for (s, e) in picked_treads_edge:
            plt.axvline(x=s, color='g')
            plt.axvline(x=e, color='g')
            plt.xlim(0, len(profile))
            
        plt.subplot(212)
        plt.cla()
        if len(treads):
            plt.plot(picked_treads.T)
            plt.legend(tread_legend)


if __name__ == '__main__':
    root = Tk()
    main_win = FileDialog(root)
    main_win.pack()


    root.mainloop()

