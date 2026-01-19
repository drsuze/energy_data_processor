import pandas as pd
from pathlib import Path

from visualizers.daily_energy_report import heatmap_daily_energy


if __name__ == "__main__":

    energy_df = pd.read_csv(Path.home() / 'Downloads/energy_data.csv')
    figp = heatmap_daily_energy(energy_df=energy_df, plot_value='Positive Energy (kWh)')
    figp.write_html(Path.home() / "Downloads/positive_energy_heatmap.html")

    fign = heatmap_daily_energy(energy_df=energy_df, plot_value='Negative Energy (kWh)')
    fign.write_html(Path.home() / "Downloads/negative_energy_heatmap.html")
