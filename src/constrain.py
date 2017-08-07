"""

if not specified, the unit of length is defaulted to mm

"""
from math import *

_pix_size = 3.75e-3
_pix_num_width = 1280
_pix_num_height = 960
_cam_focus = 5.3
INF = 1e9

_pix_num_diag = int(sqrt(_pix_num_height ** 1 + _pix_num_width ** 2))
_cam_fov_width = atan(_pix_size * _pix_num_width / 2 / _cam_focus) * 2
_cam_fov_height = atan(_pix_size * _pix_num_height / 2 / _cam_focus) * 2
_cam_fov_diag = atan(_pix_size * _pix_num_diag / 2 / _cam_focus) * 2


def calc_min_distance(tire_width, groove_width, groove_depth, nonshadow_frac=0.5):
    """ calculate the minimum distance to ensure the shadowed part of the groove

    Args:
        tire_width: the width from left most groove to right most groove
        groove_width: width of the vertical major groove
        groove_depth: depth of the vertical major groove
        nonshadow_frac: percentage of non-shadowed area to the whole groove width, default to 50%
    """
    min_distance_shadow = tire_width / 2 * groove_depth / (groove_width * nonshadow_frac)
    min_distance_fov = tire_width * _cam_fov_width / _cam_focus

    return max(min_distance_fov, min_distance_shadow)


def calc_depth_range(baseline, theta, fov_frac=1):
    """ calculate the min and max depth within the FOV of camera
    the calculation is based on camera coordinates,
    the camera's optical center (pinhole) as original point,
    x-y plane parallel to the sensor, where x-axis along the width
    and y-axis along the height
    laser is mounted on x-z plane and the projection plane is parallel
    to y-axis, if laser's position on x-z plane is (x, z),
    then: baseline = x + z / tan(theta)

    Args:
        baseline: the distance between laser and camera on x axis
        theta: angle between laser projection plan and baseline
        fov_frac: keep the laser line out of margin

    Returns: a list of [min_depth, max_depth]

    """
    alpha = atan((_pix_num_height * _pix_size * fov_frac) / (2 * _cam_focus))
    beta = pi / 2 - theta

    d_min = baseline / (tan(alpha) + tan(beta))
    d_min = INF if d_min > INF else d_min
    d_max = baseline / (tan(beta) - tan(alpha)) if alpha < beta else INF
    d_max = INF if d_max > INF else d_max

    return d_min, d_max


def calc_zres(b, wd, theta, f, sys_res):
    """
    calculate the z-resolution based on system resolution

    Args:
        b: length of baseline
        theta: angle between laser projection plan and baseline
        f: focal length of camera length
        wd: distance from sensor center
        sys_res: system intrinsic resolution (optical + sensor)
    """
    beta = pi / 2 - theta
    x = (wd * f - b * f * tan(theta)) / (wd * tan(theta))
    diff_zx = b * f / ((f * tan(beta) - x) ** 2)

    zres = sys_res * diff_zx

    return zres


def calc_groove_depth(depth1, depth2, scan_spacing, tire_radius):
    delta_angle = scan_spacing / tire_radius
    # TODO:
    pass


if __name__ == '__main__':
    # TODO:
    pass
    calc_depth_range()
