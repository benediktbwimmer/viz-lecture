import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta, timezone
from pathlib import Path

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

CACHE_FILE = Path("stock_cache.pkl")  # single on‑disk cache for all symbols


# -----------------------------------------------------------------------------
# Data acquisition helpers
# -----------------------------------------------------------------------------

def fetch_stock_data(symbol: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
    """Download historical OHLC data from Yahoo Finance and return timestamp / price."""
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(start=start_time, end=end_time)
        if df.empty:
            return pd.DataFrame(columns=["timestamp", "price", "symbol"])

        df = (
            df[["Close"]]
            .reset_index()
            .rename(columns={"Date": "timestamp", "Close": "price"})
            .assign(symbol=symbol)
        )
        return df
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame(columns=["timestamp", "price", "symbol"])


# -----------------------------------------------------------------------------
# Cache management (fixed to preserve data for *all* symbols)
# -----------------------------------------------------------------------------

def update_cache(symbol: str, start_time: datetime, end_time: datetime) -> pd.DataFrame:
    """Ensure the cache contains data for *symbol* covering [start_time, end_time].

    Returns the up‑to‑date DataFrame slice **just for that symbol**, ready for plotting.
    """
    # 1️⃣ Load the *entire* cache (may be empty)
    if CACHE_FILE.exists():
        full_cache = pd.read_pickle(CACHE_FILE)
    else:
        full_cache = pd.DataFrame(columns=["timestamp", "price", "symbol"])

    # 2️⃣ Work on the slice for the requested ticker
    symbol_df = full_cache[full_cache["symbol"] == symbol].copy()

    # Identify the cached window (if any)
    if symbol_df.empty:
        earliest_cached = end_time
        latest_cached = start_time
    else:
        earliest_cached = symbol_df["timestamp"].min()
        latest_cached = symbol_df["timestamp"].max()
        # Ensure tz‑aware
        if earliest_cached.tz is None:
            earliest_cached = earliest_cached.tz_localize(timezone.utc)
        if latest_cached.tz is None:
            latest_cached = latest_cached.tz_localize(timezone.utc)

    # 3️⃣ Fetch any missing data *before* the cached range
    if start_time < earliest_cached:
        with st.spinner(f"Fetching earlier {symbol} data …"):
            earlier = fetch_stock_data(symbol, start_time, earliest_cached)
            symbol_df = pd.concat([earlier, symbol_df]) if not earlier.empty else symbol_df

    # 4️⃣ Fetch any missing data *after* the cached range
    if end_time > latest_cached:
        with st.spinner(f"Fetching newer {symbol} data …"):
            newer = fetch_stock_data(symbol, latest_cached, end_time)
            symbol_df = pd.concat([symbol_df, newer]) if not newer.empty else symbol_df

    # 5️⃣ Normalise, dedupe, sort
    if not symbol_df.empty:
        symbol_df = (
            symbol_df.drop_duplicates(subset=["timestamp", "symbol"])
            .sort_values("timestamp")
            .reset_index(drop=True)
        )

    # 6️⃣ Persist back **whole** cache if symbol slice changed
    if not symbol_df.equals(full_cache[full_cache["symbol"] == symbol]):
        other = full_cache[full_cache["symbol"] != symbol]
        full_cache_updated = pd.concat([other, symbol_df], ignore_index=True)
        full_cache_updated.to_pickle(CACHE_FILE)

    return symbol_df


# -----------------------------------------------------------------------------
# Plotly chart helper
# -----------------------------------------------------------------------------

def create_plotly_chart(df: pd.DataFrame, symbol: str) -> go.Figure:
    """Return an interactive time‑series chart for Streamlit display."""
    fig = go.Figure()

    if df.empty:
        fig.add_annotation(
            text=f"No data for {symbol}", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
        )
        return fig

    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["price"],
            mode="lines+markers",
            name=f"{symbol} Close",
            line=dict(width=2),
            marker=dict(size=6),
        )
    )

    fig.update_layout(
        title=f"{symbol} price history",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        template="plotly_white",
        hovermode="x unified",
        dragmode="zoom",
        xaxis=dict(rangeslider=dict(visible=True), type="date"),
        uirevision="true",
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                x=0.11,
                xanchor="left",
                y=1.1,
                yanchor="top",
                showactive=True,
                pad={"r": 10, "t": 10},
                buttons=[
                    dict(args=[{"dragmode": "zoom"}], label="Zoom", method="relayout"),
                    dict(args=[{"dragmode": "pan"}], label="Pan", method="relayout"),
                    dict(args=[{"xaxis.autorange": True, "yaxis.autorange": True}], label="Reset", method="relayout"),
                ],
            )
        ],
    )

    return fig


# -----------------------------------------------------------------------------
# Streamlit app entry point
# -----------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="Interactive Stock Monitor", layout="wide")
    st.title("Interactive Stock Monitor")

    # ---- Sidebar controls ----
    st.sidebar.header("Settings")
    symbol = st.sidebar.text_input("Stock symbol (e.g. AAPL, MSFT)", "AAPL").upper().strip()
    days_back = st.sidebar.slider("Days of history", 1, 365 * 10, 30)

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=days_back)

    # ---- Fetch (and cache) data ----
    df = update_cache(symbol, start_time, end_time)

    # Ensure tz‑aware for Pandas datetime operations
    if not df.empty and df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize(timezone.utc)

    # Restrict display to requested period
    df_display = df[df["timestamp"] >= start_time].copy()

    # ---- Metrics ----
    col1, col2 = st.columns(2)
    col1.metric("Data points", len(df_display))
    latest_price = f"${df_display['price'].iloc[-1]:.2f}" if not df_display.empty else "N/A"
    col2.metric("Latest close", latest_price)

    # ---- Chart ----
    st.plotly_chart(create_plotly_chart(df_display, symbol), use_container_width=True)

    # ---- Refresh / diagnostics ----
    if st.button("Force refresh"):
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()  # blow away cache
        st.experimental_rerun()

    cache_state = (
        datetime.fromtimestamp(CACHE_FILE.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        if CACHE_FILE.exists()
        else "(none)"
    )
    st.caption(f"Cache last updated: {cache_state}")


if __name__ == "__main__":
    main()
