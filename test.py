import numpy as np
import astropy.units as u

# Works natively with degrees
angle_deg = 90 * u.deg
print(np.sin(angle_deg))  
# Output: 1.0

# Works natively with radians
angle_rad = np.pi * u.radian
print(np.cos(angle_rad))  
# Output: -1.0