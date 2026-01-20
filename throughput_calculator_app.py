import gradio as gr
import pandas as pd

from processors.power_to_energy_processor import (
    calc_per_bess_power_data, 
    power_to_daily_energy,
    get_worst_n
)
from visualizers.daily_energy_report import heatmap_daily_energy


def process(zip_folder):
    bess_power_data = calc_per_bess_power_data(zip_file=zip_folder)
    energy_df = power_to_daily_energy(power_df=bess_power_data)


    figp = heatmap_daily_energy(energy_df=energy_df, plot_value='Positive Energy (kWh)')
    fign = heatmap_daily_energy(energy_df=energy_df, plot_value='Negative Energy (kWh)')

    lowest_df = get_worst_n(energy_df=energy_df)
    return figp, fign, lowest_df, energy_df


with gr.Blocks() as demo:
    with gr.Row():
        file_input = gr.File(label="Upload zip folder of parquets", file_types=[".zip"], type="filepath")

    with gr.Row():
        plot1 = gr.Plot(label="Discharged Energy (kWh)")

    with gr.Row():
        plot2 = gr.Plot(label="Charged Energy (kWh)")

    with gr.Row():
        df1 = gr.Dataframe(label="BESS Throughput - Lowest 5 by Discharged Energy")

    with gr.Row():
        df2 = gr.Dataframe(label="BESS Throughput - All")

    file_input.change(fn=process, inputs=file_input, outputs=[plot1, plot2, df1, df2])

demo.launch()
