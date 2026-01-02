import MetaTrader5 as mt5
import pandas as pd
import streamlit as st
import time
from modular_strategy_bot import apply_indicators, generate_signal

# Set this as the first Streamlit command
st.set_page_config(page_title="Forex Signal Bot", layout="wide")

# Get symbols
def get_available_symbols():
    symbols = mt5.symbols_get()
    return [s.name for s in symbols if s.visible]

# Initialize MT5
if not mt5.initialize():
    st.error(f"MT5 initialization failed: {mt5.last_error()}")
else:
    st.success("MT5 initialized successfully.")
    account_info = mt5.account_info()
    if account_info:
        st.info(f"Logged in: {account_info.name} | Leverage: {account_info.leverage}")
    else:
        st.warning("Unable to fetch account info.")

# User selects symbol
available_symbols = get_available_symbols()
selected_symbol = st.selectbox("Select Symbol to Analyze", available_symbols)

TIMEFRAME = mt5.TIMEFRAME_M5
NUM_CANDLES = 300
SIGNAL_CONFIDENCE_THRESHOLD = 2

# Data Fetch
def get_data(symbol=selected_symbol, timeframe=TIMEFRAME, n=NUM_CANDLES):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n)
    if rates is None or len(rates) == 0:
        st.error("No data returned from MT5.")
        return pd.DataFrame()
    df = pd.DataFrame(rates)
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'], unit='s')
    else:
        st.warning("'time' column missing from MT5 data.")
        return pd.DataFrame()
    return df

# UI
st.title("AI-Driven Forex Signal Dashboard")
st.markdown(f"**Symbol:** `{selected_symbol}`")

signal_placeholder = st.empty()
chart_placeholder = st.empty()

df = get_data()
if not df.empty:
    df = apply_indicators(df)
    signal, reasons = generate_signal(df)

    # Show chart
    columns_to_plot = ['close', 'BBL_20_2.0', 'BBU_20_2.0']
    plot_columns = [col for col in columns_to_plot if col in df.columns]
    if plot_columns:
        chart_placeholder.line_chart(df[plot_columns].tail(100))
    else:
        chart_placeholder.warning("Nothing to plot. Check available columns.")

    # Show signal
    signal_placeholder.subheader(f"Current Signal: {signal}")
    st.text("Reasons:\n" + "\n".join(reasons))
else:
    st.warning("No chart available due to missing data.")

# Run loop (streamlit rerun handled by frontend refresh)
mt5.shutdown()
