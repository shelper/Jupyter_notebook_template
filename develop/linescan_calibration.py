
# coding: utf-8

# In[1]:

get_ipython().magic('load_ext autoreload')
get_ipython().magic('autoreload 2')
get_ipython().magic('qtconsole --style monokai')
get_ipython().magic('pylab')


# In[2]:

import numpy as np
import cv2
import glob

image_files = glob.glob('./calibration/*.bmp')
pattern_size = (6, 8)

def get_cam_matrix(image_files, pattern_size=(6, 8)):
    # termination criteria
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    objp = np.zeros((np.product(pattern_size), 3), np.float32)
    objp[:, :2] = np.mgrid[0:pattern_size[0], 0:pattern_size[1]].T.reshape(-1, 2)

    # Arrays to store object points and image points from all the images.
    obj_points = []  # 3d point in real world space
    img_points = []  # 2d points in image plane.

    for img_file in image_files:
        img = cv2.imread(img_file, flags=cv2.IMREAD_GRAYSCALE)

        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(img, pattern_size, None)

        # If found, add object points, image points (after refining them)
        if ret:
            obj_points.append(objp)
            cv2.cornerSubPix(img,corners,(11,11),(-1,-1),criteria)
            img_points.append(corners)
            # Draw and display the corners
            # cv2.drawChessboardCorners(img, (8,6), corners, ret)
            # cv2.imshow('img',img)
            # cv2.waitKey(500)

    ret, cam_matrix, dist_coeff, rvecs, tvecs = cv2.calibrateCamera(obj_points, img_points, img.shape[::-1], None, None)
    return ret, cam_matrix, dist_coeff, rvecs, tvecs


# In[3]:

print(get_cam_matrix(image_files[3:4]))
# h,  w = img.shape[:2]
# newcameramtx, roi=cv2.getOptimalNewCameraMatrix(mtx,dist,(w,h),1,(w,h))

# dst = cv2.undistort(img, mtx, dist, None, newcameramtx)
# cv2.imwrite('calibresult.png')


# In[108]:

mean_error = 0
for i in range(len(objpoints)):
    imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
    error = cv2.norm(imgpoints[i],imgpoints2, cv2.NORM_L2)/len(imgpoints2)
    mean_error += error

print("total error: ", mean_error/len(objpoints))

