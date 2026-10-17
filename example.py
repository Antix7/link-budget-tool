from link_budget_tool import *

link = LinkAnalysis(
    downlink_frequency = 2.2 * u.GHz,
    uplink_frequency = 2 * u.GHz,
    downlink_data_rate = 2e8 * u.Hz,
    uplink_data_rate = 5e7 * u.Hz,
    minimum_elevation_angle = 10 * u.deg
)

link.spacecraft.parabolic_antenna( # Calculates the gain and half-power angle
    diameter = 0.2 * u.m,
    efficiency = 0.55
)
link.spacecraft.transmitter_power = 20 * u.W
link.spacecraft.absolute_antenna_loss(0.8)
link.spacecraft.pointing_loss(
    pointing_offset_angle = 1.5 * u.deg
)
link.spacecraft.G_over_T = -10 * u.dB(1/u.Kelvin)

link.ground_station.G_over_T = 20 * u.dB(1/u.Kelvin)
link.ground_station.latitude = 52.00 * u.deg # Ground station in Delft
link.ground_station.longitude = 4.37 * u.deg # Needed for rain attenuation
link.ground_station.EIRP = 30 * u.dB(u.W)

link.space_loss.Earth_orbit(
    altitude = 500 * u.km
)
link.rain_availability_percent = 99.99

link.modulation.scheme("QPSK 3/4")
link.coding.no_coding()


link.downlink_analysis()
link.downlink_dB_breakdown()

link.uplink_analysis()
link.uplink_dB_breakdown()