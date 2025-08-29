import pandas as pd
import numpy as np
import pulp
import sys
import os
import matplotlib.pyplot as plt
import seaborn as sns
from pprint import pprint
from optimizer import Optimizer
from ems_study.models.windPowerForcat import windPowerForecast
from controller import EnergyController

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Adjust sys.path only if necessary
EnergyController = EnergyController()


def run_simulation(num_wind_turbines, storage_capacity_mwh):
    # Forecast annual wind power production
    annual_power_wind_production = windPowerForecast(turbine_count=num_wind_turbines)

    # Load dataset
    file_path = r"/Users/MAC/energy_management_system_simulation/ems_study/data/annual_power_input.csv"
    df = pd.read_csv(file_path, sep=",", encoding="utf-8-sig")
    df.columns = df.columns.str.strip()

    if "Time" not in df.columns:
        raise ValueError(f"Missing 'Time' column. Found columns: {df.columns.tolist()}")

    df["Time"] = pd.to_datetime(df["Time"])
    df.set_index("Time", inplace=True)

    required_columns = {"PV", "wind", "Load"}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"Missing columns: {required_columns - set(df.columns)}")

    df["wind"] = df["wind"] / 1e6  # Convert wind power to MW if needed

    optimizer = Optimizer(storage_capacity=storage_capacity_mwh)
    results = optimizer.run_simulation(df["wind"], df["Load"], df["PV"], df.index.hour)

    # Add additional data
    results['Load'] = df['Load'].values
    results['PV'] = df['PV'].values
    results['wind'] = df['wind'].values

    penetration_pv = (np.sum(results['pv_to_load']) / np.sum(df["Load"])) * 100
    penetration_storage = (np.sum(results['storage_to_load']) / np.sum(df["Load"])) * 100
    penetration_wind = (np.sum(results['wind_to_load']) / np.sum(df["Load"])) * 100
    sum_load_peackhour = np.sum(df["Load"][df.index.hour.map(EnergyController.peackHour)])

    total_storage_energy_production = np.sum(results['storage_to_load']) / 4
    total_wind_energy_production = np.sum(
        results['wind_to_load'] + results['wind_to_grid'] + results['wind_to_storage']) / 4

    sum_pv_to_load_peakhour = np.sum(results["pv_to_load"][results["Time"].map(EnergyController.peackHour)])
    sum_storage_to_load_peakhour = np.sum(results["storage_to_load"][results["Time"].map(EnergyController.peackHour)])
    sum_wind_to_load_peakhour = np.sum(results["wind_to_load"][results["Time"].map(EnergyController.peackHour)])

    penetration_pv_peakhour = sum_pv_to_load_peakhour / sum_load_peackhour * 100
    penetration_storage_peakhour = sum_storage_to_load_peakhour / sum_load_peackhour * 100
    penetration_wind_peakhour = sum_wind_to_load_peakhour / sum_load_peackhour * 100
    total_penetration_peakhour = penetration_wind_peakhour + penetration_pv_peakhour + penetration_storage_peakhour

    total_renewable_penetration = penetration_pv + penetration_storage + penetration_wind
    total_energy_delivered_to_grid = np.sum(results['system_to_grid']) / 4
    total_energy_purchased_from_grid = np.sum(results['grid_to_load']) / 4

    # Save results
    results.to_csv(r"/Users/MAC/Documents/ems-project/results/outputTest888.csv", index=False)

    results = {
        "num_wind_turbines": num_wind_turbines,
        "storage_capacity_mwh": storage_capacity_mwh,
        "total_renewable_penetration": total_renewable_penetration,
        "total_wind_energy_production": total_wind_energy_production,
        "total_storage_energy_production": total_storage_energy_production,
        "total_energy_delivered_to_grid": total_energy_delivered_to_grid,
        "total_energy_purchased_from_grid": total_energy_purchased_from_grid,
        "penetration_pv_peakhour": penetration_pv_peakhour,
        "penetration_storage_peakhour": penetration_storage_peakhour,
        "penetration_wind_peakhour": penetration_wind_peakhour,
        "total_penetration_peakhour": total_penetration_peakhour,
    }
    pprint(results)
    return results


# Candidate selection process
n_wind_candidates = [i for i in range(0, 81, 20)]
battery_candidates = [i for i in range(0, 100, 20)]
candidates = []
allData = []
min_penetration_threshold = 70

for wind in n_wind_candidates:
    for batt in battery_candidates:
        metrics = run_simulation(num_wind_turbines=wind, storage_capacity_mwh=batt)
        allData.append(metrics)
        if metrics["total_renewable_penetration"] >= min_penetration_threshold:
            candidates.append(metrics)

if not candidates:
    raise RuntimeError("No viable candidate found.")

# Normalize only penetration
penetrations = np.array([c["total_renewable_penetration"] for c in candidates])
pen_min, pen_max = penetrations.min(), penetrations.max()

for c in candidates:
    c["normalized_penetration"] = (c["total_renewable_penetration"] - pen_min) / (pen_max - pen_min + 1e-3)

# MILP Optimization Model (maximize penetration)
model = pulp.LpProblem("EnergyOptimization", pulp.LpMinimize)
candidate_vars = pulp.LpVariable.dicts("Candidate", indices=range(len(candidates)), cat="Binary")

# Objective Function: maximize penetration (minimize 1/penetration)
model += pulp.lpSum([
    (1 / (candidates[i]["normalized_penetration"] + 1e-3)) * candidate_vars[i]
    for i in range(len(candidates))
]), "Objective"

# Constraint: Select exactly one candidate
model += pulp.lpSum([candidate_vars[i] for i in range(len(candidates))]) == 1, "SelectOne"

# Solve the optimization model
model.solve(pulp.PULP_CBC_CMD(msg=1))

# Retrieve the best solution
best_candidate = None
for i in range(len(candidates)):
    if pulp.value(candidate_vars[i]) == 1:
        best_candidate = candidates[i]
        break

if best_candidate:
    print(f"Optimal Solution: Wind: {best_candidate['num_wind_turbines']}, "
          f"Battery: {best_candidate['storage_capacity_mwh']} MWh, "
          f"Penetration: {best_candidate['total_renewable_penetration']:.2f}%")
else:
    print("No optimal solution found.")

# Convert to DataFrame
df_candidates = pd.DataFrame(candidates)
df_all_data = pd.DataFrame(allData)

df_all_data.to_csv(r"/Users/MAC/energy_management_system_simulation/ems_study/results/optimisation_result_v2.csv", index=False)

print(df_candidates.head(5))

# Scatter plot: Wind turbines vs Battery capacity vs Penetration
plt.figure(figsize=(10, 6))
sns.scatterplot(
    x="num_wind_turbines",
    y="storage_capacity_mwh",
    size="total_renewable_penetration",
    hue="total_renewable_penetration",
    palette="viridis",
    sizes=(50, 400),
    data=df_all_data,
    legend="brief"
)

# Highlight best candidate
plt.scatter(
    best_candidate["num_wind_turbines"],
    best_candidate["storage_capacity_mwh"],
    color="red", s=250, marker="*", label="Optimal Solution"
)

plt.title("Candidate Solutions: Penetration by Wind & Battery")
plt.xlabel("Number of Wind Turbines")
plt.ylabel("Battery Capacity (MWh)")
plt.legend()
plt.grid(True)
plt.show()

from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata

# Create grid for interpolation
x = df_all_data['num_wind_turbines']
y = df_all_data['storage_capacity_mwh']
z = df_all_data['total_renewable_penetration']

xi = np.linspace(x.min(), x.max(), 100)
yi = np.linspace(y.min(), y.max(), 100)
X, Y = np.meshgrid(xi, yi)
Z = griddata((x, y), z, (X, Y), method='cubic')

# Plot
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')
surf = ax.plot_surface(X, Y, Z, cmap='viridis', edgecolor='none', alpha=0.8)

# Highlight best candidate
ax.scatter(
    best_candidate["num_wind_turbines"],
    best_candidate["storage_capacity_mwh"],
    best_candidate["total_renewable_penetration"],
    color="red", s=100, marker="o", label="Optimal Solution"
)

ax.set_xlabel('Wind Turbines')
ax.set_ylabel('Battery Capacity (MWh)')
ax.set_zlabel('Renewable Penetration (%)')
ax.set_title('Optimization Landscape: Penetration vs Wind & Battery')

fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label="Penetration (%)")
plt.show()

# # Plot cost vs penetration
# plt.figure(figsize=(10, 6))
# sns.scatterplot(
#     x="total_cost",
#     y="total_renewable_penetration",
#     hue="num_wind_turbines",
#     palette="coolwarm",
#     size="storage_capacity_mwh",
#     sizes=(20, 200),
#     alpha=0.7,
#     edgecolor="black",
#     data=df_candidates
# )
# plt.scatter(best_candidate["total_cost"], best_candidate["total_renewable_penetration"], color="red", s=200, label="Optimal Solution")
# plt.xlabel("Total Cost ($)")
# plt.ylabel("Renewable Penetration (%)")
# plt.title("Trade-off Between Cost and Renewable Penetration")
# plt.legend(title="Wind Turbines")
# plt.grid(True)
# plt.show()

# from mpl_toolkits.mplot3d import Axes3D
# from scipy.interpolate import griddata

# # Create grid for continuous surface
# x = df_all_data['num_wind_turbines']
# y = df_all_data['storage_capacity_mwh']
# z = df_all_data['total_renewable_penetration']

# xi = np.linspace(x.min(), x.max(), 100)
# yi = np.linspace(y.min(), y.max(), 100)
# X, Y = np.meshgrid(xi, yi)
# Z = griddata((x, y), z, (X, Y), method='cubic')

# # Plotting
# fig = plt.figure(figsize=(12, 8))
# ax = fig.add_subplot(111, projection='3d')

# # Surface plot
# surf = ax.plot_surface(X, Y, Z, cmap='berlin_r', edgecolor='none')

# # Labels
# ax.set_xlabel('Number of Wind Turbines', fontsize=12)
# ax.set_ylabel('Battery Capacity (MWh)', fontsize=12)
# ax.set_zlabel('Total Renewable Penetration (%)', fontsize=12)
# ax.set_title('Penetration vs Battery Capacity and Wind Power', fontsize=14)

# # Color bar
# cbar = plt.colorbar(surf, ax=ax, pad=0.1)
# cbar.set_label('Penetration (%)', fontsize=12)
# plt.show()
