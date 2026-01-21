# initial logic to convert time series data to daily energy stats


import logging
import zipfile
import pandas as pd
import tempfile
import os
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# melt, filter, and calculate only the BESS-level dc power from voltage x current
def calc_per_bess_power_data(zip_file) -> pd.DataFrame:
    """
    This function calculates the time series power data per BESS container.

    Input:

        zip_file: zipped folder with parquet files containing raw time series data in wide format.

    Output:

        Pandas DataFrame with BESS container dc power in kW, one row per BESS per timestamp.
    """
    bess_power_df_list = []
    raw_time_df_list = []

    # Temporary folder to extract ZIP
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_file.name, "r") as z:
            z.extractall(tmpdir)

        # Loop through all parquet files
        for filename in os.listdir(tmpdir):
            full_path = os.path.join(tmpdir, filename)
            file_df = pd.read_parquet(full_path)
            logging.info(f"Read parquet file named {filename} into a dataframe.")

            file_df = file_df.drop(
                columns=[c for c in file_df.columns if c.startswith("Unnamed")]
            )
            file_df.index.name = "timestamp"
            file_df = file_df.reset_index().drop_duplicates()
            raw_time_df_list.append(file_df)

            power_df = parse_raw_measurements(file_df)
            bess_power_df_list.append(power_df)

    full_bess_power_df = pd.concat(bess_power_df_list)
    full_time_df = pd.concat(raw_time_df_list)

    logging.info(f"Calculating data coverage...")
    gap_ranges_df = measure_data_coverage(full_time_df)

    return full_bess_power_df, gap_ranges_df


def measure_data_coverage(file_df: pd.DataFrame):
    """This functions calculates the time coverage percent of input data and reports gaps."""
    file_df.loc[:, "timestamp"] = pd.to_datetime(file_df["timestamp"])
    file_df = file_df.sort_values("timestamp")

    # first timestamp expected to start at 1 minute after midnight
    earliest_date = file_df["timestamp"].min().date()

    # last timestamp expected to end at midnight which looks like the next day
    # so subtract 1 minute before assuming latest date
    latest_date = (file_df["timestamp"].max() - pd.Timedelta(minutes=1)).date()

    day_count = (latest_date - earliest_date).days + 1
    logging.info(f"File includes data from a {day_count}-day date range")

    # create a dataframe whose index covers all minutes in the comparable data range
    start_ts = pd.Timestamp(earliest_date) + pd.Timedelta(minutes=1)
    end_ts = pd.Timestamp(latest_date) + pd.Timedelta(days=1) - pd.Timedelta(minutes=1)

    full_index = pd.date_range(start=start_ts, end=end_ts, freq="1min")
    coverage_df = pd.DataFrame(index=full_index).reset_index()
    coverage_df = coverage_df.rename(columns={"index": "timestamp"})

    # make sure the data is normalized to the minute, just in case
    file_df["timestamp"] = pd.to_datetime(file_df["timestamp"]).dt.floor("min")

    # merge for comparison
    merged = coverage_df.merge(
        file_df[["timestamp"]], on="timestamp", how="left", indicator=True
    )

    missing_minutes = merged.loc[merged["_merge"] == "left_only", "timestamp"]
    present_minutes = merged.loc[merged["_merge"] == "both", "timestamp"]
    coverage_pct = len(present_minutes) / len(full_index) * 100

    logging.info(
        "Time coverage: %.2f%% (%d / %d minutes present)",
        coverage_pct,
        len(present_minutes),
        len(full_index),
    )

    gaps = missing_minutes.diff().ne(pd.Timedelta(minutes=1)).cumsum()

    gap_ranges = missing_minutes.groupby(gaps).agg(
        gap_start="min", gap_end="max", gap_length_minutes="count"
    )
    gap_ranges["gap_length_days"] = gap_ranges["gap_length_minutes"] / (60 * 24)

    if gap_ranges.empty:
        logging.info("No gaps detected in time coverage.")
    else:
        logging.info(
            "Detected %d gap ranges:\n%s",
            len(gap_ranges),
            gap_ranges.to_string(index=False),
        )

    gap_ranges_df = gap_ranges.reset_index()
    return gap_ranges_df


def parse_raw_measurements(file_df: pd.DataFrame) -> pd.DataFrame:
    """
    Process original dataframe to get BESS container dc power in kW, one row per BESS per timestamp.
    """

    # melt wide data of many columns -> narrow data of many rows
    melt_df = file_df.melt(
        id_vars=["timestamp"], var_name="raw_name", value_name="value"
    )

    # extract the contents within the brackets
    melt_df[["Measurement Name", "Object ID"]] = melt_df["raw_name"].str.extract(
        r"^(.*?)\s*\[(.*?)\]\s*$"
    )

    # filter to just the desired metrics, voltage of the DC bess and current at corresponding dc bus
    voltage_df = melt_df[
        melt_df["raw_name"].str.contains("DC voltage of the BESS", regex=False)
    ].copy()
    current_df = melt_df[
        melt_df["raw_name"].str.contains("DC Current bus", regex=False)
    ].copy()

    voltage_df.loc[:, "Voltage (Vdc)"] = voltage_df["value"]
    current_df.loc[:, "Current (A)"] = current_df["value"]

    # BESS ID number i.e. 1 to 3
    voltage_df.loc[:, "BESS ID"] = voltage_df["Measurement Name"].str.extract(r"(\d+)")
    current_df.loc[:, "BESS ID"] = current_df["Measurement Name"].str.extract(r"(\d+)")

    # Inverter ID number is a string within previously bracketed contents, containing "PCS"
    voltage_df.loc[:, "Inverter ID"] = voltage_df["Object ID"].str.extract(
        r"(\S*PCS\S*)$"
    )
    current_df.loc[:, "Inverter ID"] = current_df["Object ID"].str.extract(
        r"(\S*PCS\S*)$"
    )

    # keep relevant columns
    voltage_df = voltage_df[["timestamp", "Inverter ID", "BESS ID", "Voltage (Vdc)"]]
    current_df = current_df[["timestamp", "Inverter ID", "BESS ID", "Current (A)"]]

    # combine voltage and current data
    power_df = pd.merge(
        voltage_df, current_df, on=["timestamp", "Inverter ID", "BESS ID"]
    )

    # multiple voltage and current to get power in W, divide by 1000 for kW
    power_df["power (kW)"] = power_df["Voltage (Vdc)"] * power_df["Current (A)"] / 1000

    return power_df


def power_to_daily_energy(
    power_df: pd.DataFrame,
    id_cols: list[str] = ["Inverter ID", "BESS ID"],
    power_kw_col: str = "power (kW)",
    timestamp_col: str = "timestamp",
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
    power_df["previous_timestamp"] = power_df.groupby(id_cols)[timestamp_col].shift(1)
    power_df["time_delta_seconds"] = (
        power_df[timestamp_col] - power_df["previous_timestamp"]
    ).dt.total_seconds()
    power_df["time_delta_seconds"] = (
        power_df["time_delta_seconds"].fillna(60).clip(upper=60)
    )

    # separate charging/discharging via positive/negative power values (reflecting current direction)
    power_df["positive_kw"] = power_df[power_kw_col].clip(lower=0)
    power_df["negative_kw"] = power_df[power_kw_col].clip(upper=0)
    power_df["Charged Energy (kWh)"] = (
        power_df["negative_kw"] * power_df["time_delta_seconds"] / 3600
    )
    power_df["Discharged Energy (kWh)"] = (
        power_df["positive_kw"] * power_df["time_delta_seconds"] / 3600
    )

    # summate daily energy totals
    power_df["date"] = power_df[timestamp_col].dt.date
    groupby_cols = ["date"] + id_cols
    energy_df = (
        power_df.groupby(by=groupby_cols)[
            ["Discharged Energy (kWh)", "Charged Energy (kWh)"]
        ]
        .sum()
        .reset_index()
    )

    return energy_df


def get_worst_n(energy_df: pd.DataFrame, n=5) -> pd.DataFrame:
    """Based on total discharged throughput, return n lowest BESS containers."""

    total_df = (
        energy_df.groupby(by=["Inverter ID", "BESS ID"])["Discharged Energy (kWh)"]
        .sum()
        .reset_index()
    )

    lowest_df = total_df.sort_values("Discharged Energy (kWh)").head(n)
    return lowest_df
