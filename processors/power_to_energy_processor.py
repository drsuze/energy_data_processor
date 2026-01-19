# initial logic to convert time series power data to daily energy stats


import pandas as pd
from pathlib import Path


# INPUT DATA TO PARSE

# location name of folder containing parquet files of power data
folder_name: str = 'Downloads/20221108'
# Get all parquet files from file path
folder = Path.home() / folder_name
task_parquet_files = folder.glob("*.parquet")


#########################################################################

# LOGIC TO PARSE DATA

# melt, filter, and process just the desired measurement type data
def filter_process_power_data(parquet_files):
    days_df_list = []
    for file in parquet_files:
        file_df = pd.read_parquet(file)
        file_df.index.name = 'timestamp'
        file_df = file_df.reset_index().drop_duplicates()

        # confirm each dataset is a complete day of 60*24 minutes
        row_count = len(file_df)
        print(f'{file} has {row_count} rows.')
        
        # melt wide data of many columns -> narrow data of many rows
        melt_df = file_df.melt(id_vars=['timestamp'], var_name="raw_name", value_name="value")
        
        # extract the contents within the brackets
        melt_df[["Measurement Name", "Object ID"]] = melt_df["raw_name"].str.extract(
    r"^(.*?)\s*\[(.*?)\]\s*$"
        )

        # filter to just the desired metrics
        voltage_df = melt_df[melt_df['raw_name'].str.contains("DC voltage of the BESS", regex=False)]
        current_df = melt_df[melt_df['raw_name'].str.contains("DC Current bus", regex=False)]

        voltage_df["Voltage (Vdc)"] = voltage_df['value']
        current_df["Current (A)"] = current_df['value']
        
        voltage_df["BESS ID"] = voltage_df["Measurement Name"].str.extract(r"(\d+)")
        current_df["BESS ID"] = current_df["Measurement Name"].str.extract(r"(\d+)")

        voltage_df["Inverter ID"] = voltage_df["Object ID"].str.extract(r"(\S*PCS\S*)$")
        current_df["Inverter ID"] = current_df["Object ID"].str.extract(r"(\S*PCS\S*)$")

        voltage_df = voltage_df[['timestamp', 'Inverter ID', 'BESS ID', "Voltage (Vdc)"]]
        current_df = current_df[['timestamp', 'Inverter ID', 'BESS ID', "Current (A)"]]

        power_df = pd.merge(voltage_df, current_df, on=['timestamp', 'Inverter ID', 'BESS ID'])
        
        power_df['power (kW)'] = power_df['Voltage (Vdc)'] * power_df['Current (A)'] / 1000

        days_df_list.append(power_df)

    full_df = pd.concat(days_df_list)
    return full_df


def power_to_daily_energy(power_df, id_cols, power_kw_col, timestamp_col='timestamp'):
    """Calculate daily energy throughput, charge and discharge separately."""
    power_df[timestamp_col] = pd.to_datetime(power_df[timestamp_col])
    power_df = power_df.sort_values(timestamp_col).reset_index()
    power_df['previous_timestamp'] = power_df.groupby(id_cols)[timestamp_col].shift(1)
    power_df['time_delta_seconds'] = (power_df[timestamp_col] - power_df['previous_timestamp']).dt.total_seconds()
    power_df['time_delta_seconds'] = power_df['time_delta_seconds'].fillna(60)
    power_df['positive_kw'] = power_df[power_kw_col].clip(lower=0)
    power_df['negative_kw'] = power_df[power_kw_col].clip(upper=0)
    power_df["Negative Energy (kWh)"] = power_df['negative_kw'] * power_df['time_delta_seconds'] / 3600
    power_df["Positive Energy (kWh)"] = power_df['positive_kw'] * power_df['time_delta_seconds'] / 3600
    power_df['date'] = power_df[timestamp_col].dt.date
    groupby_cols = ['date'] + id_cols
    energy_df = power_df.groupby(by=groupby_cols)[['Positive Energy (kWh)', 'Negative Energy (kWh)']].sum().reset_index()
    return energy_df


# execution
bess_power_data = filter_process_power_data(parquet_files=task_parquet_files)

print(bess_power_data.head())
bess_power_data.to_csv('power.csv')
bess_energy_data = power_to_daily_energy(power_df = bess_power_data,
                                         id_cols=['Inverter ID', 'BESS ID'],
                                         power_kw_col="power (kW)",
                                         timestamp_col="timestamp",
                                         )
print(bess_energy_data.head())
bess_energy_data.to_csv('energy_data.csv')
