from tkinter import constants, filedialog, Button, Frame, Tk, Entry, Label, StringVar, ttk, IntVar, Checkbutton, messagebox, Checkbutton
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

import serial
from serial.tools import list_ports
# import time
from tiretread import *

# configurations that used in the treads detection algorithm
CMD_CAPTUREFRAME = b'!Z00010000'
CMD_CAPTURE1LINE = b'!Z00010001'
CMD_DEBUGSWITCH = b'!Z00030000'

# raw image params
thresh = 30.0
pix_num, pix_size = 1500, 0.0055
# system params
baseline, sensor2baseline_offset, d0 = 10.067, 0.47, 5.549

# tread params
win_size, edge_size, edge_expand = 30, 10, 5
min_tread_width, max_tread_width, max_treads_num, treads_num = 20, 80, 8, 4
min_treads_score = 0.5

# profile smoothing params for Savitzky–Golay smoothing 
spike_size, filt_size, fit_order = 2, 11, 3
    

class FileDialog(Frame):
    def __init__(self, root):
        Frame.__init__(self, root)
        pack_opt = {'fill': constants.BOTH, 'padx': 10, 'pady': 5}

        self.img_file = StringVar()
        Label(self, text="Save image as").pack(side=constants.TOP, fill=constants.X)
        Entry(self, textvariable=self.img_file).pack(side=constants.TOP, fill=constants.X)
        self.img_file.set('0001')

        # self.acq_port = StringVar()
        # Label(self, text="Port").pack(side=constants.TOP, fill=constants.X)
        # Entry(self, textvariable=self.acq_port).pack(side=constants.TOP, fill=constants.X)
        # self.acq_port.set(port_name)
        # self.ser = serial.Serial()
        # self.timeout = 3

        # self.pullfrom = os.path.abspath('./')
        Button(self, text='LineScan', relief=constants.GROOVE, 
               font=('sans', '10', 'bold'), command=self.line_scan).pack(**pack_opt)

        # self.pullfrom = os.path.abspath('./')
        Button(self, text='FrameScan', relief=constants.GROOVE, 
               font=('sans', '10', 'bold'), command=self.frame_scan).pack(**pack_opt)

        self.baudrate = 115200
        self.port = None
        self.timeout = 3

    def line_scan(self):
        try:
            self.port = next(list_ports.grep('ASF example \(COM')).device
        except:
            messagebox.showinfo("warning", "no COM port found for the device, check connection")
            return

        #%% acquire and display line in realtime
        plt.figure('line')
        with serial.Serial(self.port, self.baudrate, timeout=self.timeout) as ser:
            # ser.write(CMD_DEBUGSWITCH)
            while True:
                ser.write(CMD_CAPTURE1LINE)
                try:
                    dummy_data = ser.read(2)
                    line = np.fromstring(ser.read(1500), dtype='uint8')
                    if not plt.fignum_exists('line'):
                        break
                    else:
                        plt.cla()
                        plt.plot(line)
                        plt.pause(0.005)
                except:
                    break
        if plt.fignum_exists('line'):
            plt.close('line')

    def frame_scan(self):
        if not self.ser.is_open: 
            self.ser.port = self.acq_port.get()
            self.ser.baudrate = 115200
            self.ser.timeout = 3
            self.ser.open()
            self.ser.write(CMD_DEBUGSWITCH)
            # try:
            #     rser.open()
                # except:
                #     messagebox.showinfo("warning", "cannot open the com port, please check device manager")
                #     return
        if self.ser.is_open:
            self.ser.write(CMD_CAPTUREFRAME)
            img = np.fromstring(self.ser.readall(), dtype='uint8')
            size = len(img)
            print(size)
            if size > pix_num:
                try:
                    offset = size - size // pix_num * pix_num
                    img = img[offset:].reshape(size // pix_num, pix_num)
                    print(img.mean())
                    fname = self.img_file.get()
                    mpl.image.imsave(fname + '.png', img, cmap=mpl.cm.Greys_r)
                    try:
                        fname = '{:04d}'.format(int(fname) + 1)
                        self.img_file.set(fname)
                    except ValueError:
                        pass

                    # img = img[:, 200:700]
                    # img = img.astype(np.float32)
                    # img -= img.min()
                    # img *= 255 / img.max()
                    # img[img < (thresh + 128)] = 0
                    plt.imshow(img, vmin=0, vmax=255);plt.show()

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
                    picked_treads_idx.sort()

                    picked_treads = treads[picked_treads_idx]
                    picked_treads_depth = treads_depth[picked_treads_idx]
                    # picked_treads_score = treads_score[picked_treads_idx]
                    picked_treads_edge = treads_edge[picked_treads_idx]

                    tread_legend = []
                    for i, d in zip(picked_treads_idx, picked_treads_depth):
                        tread_legend.append('{0:d} : {1:.1f}'.format(i, d))

                    plt.figure()
                    # resized_img = np.flipud(img[:, int(profile.min()):int(profile.max())].T)
                    # plt.subplot(311)
                    # plt.imshow(resized_img, aspect=0.1 * resized_img.shape[1]/resized_img.shape[0])

                    plt.subplot(211)
                    plt.plot(profile)
                    for (s, e) in treads_edge:
                        plt.axvline(x=s, color='r')
                        plt.axvline(x=e, color='r')
                    for (s, e) in picked_treads_edge:
                        plt.axvline(x=s, color='g')
                        plt.axvline(x=e, color='g')
                        plt.xlim(0, len(profile))
                        
                    plt.subplot(212)
                    if len(treads):
                        plt.plot(picked_treads.T)
                        plt.legend(tread_legend)
                    plt.show()
                    # self.ser.close()
                except:
                    messagebox.showinfo("warning", "no tread can be found")
            else:
                messagebox.showinfo("warning", "data reading error, try again")
                self.ser.close()
        else:
            messagebox.showinfo("warning", "cannot open the com port, please try again")
            # self.ser.close()
            

if __name__ == '__main__':
    root = Tk()
    main_win = FileDialog(root)
    main_win.pack()

    # def on_closing():
    #     if main_win.ser.is_open:
    #         main_win.ser.close()
    #     root.destroy()

    # root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

