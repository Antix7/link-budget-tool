import astropy.units as u
from astropy.constants import GM_earth, R_earth
import numpy as np
from link_budget_tool import to_dB

h = 820 * u.km
V = np.sqrt(GM_earth/(R_earth+h))
print(V)

swath_angle = 45 * u.deg
pixel_size = (0.01 * u.arcmin).to(u.deg)
line_width_px = swath_angle/pixel_size
print(line_width_px)

swath_width = (h*2*np.sin(45/2*u.deg)).to(u.m)
print(swath_width)
pixel_width = swath_width/line_width_px
print(pixel_width)

bits_per_px = 32 * u.bit

data_rate = bits_per_px * swath_width * (V/pixel_width**2)
print(data_rate.to(u.gigabit/u.s))

downlink_data_rate = data_rate*(24/0.5)
print(downlink_data_rate.to(u.gigabit/u.s))

print()
print(10**(1/10))
print(10**(3/10))
