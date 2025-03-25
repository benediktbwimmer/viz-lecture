## Data Visualization Lecture Demonstration Repository

This repository contains example code for different stages of data visualization with python, progressing in complexity.

### Stage 1

Contains a jupyter notebook showcasing:

- A global annual temperature averages plot loaded from a .csv file

### Stage 2

Contains a jupyter notebook showcasing:

- A cartopy map with a reanalysis of global residential elemental carbon PM2.5 values for the month December 2022

### Stage 3

Contains 2 streamlit dashboards which use plotly for an interactive visualization:

- An interactive Earthquake Magnitude Monitor app

- An interactive Stockprize visualization app


### Installation Instructions

You will need a recent version of Python installed (3.12 preferably). It is highly recommended to set up a virtual environment in the repo directory with:

```sh
python3.12 -m venv .venv
```

Then, activate the virtual environment with:

```
source .venv/bin/activate
```

Next, install the required packages

```
pip install -r requirements.txt
```

A recommended alternative to pip is uv, use:

```
uv pip install -r requirements.txt
```


Now you can run the jupyter notebook server to view the notebooks, or simply use the VSCode extension:

```
cd stage1
jupyter notebook
```


To run the Streamlit apps e.g.:

```
streamlit run earthquake_monitor.py
```