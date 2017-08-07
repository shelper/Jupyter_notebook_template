import serial
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
plt.ion()

pix_num = 1000
debug_port = 'COM9'
acq_port = 'COM11'
baudrate = 115200

with serial.Serial() as dser:
    dser.baudrate = baudrate
    dser.port = debug_port
    dser.timeout = 3
    dser.open()
    if dser.is_open:
        dser.write(b'D')
    else:
        print("cannot open the DEBUG COM port, check port #")
    
img_idx = 1
while True:
    with serial.Serial() as rser:
        rser.baudrate = baudrate
        rser.port = acq_port
        timeout =  input("input timeout(s), enter 'b' to stop, none for default(5s): ")
        if not timeout:
            rser.timeout = 5
        elif timeout == 'b':
            break
        else:
            rser.timeout = int(timeout)

        rser.open()
        if rser.is_open:
            raw_data = np.fromstring(rser.readline(), dtype='uint8')
            size = len(raw_data)
            if size > pix_num:
                offset = size - size // pix_num * pix_num
                raw_data = raw_data[offset:].reshape(size // pix_num, pix_num)
                plt.imshow(raw_data, vmin=0, vmax=135)
                # plt.show()
                Image.fromarray(raw_data, 'L').save('.'.join(('raw_img' + str(img_idx), 'bmp')), 'bmp')
                img_idx += 1
            else:
                print("No data read in before time out")
        else:
            print("cannot open the data COM port, check port #")


        


