import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import re
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn
import base64
from io import BytesIO
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="FinCrack API", description="Financial analysis API for stock data")

# Setup Gemini
def setup_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY not found in environment variables.")
        return None
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    return model

# Initialize Gemini model
gemini_model = setup_gemini()

# Helper function to normalize company names
def normalize_title(name):
    name = name.lower()
    name = re.sub(r'[^a-z0-9\s]', '', name)  # remove punctuation
    name = re.sub(r'\b(inc|corp|co|ltd|plc|sa|nv|se|llc|lp|group|holdings|international|limited|technologies|solutions|systems|enterprises?)\b', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

# Load ticker data at startup
try:
    with open('ticker.json', "r") as f:
        company_data = json.load(f)
    
    # Normalize and map company names to tickers
    name_to_ticker = {}
    for item in company_data.values():
        title = normalize_title(item['title'])
        ticker = item['ticker'].upper()
        name_to_ticker[title] = ticker
        name_to_ticker[ticker] = ticker
except FileNotFoundError:
    company_data = {}
    name_to_ticker = {}
    print("Warning: ticker.json not found. API will start with empty ticker data.")
except json.JSONDecodeError:
    company_data = {}
    name_to_ticker = {}
    print("Warning: Invalid JSON in ticker.json. API will start with empty ticker data.")

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
    
    # Save to BytesIO object instead of file
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)
    
    # Convert to base64 string
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return img_str

# Function to prepare Gemini prompt
def prepare_gemini_prompt(ticker, price, sma, ema, rsi, macd_val, signal_line, macd_hist, window):
    return f"""
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

# API Endpoints
@app.get("/")
def read_root():
    return {"message": "Welcome to FinCrack API", "version": "1.0.0"}

@app.get("/ticker/{company_input}")
def get_ticker(company_input: str):
    try:
        ticker = get_ticker_from_name(company_input)
        return {"ticker": ticker}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/stock/{ticker}/analysis")
def stock_analysis(ticker: str, window: int = Query(14, ge=5, le=200)):
    try:
        # Fetch all data at once
        price = round(get_stock_price(ticker), 2)
        sma = round(calculate_SMA(ticker, window), 2)
        ema = round(calculate_EMA(ticker, window), 2)
        rsi = round(calculate_RSI(ticker), 2)
        macd_val, signal_line, macd_hist = [round(v, 2) for v in calculate_MACD(ticker)]
        img_base64 = plot_stock_price(ticker)
        
        return {
            "ticker": ticker,
            "price": price,
            "window": window,
            "sma": sma,
            "ema": ema,
            "rsi": rsi,
            "macd": macd_val,
            "signal": signal_line,
            "histogram": macd_hist,
            "chart_data": img_base64
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating analysis: {str(e)}")

@app.get("/stock/{ticker}/gemini-analysis")
def stock_gemini_analysis(ticker: str, window: int = Query(14, ge=5, le=200)):
    try:
        # First get regular analysis data
        price = round(get_stock_price(ticker), 2)
        sma = round(calculate_SMA(ticker, window), 2)
        ema = round(calculate_EMA(ticker, window), 2)
        rsi = round(calculate_RSI(ticker), 2)
        macd_val, signal_line, macd_hist = [round(v, 2) for v in calculate_MACD(ticker)]
        
        # Check if Gemini model is available
        if not gemini_model:
            raise HTTPException(status_code=500, detail="Gemini API not configured. Check GEMINI_API_KEY environment variable.")
        
        # Generate Gemini analysis
        gemini_prompt = prepare_gemini_prompt(
            ticker, price, sma, ema, rsi, macd_val, 
            signal_line, macd_hist, window
        )
        
        # Run Gemini API
        response = gemini_model.generate_content(
            gemini_prompt,
            generation_config={"temperature": 0}
        )
        
        return {
            "ticker": ticker,
            "analysis": response.text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating Gemini analysis: {str(e)}")

# For running directly
if __name__ == "__main__":
    uvicorn.run("fincrack_api:app", host="0.0.0.0", port=8000, reload=True)