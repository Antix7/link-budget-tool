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

def parabolic_antenna(frequency, diameter, efficiency):
    gain = 2 * to_dB(pi * diameter * frequency / c) + to_dB(efficiency)
    half_power_angle = (u.GHz * u.m * u.deg * 21 / (frequency * diameter)).to(u.deg)  # empirical formula
    return gain, half_power_angle


class Spacecraft:
    def __init__(self, downlink_frequency, uplink_frequency):
        self.downlink_frequency = downlink_frequency
        self.uplink_frequency = uplink_frequency
        self.transmitter_power = 0 * u.Watt
        self.downlink_antenna_gain = 0 * u.dB
        self.antenna_loss = 0*u.dB #positive
        self.half_power_angle = 0*u.deg
        self.pointing_loss_value = 0*u.dB #positive
        self.EIRP = 0*u.dB(u.Watt)
        self.G_over_T = 0*u.dB(1/u.Kelvin)

    def parabolic_antenna(self, diameter, efficiency):
        self.downlink_antenna_gain, self.half_power_angle = parabolic_antenna(self.downlink_frequency, diameter, efficiency)

    def absolute_antenna_loss(self, absolute_loss):
        self.antenna_loss = -to_dB(absolute_loss)

    def pointing_loss(self, pointing_offset_angle):
        self.pointing_loss_value = 12*u.dB*((pointing_offset_angle.to(u.deg)/self.half_power_angle.to(u.deg))**2) # empirical formula

    def get_EIRP(self):
        self.EIRP = to_dB(self.transmitter_power) - self.antenna_loss + self.downlink_antenna_gain - self.pointing_loss_value
        return self.EIRP


class GroundStation:
    def __init__(self):
        self.G_over_T = 0*u.dB(1/u.Kelvin)
        self.EIRP = 0*u.dB(u.Watt)
        self.latitude = 0*u.deg
        self.longitude = 0*u.deg


class SpaceLoss:
    def __init__(self, minimum_elevation_angle):
        self.minimum_elevation_angle = minimum_elevation_angle
        self.distance = 0*u.meter
        self.loss = 0*u.dB #positive

    def get_loss(self, frequency):
        wavelength = c / frequency
        self.loss = 2*to_dB(4*pi*self.distance / wavelength)
        return self.loss

    def Earth_orbit(self, altitude):
        self.distance = R_earth * (sqrt(((R_earth+altitude) / R_earth)**2 - np.cos(self.minimum_elevation_angle)**2) - np.sin(self.minimum_elevation_angle))

    def deep_space(self, sun_distance, elongation_angle):
        self.distance = np.sqrt(au**2 + sun_distance**2 - 2*au*sun_distance*np.cos(elongation_angle))


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


class LinkAnalysis:
    def __init__(self, downlink_frequency, uplink_frequency, downlink_data_rate, uplink_data_rate, minimum_elevation_angle):
        self.downlink_frequency = downlink_frequency.si
        self.uplink_frequency = uplink_frequency.si
        self.minimum_elevation_angle = minimum_elevation_angle.to(u.deg)
        self.spacecraft = Spacecraft(self.downlink_frequency, self.uplink_frequency)
        self.ground_station = GroundStation()
        self.space_loss = SpaceLoss(self.minimum_elevation_angle)
        self.modulation = Modulation()
        self.coding = Coding()
        self.downlink_data_rate = downlink_data_rate #[bits/s = Hz]
        self.uplink_data_rate = uplink_data_rate
        self.rain_availability_percent = 0

    def atmospheric_attenuation(self, frequency):
        return atmospheric_attenuation_model.gaseous_attenuation_slant_path(
            f = frequency.to(u.GHz).value,
            el = self.minimum_elevation_angle.to(u.deg).value,
            rho = 7.5,  # Water vapor density in g/m^3
            P = 1013,  # Pressure in hPa
            T = 15,  # Temperature in Celsius
            mode = "exact"
        )

    def rain_attenuation(self, frequency):
        return rain_attenuation_model.rain_attenuation(
            lat = self.ground_station.latitude.to(u.deg).value,
            lon = self.ground_station.longitude.to(u.deg).value,
            f = frequency.to(u.GHz).value, # frequency in GHz
            el = self.minimum_elevation_angle.to(u.deg).value,
            p = 100 - self.rain_availability_percent # unavailability in %
        )

    def downlink_SNR(self):
        SNR = (self.spacecraft.get_EIRP() - self.space_loss.get_loss(self.downlink_frequency)
               - self.atmospheric_attenuation(self.downlink_frequency) - self.rain_attenuation(self.downlink_frequency)
               + self.ground_station.G_over_T + self.coding.gain - to_dB(k_B * self.downlink_data_rate / self.coding.rate))
        return SNR

    def uplink_SNR(self):
        SNR = (self.ground_station.EIRP - self.space_loss.get_loss(self.uplink_frequency)
               - self.atmospheric_attenuation(self.uplink_frequency) - self.rain_attenuation(self.uplink_frequency)
               + self.spacecraft.G_over_T + self.coding.gain - to_dB(k_B * self.uplink_data_rate / self.coding.rate))
        return SNR

    def get_margin(self, SNR):
        return SNR - self.modulation.required_SNR

    def get_bandwidth(self, data_rate):
        return data_rate / (self.coding.rate * self.modulation.spectral_efficiency)

    def downlink_analysis(self):
        margin = self.get_margin(self.downlink_SNR())
        bandwidth = self.get_bandwidth(self.downlink_data_rate)
        print("Downlink analysis results:")
        print(f"Link margin: {margin:.3f}")
        print(f"Required bandwidth: {bandwidth:.2f}")

    def uplink_analysis(self):
        margin = self.get_margin(self.uplink_SNR())
        bandwidth = self.get_bandwidth(self.uplink_data_rate)
        print("Uplink analysis results:")
        print(f"Link margin: {margin:.3f}")
        print(f"Required bandwidth: {bandwidth:.2f}")




link = LinkAnalysis(
    downlink_frequency=2.5 * u.GHz,
    uplink_frequency=2 * u.GHz,
    downlink_data_rate = 250*u.MHz,
    uplink_data_rate = 250*u.MHz,
    minimum_elevation_angle= 10*u.deg
)

link.spacecraft.parabolic_antenna(0.166*u.m, 0.55)
link.spacecraft.transmitter_power = 2 * u.W
link.spacecraft.antenna_loss = 0.97 * u.dB
link.spacecraft.pointing_loss(0.25*u.deg)
link.spacecraft.G_over_T = -10 * u.dB(1/u.Kelvin)

link.ground_station.G_over_T = 16.2*u.dB(1/u.Kelvin)
link.ground_station.latitude = 52.07*u.deg
link.ground_station.longitude = 4.30*u.deg
link.ground_station.EIRP = 50*u.dB(u.W)

link.space_loss.Earth_orbit(570*u.km)
link.rain_availability_percent = 99.9

link.modulation.scheme("QPSK 3/4")
link.coding.no_coding()

link.downlink_analysis()
link.uplink_analysis()

