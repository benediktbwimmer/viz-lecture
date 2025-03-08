import pandas as pd
import matplotlib.pyplot as plt
import os


def load_temperature_df(filepath):
    # Load CSV, skip header rows and metadata
    df = pd.read_csv(filepath, skiprows=1)
    # Convert 'Year' to datetime and select annual mean anomaly
    df["Year"] = pd.to_datetime(df["Year"], format="%Y")
    df["Annual_Mean"] = pd.to_numeric(df["J-D"], errors="coerce")
    return df

# Plot 1: Temperature Anomalies from CSV
def plot_temperature_anomalies(df):

    x = df["Year"]
    y = df["Annual_Mean"]

    plt.figure(figsize=(10, 5))
    plt.plot(x, y, color="red", label="Annual Mean Anomaly")
    plt.title("Global Temperature Anomalies (1880-2024)")
    plt.xlabel("Year")
    plt.ylabel("Temperature Anomaly (°C)")
    plt.grid(True)
    plt.legend()
    
    return plt

def main():
    # Load temperature data from CSV
    filepath = os.path.join("..", "data", "temperatures.csv")
    df = load_temperature_df(filepath)
    
    # Plot temperature anomalies
    plot = plot_temperature_anomalies(df)
    
    # Save the plot
    output_path = os.path.join("plots", "temperature_anomalies.png")

    plot.savefig(output_path)
    print(f"Temperature plot saved to '{output_path}'")

if __name__ == "__main__":
    main()