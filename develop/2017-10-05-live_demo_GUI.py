from tkinter import constants, filedialog, Button, Frame, Tk, Entry, Label, StringVar, ttk, IntVar, Checkbutton, messagebox, Checkbutton, Scale
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
CMD_CAPTURE = b'!Z0001'
CMD_CAPTUREFRAME = b'!Z00010000'
CMD_CAPTURE1LINE = b'!Z00010001'
# CMD_CAPTURE1LINE = b'!Z00010001'
CMD_FREERUNON = b'!Z00080001'
CMD_FREERUNOFF = b'!Z00080000'
# CMD_DEBUGSWITCH = b'!Z00030000'
CMD_SETGETEXPO = b'!Z000A'
CMD_SETDCOFFSET = b'!Z0007'

# raw image params
thresh = 40.0
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
        self.ser = None
        self.baudrate = 115200
        self.timeout = 3
        self.img_file = StringVar()
        self.img = None
        self.cont_capture = IntVar()
        self.root = root
        # self.ser_closed = True

        Frame.__init__(self, root)
        pack_opt = {'fill': constants.BOTH, 'padx': 10, 'pady': 5}

        Label(self, text="Save image as").pack(side=constants.TOP, fill=constants.X)
        Entry(self, textvariable=self.img_file).pack(side=constants.TOP, fill=constants.X)
        self.img_file.set('')

        self.port = StringVar()
        Label(self, text="COM Port Name").pack(side=constants.TOP, fill=constants.X)
        Entry(self, textvariable=self.port).pack(side=constants.TOP, fill=constants.X)
        self.port.set('COM11')

        self.exposure = Scale(self, label='exposure time', from_=50, to=3000, resolution=50, orient=constants.HORIZONTAL)
        self.exposure.bind("<ButtonRelease-1>", self.set_exposure)
        self.exposure.pack(**pack_opt)

        self.offsetDC = Scale(self, label='DC Offset', from_=0, to=3, resolution=0.01, orient=constants.HORIZONTAL)
        self.offsetDC.bind("<ButtonRelease-1>", self.set_offsetDC)
        self.offsetDC.pack(**pack_opt)

        Button(self, text='LineScan', relief=constants.GROOVE, 
               font=('sans', '10', 'bold'), command=self.line_scan).pack(**pack_opt)

        Button(self, text='FrameScan', relief=constants.GROOVE, 
               font=('sans', '10', 'bold'), command=self.frame_scan).pack(**pack_opt)

        Checkbutton(self, text="continuous capture", variable=self.cont_capture).pack(**pack_opt)
        self.cont_capture.set(True)

        self.offsetBL = Scale(self, label='baseline offset', from_=-1, to=1, resolution=0.01, orient=constants.HORIZONTAL)
        self.offsetBL.bind("<ButtonRelease-1>", self.draw_treads)
        self.offsetBL.pack(**pack_opt)

        Button(self, text='FreeRun', relief=constants.GROOVE, 
               font=('sans', '10', 'bold'), command=self.free_run).pack(**pack_opt)
    

    def port_ok(self):
        if self.port.get().strip() == '':
            try:
                port = next(list_ports.grep('ASF example \(COM')).device
                with serial.Serial(port, self.baudrate, timeout=self.timeout) as self.ser:
                    self.port.set(port)
                return True
            except StopIteration:
                messagebox.showinfo("warning", "no COM port found for the device")
                return False
            except serial.SerialException:
                messagebox.showinfo("warning", "cannot open the port {}".format(self.port.get()))
                return False
        else:
            try: 
                with serial.Serial(self.port.get(), self.baudrate, timeout=self.timeout) as self.ser:
                    return True
            except serial.SerialException:
                # messagebox.showinfo("warning", "wrong port number")
                try:
                    port = next(list_ports.grep('ASF example \(COM')).device
                    with serial.Serial(port, self.baudrate, timeout=self.timeout) as self.ser:
                        self.port.set(port)
                    return True
                except StopIteration:
                    messagebox.showinfo("warning", "no COM port found for the device")
                    self.port.set('')
                    return False
                except serial.SerialException:
                    messagebox.showinfo("warning", "cannot open the port {}".format(self.port.get()))
                return False

    
    def free_run(self, line_num=2, offset=2):
        if self.port_ok(): #and self.debug_on():
            with serial.Serial(self.port.get(), self.baudrate, timeout=self.timeout) as self.ser:
                self.ser.write(CMD_FREERUNON)
                print('turn on free run')
                fig = plt.figure('freerun')
                axes = fig.add_subplot(111)
                axes.clear()
                axes.set_autoscaley_on(False)
                axes.set_ylim([0, 255])
                line, = axes.plot(np.zeros(pix_num * line_num))
                cmd = CMD_CAPTURE + bytes('{:0>4}'.format(hex(line_num)[2:]), 'ascii')
                self.ser.write(cmd)
                line_idx = 0
                while plt.fignum_exists('freerun'):
                    data_size = pix_num * line_num + offset
                    self.ser.reset_input_buffer()
                    data = np.fromstring(self.ser.read(data_size), dtype='uint8')
                    if data is not None:
                        line_idx += 1
                        print('capturing {} line'.format(line_idx))
                        line.set_ydata(data[offset:])
                        plt.pause(0.01)
                    else:
                        break
                self.ser.write(CMD_FREERUNOFF)
                print('exit free run')

    
    def stop_acquisition(self):
        pass

    def set_exposure(self, event=None):
        # self.ser.write(CMD_SETGETEXPO + b'0000')
        # pulse_num = self.ser.read(4)[::-1][:2]
        # pulse_num = int.from_bytes(pulse_num, byteorder='big')
        # self.exposure.set(pulse_num)
        # print('previous exposure pulse num: ', pulse_num)
        pulse_num = self.exposure.get()
        cmd = CMD_SETGETEXPO + bytes('{:0>4}'.format(hex(pulse_num)[2:]), 'ascii')
        if self.ser.is_open:
            self.ser.write(cmd)
        else:
            with serial.Serial(self.port.get(), self.baudrate, timeout=self.timeout) as self.ser:
                self.ser.write(cmd)
        print('new exposure pulse num: ', pulse_num)


    def set_offsetDC(self, event=None):
        # if self.port_ok(): #and self.debug_on():
        offsetDC = self.offsetDC.get()
        cmd = CMD_SETDCOFFSET + bytes('{:0>4}'.format(hex(int(offsetDC * 100))[2:]), 'ascii')
        if self.ser.is_open:
            self.ser.write(cmd)
            self.ser.read(4)
        else:
            with serial.Serial(self.port.get(), self.baudrate, timeout=self.timeout) as self.ser:
                self.ser.write(cmd)
                self.ser.read(4)
        print('new DC offset set to {} volts'.format(offsetDC))


    def capture(self, line_num, ack='!z', offset=0):
        # self.ser.write(CMD_FREERUNOFF)
        # ack = self.ser.readall()
        # print('free run off', ack)
        # self.ser.write(CMD_CAPTUREFRAME)
        # ack = self.ser.read(2)
        # print('capture frame', ack)
        # cmd = CMD_CAPTURE + bytes('{:04d}'.format(line_num), 'ascii')
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
            # self.ser.reset_input_buffer()
            if len(data) == data_size:
                data = data[offset:] if line_num == 1 else data[offset:].reshape(line_num, pix_num)
                return data
            else:
                messagebox.showinfo('warning', 'received size {} != requested {}'.format(len(data), data_size))
                return None
        
    def line_scan(self, line_num=1, offset=0):  # acquire and display line in realtime
        if self.port_ok(): # and self.debug_on():
            with serial.Serial(self.port.get(), self.baudrate, timeout=self.timeout) as self.ser:
                fig = plt.figure('line')
                axes = fig.add_subplot(111)
                axes.clear()
                axes.set_autoscaley_on(False)
                axes.set_ylim([0, 255])
                data = self.capture(line_num, offset=offset)
                if data is not None:
                    line_idx = 1
                    line, = axes.plot(data)
                    while plt.fignum_exists('line') and self.cont_capture.get():
                        data = self.capture(line_num, offset=offset)
                        if data is not None:
                            line_idx += 1
                            print('capturing {} line'.format(line_idx))
                            # line.set_label('capturing {} line'.format(line_idx))
                            line.set_ydata(data)
                            plt.pause(0.01)
                            self.update()
                        else:
                            break

    def save_rawdata(self):
        fname = self.img_file.get().strip()
        if fname:
            Image.fromarray(self.img).save(fname + '.bmp', 'bmp')
            try:
                fname = '{:04d}'.format(int(fname) + 1)
                self.img_file.set(fname)
            except ValueError:
                pass

    def frame_scan(self, line_num=1000, offset=0):
        if self.port_ok(): # and self.debug_on(): 
            with serial.Serial(self.port.get(), self.baudrate, timeout=self.timeout) as self.ser:
                fig = plt.figure('Frame')
                gs = GridSpec(2, 2)
                ax1 = plt.subplot(gs[:, 0])
                plt.subplot(gs[0, 1])
                plt.subplot(gs[1:,1])
                self.img = self.capture(line_num, offset=offset)
                if self.img is not None:
                    frame_idx = 1
                    ax1.imshow(self.img, vmin=0, vmax=255)
                    self.draw_treads()
                    self.save_rawdata()
                    while plt.fignum_exists('Frame') and self.cont_capture.get():
                        self.img = self.capture(line_num, offset=offset)
                        if self.img is not None:
                            frame_idx += 1
                            print('capturing {} frame'.format(frame_idx))
                            ax1.imshow(self.img, vmin=0, vmax=255)
                            self.draw_treads()
                            self.save_rawdata()
                            self.update()
                        else:
                            break
        

    def draw_treads(self, event=None):
        if not plt.fignum_exists('Frame'):
            return
        else:
            fig = plt.figure('Frame')
            ax2, ax3 = fig.get_axes()[1:]

            profile = get_profile(self.img.copy(), thresh, spike_size, filt_size, fit_order)
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

            plt.pause(0.05) 

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

