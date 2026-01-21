import gradio as gr
import pandas as pd

from energize.processors.power_to_energy_processor import (
    calc_per_bess_power_data,
    power_to_daily_energy,
    get_worst_n,
)
from energize.visualizers.daily_energy_report import (
    heatmap_daily_energy,
    write_report_and_csv,
)


def process(zip_folder):
    bess_power_data, gaps_data = calc_per_bess_power_data(zip_file=zip_folder)
    energy_df = power_to_daily_energy(power_df=bess_power_data)

    figp = heatmap_daily_energy(
        energy_df=energy_df, plot_value="Discharged Energy (kWh)"
    )
    fign = heatmap_daily_energy(energy_df=energy_df, plot_value="Charged Energy (kWh)")

    lowest_df = get_worst_n(energy_df=energy_df)

    report_path, csv_path = write_report_and_csv(
        gaps_data, figp, fign, lowest_df, energy_df
    )
    return gaps_data, figp, fign, lowest_df, energy_df, report_path, csv_path


def main():
    with gr.Blocks() as demo:
        with gr.Row():
            file_input = gr.File(
                label="Upload zip folder of parquets",
                file_types=[".zip"],
                type="filepath",
            )
        with gr.Row():
            gaps_df = gr.Dataframe(label=f"Data Gaps (if any)")

        with gr.Row():
            plot1 = gr.Plot(label="Discharged Energy (kWh)")

        with gr.Row():
            plot2 = gr.Plot(label="Charged Energy (kWh)")

        with gr.Row():
            df1 = gr.Dataframe(label="BESS Throughput - Lowest 5 by Discharged Energy")

        with gr.Row():
            df2 = gr.Dataframe(label="BESS Throughput - All days")

        with gr.Row():
            csv_download = gr.File(label="Download 'BESS Throughput - All days' as CSV")

        with gr.Row():
            html_download = gr.File(
                label="Display download as html (2 plots and 5 Lowest table)"
            )

        file_input.change(
            fn=process,
            inputs=file_input,
            outputs=[gaps_df, plot1, plot2, df1, df2, csv_download, html_download],
        )

    demo.launch()


if __name__ == "__main__":
    main()
