from tkinter import constants, filedialog, Button, Frame, Tk, Entry, Label,\
    StringVar, ttk, IntVar, Checkbutton, messagebox, Checkbutton, Scale, \
    LabelFrame, W, E

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.gridspec import GridSpec
from PIL import Image
import serial
from serial.tools import list_ports
# import time
from tiretread import *

plt.ion()

# configurations that used in the treads detection algorithm
CMD_IMUON = b'!Z000B0001'
CMD_IMUOFF = b'!Z000B0000'
CMD_RESET = b'!Z00060000'

CMD_CAPTURE = b'!Z0001'
CMD_CAPTURE1LINE = b'!Z00010001'
CMD_FREERUNON = b'!Z00080001'
CMD_FREERUNOFF = b'!Z00080000'
CMD_DEBUGSWITCH = b'!Z00030000'
CMD_SETEXPO = b'!Z000A'
CMD_GETEXPO = b'!Z000A0000'
CMD_SETDCOFFSET = b'!Z0007'
CMD_GETDCOFFSET = b'!Z00070000'
CMD_GETVERSION = b'!Z00040000'
PULSE2EXPO = 0.3734
PULSE2DCOFFSET = 0.00080566

# raw image params
pix_num, pix_size = 1500, 0.0055
# system params
baseline, d0 = 10.067, 5.549
sensor2baseline_offset = -0.35
# tread params
win_size, edge_size, edge_expand = 30, 10, 5
min_tread_width, max_tread_width, max_treads_num, treads_num = 20, 80, 8, 4
min_treads_score = 0.5

# profile smoothing params for Savitzky–Golay smoothing 
spike_size, filt_size, fit_order = 2, 11, 3

class FileDialog(Frame):
    def __init__(self, root):
        self.root = root
        self.ser = None
        self.baudrate = 115200
        self.timeout = 3
        self.img = None
        self.img_file = StringVar()
        self.imu_on = IntVar()
        self.cont_capture = IntVar()
        self.img_from_file = IntVar()
        self.port = StringVar()
        self.fw_version = StringVar()
        self.imu_on.set(True)
        self.cont_capture.set(True)
        self.img_from_file.set(False)

        Frame.__init__(self, root)
        pack_opt = {'fill': constants.BOTH, 'padx': 10, 'pady': 5}

        group1 = LabelFrame(self, text="Board", padx=5, pady=5)
        group1.pack(padx=10, pady=10)

        Label(group1, text="Port:").grid(row=0, column=0)
        Entry(group1, textvariable=self.port, width=14).grid(row=0, column=1)
        Label(group1, text="FW ver:").grid(row=1, column=0)
        Entry(group1, textvariable=self.fw_version, width=14).grid(row=1, column=1)
        Checkbutton(group1, text="enable IMU", variable=self.imu_on).grid(row=2, columnspan=2, sticky=W+E)
        Button(group1, text='FindBoard', relief=constants.GROOVE, 
            font=('sans', '10', 'bold'), command=self.find_board).grid(row=3, columnspan=2, sticky=W+E)
        self.exposure = Scale(group1, label='exposure time(us)', from_=50, to=2000, resolution=50, orient=constants.HORIZONTAL)
        self.exposure.bind("<ButtonRelease-1>", self.set_exposure)
        self.exposure.grid(row=4, columnspan=2, sticky=W+E)
        self.offsetDC = Scale(group1, label='DC Offset(v)', from_=0, to=3.3, resolution=0.01, orient=constants.HORIZONTAL)
        self.offsetDC.bind("<ButtonRelease-1>", self.set_offsetDC)
        self.offsetDC.grid(row=5, columnspan=2, sticky=W+E)

        group2 = LabelFrame(self, text="Capture", padx=5, pady=5)
        group2.pack(padx=10, pady=10)
        Checkbutton(group2, text="continuous capture", variable=self.cont_capture).pack(**pack_opt)
        self.cont_capture.set(True)
        Button(group2, text='LineScan', relief=constants.GROOVE, 
                font=('sans', '10', 'bold'), command=self.line_scan).pack(**pack_opt)
        Button(group2, text='FrameScan', relief=constants.GROOVE, 
                font=('sans', '10', 'bold'), command=self.frame_scan).pack(**pack_opt)
        Button(group2, text='FreeRun', relief=constants.GROOVE, 
                font=('sans', '10', 'bold'), command=self.free_run).pack(**pack_opt)
        Label(group2, text="Save image as").pack(side=constants.TOP, fill=constants.X)
        Entry(group2, textvariable=self.img_file).pack(side=constants.TOP, fill=constants.X)

        group3 = LabelFrame(self, text="Processing", padx=5, pady=5)
        group3.pack(padx=10, pady=10)
        Checkbutton(group3, text="image from file", variable=self.img_from_file).pack(**pack_opt)
        self.offsetBL = Scale(group3, label='baseline offset', from_=-1, to=1, resolution=0.01, orient=constants.HORIZONTAL)
        self.offsetBL.bind("<ButtonRelease-1>", self.draw_treads)
        self.offsetBL.pack(**pack_opt)
        self.intensityBL = Scale(group3, label='Intensity baseline', from_=0, to=100, resolution=1, orient=constants.HORIZONTAL)
        self.intensityBL.bind("<ButtonRelease-1>", self.draw_treads)
        self.intensityBL.pack(**pack_opt)
       
    def toggle_board_debug(self):
        if self.ser.is_open:
            self.ser.write(CMD_DEBUGSWITCH)
        else:
            with serial.Serial(self.port.get(), self.baudrate, timeout=self.timeout) as self.ser:
                self.ser.write(CMD_DEBUGSWITCH)
        print('debug toggled')

    def update_board_config(self):
        if self.imu_on.get():
        #     self.ser.write(CMD_IMUON)
        #     print('imu id:', self.ser.read(6))
        #     self.ser.write(CMD_IMUOFF)
        #     self.ser.reset_input_buffer()
        #     # imu_data = self.ser.read(120)
        #     # print(imu_data)
            print('IMU ON')
        else:
            self.ser.write(CMD_IMUOFF)
        #     imu_data = self.ser.read(10)
        #     print(imu_data)
            print('IMU OFF')
        
        self.ser.write(CMD_GETVERSION)
        version = self.ser.read(4)[2:4][::-1]
        # version = int.from_bytes(version, byteorder='big')
        self.fw_version.set(version.hex())
        self.ser.write(CMD_GETEXPO)
        pulse_num = self.ser.read(4)
        pulse_num = pulse_num[2:4][::-1]
        pulse_num = int.from_bytes(pulse_num, byteorder='big')
        # pulse_num = self.ser.read(6)[2:][::-1]
        # pulse_num = int(pulse_num.decode('ascii'), 16)
        self.exposure.set(int(pulse_num * PULSE2EXPO))

        self.ser.write(CMD_GETDCOFFSET)
        offsetDC = self.ser.read(4)
        # print(offsetDC)
        offsetDC = offsetDC[2:4][::-1]
        offsetDC = int.from_bytes(offsetDC, byteorder='big')
        # offsetDC /= 100
        # offsetDC = offsetDC / 4096 * 3.3
        self.offsetDC.set(offsetDC * PULSE2DCOFFSET)
    
    def find_board(self):
        if self.ser is not None and self.ser.is_open:
            self.update_board_config()
        elif self.port.get().strip() == '':
            try:
                port = next(list_ports.grep('ASF example \(COM')).device
                with serial.Serial(port, self.baudrate, timeout=self.timeout) as self.ser:
                    self.port.set(port)
                    self.update_board_config()
            except StopIteration:
                messagebox.showinfo("warning", "no COM port found for the device")
                return False
            except serial.SerialException:
                messagebox.showinfo("warning", "cannot open the port {}".format(self.port.get()))
                return False
        else:
            try: 
                with serial.Serial(self.port.get(), self.baudrate, timeout=self.timeout) as self.ser:
                    self.update_board_config()
            except serial.SerialException:
                try:
                    port = next(list_ports.grep('ASF example \(COM')).device
                    with serial.Serial(port, self.baudrate, timeout=self.timeout) as self.ser:
                        self.port.set(port)
                        self.update_board_config()
                except StopIteration:
                    messagebox.showinfo("warning", "no COM port found for the device")
                    self.port.set('')
                    return False
                except serial.SerialException:
                    messagebox.showinfo("warning", "cannot open the port {}".format(self.port.get()))
                return False

        # self.toggle_board_debug()
        return True

    def set_exposure(self, event=None):
        pulse_num = int(self.exposure.get()/PULSE2EXPO)
        cmd = CMD_SETEXPO + bytes('{:0>4}'.format(hex(pulse_num)[2:]), 'ascii')
        if self.ser is not None:
            if self.ser.is_open:
                self.ser.write(cmd)
            else:
                with serial.Serial(self.port.get(), self.baudrate, timeout=self.timeout) as self.ser:
                    self.ser.write(cmd)
            print('new exposure pulse num: ', pulse_num)

    def set_offsetDC(self, event=None):
        offsetDC = int(self.offsetDC.get()/PULSE2DCOFFSET)
        cmd = CMD_SETDCOFFSET + bytes('{:0>4}'.format(hex(offsetDC)[2:]), 'ascii')
        if self.ser is not None:
            if self.ser.is_open:
                self.ser.write(cmd)
                # print(self.ser.read(4))
            else:
                with serial.Serial(self.port.get(), self.baudrate, timeout=self.timeout) as self.ser:
                    self.ser.write(cmd)
                    # print(self.ser.read(4))
            print('new DC offset set to {} volts'.format(offsetDC))

    def save_rawdata(self):
        fname = self.img_file.get().strip()
        if fname:
            Image.fromarray(self.img).save(fname + '.bmp', 'bmp')
            try:
                fname = '{:04d}'.format(int(fname) + 1)
                self.img_file.set(fname)
            except ValueError:
                pass

    def capture(self, line_num, ack='!z', offset=0):
        self.ser.reset_input_buffer() # has to clear up the buffer as the results has redundant data  
        cmd = CMD_CAPTURE + bytes('{:0>4}'.format(hex(line_num)[2:]), 'ascii')
        self.ser.write(cmd)
        ack_received = self.ser.read(len(ack))
        if ack_received != b'!z':
            messagebox.showinfo('warning', 'received ack {} != {}'.format(ack_received, ack))
            return None
        else:
            data_size = pix_num * line_num + offset
            data = np.fromstring(self.ser.read(data_size), dtype='uint8')
            # data = np.fromstring(self.ser.readall(), dtype='uint8')
            if len(data) == data_size:
                data = data[offset:] if line_num == 1 else data[offset:].reshape(line_num, pix_num)
                return data
            else:
                messagebox.showinfo('warning', 'received size {} != requested {}'.format(len(data), data_size))
                return None
        
    def line_scan(self, line_num=1):  # acquire and display line in realtime
        with serial.Serial(self.port.get(), self.baudrate, timeout=self.timeout) as self.ser:
                fig = plt.figure('line')
                axes = fig.add_subplot(111)
                axes.clear()
                axes.set_autoscaley_on(False)
                axes.set_ylim([0, 255])
                data = self.capture(line_num)
                if data is not None:
                    line_idx = 1
                    line, = axes.plot(data)
                    while plt.fignum_exists('line') and self.cont_capture.get():
                        data = self.capture(line_num)
                        if data is not None:
                            line_idx += 1
                            print('capturing {} line'.format(line_idx))
                            # line.set_label('capturing {} line'.format(line_idx))
                            line.set_ydata(data)
                            plt.pause(0.01)
                            self.update()
                        else:
                            break

    def frame_scan(self, line_num=1000):
        with serial.Serial(self.port.get(), self.baudrate, timeout=self.timeout) as self.ser:
            fig = plt.figure('Frame')
            gs = GridSpec(2, 2)
            plt.subplot(gs[:, 0])
            plt.subplot(gs[0, 1])
            plt.subplot(gs[1:,1])
            self.img = self.capture(line_num)
            if self.img is not None:
                frame_idx = 1
                self.save_rawdata()
                self.draw_treads()
                while plt.fignum_exists('Frame') and self.cont_capture.get():
                    self.img = self.capture(line_num)
                    if self.img is not None:
                        frame_idx += 1
                        # print('capturing {} frame'.format(frame_idx))
                        self.save_rawdata()
                        self.draw_treads()
                        plt.pause(0.05)
                        self.update()
                    else:
                        break
        
    def free_run(self):
        with serial.Serial(self.port.get(), self.baudrate, timeout=self.timeout) as self.ser:
            self.ser.write(CMD_FREERUNON)
            print('turn on free run')
            fig = plt.figure('freerun')
            axes = fig.add_subplot(111)
            axes.clear()
            axes.set_autoscaley_on(False)
            axes.set_ylim([0, 255])
            self.ser.write(CMD_CAPTURE1LINE)
            self.ser.read(2)
            data = np.fromstring(self.ser.read(pix_num), dtype='uint8')
            if data is not None:
                line, = axes.plot(data)
                line_idx = 1
                while plt.fignum_exists('freerun'):
                    self.ser.reset_input_buffer()
                    self.ser.read(2)
                    data = np.fromstring(self.ser.read(pix_num), dtype='uint8')
                    if data is not None:
                        line_idx += 1
                        # print('capturing {} line'.format(line_idx))
                        line.set_ydata(data)
                        plt.pause(0.01)
                        self.update()
                    else:
                        break
            self.ser.write(CMD_FREERUNOFF)
            self.ser.write(CMD_RESET)
            print('exit free run')

    def draw_treads(self, event=None):
        if self.img_from_file.get():
            try:
                self.img = np.array(Image.open(self.img_file.get()))
            except:
                return
        if plt.fignum_exists('Frame') :
            fig = plt.figure('Frame')
        else:
            fig = plt.figure('Frame')
            gs = GridSpec(2, 2)
            plt.subplot(gs[:, 0])
            plt.subplot(gs[0, 1])
            plt.subplot(gs[1:,1])

        ax1, ax2, ax3 = fig.get_axes()
        self.img2 = self.img.astype(np.int16)
        self.img2 -= self.img.min()
        self.img2 -= self.intensityBL.get()
        self.img2[self.img2 < 0] = 0
        self.img2[self.img2 > 127] = 0
        self.img2 = self.img2.astype(np.uint8)
        ax1.imshow(self.img2, vmin=0, vmax=255)
        profile = get_profile(self.img2, spike_size, filt_size, fit_order)
        profile_diff = profile[:-edge_size] - profile[edge_size:]
        treads_edge = find_treads(profile_diff, edge_size, win_size, max_treads_num, min_tread_width, max_tread_width)
        treads = calibrate_treads(profile, treads_edge, pix_size, edge_expand, 
                                    baseline, d0, self.offsetBL.get())
        if treads is None:
            plt.sca(ax2)
            plt.cla()
            plt.sca(ax3)
            plt.cla()
        else:
            treads_depth = -treads.min(axis=1)
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

            plt.sca(ax2)
            plt.cla()
            plt.plot(profile)
            for (s, e) in treads_edge:
                plt.axvline(x=s, color='r')
                plt.axvline(x=e, color='r')
            for (s, e) in picked_treads_edge:
                plt.axvline(x=s, color='g')
                plt.axvline(x=e, color='g')
                plt.xlim(0, len(profile))
                
            # plt.subplot(212)
            plt.sca(ax3)
            plt.cla()
            if len(treads):
                plt.plot(picked_treads.T)
                plt.legend(tread_legend)


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

