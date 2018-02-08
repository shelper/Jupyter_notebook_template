from tkinter import constants, filedialog, Button, Frame, Tk, Entry, Label,\
    StringVar, ttk, IntVar, Checkbutton, messagebox, Checkbutton, Scale, \
    LabelFrame, W, E

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import serial
from serial.tools import list_ports
from scipy.optimize import minimize, least_squares


CMD_CAPTURE = b'!Z0001'
CMD_FREERUNON = b'!Z00080001'
CMD_FREERUNOFF = b'!Z00080000'
CMD_SETEXPO = b'!Z000A'
CMD_GETEXPO = b'!Z000A0000'
CMD_GETVERSION = b'!Z00040000'
PULSE2EXPO = 0.3734

pix_num = 1500
pix_size = 0.0055


class CalibrationTool(Frame):
    def __init__(self, root):
        self.root = root
        self.ser = None
        self.baudrate = 115200
        self.timeout = 3
        self.img = None
        self.img_file = StringVar()
        self.port = StringVar()
        self.fw_version = StringVar()

        Frame.__init__(self, root)
        pack_opt = {'fill': constants.BOTH, 'padx': 10, 'pady': 5}

        group0 = LabelFrame(self, text="Board", padx=5, pady=5)
        group0.pack(padx=10, pady=10)
        Label(group0, text="Port:").grid(row=0, column=0)
        Entry(group0, textvariable=self.port, width=14).grid(row=0, column=1)
        Label(group0, text="FW ver:").grid(row=1, column=0)
        Entry(group0, textvariable=self.fw_version, width=14).grid(row=1, column=1)
        Button(group0, text='FindBoard', relief=constants.GROOVE, 
            font=('sans', '10', 'bold'), command=self.connect).grid(row=3, columnspan=2, sticky=W+E)
        self.exposure = Scale(group0, label='exposure time(us)', from_=50, to=2000, resolution=50, orient=constants.HORIZONTAL)
        self.exposure.bind("<ButtonRelease-1>", self.set_exposure)
        self.exposure.grid(row=4, columnspan=2, sticky=W+E)

        group1 = LabelFrame(self, text="Board", padx=5, pady=5)
        group1.pack(padx=10, pady=10)
        Button(group1, text='FreeRun', relief=constants.GROOVE, 
                font=('sans', '10', 'bold'), command=self.free_run).pack(**pack_opt)
        Button(group1, text='FrameScan', relief=constants.GROOVE, 
                font=('sans', '10', 'bold'), command=self.frame_scan).pack(**pack_opt)
        Label(group1, text="Save image as").pack(side=constants.TOP, fill=constants.X)
        Entry(group1, textvariable=self.img_file).pack(side=constants.TOP, fill=constants.X)

        self.port.set('COM11')
        self.connect()

        self.step=2.5
        self.offset=11.125
        self.efl=5
        self.baseline=10


    def update_board_config(self):
        self.ser.write(CMD_GETVERSION)
        # version = 
        version = int.from_bytes(self.ser.read(4)[2:4], byteorder='big')
        self.fw_version.set(version)
        # self.fw_version.set(version.hex())

        self.ser.write(CMD_GETEXPO)
        pulse_num = self.ser.read(4)
        pulse_num = pulse_num[2:4][::-1]
        pulse_num = int.from_bytes(pulse_num, byteorder='big')
        self.exposure.set(int(pulse_num * PULSE2EXPO))

    
    def connect(self):
        if self.ser is not None and self.ser.is_open:
            self.update_board_config()
        else:
            try: 
                with serial.Serial(self.port.get(), self.baudrate, timeout=self.timeout) as self.ser:
                    self.update_board_config()
                return True
            except serial.SerialException:
                messagebox.showinfo("warning", "cannot open the port {}".format(self.port.get()))
                return False


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


    def capture(self, line_num, ack='!z', offset=0):
        self.ser.reset_input_buffer() # has to clear up the buffer as the results has redundant data  
        # if line_num == 1000:
        #     cmd = CMD_CAPTURE + b'0000' 
        # else:
        cmd = CMD_CAPTURE + bytes('{:0>4}'.format(hex(line_num)[2:]), 'ascii')
        self.ser.write(cmd)
        ack_received = self.ser.read(len(ack))
        if ack_received != b'!z':
            messagebox.showinfo('warning', 'received ack {} != {}'.format(ack_received, ack))
            # self.ser.reset_input_buffer()
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
        

    def frame_scan(self, line_num=1000):
        with serial.Serial(self.port.get(), self.baudrate, timeout=self.timeout) as self.ser:
            self.img = self.capture(line_num)
            if self.img is None:
                print('fail to acquire frame')
            else:
                fname = self.img_file.get().strip()
                if fname:
                    Image.fromarray(self.img).save(fname + '.bmp', 'bmp')
                    try:
                        fname = '{:04d}'.format(int(fname) + 1)
                        self.img_file.set(fname)
                    except ValueError:
                        pass

    def find_steps(self):
        #TODO put Lintao's MatLab algorithm here
        pass


    def calibrate(self):
        from sympy.abc import b, f, o, x

        peaks = self.find_steps(self.img)

        y = (o + x) * f / ((o + x) - b)
        # x = (y * b) / (y - f) - o
        xs = [i * pix_size for i in peaks]
        for i, xn in enumerate(xs):
            if i == 0:
                e = 0 
            else:
                e += (y.subs(x, xn) - y.subs(x, xp) - step) ** 2
            xp = xn

        cost_func = lambdify([[o, f, b]], e)
        get_depth = lambdify((o, f, b, x), y)
        get_error = lambdify((o, f, b), e)

        cal_args = minimize(cost_func, [self.offset, self.efl, self.baseline], method='CG')
        self.offset, self.efl, self.baseline = cal_args.x
        measured_depths = [get_depth(self.offset, self.efl, self.baseline, x) for x in xs]
        error = get_error(self.offset, self.efl, self.baseline)


    def free_run(self):
        with serial.Serial(self.port.get(), self.baudrate, timeout=self.timeout) as self.ser:
            self.ser.write(CMD_FREERUNON)
            # print(self.ser.read(3))
            print('turn on free run, response:', self.ser.read(3))
            fig = plt.figure('freerun')
            axes = fig.add_subplot(111)
            axes.clear()
            axes.set_autoscaley_on(False)
            axes.set_ylim([0, 255])
            line_idx = 0
            while plt.fignum_exists('freerun'):
                data = self.capture(1)
                # self.ser.reset_input_buffer()
                # self.ser.write(CMD_CAPTURE1LINE)
                # self.ser.read(2)
                # data = np.fromstring(self.ser.read(pix_num), dtype='uint8')
                line_idx += 1
                if line_idx == 1:
                    line, = axes.plot(data)
                else:
                    line.set_ydata(data)
                plt.pause(0.01)
                self.update()

            self.ser.write(CMD_FREERUNOFF)
            print('exit free run')


if __name__ == '__main__':
    root = Tk()
    main_win = CalibrationTool(root)
    main_win.pack()

    # def on_closing():
    #     if main_win.ser.is_open:
    #         main_win.ser.close()
    #     root.destroy()

    # root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

