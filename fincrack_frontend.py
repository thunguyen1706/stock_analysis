import streamlit as st
import requests
import json
import base64
from io import BytesIO
from PIL import Image

# API endpoint (change this to match your deployment)
API_URL = "http://localhost:8000"

def main():
    # Streamlit UI
    st.title('📈 Gemini Stock Analysis Assistant')
    
    # Check API connection
    try:
        response = requests.get(f"{API_URL}/")
        if response.status_code != 200:
            st.error(f"Error connecting to API at {API_URL}. Response: {response.text}")
            st.stop()
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to API at {API_URL}. Make sure the API is running.")
        st.stop()
    
    # Main UI components
    company_input = st.text_input("Enter company name or stock ticker (e.g., Apple or AAPL):")
    window = st.slider("Select window size for SMA/EMA:", 5, 50, 14)

    if company_input:
        try:
            # Step 1: Get ticker symbol
            with st.spinner("Identifying ticker..."):
                ticker_response = requests.get(f"{API_URL}/ticker/{company_input}")
                
                if ticker_response.status_code != 200:
                    st.error(f"Error: {ticker_response.json().get('detail', 'Unknown error')}")
                    st.stop()
                
                ticker = ticker_response.json()["ticker"]
                st.subheader(f"Fetching data for {ticker}...")
            
            # Step 2: Get complete analysis
            with st.spinner("Analyzing stock data..."):
                analysis_response = requests.get(f"{API_URL}/stock/{ticker}/analysis", params={"window": window})
                
                if analysis_response.status_code != 200:
                    st.error(f"Error: {analysis_response.json().get('detail', 'Unknown error')}")
                    st.stop()
                
                analysis_data = analysis_response.json()
                
                # Extract data
                price = analysis_data["price"]
                sma = analysis_data["sma"]
                ema = analysis_data["ema"]
                rsi = analysis_data["rsi"]
                macd_val = analysis_data["macd"]
                signal_line = analysis_data["signal"]
                macd_hist = analysis_data["histogram"]
                chart_data = analysis_data["chart_data"]
            
            # Display basic data
            st.write(f"💵 Latest Price: ${price}")
            st.write(f"📊 {window}-Day SMA: ${sma}")
            st.write(f"📈 {window}-Day EMA: ${ema}")
            st.write(f"📉 RSI: {rsi}")
            st.write(f"📐 MACD: {macd_val} | Signal: {signal_line} | Histogram: {macd_hist}")
            
            # Display chart
            image_bytes = base64.b64decode(chart_data)
            image = Image.open(BytesIO(image_bytes))
            st.image(image, caption=f"{ticker} Closing Price - Last 1 Year")
            
            # Step 3: Get Gemini analysis from backend
            with st.spinner("Generating AI analysis..."):
                gemini_response = requests.get(f"{API_URL}/stock/{ticker}/gemini-analysis", params={"window": window})
                
                if gemini_response.status_code != 200:
                    st.error(f"Error generating AI analysis: {gemini_response.json().get('detail', 'Gemini API error')}")
                else:
                    # Display Gemini Analysis
                    st.subheader("📋 Gemini Analysis")
                    st.write(gemini_response.json()["analysis"])

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()