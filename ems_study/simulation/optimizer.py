# simulation/optimizer.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from final_project.config import BATTERY_NOMINAL_POWER_MW, BATTERY_CAPACITY_MWh
from controller100storage import EnergyController

import pandas as pd

class Optimizer:
    def __init__(self, storage_capacity=BATTERY_CAPACITY_MWh):
        self.controller = EnergyController(capacity=storage_capacity)

    def run_simulation(self, wind_df, load_df, pv_df, time):
        results = []
        time_values = time.to_numpy()  # Convert DatetimeIndex to an array
        for i in range(len(wind_df)):
            result = self.controller.manage_energy(pv_df.iloc[i], wind_df.iloc[i], load_df.iloc[i], time_values[i])
            results.append({**result})
        return pd.DataFrame(results)
