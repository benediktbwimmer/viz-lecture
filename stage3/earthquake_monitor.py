import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Cache setup
CACHE_FILE = Path("earthquake_cache.pkl")

def fetch_earthquake_response(start_time: datetime, end_time: datetime):
    start_time_str = start_time.strftime('%Y-%m-%dT%H:%M:%S')
    end_time_str = end_time.strftime('%Y-%m-%dT%H:%M:%S')
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={start_time_str}&endtime={end_time_str}"
    return requests.get(url)

@st.cache_data(ttl=3600)  # Cache API calls for 1 hour
def fetch_earthquake_json(start_time: datetime, end_time: datetime):
    response = fetch_earthquake_response(start_time, end_time)
    if response.status_code != 200:
        st.error(f"API Error (Status {response.status_code}): {response.text}")
        return {"features": []}
    return response.json()

def construct_earthquake_df(data_json):
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

def update_cache(start_time, end_time):
    """Update the persistent cache with new data in both directions"""
    # Load existing cache if it exists
    if CACHE_FILE.exists():
        cached_df = pd.read_pickle(CACHE_FILE)
    else:
        cached_df = pd.DataFrame(columns=["timestamp", "magnitude"])
    
    updated_df = cached_df.copy()
    
    # Check for earlier data
    if not cached_df.empty:
        earliest_cached = cached_df["timestamp"].min().tz_localize(timezone.utc)
        latest_cached = cached_df["timestamp"].max().tz_localize(timezone.utc)
    else:
        earliest_cached = end_time
        latest_cached = start_time
    
    # Fetch earlier data if needed
    if start_time < earliest_cached:
        with st.spinner(f"Fetching earlier data from {start_time} to {earliest_cached}..."):
            earlier_json = fetch_earthquake_json(start_time, earliest_cached)
            earlier_df = construct_earthquake_df(earlier_json)
            updated_df = pd.concat([earlier_df, updated_df])
    
    # Fetch newer data if needed
    if end_time > latest_cached:
        with st.spinner(f"Fetching newer data from {latest_cached} to {end_time}..."):
            newer_json = fetch_earthquake_json(latest_cached, end_time)
            newer_df = construct_earthquake_df(newer_json)
            updated_df = pd.concat([updated_df, newer_df])
    
    # If we fetched new data, update the cache
    if not updated_df.equals(cached_df):
        updated_df = updated_df.drop_duplicates(subset=["timestamp"])
        updated_df = updated_df.sort_values("timestamp")
        updated_df.to_pickle(CACHE_FILE)
    
    return updated_df

def create_plotly_chart(df):
    """Create an interactive Plotly chart with enhanced zooming"""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No earthquake data available",
                         xref="paper", yref="paper",
                         x=0.5, y=0.5, showarrow=False)
        return fig
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["magnitude"],
        mode='lines+markers',
        name='Magnitude',
        line=dict(color='blue'),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="Earthquake Magnitudes",
        xaxis_title="Time (UTC)",
        yaxis_title="Magnitude",
        template="plotly_white",
        hovermode="x unified",
        dragmode="zoom",  # Default to zoom mode
        xaxis=dict(
            rangeslider=dict(visible=True),  # Add a range slider for x-axis
            type="date"
        ),
        # Enable independent axis zooming
        uirevision='true',  # Preserve UI state
    )
    
    # Configure buttons for different zoom behaviors
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=list([
                    dict(args=[{"dragmode": "zoom"}], label="Zoom", method="relayout"),
                    dict(args=[{"dragmode": "pan"}], label="Pan", method="relayout"),
                    dict(args=[{"xaxis.autorange": True, "yaxis.autorange": True}], 
                         label="Reset", method="relayout")
                ]),
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.11,
                xanchor="left",
                y=1.1,
                yanchor="top"
            ),
        ]
    )
    
    return fig

def main():
    st.title("Interactive Earthquake Monitor")
    
    # Sidebar controls
    st.sidebar.header("Settings")
    days_back = st.sidebar.slider("Days of history", 1, 30, 1)
    min_magnitude = st.sidebar.slider("Minimum Magnitude", 0.0, 10.0, 0.0)
    
    # Calculate time range
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=days_back)
    
    # Update and get cached data
    df = update_cache(start_time, end_time)
    
    # Ensure the timestamp column is timezone-aware
    if not df.empty and df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize(timezone.utc)
    
    # Filter data
    filtered_df = df[df["magnitude"] >= min_magnitude].copy()
    filtered_df = filtered_df[filtered_df["timestamp"] >= start_time]
    
    # Display metrics
    col1, col2 = st.columns(2)
    col1.metric("Total Events", len(filtered_df))
    col2.metric("Max Magnitude", f"{filtered_df['magnitude'].max():.1f}" if not filtered_df.empty else "N/A")
    
    # Create and display interactive chart
    fig = create_plotly_chart(filtered_df)
    st.plotly_chart(fig, use_container_width=True)
    
    # Add refresh button and cache info
    if st.button("Force Refresh"):
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()  # Delete cache to force full refresh
        st.rerun()
    
    st.caption(f"Cache last updated: {datetime.fromtimestamp(CACHE_FILE.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S') if CACHE_FILE.exists() else 'No cache yet'}")
    

if __name__ == "__main__":
    main()