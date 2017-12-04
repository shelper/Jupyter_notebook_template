from sympy import *
import numpy as np

b0, f0, theta0, alpha = 11.08, 6.14, 0, np.radians(29)
x0 = b0 + f0 * np.tan(alpha)
b, f, theta, x, y = symbols('b f theta x y')
y = x * f / (x + f * tan(theta) - b)
df = diff(y, f)
dx = diff(y, x)
dtheta = diff(y, theta)
db = diff(y, b)

dyf = df.subs([(b, b0), (theta, theta0), (x, x0)])
dyb = db.subs([(f, f0), (theta, theta0), (x, x0)])
dytheta = dtheta.subs([(f, f0), (b, b), (x, x0)])
dyx = dx.subs([(f, f0), (b, b), (theta, theta0)])

