#%%
%qtconsole

#%%
import numpy as np
import matplotlib.pyplot as plt
import serial

%matplotlib
plt.ion()

CMD_START = b'!Z00010000'
CMD_READALL = b'!Z00030000'
CMD_READLINE = b'!Z0002'
CMD_STREAMING = b'!Z00080000'

port = 'COM10'
line_num = 1000
rate = 115200
dummy_data_size = 2

#%% old firmware
port = 'COM10'
with serial.Serial(port, rate, timeout=3) as ser:
    ser.write(CMD_READALL)
    ser.write(CMD_START)
    img = np.fromstring(ser.readall(), dtype='uint8')
    print(len(img))
    if len(img):
        img = img[2:]
        img = img.reshape(1000, 1500)
        plt.figure('')
        plt.imshow(img, vmin=0, vmax=255)


#%% start acquisition for whole 1000 lines
with serial.Serial(port, rate, timeout=3) as ser:
    ser.write(CMD_READALL)
    ser.write(CMD_START)
    dummy_data = ser.read(2)
    print(dummy_data)
    if dummy_data == b'!z':
        img = np.fromstring(ser.readall(), dtype='uint8')
        img = img.reshape(1000, 1500)
        # img = img[:100, :]
        plt.figure('')
        plt.imshow(img, vmin=0, vmax=255)

#%% acquire and display line in realtime
with serial.Serial(port, rate, timeout=3) as ser:
    plt.figure(1)
    while True:
        ser.write(CMD_START)
        for i in range(0, 1000, 30):
            ser.write(CMD_READLINE + bytes('{:04d}'.format(1), 'ascii'))
            # dummy_data = ser.read(2)
            line = np.fromstring(ser.read(1500), dtype='uint8')
            if not plt.fignum_exists(1):
                break
            else:
                plt.cla()
                plt.plot(line)
                plt.pause(0.02)
        if not plt.fignum_exists(1):
            break


#%% test readline
with serial.Serial(port, rate, timeout=3) as ser:
    ser.write(CMD_START)
    for i in range(0, 1000, 100):
        ser.write(CMD_READLINE + bytes('{:04d}'.format(1), 'ascii'))
        # dummy_data = ser.readline(2)
        line = np.fromstring(ser.read(3000), dtype='uint8')
        plt.plot(line)
