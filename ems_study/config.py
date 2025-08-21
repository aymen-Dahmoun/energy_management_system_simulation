# config.py
# Define battery system configuration
BATTERY_CAPACITY_MWh = 50
BATTERY_NOMINAL_POWER_MW = 15

# Define wind farm configuration
TURBINE_TYPE = "E-53/800"
TURBINE_COUNT = 1
WIND_FARM_INSTALLED_POWER_MW = 0.8 * TURBINE_COUNT

PV_TILT = 30  # degrees
PV_AZIMUTH = 180  # South
PV_MODULE = 'Canadian_Solar_Inc__CS1U_430MS'
PV_INVERTER = "ABB__MICRO_0_25_I_OUTD_US_208__208V_"
PV_COUNT = 10


