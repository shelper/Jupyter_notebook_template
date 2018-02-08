#%%
import scipy as sp
import numpy as np
import matplotlib.pyplot as plt
from sympy import *
import numpy as np
from scipy.optimize import minimize, least_squares
from sympy.abc import b, f, o, x

#%%
dy = 2.5
y0 = 5
pix_size = 0.0055

y = (o + x) * f / ((o + x) - b)
# x = (y * b) / (y - f) - o
peaks = [793, 744, 702, 672, 642, 620, 600, 582, 568, 556]
xs = [i * pix_size for i in peaks]
for i, xn in enumerate(xs):
    if i == 0:
        e = 0 
    else:
        e += (y.subs(x, xn) - y.subs(x, xp) - dy) ** 2
    xp = xn

cost_func = lambdify([[o, f, b]], e)

#%% evaluate minimization methods
methods = ['Nelder-Mead', 'Powell', 'CG', 'BFGS',
           'L-BFGS-B', 'TNC', 'COBYLA',
           'SLSQP', 'dogleg', 'Newton-CG', 'trust-ncg', ]

X0 = [8, 5, 10]
for m in methods:
    X = minimize(cost_func, X0, method=m)
    get_depth = lambdify((o, f, b, x), y)
    get_error = lambdify((o, f, b), e)
    measured_depths = [get_depth(*X.x, x) for x in xs]
    squared_error = get_error(*X.x)
    print(m, X.x, squared_error)

# dtf = diff(treads_depth, f)
m = 'CG'
X = minimize(cost_func, X0, method=m)
get_depth = lambdify((o, f, b, x), y)
get_error = lambdify((o, f, b), e)
measured_depths = [get_depth(*X.x, x) for x in xs]
squared_error = get_error(*X.x)
print(m, X.x, squared_error)
