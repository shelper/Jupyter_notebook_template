
# coding: utf-8

# In[39]:

from sympy import *
import numpy as np
import matplotlib.pyplot as plt
get_ipython().magic('matplotlib inline')


# In[70]:

tread_width = 50
flat_edge_width = 50
tread_bottom_width = 50

x = symbols('x')
smooth_step_func = lambdify(x, 3 * x**2 - 2 * x**3)

tread_right_edge = smooth_step_func(np.linspace(0, 1, tread_bottom_width)) - 1
tread_left_edge =  - tread_right_edge - 1

major_tread = np.concatenate((np.zeros(flat_edge_width), 
                        tread_left_edge, 
                        -np.ones(tread_width), 
                        tread_right_edge,
                        np.zeros(flat_edge_width)))

minor_tread = np.concatenate((np.zeros(flat_edge_width), 
                        tread_left_edge * 0.5, 
                        tread_right_edge * 0.5,
                        np.zeros(flat_edge_width)))

plt.plot(major_tread)
plt.plot(minor_tread)


# In[ ]:

speed_variation
x = np.arange(len(major_tread))

xp = np.cumsum(abs(3 + np.cumsum(np.random.randn(100)*10))))

c1, c2, c3 = symbols('c1 c2 c3')

drift_func = c1 * x + c2 ** x


tread_drift = symbol()

depth
width
center
edge_size
disortion
drift


catagerys = ['major_tread', 'minor_tread', 'partial_major_tread', 'partial_minor_tread', 'none_tread']

