import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import yfinance as yf
import google.generativeai as genai
import re 
# Load ticker mappings from JSON
with open(r"D:\hackabull\ticker.json", "r") as f:
    company_data = json.load(f)

def normalize_title(name):
    name = name.lower()
    name = re.sub(r'[^a-z0-9\s]', '', name)  # remove punctuation
    name = re.sub(r'\b(inc|corp|co|ltd|plc|sa|nv|se|llc|lp|group|holdings|international|limited|technologies|solutions|systems|enterprises?)\b', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

# Normalize and map company names to tickers
name_to_ticker = {}
for item in company_data.values():
    title = normalize_title(item['title'])
    ticker = item['ticker'].upper()
    name_to_ticker[title] = ticker
    name_to_ticker[ticker] = ticker

# Setup Gemini
genai.configure(api_key="AIzaSyA7YdCpR_0AIerXm7L0p-lte9YRTNcSz10")
model = genai.GenerativeModel("gemini-2.0-flash")

# Helper to find ticker by company name
def get_ticker_from_name(input_text):
    input_text_norm = normalize_title(input_text)
    ticker = name_to_ticker.get(input_text.upper()) or name_to_ticker.get(input_text_norm)

    if not ticker:
        raise ValueError(f"Could not find ticker for input: '{input_text}'. Please try a valid company name or ticker.")

    return ticker


# Analysis Functions
def get_stock_price(ticker):
    return yf.Ticker(ticker).history(period='1y').iloc[-1].Close

def calculate_SMA(ticker, window):
    return yf.Ticker(ticker).history(period='1y').Close.rolling(window=window).mean().iloc[-1]

def calculate_EMA(ticker, window):
    return yf.Ticker(ticker).history(period='1y').Close.ewm(span=window, adjust=False).mean().iloc[-1]

def calculate_RSI(ticker):
    close = yf.Ticker(ticker).history(period='1y').Close
    delta = close.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=14-1, adjust=False).mean()
    ema_down = down.ewm(com=14-1, adjust=False).mean()
    rs = ema_up / ema_down
    return 100 - (100 / (1 + rs)).iloc[-1]

def calculate_MACD(ticker):
    close = yf.Ticker(ticker).history(period='1y').Close
    short_ema = close.ewm(span=12, adjust=False).mean()
    long_ema = close.ewm(span=26, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    return macd.iloc[-1], signal.iloc[-1], hist.iloc[-1]

def plot_stock_price(ticker):
    data = yf.Ticker(ticker).history(period='1y')
    plt.figure(figsize=(10, 5))
    plt.plot(data.index, data.Close)
    plt.title(f'{ticker} Stock Price Over Last Year')
    plt.xlabel('Date')
    plt.ylabel('Stock Price ($)')
    plt.grid(True)
    plt.savefig('stock.png')
    plt.close()

available_functions = {
    'get_stock_price': get_stock_price,
    'calculate_SMA': calculate_SMA,
    'calculate_EMA': calculate_EMA,
    'calculate_RSI': calculate_RSI,
    'calculate_MACD': calculate_MACD,
    'plot_stock_price': plot_stock_price
}

# Streamlit UI
st.title('📈 Gemini Stock Analysis Assistant')
company_input = st.text_input("Enter company name or stock ticker (e.g., Apple or AAPL):").upper()
window = st.slider("Select window size for SMA/EMA:", 5, 50, 14)

if company_input:
    try:
        ticker = get_ticker_from_name(company_input)
        st.subheader(f"Fetching data for {ticker}...")

        # Data Fetch
        price = round(get_stock_price(ticker), 2)
        sma = round(calculate_SMA(ticker, window), 2)
        ema = round(calculate_EMA(ticker, window), 2)
        rsi = round(calculate_RSI(ticker), 2)
        macd_val, signal_line, macd_hist = [round(v, 2) for v in calculate_MACD(ticker)]
        plot_stock_price(ticker)

        # Display Data
        st.write(f"💵 Latest Price: ${price}")
        st.write(f"📊 {window}-Day SMA: ${sma}")
        st.write(f"📈 {window}-Day EMA: ${ema}")
        st.write(f"📉 RSI: {rsi}")
        st.write(f"📐 MACD: {macd_val} | Signal: {signal_line} | Histogram: {macd_hist}")
        st.image("stock.png", caption=f"{ticker} Closing Price - Last 1 Year")

        # Prepare Gemini Prompt
        gemini_prompt = f"""
You are a financial assistant that helps users analyze stock market data.

Given the following stock information for the ticker {ticker}, generate an easy-to-understand analysis:

- Latest closing price: ${price}
- {window}-day Simple Moving Average (SMA): ${sma}
- {window}-day Exponential Moving Average (EMA): ${ema}
- Relative Strength Index (RSI): {rsi}
- MACD: {macd_val}
- Signal Line: {signal_line}
- MACD Histogram: {macd_hist}

Provide insights, explain what it means for investors, and suggest if the user should buy, hold, or sell.
"""

        # Run Gemini API
        response = model.generate_content(
            gemini_prompt,
            generation_config={"temperature": 0}
        )

        # Display Gemini Analysis
        st.subheader("📋 Gemini Analysis")
        st.write(response.text)

    except Exception as e:
        st.error(f"❌ Error: {e}")
