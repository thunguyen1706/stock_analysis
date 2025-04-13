# 📈 Gemini Stock Analysis Assistant

Gemini Stock Analysis Assistant is an interactive Streamlit web app that combines financial data processing with Google’s Gemini AI to help users analyze and interpret stock market trends based on a company name or stock ticker.

## 🔍 Features

- 🔎 Accepts company names or stock tickers (e.g., Apple or AAPL)
- 📌 Fetches real-time financial data using Yahoo Finance
- 📊 Computes technical indicators:
  - Simple Moving Average (SMA)
  - Exponential Moving Average (EMA)
  - Relative Strength Index (RSI)
  - Moving Average Convergence Divergence (MACD)
- 🖼️ Displays line chart of 1-year stock price
- 🤖 Summarizes data using Gemini API with actionable suggestions (Buy / Hold / Sell)

## 🚀 How to Run

```bash
python -m venv venv
venv/Scripts/activate
pip install -r requirements.txt
python fincrack_api.py
streamlit run fincrack_frontend.py