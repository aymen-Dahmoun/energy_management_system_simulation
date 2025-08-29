import pandas as pd
from windpowerlib import ModelChain, WindTurbine
import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from ems_study.config import TURBINE_COUNT, TURBINE_TYPE

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))  # project root
DATA_DIR = os.path.join(BASE_DIR, "data")

def windPowerForecast(flag=False, turbine_count=TURBINE_COUNT, turbine_type=TURBINE_TYPE):
    # File paths
    file_weather_path = r"/Users/MAC/energy_management_system_simulation/ems_study/data/weather.csv"
    existing_file_path = r"/Users/MAC/energy_management_system_simulation/ems_study/data/annual_power_input.csv"

    # Load weather data
    weather_raw = pd.read_csv(file_weather_path, header=[0, 1], index_col=0, parse_dates=True)

    # Rename columns for clarity
    weather = weather_raw.copy()
    weather.columns = ['Pressure', 'Temperature_2m', 'WindSpeed_10m', 'RoughnessLength', 'Temperature_80m',
                       'WindSpeed_80m']

    # Format weather data for Windpowerlib
    weather_formatted = pd.DataFrame(
        {
            ('wind_speed', 10): weather['WindSpeed_10m'],
            ('temperature', 2): weather['Temperature_2m'],
            ('pressure', 0): weather['Pressure'],
            ('roughness_length', 0): weather['RoughnessLength']
        },
        index=weather.index
    )
    weather_formatted.columns = pd.MultiIndex.from_tuples(weather_formatted.columns)

    # Wind farm configuration
    wind_farm_config = [
        {"turbine_type": turbine_type, "hub_height": 80, "rotor_diameter": 53, "count": turbine_count},
    ]

    # Simulate power generation
    total_power_output = pd.Series(0, index=weather.index)
    for turbine_config in wind_farm_config:
        turbine = WindTurbine(
            hub_height=turbine_config["hub_height"],
            rotor_diameter=turbine_config["rotor_diameter"],
            turbine_type=turbine_config["turbine_type"]
        )
        mc = ModelChain(turbine, wind_speed_model="logarithmic", density_model="ideal_gas")
        mc.run_model(weather_formatted)
        total_power_output += mc.power_output * turbine_config["count"]

    # Compute energy
    time_step_hours = (weather.index[1] - weather.index[0]).seconds / 3600
    total_energy_wh = total_power_output * time_step_hours
    annual_energy_mwh = total_energy_wh.sum() / 1e6

    if flag:
        return annual_energy_mwh

    # Load existing CSV file
    existing_df = pd.read_csv(existing_file_path)
    if 'Time' not in existing_df.columns:
        print("Error: 'Time' column not found in the existing dataset.")
        print("Existing columns:", existing_df.columns)
        exit()

    # Ensure datetime alignment
    existing_df['Time'] = pd.to_datetime(existing_df['Time'], utc=True)

    # Prepare wind output dataframe
    wind_output_df = total_power_output.reset_index()
    wind_output_df.columns = ['Time', 'wind']
    wind_output_df['Time'] = pd.to_datetime(wind_output_df['Time'], utc=True)

    # Match lengths
    min_length = min(len(existing_df), len(wind_output_df))
    existing_df = existing_df.iloc[:min_length]
    wind_output_df = wind_output_df.iloc[:min_length]

    # Update 'wind' column
    if 'wind' in existing_df.columns:
        existing_df.drop(columns=['wind'], inplace=True)
    existing_df['wind'] = wind_output_df['wind'].values

    # Save back to CSV
    existing_df.to_csv(existing_file_path, index=False)

    return annual_energy_mwh
