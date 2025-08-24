# simulation/controller.py
import pandas as pd
import sys
import os

# Append the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from ems_study.models.battery import BatterySystem  # Now it should work
from ems_study.config import BATTERY_CAPACITY_MWh


class EnergyController:
    def __init__(self, capacity=BATTERY_CAPACITY_MWh):
        self.battery = BatterySystem(capacity_MWh=capacity)  # Keep only the battery as a class attribute

    def manage_energy(self, pv_power, wind_power, load_demand, time):
        """
        Replacement decision algorithm that:
          - Prioritizes covering load from PV then Wind.
          - On PEAK hours: uses battery discharge before importing from grid.
          - On OFF-PEAK hours: prefers charging battery with surplus; avoids discharging unless needed for stability.
          - Splits surplus between storage and grid, respecting nominal power and efficiency.
          - Preserves the original return structure and semantics.
        """

        # -------------------- Init all outputs to zero (preserve keys) --------------------
        port = ''
        pv_to_load = 0.0
        wind_to_load = 0.0
        storage_to_load = 0.0
        grid_import_to_load = 0.0  # positive means importing to serve load
        system_export_to_grid = 0.0  # positive means exporting surplus

        pv_to_grid = 0.0
        wind_to_grid = 0.0
        pv_to_storage = 0.0
        wind_to_storage = 0.0

        is_peak = self.peackHour(time)
        soc = self.battery.get_soc()
        nominal = getattr(self.battery, "nominal_power", 0.0)
        eff = getattr(self.battery, "efficiency", 1.0)

        # -------------------- Step 1: Serve load from PV then Wind -----------------------
        remaining_load = float(load_demand)

        pv_to_load = min(pv_power, remaining_load)
        remaining_load -= pv_to_load
        pv_remain = pv_power - pv_to_load  # PV not used for load (potential surplus)

        wind_to_load = min(wind_power, remaining_load)
        remaining_load -= wind_to_load
        wind_remain = wind_power - wind_to_load  # Wind not used for load

        # -------------------- Step 2: Battery vs Grid for residual load ------------------
        # Peak: discharge before grid, Off-peak: prefer grid (keep battery for peak)
        if remaining_load > 0:
            if is_peak and soc > 20:
                # Discharge limited by nominal power
                discharge_request = min(remaining_load, nominal)
                if discharge_request > 0:
                    self.battery.discharge(discharge_request)
                    storage_to_load = discharge_request
                    remaining_load -= discharge_request

            # Whatever remains is grid import
            if remaining_load > 0:
                grid_import_to_load = remaining_load
                remaining_load = 0.0

        # -------------------- Step 3: Surplus handling (PV/Wind remaining) --------------
        # Charge storage first (up to nominal), then export to grid.
        total_surplus = pv_remain + wind_remain
        if total_surplus > 0:
            # Charge limited by nominal power
            charge_power = min(total_surplus, nominal)

            # Proportional split of charge between PV and Wind based on their remaining surplus
            pv_share = pv_remain / total_surplus if total_surplus > 0 else 0.0
            wind_share = 1.0 - pv_share

            charge_pv = charge_power * pv_share
            charge_wind = charge_power * wind_share

            # Charge battery (record energy to_storage with efficiency as in your original code)
            if charge_power > 0:
                self.battery.charge(charge_power)
                pv_to_storage = charge_pv * eff
                wind_to_storage = charge_wind * eff

            # Any surplus beyond charge goes to grid, split proportionally
            export_power = total_surplus - charge_power
            if export_power > 0:
                pv_export = min(pv_remain - charge_pv, max(0.0, export_power * pv_share))
                wind_export = min(wind_remain - charge_wind, max(0.0, export_power * wind_share))

                # Numerical safety
                pv_export = max(0.0, pv_export)
                wind_export = max(0.0, wind_export)

                pv_to_grid = pv_export
                wind_to_grid = wind_export
                system_export_to_grid = pv_export + wind_export

        # -------------------- Step 4: Port / labeling (human-readable mode) -------------
        used = []
        if pv_to_load > 0: used.append("pv")
        if wind_to_load > 0: used.append("wind")
        if storage_to_load > 0: used.append("storage")
        if grid_import_to_load > 0: used.append("grid")
        mode = "[peak]" if is_peak else "[off-peak]"
        if not used and system_export_to_grid > 0:
            port = f"export only {mode}"
        elif not used:
            port = f"idle {mode}"
        else:
            port = " + ".join(used) + f" {mode}"

        # -------------------- Step 5: Peak-hour tracking fields --------------------------
        pv_to_load_peakhour = pv_to_load if is_peak else 0.0
        load_demand_peakhour = load_demand if is_peak else 0.0

        # -------------------- Step 6: Preserve original return structure -----------------

        return {
            "Time": time,
            "pv_to_load": pv_to_load,
            "wind_to_load": wind_to_load,
            "storage_to_load": storage_to_load,
            "grid_to_load": grid_import_to_load,  # positive import to load
            "system_to_grid": system_export_to_grid,  # positive export to grid
            "pv_to_grid": abs(pv_to_grid),
            "wind_to_grid": abs(wind_to_grid),
            "wind_to_storage": abs(wind_to_storage),
            "pv_to_storage": abs(pv_to_storage),
            "battery_soc": self.battery.get_soc(),
            "port": port,
            "pv_to_load_peakhour": pv_to_load_peakhour,
            "load_demand_peakhour": load_demand_peakhour
        }

    def peackHour(self, time):
        hours = [19, 20, 21, 22, 23, 0, 11, 12, 18]
        return int(time) in hours
