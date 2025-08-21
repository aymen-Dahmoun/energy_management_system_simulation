import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Load the data
csv_path = r"C:\Users\surface\matArticle\final_project\results\optimisation_result_v2.csv"
df_all_data = pd.read_csv(csv_path)

# ------------------------------------------
# 2D Plot: Penetration at Peak Hour vs Battery Capacity (Ignoring Wind Power)
# ------------------------------------------
df_battery_only = df_all_data[df_all_data['num_wind_turbines'] == 0]  # Consider only battery impact

plt.figure(figsize=(8, 6))
sns.scatterplot(x=df_battery_only['storage_capacity_mwh'], y=df_battery_only['total_penetration_peakhour'], color='b', label="Data Points")
sns.lineplot(x=df_battery_only['storage_capacity_mwh'], y=df_battery_only['total_penetration_peakhour'], color='r', linestyle='dashed', label="Trend")

plt.xlabel('Battery Storage Capacity (MWh)', fontsize=12)
plt.ylabel('Renewable Penetration at Peak Hours (%)', fontsize=12)
plt.title('Peak Hour Penetration vs Battery Capacity (Wind = 0 MW)', fontsize=14)
plt.legend()
plt.grid(True)
plt.show()

# ------------------------------------------
# 2D Plot: Penetration at Peak Hour vs Installed Wind Power (Ignoring Storage)
# ------------------------------------------
df_wind_only = df_all_data[df_all_data['storage_capacity_mwh'] == 0]  # Consider only wind impact

plt.figure(figsize=(8, 6))
sns.scatterplot(x=df_wind_only['num_wind_turbines'] * 0.8, y=df_wind_only['total_penetration_peakhour'], color='g', label="Data Points")
sns.lineplot(x=df_wind_only['num_wind_turbines'] * 0.8, y=df_wind_only['total_penetration_peakhour'], color='orange', linestyle='dashed', label="Trend")

plt.xlabel('Installed Wind Power (MW)', fontsize=12)
plt.ylabel('Renewable Penetration at Peak Hours (%)', fontsize=12)
plt.title('Peak Hour Penetration vs Installed Wind Power (Storage = 0 MWh)', fontsize=14)
plt.legend()
plt.grid(True)
plt.show()
