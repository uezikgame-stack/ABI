import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Настройка интерфейса
st.set_page_config(page_title="ABI Terminal", layout="wide")
st.title("🛡️ ABI: Russian Markets & Daily Growth")

# Панель управления
st.sidebar.header("ABI Control Panel")
budget = st.sidebar.number_input("Ваш капитал ($)", value=1000, step=100)
market_choice = st.sidebar.selectbox("Выберите рынок", ["USA", "RF", "CRYPTO", "CHINA", "GOODS"])

# Исправленные тикеры для РФ и других рынков
MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC",
    "RF": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME NVTK.ME GMKN.ME TATN.ME CHMF.ME",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD",
    "CHINA": "BABA BIDU JD PDD LI NIO",
    "GOODS": "GC=F SI=F CL=F NG=F"
}

@st.cache_data(ttl=300)
def load_abi_data(tickers):
    data = yf.download(tickers, period="1y", interval="1d", group_by='ticker', progress=False)
    results = []
    for t in tickers.split():
        try:
            df = data[t].dropna() if len(tickers.split()) > 1 else data.dropna()
            if df.empty: continue
            
            close = df['Close'].values
            alpha = 0.35 
            smoothed = [close[0]]
            for i in range(1, len(close)):
                smoothed.append(alpha * close[i] + (1 - alpha) * smoothed[-1])
            
            p_now = float(close[-1])
            last_trend = smoothed[-1] - smoothed[-2]
            vol = float(df['Close'].pct_change().std())
            
            results.append({
                "ticker": t, "price": round(p_now, 2), 
                "trend": last_trend, "vol": vol, "history": close[-15:]
            })
        except: continue
    return results

assets = load_abi_data(MARKETS[market_choice])
if not assets:
    st.error("Ошибка загрузки данных. Попробуйте сменить рынок.")
else:
    df_assets = pd.DataFrame(assets).sort_values(by="price", ascending=False).reset_index(drop=True)
    df_assets.index += 1 

    st.subheader(f"📊 Котировки: {market_choice}")
    st.dataframe(df_assets[["ticker", "price"]], use_container_width=True)

    st.divider()
    selected_ticker = st.selectbox("Актив для анализа:", df_assets["ticker"].tolist())

    if selected_ticker:
        asset = next(item for item in assets if item["ticker"] == selected_ticker)
        
        # Генерация прогноза и роста по дням
        forecast = [asset['price']]
        daily_growth = []
        current_date = datetime.now()

        for i in range(1, 8):
            damping = 0.85 ** i
            noise = np.random.normal(0, asset['price'] * asset['vol'] * 0.3)
            next_val = forecast[-1] + (asset['trend'] * damping) + noise
            next_val = max(next_val, 0.01)
            
            diff = next_val - forecast[-1]
            pct = (diff / forecast[-1]) * 100
            
            forecast.append(next_val)
            daily_growth.append({
                "День": (current_date + timedelta(days=i)).strftime("%d.%m"),
                "Прогноз цены": round(next_val, 2),
                "Рост ($)": round(diff, 2),
                "Рост (%)": f"{pct:+.2f}%"
            })

        # Вывод основных метрик
        c1, c2, c3 = st.columns(3)
        c1.metric("Цена СЕЙЧАС", f"${asset['price']}")
        c2.metric("Цель через неделю", f"${round(forecast[-1], 2)}", f"{((forecast[-1]/asset['price'])-1)*100:+.2f}%")
        profit = (forecast[-1] * (budget/asset['price'])) - budget
        c3.metric("Ваша прибыль", f"${profit:.2f}")

        # График
        fig, ax = plt.subplots(figsize=(10, 4))
        history = list(asset['history'])
        ax.plot(range(len(history)), history, color='gray', alpha=0.4, label="История")
        ax.plot(range(len(history)-1, len(history) + 7), forecast, marker='o', color='#007bff', label="ABI Ultra")
        ax.axhline(asset['price'], color='red', linestyle='--', alpha=0.5)
        ax.legend()
        st.pyplot(fig)

        # ТАБЛИЦА РОСТА ПО ДНЯМ
        st.write("### 📅 Детальный прогноз роста по дням")
        st.table(pd.DataFrame(daily_growth))
