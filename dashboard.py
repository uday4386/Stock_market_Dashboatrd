import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, date
import time

# Add a colored header using HTML/CSS
st.markdown("""
    <div style='background-color:#1f77b4;padding:16px;border-radius:8px;margin-bottom:16px;'>
        <h1 style='color:#fff;margin:0;'>📈 Real-Time Stock Market Dashboard</h1>
    </div>
""", unsafe_allow_html=True)

default_tickers = ["AAPL", "MSFT", "TSLA", "AMZN", "GOOGL"]

st.sidebar.header("Stock Selection & Settings")

all_tickers = default_tickers + ["META", "NVDA", "NFLX", "BABA", "JPM", "V", "DIS"]
selected_ticker = st.sidebar.selectbox(
    "Select stock ticker", options=sorted(set(all_tickers)), index=0, help="Search or select a stock."
)

custom_ticker = st.sidebar.text_input("Or enter custom ticker (overrides selection)")
if custom_ticker:
    selected_ticker = custom_ticker.strip().upper()

start_date = st.sidebar.date_input("Start date", value=date.today().replace(year=date.today().year-1))
end_date = st.sidebar.date_input("End date", value=date.today())

st.sidebar.markdown("**Technical Indicators**")
show_sma = st.sidebar.checkbox("Show SMA (20)", value=True)
show_ema = st.sidebar.checkbox("Show EMA (20)", value=False)

refresh_rate = st.sidebar.slider("Auto-refresh (seconds)", min_value=0, max_value=300, value=0, step=5, help="Set to 0 to disable auto-refresh.")

if refresh_rate > 0:
    st.experimental_rerun()
    time.sleep(refresh_rate)

# Add a colored subheader for live details
st.markdown(f"""
    <div style='background-color:#e0e7ef;padding:10px 16px;border-radius:6px;margin-bottom:10px;'>
        <h2 style='color:#1f77b4;margin:0;'>Live Stock Details: {selected_ticker}</h2>
    </div>
""", unsafe_allow_html=True)

try:
    stock = yf.Ticker(selected_ticker)
    fast_info = getattr(stock, 'fast_info', None)
    price = fast_info.get("lastPrice") if fast_info else None
    change = fast_info.get("regularMarketChange") if fast_info else None
    percent = fast_info.get("regularMarketChangePercent") if fast_info else None
    name = selected_ticker
    try:
        name = stock.info.get("shortName", selected_ticker)
    except Exception:
        pass
    st.metric(label=f"{name} ({selected_ticker})", value=f"${price}" if price else "N/A", delta=f"{change:.2f} ({percent:.2f}%)" if change and percent else "N/A")
except Exception as e:
    st.error(f"{selected_ticker}: Error loading data")

data = None
try:
    data = yf.download(selected_ticker, start=start_date, end=end_date, interval="1d", auto_adjust=True)
    if data.empty:
        st.warning(f"No data found for {selected_ticker}.")
    else:
        if show_sma:
            data['SMA20'] = data['Close'].rolling(window=20).mean()
        if show_ema:
            data['EMA20'] = data['Close'].ewm(span=20, adjust=False).mean()

        # Always show the graph on the main page
        st.write(f"#### {selected_ticker} Stock Price Chart")
        if 'Close' in data:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close Price', line=dict(color='#1f77b4', width=2)))
            if show_sma and 'SMA20' in data:
                fig.add_trace(go.Scatter(x=data.index, y=data['SMA20'], mode='lines', name='SMA 20', line=dict(color='orange', width=1)))
            if show_ema and 'EMA20' in data:
                fig.add_trace(go.Scatter(x=data.index, y=data['EMA20'], mode='lines', name='EMA 20', line=dict(color='green', width=1)))
            fig.update_layout(title=f"{selected_ticker} Price Chart", xaxis_title="Date", yaxis_title="Price (USD)", legend=dict(orientation="h"), plot_bgcolor='#f5f7fa', paper_bgcolor='#f5f7fa')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No closing price data available to plot.")

        # Tabs for summary and table
        tab1, tab2 = st.tabs(["Summary", "Table"])
        with tab1:
            st.write("**Key Indicators (last 3 days):**")
            st.write(data.tail(3)[['Open', 'High', 'Low', 'Close', 'Volume']])
            st.write("**Company Info:**")
            try:
                st.write(stock.info)
            except Exception:
                st.write("No company info available.")
        with tab2:
            st.dataframe(data.tail(60))
            csv = data.to_csv().encode('utf-8')
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name=f'{selected_ticker}_data.csv',
                mime='text/csv',
            )
except Exception as e:
    st.error(f"Error fetching data for {selected_ticker}: {e}")

st.caption("Data provided by Yahoo Finance via yfinance.") 