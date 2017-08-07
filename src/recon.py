"""
this module contains the function for 2D to 3D reconstruction

"""
import cv2
import numpy as np


def calibrate_baseline(points_3d, points_2d):
    #TODO: calibrate the cam using points mapped between 2D and 3D
    pass


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

    return cv2.calibrateCamera(obj_points, img_points, img.shape[::-1], None, None)
    # return ret, cam_matrix, dist_coeff, rvecs, tvecs

def undistort_img():
    pass

def extract_laserline(image, background=None):
    #TODO: extract laser line
    pass

