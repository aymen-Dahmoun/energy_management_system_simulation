import pandas as pd
from pvlib import pvsystem, modelchain, location
import sys, os
from ems_study.config import PV_TILT, PV_AZIMUTH, PV_MODULE, PV_INVERTER, PV_COUNT

def pvPowerForecast(flag=True, pv_count=PV_COUNT,
                    tilt=PV_TILT, azimuth=PV_AZIMUTH,
                    module_name=PV_MODULE, inverter_name=PV_INVERTER):
    # File paths
    file_weather_path = r"data\weather_pv.csv"
    existing_file_path = r"data\annual_power_input.csv"

    # Load weather data
    weather_raw = pd.read_csv(file_weather_path, index_col=0, parse_dates=True)
    weather_raw.columns = [col[0] if isinstance(col, tuple) else col for col in weather_raw.columns]

    # Keep only required columns
    weather_formatted = weather_raw[['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed']]

    # Location object
    loc = location.Location(latitude=35.0, longitude=1.0, tz='UTC', altitude=100)

    # Define PV system
    system = pvsystem.PVSystem(
        surface_tilt=tilt,
        surface_azimuth=azimuth,
        module_parameters=pvsystem.retrieve_sam('CECMod')[module_name],
        inverter_parameters=pvsystem.retrieve_sam('cecinverter')[inverter_name],
        racking_model='open_rack',
        module_type='glass_polymer'
    )

    # Run model chain
    mc = modelchain.ModelChain(system, loc, aoi_model='physical', spectral_model='no_loss')
    mc.run_model(weather_formatted)

    # Get AC power
    ac_power = mc.results.ac * pv_count
    time_step_hours = (ac_power.index[1] - ac_power.index[0]).seconds / 3600
    total_energy_wh = ac_power * time_step_hours
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

    # Prepare PV output
    pv_output_df = ac_power.reset_index()
    pv_output_df.columns = ['Time', 'PV']
    pv_output_df['Time'] = pd.to_datetime(pv_output_df['Time'], utc=True)

    # Match lengths
    min_length = min(len(existing_df), len(pv_output_df))
    existing_df = existing_df.iloc[:min_length]
    pv_output_df = pv_output_df.iloc[:min_length]

    # Update 'pv' column
    if 'PV' in existing_df.columns:
        existing_df.drop(columns=['PV'], inplace=True)
    existing_df['PV'] = pv_output_df['PV'].values

    # Save updated CSV
    existing_df.to_csv(existing_file_path, index=False)

    return annual_energy_mwh
