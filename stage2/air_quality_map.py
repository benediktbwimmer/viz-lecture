import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import xarray as xr
import numpy as np
import pandas as pd
import colorcet as cc
import os

# Function to load air quality data from CAMS NetCDF or cached JSON
def load_air_quality_data():
    # Paths for NetCDF and cached JSON
    data_dir = os.path.join("..", "data")
    netcdf_filename = "cams.eaq.vra.ENSa.ecres.l0.2022-12.nc"
    netcdf_path = os.path.join(data_dir, netcdf_filename)
    json_path = os.path.join(data_dir, "pm25_data.json")
    
    # Create data directory if it doesn’t exist
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Check if cached JSON exists
    if os.path.exists(json_path):
        print("Loading cached DataFrame from", json_path)
        return pd.read_json(json_path)
    
    print("Processing NetCDF file (this may take a moment)...")
    # Load the dataset
    ds = xr.open_dataset(netcdf_path)
    
    # Verify ecres attributes (residential EC within PM2.5)
    print("ecres attributes:", ds["ecres"].attrs)
    
    # Extract residential EC within PM2.5 (ecres)
    pm25 = ds["ecres"]  # Replace with 'pm2_5' or 'concpm25' for total PM2.5
    
    # Filter for Western Europe (-10 to 25 lon, 35 to 60 lat)
    pm25_we = pm25.sel(
        lon=slice(-10, 25),
        lat=slice(35, 60)
    )
    
    # Average over time (December 2022)
    pm25_mean = pm25_we.mean(dim="time")
    
    # Extract coordinates
    lat_we = pm25_mean["lat"]
    lon_we = pm25_mean["lon"]
    
    # Convert to DataFrame
    pm25_values = pm25_mean.values.flatten()
    lat_values = np.repeat(lat_we.values, len(lon_we)).flatten()
    lon_values = np.tile(lon_we.values, len(lat_we)).flatten()
    
    df = pd.DataFrame({
        "lat": lat_values,
        "lon": lon_values,
        "pm25": pm25_values
    })
    
    # Drop NaN values
    df = df.dropna()
    
    if df.empty:
        print("Warning: No valid data after filtering.")
    
    # Cache the DataFrame as JSON
    df.to_json(json_path, orient="records")
    print("Cached DataFrame to", json_path)
    return df

# Function to plot the air quality map
def plot_air_quality_map(df):
    if df.empty:
        print("No data to plot.")
        return

    projection = ccrs.PlateCarree()
    extent = [-10, 25, 35, 60]

    fig = plt.figure(figsize=(7, 5))
    ax = plt.axes(projection=projection)
    ax.set_extent(extent, crs=ccrs.PlateCarree())

    # Add map features with light gray borders and coastlines
    ax.add_feature(cfeature.LAND, facecolor="lightgray")
    ax.add_feature(cfeature.OCEAN, facecolor="lightblue")
    ax.add_feature(cfeature.BORDERS, edgecolor="gray", linewidth=0.5)
    ax.add_feature(cfeature.COASTLINE, edgecolor="gray", linewidth=0.8)

    # Scatter plot
    scatter = ax.scatter(
        df["lon"], df["lat"],
        c=df["pm25"],
        cmap=cc.cm.fire,
        s=20,
        alpha=0.6,
        transform=ccrs.PlateCarree()
    )

    # Add colorbar
    plt.colorbar(scatter, ax=ax, label="Residential EC in PM2.5 (µg/m³)", shrink=0.7)
    
    # Set title
    ax.set_title("Residential EC in PM2.5 - Western Europe (Dec 2022)")
    
    # Remove axis labels
    ax.set_xticks([])
    ax.set_yticks([])
    
    plt.tight_layout()
    
    return plt

def main():

    os.makedirs("plots", exist_ok=True)  # Create plots directory if it doesn't exist
    output_path = os.path.join("plots", "air_quality_map.png")

    df = load_air_quality_data()
    plot = plot_air_quality_map(df)

    plot.savefig(output_path)
    print(f"Air quality map saved to '{output_path}'")

if __name__ == "__main__":
    main()


