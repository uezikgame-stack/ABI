import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Настройка стиля и скрытие мусора
st.set_page_config(page_title="ABI Terminal", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="metric-container"] {
        background-color: #1e2130;
        border: 1px solid #3d4466;
        padding: 15px;
        border-radius: 10px;
        color: white;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ ABI: Smart Intelligence Terminal")

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
            slope, _ = np.polyfit(x, y, 1)
            vol = float(df['Close'].pct_change().std())
            results.append({"Тикер": t, "Цена": round(p, 2), "Тренд": slope, "Вол": vol})
        except: continue
    return results

assets = load_abi_data(MARKETS[market_choice])
df_assets = pd.DataFrame(assets).sort_values(by="Цена", ascending=False).reset_index(drop=True)
df_assets.index += 1 

# Красивая таблица лидеров
st.subheader(f"📊 Аналитический срез: {market_choice}")
st.dataframe(df_assets[["Тикер", "Цена"]], use_container_width=True)

st.divider()
selected_ticker = st.selectbox("Выберите актив для анализа:", df_assets["Тикер"].tolist())

if selected_ticker:
    asset = next(item for item in assets if item["Тикер"] == selected_ticker)
    
    # Расчет прогноза
    prices = [asset['Цена']]
    for _ in range(7):
        prices.append(prices[-1] + asset['Тренд'] * 0.2 + np.random.normal(0, asset['Цена'] * asset['Вол'] * 0.4))
    
    # Дизайн верхних карточек
    st.write(f"### 🎯 Статус и прогноз: {selected_ticker}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Текущая цена", f"${asset['Цена']}")
    
    target_price = round(prices[-1], 2)
    change_pct = ((target_price / asset['Цена']) - 1) * 100
    c2.metric("Цена через 7 дней", f"${target_price}", f"{change_pct:.2f}%")
    
    profit = (prices[-1] * (budget/asset['Цена'])) - budget
    c3.metric("Ваша прибыль", f"${profit:.2f}")

    # График с новым цветом
    col_chart, col_logic = st.columns([2, 1])
    with col_chart:
        fig, ax = plt.subplots(figsize=(10, 4), facecolor='#0e1117')
        ax.set_facecolor('#0e1117')
        ax.plot(prices, marker='o', color='#00ffcc', linewidth=2, label="Модель ABI")
        ax.axhline(asset['Цена'], color='#ff4b4b', linestyle='--', alpha=0.6, label="Вход")
        ax.tick_
