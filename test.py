import itur

# --- Mission Parameters ---
lat = 52.07           # Latitude in degrees
lon = 4.30            # Longitude in degrees
freq = 14.0           # Frequency in GHz
el_angle = 90.0       # Satellite elevation angle in degrees
tau = 45.0            # Polarization tilt angle (45° = Circular)
p = 0.01              # Exceedance probability (0.01% of an average year)
hs = 0.0              # Ground station altitude in km

# --- Step 1: ITU-R P.837-6 (Rainfall Rate) ---
R_001 = itur.models.itu837.rainfall_rate(lat, lon, p)
print(f"Rainfall Rate (R_0.01): {R_001.value:.2f} mm/h")

# --- Step 2: ITU-R P.838-3 (Specific Attenuation) ---
gamma_R = itur.models.itu838.rain_specific_attenuation(R_001, freq, el_angle, tau)
print(f"Specific Attenuation: {gamma_R.value:.3f} dB/km")

# --- Step 3: ITU-R P.618 (Total Slant Path Attenuation) ---
# FIXED: Using explicit keyword arguments for hs and p
total_rain_attenuation = itur.models.itu618.rain_attenuation(lat, lon, freq, el_angle, hs=hs, p=p)
print(f"Total Slant Path Rain Attenuation: {total_rain_attenuation.value:.2f} dB")