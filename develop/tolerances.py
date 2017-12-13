#%%
%qtconsole

#%%
from sympy import *
import numpy as np

b0, f0, e0, alpha = 11.08, 6.14, 0, np.radians(29)
x0 = b0 + f0 * np.tan(alpha)

#%% depth measurement error
b, f, e, x, y = symbols('b f e x y')
y = x * f / (x + f * tan(e) - b)
dyf = diff(y, f)
dyx = diff(y, x)
dyb = diff(y, b)
dye = diff(y, e)
dydf = dyf.subs([(f, f0), (b, b0), (e, e0), (x, x0)])
dydb = dyb.subs([(f, f0), (b, b0), (e, e0), (x, x0)])
dydx = dyx.subs([(f, f0), (b, b0), (e, e0), (x, x0)])
dyde = dye.subs([(f, f0), (b, b0), (e, e0), (x, x0)])

#%% tread depth measurement error
x1, x2 = symbols('x1 x2')
y01, y02 = 20, 25
x01 = y01 * b0 / (y01 - f0)
x02 = y02 * b0 / (y02 - f0)
treads_depth = x1 * f / (x1 + f * tan(e) - b) - x2 * f / (x2 + f * tan(e) - b) 

dtf = diff(treads_depth, f)
dtx = diff(treads_depth, x)
dtb = diff(treads_depth, b)
dte = diff(treads_depth, e)

dtdf = dtf.subs([(f, f0), (b, b0), (e, e0), (x1, x01), (x2, x02)])
dtdb = dtb.subs([(f, f0), (b, b0), (e, e0), (x1, x01), (x2, x02)])
dtdx = dtx.subs([(f, f0), (b, b0), (e, e0), (x1, x01), (x2, x02)])
dtde = dte.subs([(f, f0), (b, b0), (e, e0), (x1, x01), (x2, x02)])




