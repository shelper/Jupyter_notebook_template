import numpy as np
import cv2

gray = cv2.imread('../data/box.png', 0)

gray = np.float32(gray)

corners = cv2.goodFeaturesToTrack(gray, 100, 0.01, 50)
corners = np.int0(corners)
img = cv2.cvtColor(gray,cv2.COLOR_GRAY2RGB)

for corner in corners:
    x,y = corner.ravel()
    cv2.circle(img,(x,y),10,255,-1)

plt.imshow(img)
plt.show()

dst = cv2.cornerHarris(gray,10,1,0.08)
dst = np.round(dst)
plt.imshow(dst, cmap='hot')
plt.show()

# Threshold for an optimal value, it may vary depending on the image.
img = cv2.cvtColor(gray,cv2.COLOR_GRAY2RGB)
for corner in dst:
    x,y = corner.ravel()
    cv2.circle(img,(x,y),30,255,-1)
plt.imshow(img)
plt.show()

# line detection
edges = cv2.Canny(gray,50,150,apertureSize = 3)
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

plt.imshow(img, cmap='hot')
plt.show()
