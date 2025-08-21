import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load the data
csv_path = r"C:\Users\pc\Desktop\project\ems_study\results\final_output.csv"
df = pd.read_csv(csv_path)

# Ensure 'Time' is parsed correctly
df['Time'] = pd.to_datetime(df['Time'])
df.set_index('Time', inplace=True)

# Convert numeric columns
df = df.apply(pd.to_numeric, errors='coerce').fillna(0)

# Choose date range
start_date = "2025-01-01"
end_date = "2025-01-06"  # Adjust this for more days
df_filtered = df.loc[start_date:end_date].resample('30T').mean()

# Create figure
fig, ax1 = plt.subplots(figsize=(14, 6))

# Define bar width for smooth histogram
bar_width = 0.012  # Adjust for thinner bars

# Bar plots for energy sources
ax1.bar(df_filtered.index, df_filtered['pv_to_load'], width=bar_width, color='#00ffff', label="PV to Load", alpha=1)
ax1.bar(df_filtered.index, df_filtered['wind_to_load'], width=bar_width, bottom=df_filtered['pv_to_load'], color='#000f18', label="Wind to Load", alpha=1)
ax1.bar(df_filtered.index, df_filtered['grid_to_load'], width=bar_width, bottom=df_filtered['pv_to_load'] + df_filtered['wind_to_load'], color='#ff54c6', label="Grid to Load", alpha=0.8)
ax1.bar(df_filtered.index, df_filtered['storage_to_load'], width=bar_width, bottom=df_filtered['pv_to_load'] + df_filtered['wind_to_load'] + df_filtered['grid_to_load'], color='#fff647', label="Battery to Load", alpha=0.8)

# Load curve
ax1.plot(df_filtered.index, df_filtered['Load'], color='black', linewidth=3, linestyle='dotted', label="Load")

# Secondary y-axis for SOC
ax2 = ax1.twinx()
ax2.plot(df_filtered.index, df_filtered['battery_soc'], color='red', linewidth=1, linestyle='dashed', label="Battery SOC (%)")

# Labels and grid
ax1.set_xlabel("Time")
ax1.set_ylabel("Power (MW)")
ax2.set_ylabel("SOC (%)")
ax1.set_ylim(0, 25)
ax2.set_ylim(0, 100)
ax1.set_title(f"Energy Distribution from {start_date} to {end_date}")

# Adjust x-axis for readability
ax1.xaxis.set_major_locator(plt.MaxNLocator(integer=True))

# Legends
ax1.legend(loc="upper left")
ax2.legend(loc="upper right")

# Better grid style
ax1.grid(True, which="both", linestyle="--", linewidth=0.5)

plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
plt.show()
