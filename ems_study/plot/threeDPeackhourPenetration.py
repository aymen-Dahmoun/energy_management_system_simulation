import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.interpolate import griddata
from mpl_toolkits.mplot3d import Axes3D

# Load the data
csv_path = r"C:\Users\surface\matArticle\final_project\results\optimisation_result_v2.csv"
df_all_data = pd.read_csv(csv_path)

# 3D Plot: Penetration vs Battery Capacity and Wind Power
x = df_all_data['storage_capacity_mwh']
y = df_all_data['num_wind_turbines'] * 0.8  # Convert turbines to MW
z = df_all_data['total_penetration_peakhour']

# Create grid for continuous surface
xi = np.linspace(x.min(), x.max(), 100)
yi = np.linspace(y.min(), y.max(), 100)
X, Y = np.meshgrid(xi, yi)
Z = griddata((x, y), z, (X, Y), method='cubic')

# 3D Plot
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

# Surface plot
surf = ax.plot_surface(X, Y, Z, cmap='viridis', edgecolor='none')

# Labels
ax.set_xlabel('Battery Capacity (MWh)', fontsize=10)
ax.set_ylabel('Wind Farm Installed Power (MW)', fontsize=10)
ax.set_zlabel('Total Renewable Penetration at Peak Hours (%)', fontsize=10)
ax.set_title('Penetration vs Battery Capacity and Wind Power at Peak Hours', fontsize=14)

# Color bar
cbar = fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)
cbar.set_label('Penetration (%)', fontsize=12)

plt.show()
