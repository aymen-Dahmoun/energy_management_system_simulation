import numpy as np
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from ems_study.config import BATTERY_NOMINAL_POWER_MW, BATTERY_CAPACITY_MWh

class BatterySystem():
    def __init__(self, capacity_MWh=BATTERY_CAPACITY_MWh, nominal_power_MW=BATTERY_NOMINAL_POWER_MW, efficiency=1, 
                 capital_cost_per_kWh=350, # USD/kWh
                 replacement_cost_per_kWh=180, # USD/kWh
                 operational_maintenance_cost_per_kWh=6, # USD/kWh/year
                 project_lifetime_years=20,
                 annual_degradation_rate=0.02):
        """
        Initialize battery system with LCOS-related parameters
        
        Args:
            capacity_MWh (float): Battery capacity in MWh
            nominal_power_MW (float): Nominal power in MW
            efficiency (float): Round-trip efficiency
            capital_cost_per_kWh (float): Initial capital cost per kWh
            replacement_cost_per_kWh (float): Replacement cost per kWh
            operational_maintenance_cost_per_kWh (float): O&M cost per kWh per year
            project_lifetime_years (int): Project lifetime in years
            annual_degradation_rate (float): Annual battery capacity degradation
        """
        self.capacity = capacity_MWh
        self.energy_stored = self.capacity * 1  # Assume 50% initial SoC
        self.efficiency = efficiency
        self.nominal_power = nominal_power_MW
        
        # LCOS parameters
        self.capital_cost_per_kWh = capital_cost_per_kWh
        self.replacement_cost_per_kWh = replacement_cost_per_kWh
        self.operational_maintenance_cost_per_kWh = operational_maintenance_cost_per_kWh
        self.project_lifetime_years = project_lifetime_years
        self.annual_degradation_rate = annual_degradation_rate

    def charge(self, power_MW, time_m=15):
        """Charge the battery with given power (MW) over time (minutes)."""
        power_MW = min(power_MW, self.nominal_power)  # Limit to nominal power
        energy_added = power_MW * self.efficiency * (time_m / 60)  # Convert MW to MWh
        self.energy_stored = min(self.energy_stored + energy_added, self.capacity)
    
    def discharge(self, power_MW, time_m=15):
        """Discharge the battery with given power (MW) over time (hours)."""
        power_MW = min(power_MW, self.nominal_power)  # Limit to nominal power
        energy_needed = power_MW * (time_m / 60) / self.efficiency  # Convert MW to MWh
        self.energy_stored = max(self.energy_stored - energy_needed, 0)
        if self.capacity == 0:
            self.energy_stored = 0
   
    def get_soc(self):
        """Return the state of charge (SoC) as a percentage."""
        if self.capacity == 0:
            return 0
        return (self.energy_stored / self.capacity) * 100

    # def calculate_lcos(self, annual_energy_throughput_MWh=None, discount_rate=0.07):
    #     """
    #     Calculate Levelized Cost of Storage (LCOS)
        
    #     Args:
    #         annual_energy_throughput_MWh (float): Annual energy throughput, defaults to full capacity
    #         discount_rate (float): Financial discount rate
        
    #     Returns:
    #         float: Levelized Cost of Storage in USD/MWh
    #     """
    #     # If no annual throughput specified, assume full battery capacity cycled annually
    #     if annual_energy_throughput_MWh is None:
    #         annual_energy_throughput_MWh = self.capacity

    #     # Calculate capital expenditure (CAPEX)
    #     initial_capex = self.capacity * 1000 * self.capital_cost_per_kWh  # Convert MWh to kWh

    #     # Calculate replacement costs
    #     total_replacement_cost = 0
    #     remaining_life = self.project_lifetime_years
    #     replacement_interval = int(np.ceil(10 / (1 - self.annual_degradation_rate)))
        
    #     while remaining_life > 0:
    #         total_replacement_cost += (self.capacity * 1000 * self.replacement_cost_per_kWh) / (1 + discount_rate) ** replacement_interval
    #         remaining_life -= replacement_interval

    #     # Calculate operational expenditure (OPEX)
    #     annual_opex = self.capacity * 1000 * self.operational_maintenance_cost_per_kWh

    #     # Calculate total annualized cost
    #     total_annualized_cost = (
    #         initial_capex / (((1 + discount_rate) ** self.project_lifetime_years - 1) / 
    #                          (discount_rate * (1 + discount_rate) ** self.project_lifetime_years)) +
    #         total_replacement_cost / (((1 + discount_rate) ** self.project_lifetime_years - 1) / 
    #                                   (discount_rate * (1 + discount_rate) ** self.project_lifetime_years)) +
    #         annual_opex * self.project_lifetime_years
    #     )

    #     # Calculate LCOS
    #     lcos = total_annualized_cost / annual_energy_throughput_MWh

    #     return lcos
