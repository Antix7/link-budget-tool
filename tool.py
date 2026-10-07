from math import *
import numpy as np
import astropy.units as u
from astropy.constants import k_B, c, R_earth, au
import itur.models.itu676 as atmospheric_attenuation_model
import itur.models.itu618 as rain_attenuation_model


coding_schemes = { # name: [rate, gain]
    "Convolutional code": [1/2, 5],
    "Convolutional-RS": [1/2, 7],
    "Turbo-Code": [1/6, 10],
    "LDPC": [3/4, 10]
}

modulation_schemes = { # name: [required SNR, spectral efficiency] - BER=1e-9
    "QPSK 1/4": [2.2, 0.49],
    "QPSK 1/3": [2.1, 0.66],
    "QPSK 2/5": [2.2, 0.79],
    "QPSK 1/2": [2.5, 0.99],
    "QPSK 3/5": [2.9, 1.19],
    "QPSK 2/3": [3.4, 1.32],
    "QPSK 3/4": [3.8, 1.49],
    "QPSK 4/5": [4.2, 1.59],
    "QPSK 5/6": [4.5, 1.65],
    "QPSK 8/9": [5.2, 1.77],
    "QPSK 9/10": [5.4, 1.79],
    "8PSK 3/5": [4.5, 1.78],
    "8PSK 2/3": [5.1, 1.98],
    "8PSK 3/4": [5.9, 2.23],
    "8PSK 5/6": [7.0, 2.48],
    "8PSK 8/9": [8.0, 2.65],
    "8PSK 9/10": [8.2, 2.68],
    "16APSK 2/3": [6.3, 2.64],
    "16APSK 3/4": [7.0, 2.97],
    "16APSK 4/5": [7.5, 3.17],
    "16APSK 5/6": [7.9, 3.3],
    "16APSK 8/9": [8.9, 3.52],
    "16APSK 9/10": [9.1, 3.57]
}


def available_codes():
    print(coding_schemes.keys())
    return coding_schemes.keys()

def available_modulations():
    print(modulation_schemes.keys())
    return modulation_schemes.keys()

def to_dB(quantity):
    if type(quantity) in (float, int): # check if it is dimensionless
        return 10*log10(quantity)*u.dB
    if hasattr(quantity.unit, 'physical_unit'): # check if it is already in dB
        return quantity
    return quantity.to(u.dB(quantity.si.unit))


class Spacecraft:
    #TODO: pointing error
    def __init__(self, wavelength):
        self.wavelength = wavelength
        self.power = 0*u.Watt
        self.gain = 0*u.dB
        self.loss = 0*u.dB #positive

    def parabolic_antenna(self, diameter, efficiency):
        self.gain = 2*to_dB(pi*diameter / self.wavelength) + to_dB(efficiency)

    def absolute_loss(self, absolute_loss):
        self.loss = -to_dB(absolute_loss)

    def EIRP(self):
        return to_dB(self.power) - self.loss + self.gain


class GroundStation:
    def __init__(self):
        self.G_over_T = 0*u.dB(1/u.Kelvin)
        self.latitude = 0*u.deg
        self.longitude = 0*u.deg


class SpaceLoss:
    def __init__(self, wavelength):
        self.wavelength = wavelength
        self.distance = 0*u.meter
        self.loss = 0*u.dB #positive

    def calculate_loss(self):
        self.loss = 2*to_dB(4*pi*self.distance / self.wavelength)

    def Earth_orbit(self, altitude, elevation_angle):
        self.distance = R_earth * (sqrt(((R_earth+altitude) / R_earth)**2 - np.cos(elevation_angle)**2) - np.sin(elevation_angle))
        self.calculate_loss()

    def deep_space(self, sun_distance, elongation_angle):
        self.distance = np.sqrt(au**2 + sun_distance**2 - 2*au*sun_distance*np.cos(elongation_angle))
        self.calculate_loss()


class Modulation:
    def __init__(self):
        self.required_SNR = 0*u.dB
        self.spectral_efficiency = 0 #[bits/s/Hz = Hz/Hz = dimensionless]
        self.BER = 0 #[dimensionless]

    def scheme(self, name):
        self.required_SNR = modulation_schemes[name][0]*u.dB
        self.spectral_efficiency = modulation_schemes[name][1]
        self.BER = 1.0e-9


class Coding:
    def __init__(self):
        self.rate = 0 #[dimensionless]
        self.gain = 0*u.dB

    def no_coding(self):
        self.rate = 1
        self.gain = 0*u.dB

    def scheme(self, name):
        self.rate = coding_schemes[name][0]
        self.gain = coding_schemes[name][1]*u.dB


class Analysis:
    def __init__(self, frequency):
        self.frequency = frequency.si
        self.wavelength = c/self.frequency
        self.spacecraft = Spacecraft(self.wavelength)
        self.ground_station = GroundStation()
        self.space_loss = SpaceLoss(self.wavelength)
        self.atmospheric_loss = 0*u.dB
        self.rain_loss = 0*u.dB
        self.modulation = Modulation()
        self.coding = Coding()
        self.data_rate = 0*u.Hz #[bits/s = Hz]

    def atmospheric_attenuation(self, elevation_angle):
        self.atmospheric_loss = atmospheric_attenuation_model.gaseous_attenuation_slant_path(
            f = self.frequency.to(u.GHz).value,
            el = elevation_angle.to(u.deg).value,
            rho = 7.5,  # Water vapor density in g/m^3
            P = 1013,  # Pressure in hPa
            T = 15,  # Temperature in Celsius
            mode = "exact"
        )

    def rain_attenuation(self, availability_percent, elevation_angle):
        self.rain_loss = rain_attenuation_model.rain_attenuation(
            lat = self.ground_station.latitude.to(u.deg).value,
            lon = self.ground_station.longitude.to(u.deg).value,
            f = self.frequency.to(u.GHz).value, # frequency in GHz
            el = elevation_angle.to(u.deg).value,
            p = 100 - availability_percent # unavailability in %
        )

    def received_SNR(self):
        SNR = (self.spacecraft.EIRP() - self.space_loss.loss - self.atmospheric_loss - self.rain_loss
               + self.ground_station.G_over_T + self.coding.gain - to_dB(k_B * self.data_rate / self.coding.rate))
        return SNR

    def get_margin(self):
        return self.received_SNR() - self.modulation.required_SNR

    def get_bandwidth(self):
        return self.data_rate / (self.coding.rate * self.modulation.spectral_efficiency)

    def get_result(self):
        margin = self.get_margin()
        bandwidth = self.get_bandwidth()
        print(f"Link margin: {margin:.3f}")
        print(f"Required bandwidth: {bandwidth:.2f}")




link = Analysis(frequency=2.5*u.GHz)
link.data_rate = 250*u.MHz

link.spacecraft.power = 2*u.W
link.spacecraft.gain = 10.2*u.dB
link.spacecraft.loss = 0.97*u.dB

link.ground_station.G_over_T = 16.2*u.dB(1/u.Kelvin)
link.ground_station.latitude = 52.07*u.deg
link.ground_station.longitude = 4.30*u.deg

link.space_loss.Earth_orbit(570*u.km, 10*u.deg)
link.atmospheric_attenuation(10*u.deg)
link.rain_attenuation(99.9, 10*u.deg)

link.modulation.scheme("QPSK 3/4")
link.coding.no_coding()

link.get_result()

