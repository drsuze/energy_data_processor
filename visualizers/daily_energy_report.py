# visualize daily energy stats using tables and graphs e.g. heatmaps

import pandas as pd
import plotly.express as px
from pathlib import Path


def heatmap_daily_energy(energy_df: pd.DataFrame, plot_value: str = 'Positive Energy (kWh)'):
    """Given daily energy stats, create heatmap of throughput amounts across the site."""
    
    energy_df['BESS container ID'] = energy_df['Inverter ID'] + '-' + energy_df['BESS ID'].astype(str)
    
    pivot_df = energy_df.pivot(index='date', columns='BESS container ID', values=plot_value)
    fig = px.imshow(
    pivot_df,
    color_continuous_scale='Viridis', # Customize the color scale
    title=f'Heatmap of daily {plot_value} per BESS container'
    )

    return fig

