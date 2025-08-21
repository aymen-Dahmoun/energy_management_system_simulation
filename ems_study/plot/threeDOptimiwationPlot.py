import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata

# Load the data
csv_path = r"C:\Users\surface\matArticle\final_project\results\optimisation_result_v2.csv"
df_all_data = pd.read_csv(csv_path)

# Plot cost vs penetration
plt.figure(figsize=(10, 6))
sns.scatterplot(
    x="total_cost",
    y="total_renewable_penetration",
    hue="num_wind_turbines",
    palette="coolwarm",
    size="storage_capacity_mwh",
    sizes=(20, 200),
    alpha=0.7,
    edgecolor="black",
    data=df_all_data
)

# Find the best candidate (minimum cost and highest penetration)
best_candidate = df_all_data.loc[df_all_data['total_cost'].idxmin()]
plt.scatter(
    best_candidate["total_cost"],
    best_candidate["total_renewable_penetration"],
    color="red",
    s=200,
    label="Optimal Solution"
)

plt.xlabel("Total Cost ($)")
plt.ylabel("Renewable Penetration (%)")
plt.title("Trade-off Between Cost and Renewable Penetration")
plt.legend(title="Wind Turbines")
plt.grid(True)
plt.show()

# 3D Plot: Penetration vs Battery Capacity and Wind Power
x = df_all_data['storage_capacity_mwh']
y = df_all_data['num_wind_turbines'] * 0.8
z = df_all_data['total_renewable_penetration']

# Create grid for continuous surface
xi = np.linspace(x.min(), x.max(), 100)
yi = np.linspace(y.min(), y.max(), 100)
X, Y = np.meshgrid(xi, yi)
Z = griddata((x, y), z, (X, Y), method='cubic')

# Plotting
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

# Surface plot
surf = ax.plot_surface(X, Y, Z, cmap='berlin_r', edgecolor='none')

# Labels
ax.set_xlabel('Battery Capacity (MWh)', fontsize=8)
ax.set_ylabel('Wind Farm Installed Power MW', fontsize=8)
ax.set_zlabel('Total Renewable Penetration (%)', fontsize=8)
ax.set_title('Penetration vs Battery Capacity and Wind Power', fontsize=14)

# Color bar
cbar = plt.colorbar(surf, ax=ax, pad=0.1)
cbar.set_label('Penetration (%)', fontsize=12)
plt.show()
