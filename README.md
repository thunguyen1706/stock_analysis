📈 Gemini Stock Analysis Assistant
Gemini Stock Analysis Assistant is an interactive Streamlit web app that combines financial data processing with Google’s Gemini AI to help users analyze and interpret stock market trends based on a company name or stock ticker.

🔍 Features
🔎 Accepts company names or stock tickers (e.g., Apple or AAPL)

📈 Fetches real-time financial data using Yahoo Finance

🧮 Computes technical indicators:

Simple Moving Average (SMA)

Exponential Moving Average (EMA)

Relative Strength Index (RSI)

Moving Average Convergence Divergence (MACD)

📊 Displays line chart of 1-year stock price

🤖 Summarizes data using Gemini API with actionable suggestions (Buy / Hold / Sell)

🚀 How to Run
Install dependencies:

bash
Copy
Edit
pip install -r requirements.txt
Run the app:

bash
Copy
Edit
streamlit run fincrack_v1.py
Open in browser:

Local: http://localhost:8501

Network: Shown in console

🔑 API Key
Set your Gemini API key in the script:

python
Copy
Edit
genai.configure(api_key="YOUR_GEMINI_API_KEY")
🧠 Tech Stack
Streamlit – for UI

YFinance – for stock data

Matplotlib – for plotting

Google Generative AI (Gemini) – for natural language insights
