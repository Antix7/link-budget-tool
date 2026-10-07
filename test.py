import astropy.units as u
from astropy.constants import k_B, c

EIRP = 100 * u.dB(u.Watt)

loss = 100 * u.dB

G_over_T = 20 * u.dB(1/u.Kelvin)

data_rate = 1000 * u.MHz
noise = (data_rate * k_B).to(u.dB(u.Watt/u.Kelvin))

snr = EIRP - loss + G_over_T - noise
print(snr)