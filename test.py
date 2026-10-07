import astropy.units as u


class EnforcedUnitQuantity:
    """A descriptor that enforces a specific Astropy unit upon assignment."""

    def __init__(self, target_unit):
        self.target_unit = target_unit
        self.private_name = None

    def __set_name__(self, owner, name):
        # Automatically called to get the variable name (e.g., 'bit_rate')
        self.private_name = f"_{name}"

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self.private_name, None)

    def __set__(self, instance, value):
        if not isinstance(value, u.Quantity):
            raise TypeError(f"Value must be an astropy Quantity with units of {self.target_unit}")

        # Converts the input to the required unit, throwing an error if incompatible
        setattr(instance, self.private_name, value.to(self.target_unit))


class SpacecraftLink:
    # Define your parameters and their required internal units once
    transmit_power = EnforcedUnitQuantity(u.W)
    bit_rate = EnforcedUnitQuantity(u.Hz)
    system_noise_temp = EnforcedUnitQuantity(u.K)


# Usage
sat = SpacecraftLink()

sat.transmit_power = 2 * u.kW  # Automatically converts to 2000.0 W
sat.bit_rate = 5 * u.MHz  # Automatically converts to 5000000.0 Hz

print(sat.transmit_power)  # Output: 2000.0 W
print(sat.bit_rate)  # Output: 5000000.0 Hz