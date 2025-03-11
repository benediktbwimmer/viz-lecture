import pandas as pd


def load_temperature_df(filepath):
    # Load CSV, skip header rows and metadata
    df = pd.read_csv(filepath, skiprows=1)
    # Convert 'Year' to datetime and select annual mean anomaly
    df["Year"] = pd.to_datetime(df["Year"], format="%Y")
    df["Annual_Mean"] = pd.to_numeric(df["J-D"], errors="coerce")
    return df


