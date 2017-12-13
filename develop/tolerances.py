#%%
%qtconsole

#%%
from sympy import *
import numpy as np

b0, f0, theta0, alpha = 11.08, 6.14, 0, np.radians(29)
x0 = b0 + f0 * np.tan(alpha)

#%% depth measurement error
b, f, theta, x, y = symbols('b f theta x y')
y = x * f / (x + f * tan(theta) - b)
dyf = diff(y, f)
dyx = diff(y, x)
dyb = diff(y, b)
dytheta = diff(y, theta)
dydf = dyf.subs([(f, f0), (b, b0), (theta, theta0), (x, x0)])
dydb = dyb.subs([(f, f0), (b, b0), (theta, theta0), (x, x0)])
dydx = dyx.subs([(f, f0), (b, b0), (theta, theta0), (x, x0)])
dydtheta = dytheta.subs([(f, f0), (b, b0), (theta, theta0), (x, x0)])

#%% tread depth measurement error
x1, x2 = symbols('x1 x2')
treads_depth = x1 * f / (x1 + f * tan(theta) - b) - x2 * f / (x2 + f * tan(theta) - b) 

dtf = diff(treads_depth, f)
dtx = diff(treads_depth, x)
dtb = diff(treads_depth, b)
dtheta = diff(treads_depth, theta)

dyf = df.subs([(f, f0), (b, b0), (theta, theta0), (x, x0)])
dyb = db.subs([(f, f0), (b, b0), (theta, theta0), (x, x0)])
dyx = dx.subs([(f, f0), (b, b0), (theta, theta0), (x, x0)])
dytheta = dtheta.subs([(f, f0), (b, b0), (theta, theta0), (x, x0)])




