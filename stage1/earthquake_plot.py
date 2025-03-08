import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, timezone
import os


def fetch_earthquake_response(start_time: datetime, end_time: datetime):
    # Format the timestamps correctly for USGS API using ISO format
    # USGS expects ISO 8601 format without spaces
    start_time_str = start_time.strftime('%Y-%m-%dT%H:%M:%S')
    end_time_str = end_time.strftime('%Y-%m-%dT%H:%M:%S')
    
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={start_time_str}&endtime={end_time_str}"
    response = requests.get(url)

    return response


def fetch_earthquake_json(start_time: datetime, end_time: datetime):
    """
    Fetch earthquake data and return JSON directly
    """
    response = fetch_earthquake_response(start_time, end_time)
    
    if response.status_code != 200:
        print(f"API Error (Status {response.status_code}):")
        print(response.text)
        return {"features": []}
    
    return response.json()


def construct_earthquake_df(data_json):
    """
    Construct DataFrame from earthquake JSON data
    """
    if not data_json or "features" not in data_json:
        return pd.DataFrame(columns=["timestamp", "magnitude"])
    
    events = [(event["properties"]["time"], event["properties"]["mag"]) 
             for event in data_json["features"] 
             if event["properties"]["mag"] is not None]
    
    df = pd.DataFrame(events, columns=["timestamp", "magnitude"])
    
    if len(df) > 0:
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df = df.sort_values("timestamp")
    
    return df


# Plot 2: Live Earthquake Magnitudes from USGS API
def plot_earthquake_magnitudes(df):
    
    plt.figure(figsize=(12, 5))
    
    if len(df) == 0:
        plt.text(0.5, 0.5, "No earthquake data available", 
                horizontalalignment='center', verticalalignment='center',
                transform=plt.gca().transAxes, fontsize=14)
    else:
        plt.plot(df["timestamp"], df["magnitude"], "bo-")
    
    plt.title("Earthquake Magnitudes (Last 24 Hours)")
    plt.xlabel("Time (UTC)")
    plt.ylabel("Magnitude")
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return plt


def main():
    # Fetch earthquake data from USGS API
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=1)
    
    # Use the JSON fetching function
    data_json = fetch_earthquake_json(start_time, end_time)
    
    if not data_json or "features" not in data_json:
        print("Failed to fetch valid earthquake data")
        return
    
    # Construct earthquake dataframe
    df = construct_earthquake_df(data_json)
    
    # Plot earthquake magnitudes
    plot = plot_earthquake_magnitudes(df)
    
    # Save the plot
    os.makedirs("plots", exist_ok=True)  # Create plots directory if it doesn't exist
    output_path = os.path.join("plots", "earthquake_magnitudes.png")
    plot.savefig(output_path)
    print(f"Earthquake plot saved to '{output_path}'")

if __name__ == "__main__":
    main()