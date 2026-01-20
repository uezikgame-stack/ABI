import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Настройка интерфейса
st.set_page_config(page_title="ABI Terminal", layout="wide")
st.title("🛡️ ABI: Analytics Terminal")

# Панель управления
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
    data = yf.download(tickers, period="6mo", interval="1d", group_by='ticker', progress=False)
    results = []
    for t in tickers.split():
        try:
            df = data[t].dropna()
            if df.empty: continue
            p = float(df['Close'].iloc[-1])
            y = df['Close'].values
            x = np.arange(len(y))
            slope, _ = np.polyfit(x, y, 1) # Линейный тренд
            vol = float(df['Close'].pct_change().std())
            results.append({"Тикер": t, "Цена": round(p, 2), "Тренд": slope, "Вол": vol})
        except: continue
    return results

assets = load_abi_data(MARKETS[market_choice])
df_assets = pd.DataFrame(assets).sort_values(by="Цена", ascending=False).reset_index(drop=True)
df_assets.index += 1 

st.subheader(f"📊 Котировки: {market_choice}")
st.dataframe(df_assets[["Тикер", "Цена"]], use_container_width=True)

st.divider()
selected_ticker = st.selectbox("Выберите актив:", df_assets["Тикер"].tolist())

if selected_ticker:
    asset = next(item for item in assets if item["Тикер"] == selected_ticker)
    
    # Расчет прогноза (Математическая модель)
    prices = [asset['Цена']]
    for _ in range(7):
        # Тренд + волатильность
        next_p = prices[-1] + asset['Тренд'] * 0.2 + np.random.normal(0, asset['Цена'] * asset['Вол'] * 0.4)
        prices.append(max(next_p, 0.01))
    
    # Блок цифр
    st.write(f"### 🎯 Прогноз для {selected_ticker}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Цена СЕЙЧАС", f"${asset['Цена']}")
    
    target_p = round(prices[-1], 2)
    change = ((target_p / asset['Цена']) - 1) * 100
    c2.metric("Цена через 7 дней", f"${target_p}", f"{change:.2f}%")
    
    profit = (prices[-1] * (budget/asset['Цена'])) - budget
    c3.metric("Ваш профит", f"${profit:.2f}")

    # График (Возвращаем чистый вид)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(prices, marker='o', color='#007bff', linewidth=2, label="Модель ABI")
    ax.axhline(asset['Цена'], color='red', linestyle='--', alpha=0.5, label="Текущая цена")
    ax.set_title(f"Динамика {selected_ticker} (7 дней)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    st.pyplot(fig)
