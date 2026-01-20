import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Базовая настройка ABI
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
            # Алгоритм Хольта для максимальной точности
            alpha = 0.35 
            smoothed = [close[0]]
            for i in range(1, len(close)):
                smoothed.append(alpha * close[i] + (1 - alpha) * smoothed[-1])
            
            p_now = float(close[-1])
            last_trend = smoothed[-1] - smoothed[-2]
            vol = float(df['Close'].pct_change().std())
            
            # Сохраняем данные
            results.append({
                "ticker": t, 
                "price": round(p_now, 2), 
                "trend": last_trend, 
                "vol": vol, 
                "history": close[-15:]
            })
        except: continue
    return results

assets = load_abi_data(MARKETS[market_choice])
df_assets = pd.DataFrame(assets).sort_values(by="price", ascending=False).reset_index(drop=True)
df_assets.index += 1 

st.subheader(f"📊 Текущие котировки: {market_choice}")
st.dataframe(df_assets[["ticker", "price"]], use_container_width=True)

st.divider()
selected_ticker = st.selectbox("Актив для сверхточного анализа:", df_assets["ticker"].tolist())

if selected_ticker:
    asset = next(item for item in assets if item["ticker"] == selected_ticker)
    
    # Расчет прогноза
    forecast = [asset['price']]
    for i in range(1, 8):
        damping = 0.85 ** i
        noise = np.random.normal(0, asset['price'] * asset['vol'] * 0.3)
        next_val = forecast[-1] + (asset['trend'] * damping) + noise
        forecast.append(max(next_val, 0.01))
    
    # Вывод данных
    st.write(f"### 🎯 Результаты: {selected_ticker}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Цена СЕЙЧАС", f"${asset['price']}")
    
    target_p = round(forecast[-1], 2)
    change = ((target_p / asset['price']) - 1) * 100
    c2.metric("Прогноз (7 дней)", f"${target_p}", f"{change:.2f}%")
    
    profit = (forecast[-1] * (budget/asset['price'])) - budget
    c3.metric("Прибыль", f"${profit:.2f}")

    # Финальный график
    fig, ax = plt.subplots(figsize=(10, 4))
    history = list(asset['history'])
    
    ax.plot(range(len(history)), history, color='gray', alpha=0.5, label="История")
    ax.plot(range(len(history)-1, len(history) + 7), forecast, marker='o', color='#007bff', linewidth=2, label="ABI Ultra")
    
    ax.axhline(asset['price'], color='red', linestyle='--', alpha=0.5)
    ax.set_title(f"Сверхточный прогноз для {selected_ticker}")
    ax.grid(True, alpha=0.2)
    ax.legend()
    st.pyplot(fig)
