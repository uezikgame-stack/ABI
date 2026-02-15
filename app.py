import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from gnews import GNews
from datetime import datetime
import xgboost as xgb

# --- 1. CONFIG & STYLE ---
st.set_page_config(page_title="Rillet ML", layout="wide")
st.markdown("""<style>
    .stApp { background-color: #020508 !important; color: #00ffcc; }
    .metric-card { background: rgba(0, 0, 0, 0.9); border: 1px solid #00ffcc; padding: 15px; text-align: center; border-radius: 10px; margin-bottom: 10px; }
    .news-tag { background: #00ffcc22; border: 1px solid #00ffcc; padding: 5px; border-radius: 5px; margin-bottom: 5px; }
    h1, h2, h3, p, span { color: #00ffcc !important; }
</style>""", unsafe_allow_html=True)

# --- 2. РЕЕСТР ТОП-15 БРОКЕРОВ (2026) ---
BROKERS_DB = {
    "Interactive Brokers": {"trust": 99.2, "lic": "SEC, FCA, ASIC", "fees": "$0.005/sh", "fact": "Pioneered electronic trading."},
    "Fidelity": {"trust": 98.5, "lic": "FINRA, SEC", "fees": "$0 (Stocks)", "fact": "Best for retirement and long-term."},
    "Charles Schwab": {"trust": 98.0, "lic": "SEC, FINRA", "fees": "$0 (Stocks)", "fact": "Largest US broker-dealer."},
    "Saxo Bank": {"trust": 96.0, "lic": "Danish FSA", "fees": "0.1%+", "fact": "Advanced global market access."},
    "Freedom Finance": {"trust": 94.5, "lic": "SEC, CySEC", "fees": "0.02%", "fact": "Focus on IPOs and EU/Asia."},
    "Vantage": {"trust": 93.8, "lic": "ASIC, FCA", "fees": "Low spread", "fact": "Ranked #1 Global Broker 2026."},
    "Pepperstone": {"trust": 92.5, "lic": "FCA, ASIC", "fees": "Tight spreads", "fact": "Preferred by active day traders."},
    "Exante": {"trust": 91.2, "lic": "CySEC, SFC", "fees": "0.02%", "fact": "Multi-asset DMA access."},
    "Webull": {"trust": 90.0, "lic": "SEC, FINRA", "fees": "$0", "fact": "Best mobile charting experience."},
    "Tiger Brokers": {"trust": 89.5, "lic": "ASIC, MAS", "fees": "Low", "fact": "Fastest growth in Asian markets."},
    "Robinhood": {"trust": 88.0, "lic": "SEC, FINRA", "fees": "$0", "fact": "Simplified mobile-first UI."},
    "E*TRADE": {"trust": 93.0, "lic": "SEC", "fees": "$0", "fact": "Owned by Morgan Stanley."},
    "Merrill Edge": {"trust": 94.0, "lic": "SEC", "fees": "$0", "fact": "Bank of America ecosystem."},
    "Swissquote": {"trust": 95.5, "lic": "FINMA", "fees": "High", "fact": "Swiss banking security."},
    "AvaTrade": {"trust": 87.5, "lic": "Central Bank of Ireland", "fees": "Spread-based", "fact": "Strong for fixed income CFDs."}
}

# --- 3. ML & NEWS CORE ---
def get_sentiment(ticker):
    try:
        gn = GNews(period='7d', max_results=5)
        news = gn.get_news(f"{ticker} stock")
        if not news: return "NEUTRAL", []
        titles = [n['title'].lower() for n in news]
        pos = sum(1 for t in titles if any(w in t for w in ['up', 'growth', 'buy', 'win']))
        neg = sum(1 for t in titles if any(w in t for w in ['down', 'crash', 'sell', 'risk']))
        signal = "BUY" if pos > neg else ("SELL" if neg > pos else "HOLD")
        return signal, news
    except: return "HOLD", []

def run_ml_forecast(df):
    try:
        d = df[['Close']].copy()
        d['lag'] = d['Close'].shift(1); d['ma'] = d['Close'].rolling(5).mean()
        d = d.dropna()
        model = xgb.XGBRegressor(n_estimators=100); model.fit(d[['lag', 'ma']], d['Close'])
        p = model.predict(np.array([[d['Close'].iloc[-1], d['ma'].iloc[-1]]]))[0]
        return p
    except: return None

# --- 4. UI ---
st.sidebar.title("RILLET ML 2026")
page = st.sidebar.selectbox("MENU", ["MARKET", "TOP 15 BROKERS"])

if page == "MARKET":
    ticker = st.text_input("ENTER TICKER (e.g. BABA, AAPL):", "BABA")
    df = yf.download(ticker, period="1y", auto_adjust=True)
    
    if not df.empty:
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        sig, news_list = get_sentiment(ticker)
        p_now = df['Close'].iloc[-1]
        p_ml = run_ml_forecast(df)
        
        # Dashboard
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-card'>CURRENT<br><h3>{p_now:,.2f} $</h3></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'>NEWS SIGNAL<br><h3>{sig}</h3></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card'>ML TARGET<br><h3>{p_ml:,.2f} $</h3></div>", unsafe_allow_html=True)
        
        st.line_chart(df['Close'].tail(50))
        
        st.write("### 📰 LATEST ANALYSIS")
        for n in news_list[:3]:
            st.markdown(f"<div class='news-tag'><b>{n['title']}</b><br><small>{n['published date']}</small></div>", unsafe_allow_html=True)
    else: st.error("Data Unavailable")

elif page == "TOP 15 BROKERS":
    st.write("## 🏛️ WORLD TOP 15 BROKERS REESRT")
    for name, info in BROKERS_DB.items():
        with st.expander(f"{name} (Trust: {info['trust']}%)"):
            st.write(f"**License:** {info['lic']}")
            st.write(f"**Fees:** {info['fees']}")
            st.write(f"**Fact:** {info['fact']}")
