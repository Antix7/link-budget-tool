# User manual

LinkBudgetTool is a Python library capable of performing downlink and
uplink budget analyses for different space mission profiles. It allows
the user to set various mission parameters in a unit-safe way and
outputs the link margin along with the required bandwidth.

Before using the tool, it is important to know how to use the
`astropy.units` library, abbreviated as `u`. It provides a way for
Python to store and manipulate physical variables such as meters
(`u.m`), Watts (`u.W`) or degrees (`u.deg`). It also supports metric
prefixes (`u.GHz`, `u.km`) and logarithmic units like `u.dB`. If a
quantity represents a dimensionless gain, it has the unit of `u.dB`,
while dimensional quantities need a base unit in order to be expressed
in decibels. This is done by passing the base unit as an argument to the
`u.dB` function -- for example, `u.dB(u.W)` would represent power in
decibels.

All dimensional input parameters need to be expressed in proper units,
which is most easily done by multiplying a Python number by a base unit
-- for example, `5*u.m` represents a value of $5$ meters. Dimensionless
values like efficiency can be expressed as regular numbers. There is one
very important caveat regarding the unit of data rate:
$\frac{\text{bits}}{\text{second}}$ are expressed as
$\frac{\text{1}}{\text{second}} = \text{Hz}$, because there is no such
unit as bits in the SI system.

To get started, you first need to install the required dependencies by
executing `pip install numpy astropy itur` in the command prompt. You
can import the library by placing its Python file in the same folder as
your script and adding `from link_budget_tool import *` to your header.

To define an analysis, you need to create an instance of the
`LinkAnalysis` class, as seen in the example below. If you are interested in the downlink analysis
only, the uplink parameters can be set to any placeholder value. The
gain and half-power angle of the spacecraft antenna can be calculated
using the `parabolic_antenna` function or set manually. Space loss can
be calculated using the `Earth_orbit` or `deep_space` functions
depending on your mission. To see the available modulation and coding
schemes, you can use the `available_codes()` and
`available_modulations()` functions.

Example link analysis:
```Python
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
link.uplink_analysis()
```
Output:
```
Downlink analysis results:
Link margin: 20.382 dB
Required bandwidth: 134.23 MHz
Uplink analysis results:
Link margin: 4.532 dB
Required bandwidth: 33.56 MHz
```
