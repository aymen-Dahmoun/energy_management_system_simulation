import pandas as pd
from simulation.optimizer import Optimizer
import numpy as np
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from models.windPowerForcat import windPowerForecast
from models.pv import pvPowerForecast
from simulation.controller import EnergyController
EnergyController = EnergyController()

flag = False
annual_power_wind_production = windPowerForecast(flag)
annual_power_pv_production = pvPowerForecast(flag)


df = pd.read_csv(
    r"/Users/MAC/energy_management_system_simulation/ems_study/data/annual_power_input.csv",
    sep=",",
    encoding="utf-8-sig",
)

df.columns = df.columns.str.strip()

df["Time"] = pd.to_datetime(df["Time"])
df.set_index("Time", inplace=True)

# Ensure all required columns exist
required_columns = {"PV", "wind", "Load"}
if not required_columns.issubset(df.columns):
    raise ValueError(f"Missing columns: {required_columns - set(df.columns)}")


df["wind"] = df["wind"] / 1e6  # Convert wind power to kW
# Run optimization with PV, wind, and load data
optimizer = Optimizer()
results = optimizer.run_simulation(df["wind"], df["Load"], df["PV"], df.index.hour)
results['Load'] = df['Load'].values
results['PV'] = df['PV'].values
results['wind'] = df['wind'].values

total_load = np.sum(df["Load"])
if total_load > 0:
    penetration_pv = (np.sum(results['pv_to_load']) / total_load) * 100
    penetration_storage = (np.sum(results['storage_to_load']) / total_load) * 100
    penetration_wind = (np.sum(results['wind_to_load']) / total_load) * 100
    sum_load_peackhour = np.sum(df["Load"][df.index.hour.map(EnergyController.peackHour)])
else:
    penetration_pv = penetration_storage = penetration_wind = 0  # Set to zero or handle appropriately

total_storage_energy_production = np.sum(results['storage_to_load'] ) / 4

total_wind_energy_production = np.sum(results['wind_to_load'] + results['wind_to_grid'] + results['wind_to_storage']) / 4



total_renewable_penetration = penetration_pv + penetration_storage + penetration_wind

total_energy_delivered_to_grid = np.sum(results['system_to_grid']) / 4

total_energy_purchased_from_grid = np.sum(results['grid_to_load']) / 4
#
# sum_pv_to_load_peakhour = np.sum(results["pv_to_load"][results["Time"].map(EnergyController.peackHour)])
#
# sum_storage_to_load_peakhour = np.sum(results["storage_to_load"][results["Time"].map(EnergyController.peackHour)])
#
# sum_wind_to_load_peakhour = np.sum(results["wind_to_load"][results["Time"].map(EnergyController.peackHour)])
#
# penetration_pv_peakhour = sum_pv_to_load_peakhour / sum_load_peackhour * 100
#
# penetration_storage_peakhour = sum_storage_to_load_peakhour / sum_load_peackhour * 100
#
# penetration_wind_peakhour = sum_wind_to_load_peakhour / sum_load_peackhour * 100
#
# total_penetration_peakhour = penetration_wind_peakhour + penetration_pv_peakhour + penetration_storage_peakhour

print("annual wind energy production: ", annual_power_wind_production, "MWh")
print("annual pv energy production: ", annual_power_pv_production, "MWh")
print(f"Total load: {total_load:.2f} MWh")
print(f"Total penetration of renewable energy: {total_renewable_penetration:.2f}%")
print(f"PV penetration: {penetration_pv:.2f}%")
print(f"Storage penetration: {penetration_storage:.2f}%")
print(f"Wind penetration: {penetration_wind:.2f}%")
print(f"Total storage energy production: {total_storage_energy_production:.2f} MWh")
print(f"Total wind energy production: {total_wind_energy_production:.2f} MWh")
print(f"total energy delivered to grid: {total_energy_delivered_to_grid} MWh")
print(f"total energy purchasedred from grid: {total_energy_purchased_from_grid} MWh")
# print(f"sum of load demand at peak hour: {sum_load_peackhour}")
# print(f"sum of pv to load at peak hour: {sum_pv_to_load_peakhour}")
# print(f"sum of storage to load at peak hour: {sum_storage_to_load_peakhour}")
# print(f"sum of wind to load at peak hour: {sum_wind_to_load_peakhour}")
# print(f"pv penetration at peak hour: {penetration_pv_peakhour}")
# print(f"storage penetration at peak hour: {penetration_storage_peakhour}")
# print(f"wind penetration at peak hour: {penetration_wind_peakhour}")
# print(f"Total penetration at peak hour: {total_penetration_peakhour}")

# Save results

file_path = r"results\final_output.csv"
results["Time"] = df.index

# Now save the new results
results.to_csv(file_path, index=False)