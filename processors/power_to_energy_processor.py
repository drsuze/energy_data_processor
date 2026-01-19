# initial logic to convert time series power data to daily energy stats


import pandas as pd
from pathlib import Path


# LOGIC TO PARSE DATA

# melt, filter, and calculate only the BESS-level dc power from voltage x current
def calc_per_bess_power_data(parquet_files: list[Path]) -> pd.DataFrame:
    """
    This function calculates the time series power data per BESS container.

    Input:
    
        parquet_files: list of parquet file Paths containing raw time series data in wide format.
       
    Output: 
            
        Pandas DataFrame with BESS container dc power in kW, one row per BESS per timestamp.
    """
    days_df_list = []

    for file in parquet_files:

        file_df = pd.read_parquet(file)
        file_df.index.name = 'timestamp'
        file_df = file_df.reset_index().drop_duplicates()

        # expect each dataset is a complete day of 60*24 minutes so 1660 rows
        row_count = len(file_df)
        print(f'{file} has {row_count} rows.')
        
        # melt wide data of many columns -> narrow data of many rows
        melt_df = file_df.melt(id_vars=['timestamp'], var_name="raw_name", value_name="value")
        
        # extract the contents within the brackets
        melt_df[["Measurement Name", "Object ID"]] = melt_df["raw_name"].str.extract(
            r"^(.*?)\s*\[(.*?)\]\s*$"
        )

        # filter to just the desired metrics, voltage of the DC bess and current at corresponding dc bus
        voltage_df = melt_df[melt_df['raw_name'].str.contains("DC voltage of the BESS", regex=False)]
        current_df = melt_df[melt_df['raw_name'].str.contains("DC Current bus", regex=False)]

        voltage_df["Voltage (Vdc)"] = voltage_df['value']
        current_df["Current (A)"] = current_df['value']
        
        # BESS ID number i.e. 1 to 3
        voltage_df["BESS ID"] = voltage_df["Measurement Name"].str.extract(r"(\d+)")
        current_df["BESS ID"] = current_df["Measurement Name"].str.extract(r"(\d+)")

        # Inverter ID number is a string within previously bracketed contents, containing "PCS"
        voltage_df["Inverter ID"] = voltage_df["Object ID"].str.extract(r"(\S*PCS\S*)$")
        current_df["Inverter ID"] = current_df["Object ID"].str.extract(r"(\S*PCS\S*)$")

        # keep relevant columns
        voltage_df = voltage_df[['timestamp', 'Inverter ID', 'BESS ID', "Voltage (Vdc)"]]
        current_df = current_df[['timestamp', 'Inverter ID', 'BESS ID', "Current (A)"]]

        # combine voltage and current data
        power_df = pd.merge(voltage_df, current_df, on=['timestamp', 'Inverter ID', 'BESS ID'])
        
        # multiple voltage and current to get power in W, divide by 1000 for kW
        power_df['power (kW)'] = power_df['Voltage (Vdc)'] * power_df['Current (A)'] / 1000

        days_df_list.append(power_df)

    full_df = pd.concat(days_df_list)
    return full_df


def power_to_daily_energy(power_df: pd.DataFrame, 
                          id_cols: list[str] = ['Inverter ID', 'BESS ID'],
                          power_kw_col: str = 'power (kW)', 
                          timestamp_col: str ='timestamp',
                          ) -> pd.DataFrame:
    """
    
    This function calculates daily energy throughput from time series power data, charge and discharge separately.
    
    Input:
    power_df: Pandas Dataframe containing time series power data, 1 or more devices
    id_cols: list of strings of device ID types to group with
    power_kw_col: string column name to find the power data in kW
    timestamp_col: string column name to find the timestamp data
    
    Output:
    Pandas Dataframe summarizing daily energy throughput per device per direction

    """

    # make sure it's in pandas datetime and sort ascending
    power_df[timestamp_col] = pd.to_datetime(power_df[timestamp_col])
    power_df = power_df.sort_values(timestamp_col).reset_index()

    # find timedelta and set maximum gap as 60 seconds
    power_df['previous_timestamp'] = power_df.groupby(id_cols)[timestamp_col].shift(1)
    power_df['time_delta_seconds'] = (power_df[timestamp_col] - power_df['previous_timestamp']).dt.total_seconds()
    power_df['time_delta_seconds'] = power_df['time_delta_seconds'].fillna(60).clip(upper=60)
    
    # separate charging/discharging via positive/negative power values (reflecting current direction)
    power_df['positive_kw'] = power_df[power_kw_col].clip(lower=0)
    power_df['negative_kw'] = power_df[power_kw_col].clip(upper=0)
    power_df["Negative Energy (kWh)"] = power_df['negative_kw'] * power_df['time_delta_seconds'] / 3600
    power_df["Positive Energy (kWh)"] = power_df['positive_kw'] * power_df['time_delta_seconds'] / 3600
    
    # summate daily energy totals
    power_df['date'] = power_df[timestamp_col].dt.date
    groupby_cols = ['date'] + id_cols
    energy_df = power_df.groupby(by=groupby_cols)[['Positive Energy (kWh)', 'Negative Energy (kWh)']].sum().reset_index()
    
    return energy_df

