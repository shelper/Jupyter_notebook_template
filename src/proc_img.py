from PIL import Image, ImageFilter
import numpy as np
import matplotlib.pyplot as plt

import matplotlib
matplotlib.pyplot.plot()

im0 = np.array(Image.open('../data/20170126/H12.4_D15.5_Off.bmp').convert("L")).astype('float')
im1 = np.array(Image.open('../data/20170126/H12.4_D15.5_On.bmp').convert("L")).astype('float')

img_lsr = im1-im0
img_lsr[img_lsr<0] = 0
Image.fromarray(img_lsr.astype(np.uint8)).save('H12.4_D15.5.bmp')
import cv2

img = cv2.imread('H12.4_D15.5.bmp', 0)
img = img[:-1, :]

w = 30
line_center = np.argmax(img.mean(axis=1))
subimg = img[line_center - w: line_center + w, :]

plt.imshow(subimg>50)

edges = cv2.Canny(img,50,150,apertureSize = 3)

lines = cv2.HoughLines(edges,1,np.pi/180,200)
for rho,theta in lines[0]:
    a = np.cos(theta)
    b = np.sin(theta)
    x0 = a*rho
    y0 = b*rho
    x1 = int(x0 + 1000*(-b))
    y1 = int(y0 + 1000*(a))
    x2 = int(x0 - 1000*(-b))
    y2 = int(y0 - 1000*(a))

    cv2.line(img,(x1,y1),(x2,y2),(0,0,255),2)

cv2.imwrite('houghlines3.jpg',img)


class ClassName(object):
    """Documentation for ClassName

    """
    def __init__(self, args):
        super(ClassName, self).__init__()
        self.args = args



