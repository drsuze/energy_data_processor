from processors.power_to_energy_processor import calc_per_bess_power_data, power_to_daily_energy

from pathlib import Path


# INPUT DATA TO PARSE

# location name of folder containing parquet files of power data
folder_name: str = 'Downloads/20221108'
# Get all parquet files from file path
folder = Path.home() / folder_name
task_parquet_files = folder.glob("*.parquet")


def main():
    """Parse parquet files of raw data into total energy throughput per BESS container."""
    bess_power_data = calc_per_bess_power_data(parquet_files=task_parquet_files)
    bess_energy_data = power_to_daily_energy(power_df=bess_power_data)

    print(bess_energy_data.head())
    bess_energy_data.to_csv(Path.home() / 'Downloads/energy_data.csv')
    print('Completed.')


