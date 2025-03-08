import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Cache setup
CACHE_FILE = Path("stock_cache.pkl")

def fetch_stock_data(symbol: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
    """Fetch stock data from yfinance"""
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(start=start_time, end=end_time)
        if df.empty:
            return pd.DataFrame(columns=["timestamp", "price"])
        # Rename and select relevant columns
        df = df[['Close']].reset_index().rename(columns={'Date': 'timestamp', 'Close': 'price'})
        return df
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {str(e)}")
        return pd.DataFrame(columns=["timestamp", "price"])

def update_cache(symbol: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
    """Update the persistent cache with new stock data in both directions"""
    # Load existing cache if it exists
    if CACHE_FILE.exists():
        cached_df = pd.read_pickle(CACHE_FILE)
        # Filter for the current symbol if cache contains multiple symbols
        if 'symbol' in cached_df.columns:
            cached_df = cached_df[cached_df['symbol'] == symbol]
    else:
        cached_df = pd.DataFrame(columns=["timestamp", "price", "symbol"])
    
    updated_df = cached_df.copy()
    
    # Add symbol column if not present
    if 'symbol' not in updated_df.columns:
        updated_df['symbol'] = symbol
    
    # Check for earlier and later data
    if not cached_df.empty:
        earliest_cached = cached_df["timestamp"].min()
        if earliest_cached.tz is None:
            earliest_cached = earliest_cached.tz_localize(timezone.utc)
        latest_cached = cached_df["timestamp"].max()
        if latest_cached.tz is None:
            latest_cached = latest_cached.tz_localize(timezone.utc)
    else:
        earliest_cached = end_time
        latest_cached = start_time
    
    # Fetch earlier data if needed
    if start_time < earliest_cached:
        with st.spinner(f"Fetching earlier data for {symbol} from {start_time} to {earliest_cached}..."):
            earlier_df = fetch_stock_data(symbol, start_time, earliest_cached)
            if not earlier_df.empty:
                earlier_df['symbol'] = symbol
                updated_df = pd.concat([earlier_df, updated_df])
    
    # Fetch newer data if needed
    if end_time > latest_cached:
        with st.spinner(f"Fetching newer data for {symbol} from {latest_cached} to {end_time}..."):
            newer_df = fetch_stock_data(symbol, latest_cached, end_time)
            if not newer_df.empty:
                newer_df['symbol'] = symbol
                updated_df = pd.concat([updated_df, newer_df])
    
    # If we fetched new data, update the cache
    if not updated_df.equals(cached_df):
        updated_df = updated_df.drop_duplicates(subset=["timestamp"])
        updated_df = updated_df.sort_values("timestamp")
        updated_df.to_pickle(CACHE_FILE)
    
    return updated_df

def create_plotly_chart(df: pd.DataFrame, symbol: str) -> go.Figure:
    """Create an interactive Plotly chart with enhanced zooming"""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text=f"No stock data available for {symbol}",
                         xref="paper", yref="paper",
                         x=0.5, y=0.5, showarrow=False)
        return fig
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["price"],
        mode='lines+markers',
        name=f'{symbol} Price',
        line=dict(color='blue'),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title=f"Stock Price for {symbol}",
        xaxis_title="Time",
        yaxis_title="Price (USD)",
        template="plotly_white",
        hovermode="x unified",
        dragmode="zoom",
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="date"
        ),
        uirevision='true',
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
    st.title("Interactive Stock Monitor")
    
    # Sidebar controls
    st.sidebar.header("Settings")
    symbol = st.sidebar.text_input("Stock Symbol (e.g., AAPL, MSFT)", "AAPL").upper()
    days_back = st.sidebar.slider("Days of history", 1, 365*10, 30)  # Extended range for stocks
    
    # Calculate time range
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=days_back)
    
    # Update and get cached data
    df = update_cache(symbol, start_time, end_time)
    
    # Ensure the timestamp column is timezone-aware
    if not df.empty and df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize(timezone.utc)
    
    # Filter data for display
    filtered_df = df[df["timestamp"] >= start_time].copy()
    
    # Display metrics
    col1, col2 = st.columns(2)
    col1.metric("Total Data Points", len(filtered_df))
    col2.metric("Latest Price", f"${filtered_df['price'].iloc[-1]:.2f}" if not filtered_df.empty else "N/A")
    
    # Create and display interactive chart
    fig = create_plotly_chart(filtered_df, symbol)
    st.plotly_chart(fig, use_container_width=True)
    
    # Add refresh button and cache info
    if st.button("Force Refresh"):
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()  # Delete cache to force full refresh
        st.rerun()
    
    st.caption(f"Cache last updated: {datetime.fromtimestamp(CACHE_FILE.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S') if CACHE_FILE.exists() else 'No cache yet'}")
    

if __name__ == "__main__":
    main()