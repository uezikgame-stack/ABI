import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Настройка интерфейса ABI
st.set_page_config(page_title="ABI Terminal", layout="wide")
st.title("🛡️ ABI: Ultra Precision Terminal")

# Контрольная панель
st.sidebar.header("ABI Control Panel")
budget = st.sidebar.number_input("Ваш капитал ($)", value=1000, step=100)
market_choice = st.sidebar.selectbox("Выберите рынок", ["USA", "RF", "CRYPTO", "CHINA", "GOODS"])

MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC ADBE CRM AVGO QCOM TXN",
    "RF": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME NVTK.ME GMKN.ME TATN.ME MTSS.ME",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD XRP-USD LINK-USD AVAX-USD DOGE-USD UNI-USD",
    "CHINA": "BABA BIDU JD PDD LI NIO TCEHY NTES XPEV BYDDY",
    "GOODS": "GC=F SI=F PL=F HG=F PA=F CL=F NG=F BZ=F ZW=F ZC=F"
}

@st.cache_data(ttl=300)
def load_abi_data(tickers):
    data = yf.download(tickers, period="1y", interval="1d", group_by='ticker', progress=False)
    results = []
    for t in tickers.split():
        try:
            df = data[t].dropna()
            if df.empty: continue
            
            close = df['Close'].values
            # Экспоненциальное сглаживание для точности
            alpha = 0.3 # Вес последних данных
            smoothed = [close[0]]
            for i in range(1, len(close)):
                smoothed.append(alpha * close[i] + (1 - alpha) * smoothed[-1])
            
            p_now = float(close[-1])
            last_trend = smoothed[-1] - smoothed[-2]
            vol = float(df['Close'].pct_change().std())
            
            results.append({"Тикер": t, "Цена": round(p_now, 2), "Тренд_Ультра": last_trend, "Вол": vol, "History": close[-20:]})
        except: continue
    return results

assets = load_abi_data(MARKETS[market_choice])
df_assets = pd.DataFrame(assets).sort_values(by="Цена", ascending=False).reset_index(drop=True)
df_assets.index += 1 

st.subheader(f"📊 Живые котировки: {market_choice}")
st.dataframe(df_assets[["Тикер", "Цена"]], use_container_width=True)

st.divider()
selected_ticker = st.selectbox("Актив для сверхточного анализа:", df_assets["Тикер"].tolist())

if selected_ticker:
    asset = next(item for item in assets if item["Тикер"] == selected_ticker)
    
    # Рас
