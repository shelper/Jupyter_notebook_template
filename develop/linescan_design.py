
# coding: utf-8

# In[13]:

import matplotlib.pyplot as plt
from math import *
import numpy as np
import sys
from ipywidgets import interact, interactive, fixed
import ipywidgets as widgets

sys.path.append('../src')
import constrain
from constrain import *
from recon import *


# In[10]:

tire_width = 100
groove_depth = 8
groove_width = 5
nonshadow_frac = 0.5
efl = 5.37
xc_res = 1.0 * constrain._pix_size
wd_min = 200
wd_max = 1000
wd_range_min = 300

tire_radius = 500
emax = 0.2 # max acceptable measurement error due to flat tire surface assumption
zres_min = 1/5 # min acceptable resolution 5lines per mm, or 0.2mm


# In[ ]:




# the minimum distance is requried to ensure that the groove is not completely shadowed by the ridge, otherwise, laser line cannot get into the groove, thus cannot image the depth of the groove.
# Figure below explains this shadowing issue. 
# <img src='../../figures/shadow.png'  alt="groove shadow"  style="width: 50%; height: 50%"/>

# In[4]:

# below ensure 2 specs: 
# 1) imager capture whole tire width, 
# 2) > 0.5 area has laser rather than shadowed
wd_min = calc_min_distance(tire_width, groove_width, groove_depth, nonshadow_frac)   
print('minimal working distance for capture:', wd_min, 'mm')


# As the incident angle of the laser to the tire is not vertical to the tire surface, we need to do angle correction of the measured groove depth. we decide to use two laser lines to measure depth profile at two different positions on the tire, and based on the relationship between the two measurements and some assumptions, we can potentially approximate the angle and perform the angle correction. the equation for the correction is:
#     $$ v_0 = v \times (\sin\theta\cos(\Delta + \delta) - \cos\theta \sin(\Delta + \delta)) $$
# where v is the measured depth and $v_0$ is the actually depth, $\Delta$ is the angle between the two laser lines(laser projection plane) and $\delta$ is the angle change due to the surface curvature. if we assume the surface is flat, then $\delta = 0$, we have an error of measurement as:
#     $$ \epsilon = v \times (\sin\theta\cos(\Delta + \delta) - \cos\theta \sin(\Delta + \delta)) - v \times (\sin\theta\cos(\Delta) - \cos\theta \sin(\Delta)) $$
# we can simplify and approximate this as 
#     $$\epsilon \approx 2v \times \sin(\frac{\delta}{2}) \cos\theta $$  
# usually $\delta$ is fairly small and we can further simplify the equation to:
#     $$\epsilon \approx v \times \delta \cos\theta $$  
# 
# based on previous figure, without loss of generality, we assume $\theta = 60^\circ$ and $ v = 5$, we have:
#     $$ \epsilon \approx 2.5 \times \delta < \Delta z $$
# 
# based on above, we can calulate the maximum seperation of the two laser scan lines due to assuming flat tire surface.

# In[5]:

# laser_fov_frac = 0.1 # seperation of the two scanning laser lines 
# s = 2 * d * tan(laser_fov_frac * constrain._cam_fov_height / 2) # space between the two scanning line on tire surface
# e = 2.5 * s / tire_radius

d = 360 
smax = emax * tire_radius / 2.5
laser_maxsep = np.arctan(smax / 2 / d) * 2 / constrain._cam_fov_height


# now we calculate the angle between the two laser lines is about 7 degrees, we then can calculate the effective depth-range to position the tire surface so that both line is in the camera FOV
# 
# below calculates the minimal and maximum depth for laser line to be captured within the FOV of camera. figure below explains the meaning of parameters
# <img src='../../figures/depth_range.png'  alt="depth range"  style="width: 30%"/>

# In[6]:

bmin, bmax = 1, 100 # min and max of baseline length
tmin, tmax = 1, 91 # min and max of the angle between baseline and laser projection plane
bgrid, tgrid = np.mgrid[bmin:bmax, tmin:tmax]
tgrid = tgrid * pi / 180

tmp_ufunc = np.frompyfunc(calc_depth_range, 3, 2)
rmin, rmax = tmp_ufunc(bgrid, tgrid, 1)
rmin = rmin.astype(np.float)
rmax = rmax.astype(np.float)


plt.figure(), 
ax = plt.subplot(1,2,1) 
im = ax.imshow(rmin, vmin=0, vmax=wd_min)
plt.xlabel(r"$\theta$", fontsize=16)
plt.ylabel(r"baseline", fontsize=16)
plt.title("$d_{min}$", fontsize=12)
plt.colorbar(im,fraction=0.05, pad=0.04)


ax = plt.subplot(1,2,2) 
im = ax.imshow(rmax, vmin=0, vmax=wd_max)
plt.xlabel(r"$\theta$", fontsize=16)
plt.ylabel(r"baseline", fontsize=16)
plt.title("$d_{max}$", fontsize=12)
plt.colorbar(im,fraction=0.05, pad=0.04)
plt.tight_layout()

plt.figure()
wd_mask  = (rmin < wd_min) * (rmax > wd_max)
plt.imshow(wd_mask)
plt.xlabel(r"$\theta$", fontsize=16)
plt.ylabel(r"baseline", fontsize=16)
plt.title("$d_{max} > 1000mm$ \n & $d_{min} < 200mm $", fontsize=12)


# for two laser scanning lines, the working distances of them should have overlap so both line will be in the camera FOV, as shown below, the usable working distance is highlighted in red:
# <img src='../../figures/wd_range.png'  alt="working distance"  style="width: 50%; height: 60%"/>

# In[7]:

shift = int(degrees(laser_maxsep * constrain._cam_fov_height))
rmax2 = np.roll(rmax, -shift, axis=1)
rmin2 = np.roll(rmin, -shift, axis=1)

rmin_new = np.maximum(rmin, rmin2)
rmax_new = np.minimum(rmax, rmax2)
rmin_new[:, -shift:] = 0 
rmax_new[:, -shift:] = 0 
wd_range_min = 300 
wd_usable = ((rmax_new - rmin_new) > wd_range_min)
wd_usable[:, -shift:] = 1
plt.figure() 
plt.imshow(wd_usable)
plt.xlabel(r"$\theta$", fontsize=16)
plt.ylabel(r"baseline", fontsize=16)
plt.title("work distance required for \n laser line in camera FOV", fontsize=12)


# depth resolution is also determined by the baseline and position of x. for a simplified setup, reconstruction can be done in a simplified way, that the laser projection plane is parallel to the y axis, and the baseline is parallel to the x axis. ![fig.1 simplified setup](../../figures/simple_setup.png)
# as such, 3D point (x, y, z) in camera coordinate can be calculated as:
#     $$(x, y, z) = t * (x', y', f)$$
# where x', y' is the distance of the 2D pixel to the center of the camera, 
# b is the length of baseline and theta is the angle between baseline and the 
# laser projection plane, and 
#     $$t = \frac{b}{f * cot(\theta) - x'}$$ 
#     $$z = \frac{bf}{f * cot(\theta) - x'}$$ 
# based on this we can calculate the resolution in z depth, by:
#     $$\left. \Delta z = \frac{dz}{dx} \right|_{x'} * \Delta x'$$
# where $\Delta x$ is the system resolution on the imaging sensor, here we use 1 pixel, and x is the position of the laser line to the sensor center along x-axis, we furture calculate $\Delta z$ as:
#     $$ \Delta z = \frac{b f \Delta x'}{(f \cot \theta - x')^2}$$

# In[8]:

# x = laser_maxsep * constrain._pix_num_height * constrain._pix_size/ 2
bgrid, wdgrid = np.mgrid[15:60, 200:500:5]
tmp_ufunc = np.frompyfunc(calc_zres, 5, 1)
zres = tmp_ufunc(bgrid, wdgrid, 80, efl, 0.00375)
zres = zres.astype(np.float)

plt.figure(), plt.imshow(zres, vmin=0, vmax=2), plt.colorbar()
plt.xlabel(r"working distance", fontsize=16)
plt.xticks(np.arange(0,60,10), np.arange(200,500,50))
plt.ylabel(r"baseline", fontsize=16)
plt.yticks(np.arange(0,45,10), np.arange(15,60,10))
plt.title("depth resolution vs. working distance")


# In[6]:

min_b = 15
max_b = 60
tire_width = 300
min_tire_width = 150
wd2hfov = tan(constrain._cam_fov_width / 2) * 2 
min_wd = round(min_tire_width/wd2hfov)
max_wd = round(tire_width/wd2hfov)

bgrid, wdgrid = np.mgrid[min_b:max_b:0.5, min_wd:max_wd:2]
tmp_ufunc = np.frompyfunc(calc_zres, 5, 1)
zres = tmp_ufunc(bgrid, wdgrid, 80, efl, 0.00375)
zres = zres.astype(np.float)

@interact(tire_width=widgets.IntSlider(min=min_tire_width,max=tire_width,step=1,value=10), 
          baseline=widgets.IntSlider(min=min_b, max=max_b, step=1, value=30), 
          zres=fixed(zres))
def find_min_wd(tire_width, baseline, zres):
    wd2hfov = tan(constrain._cam_fov_width / 2) * 2 
    col = round((tire_width / wd2hfov - min_wd)/2)
    new_zres = zres.copy()
    res = new_zres[(baseline-min_b) * 2 - 1, int(col)]
    new_zres[:, int(col)] = 0
    new_zres[(baseline-min_b) * 2 - 1, :] = 0
    num_b, num_wd = new_zres.shape

    plt.figure(), plt.imshow(new_zres, vmin=0, vmax=2), plt.colorbar()
    plt.xlabel("working distance: {}".format(min_wd + col * 2), fontsize=16)
    x_ticks = np.arange(min_wd, max_wd, (max_wd-min_wd)/num_wd * 20)
    plt.xticks(np.arange(0,num_wd,20), x_ticks.astype(int))
    plt.ylabel("baseline", fontsize=16)
    plt.yticks(np.arange(0,num_b,10), np.arange(min_b,max_b, (max_b - min_b)/num_b *10))
    plt.title("depth resolution vs. working distance, resolution: {:.2f}".format(res))
    


# notice that in above, when $b \rightarrow 0$, you see resolution improvemnt, which is due to that $\cot \theta \rightarrow \infty$, that further caused errors. we should not expect decreasing b improves depth resolution
# 
# other concerns:
# * calibration target design
# * errors due to that laser projection plane is not parallet to y-axis
# * adaptive illumination and exposure time to address different lighting
#     - need to turn off the LED
#     - laser intensity fall off with distance increase

# assume we need to cover a tire with size of 300mm wide, the camera has to be 330mm away from the area on the tire it is imaging. as such, heightwise 
