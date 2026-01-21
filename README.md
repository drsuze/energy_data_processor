# energy_data_processor
This repository includes the package named 'energizer' which generates daily energy statistics and related visuals by aggregating time series power data, including via an app that can be launched locally in your browser.

### How to install and use the latest version of the energizer package available in TestPyPi
1. Make sure you have Python3.12 installed
2. In your terminal, create and activate a new environment using Python3.12
```bash
# macOS
python3.12 -m venv energize_venv
source energize_venv/bin/activate  
# OR for Windows + conda users
conda create -n energize_venv python=3.12
conda activate energize_venv
```
If you have trouble getting through these first two steps, consult the detailed setups instructions here: https://github.com/drsuze/energy_data_processor/blob/main/docs/setup.md

3. Install the latest available 'energizer' package with the following command:
```bash
pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple \
  energize
```
4. To launch the app, enter the following terminal command:
```bash
python -m energize.throughput_calculator_app
```

### Using the App
1. The resulting terminal output should tell you that the app is running somewhere like http://127.0.0.1:7860; open that URL in your browser

2. The app indicates you where you upload your zip-file, which contains the 1 or more parquet files** that you would like to process. Once uploaded, the processing will start automatically.

3. With the sample dataset this was originally built from, the processing may take around 1 minute. Once complete, you should see two heatmaps and two tables displaying energy data.

**   Note: 
The particular formatting required of the input parquet files is bespoke to certain power system outputs, and is not described here for confidentiality reasons. You can email the author with questions.

