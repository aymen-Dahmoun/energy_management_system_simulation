import pandas as pd
from pvlib import pvsystem, modelchain, location
import sys, os

# Path setup
from ems_study.config import PV_TILT, PV_AZIMUTH, PV_MODULE, PV_INVERTER, PV_COUNT


def pvPowerForecast(flag=True, pv_count=PV_COUNT,
                    tilt=PV_TILT, azimuth=PV_AZIMUTH,
                    module_name=PV_MODULE, inverter_name=PV_INVERTER):
    # File paths
    file_weather_path = r"data\weather_pv.csv"
    existing_file_path = r"data\annual_power_input.csv"

    # Load weather data
    weather_raw = pd.read_csv(file_weather_path, index_col=0, parse_dates=True)

    # Flatten multi-index columns if necessary
    weather_raw.columns = [col[0] if isinstance(col, tuple) else col for col in weather_raw.columns]

    # Rename expected columns (ensure these match your CSV structure)
    # weather = weather_raw.rename(columns={
    #     'Temperature_2m': 'temp_air',
    #     'WindSpeed_10m': 'wind_speed',
    #     'ghi': 'ghi',
    #     'dni': 'dni',
    #     'dhi': 'dhi'
    # })

    # Filter only required columns for the model
    weather_formatted = weather_raw[['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed']]

    # Create location object (use correct lat/lon/elevation if known)
    loc = location.Location(latitude=35.0, longitude=1.0, tz='UTC', altitude=100)

    # Define PV system
    system = pvsystem.PVSystem(
        surface_tilt=tilt,
        surface_azimuth=azimuth,
        module_parameters=pvsystem.retrieve_sam('CECMod')[module_name],
        inverter_parameters=pvsystem.retrieve_sam('cecinverter')[inverter_name],
        racking_model='open_rack',  # Add this line
        module_type='glass_polymer'  # And this line
    )

    # Create and run model chain
    mc = modelchain.ModelChain(system, loc, aoi_model='physical', spectral_model='no_loss')
    mc.run_model(weather_formatted)

    # Get AC power output
    ac_power = mc.results.ac * pv_count

    # Use fixed time step (assumes evenly spaced data)
    time_step_hours = (ac_power.index[1] - ac_power.index[0]).seconds / 3600
    total_energy_wh = ac_power * time_step_hours
    annual_energy_mwh = total_energy_wh.sum() / 1e6

    # If flag is set, return annual energy only
    if flag:
        return annual_energy_mwh

    # Load existing Excel file to update PV output column
    existing_df = pd.read_excel(existing_file_path)

    if 'timestamp' not in existing_df.columns:
        print("Error: 'timestamp' column not found in the existing dataset.")
        print("Existing columns:", existing_df.columns)
        exit()

    # Ensure datetime alignment
    existing_df['timestamp'] = pd.to_datetime(existing_df['timestamp'], utc=True)

    # Format PV output
    pv_output_df = ac_power.reset_index()
    pv_output_df.columns = ['timestamp', 'pv']
    pv_output_df['timestamp'] = pd.to_datetime(pv_output_df['timestamp'], utc=True)

    # Match length
    min_length = min(len(existing_df), len(pv_output_df))
    existing_df = existing_df.iloc[:min_length]
    pv_output_df = pv_output_df.iloc[:min_length]

    # Update 'pv' column
    if 'pv' in existing_df.columns:
        existing_df.drop(columns=['pv'], inplace=True)
    existing_df['pv'] = pv_output_df['pv'].values

    # Save updated file (remove timezone to avoid Excel issues)
    existing_df['timestamp'] = existing_df['timestamp'].dt.tz_localize(None)
    existing_df.to_excel(existing_file_path, index=False)

    return annual_energy_mwh

