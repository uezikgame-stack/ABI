import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Убираем лишние отступы и скрываем мусор
st.set_page_config(page_title="ABI Terminal", layout="wide")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>", unsafe_allow_html=True)

st.title("🛡️ ABI: Analytics & Intelligence")

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
            results.append({"Тикер": t, "Цена": round(p, 2), "Тренд": slope, "Вол": float(df['Close'].pct_change().std())})
        except: continue
    return results

assets = load_abi_data(MARKETS[market_choice])
df_assets = pd.DataFrame(assets).sort_values(by="Цена", ascending=False).reset_index(drop=True)
df_assets.index += 1 

st.subheader(f"📊 Текущие котировки: {market_choice}")
st.dataframe(df_assets[["Тикер", "Цена"]], use_container_width=True)

st.divider()
selected_ticker = st.selectbox("Выберите актив:", df_assets["Тикер"].tolist())

if selected_ticker:
    asset = next(item for item in assets if item["Тикер"] == selected_ticker)
    asset_info = yf.Ticker(selected_ticker)
    
    # Прогноз
    prices = [asset['Цена']]
    for _ in range(7):
        prices.append(prices[-1] + asset['Тренд'] * 0.2 + np.random.normal(0, asset['Цена'] * asset['Вол'] * 0.4))
    
    st.write(f"### 🎯 Анализ {selected_ticker}")
    c1, c2 = st.columns([2, 1])
    
    with c1:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(prices, marker='o', color='#28a745', label="Прогноз ABI")
        ax.axhline(asset['Цена'], color='red', linestyle='--', label="Сейчас")
        ax.legend()
        st.pyplot(fig)
        
    with c2:
        profit = (prices[-1] * (budget/asset['Цена'])) - budget
        st.metric("Цена через неделю", f"${prices[-1]:.2f}")
        st.metric("Чистый доход", f"${profit:.2f}", f"{((prices[-1]/asset['Цена'])-1)*100:.2f}%")
        if profit > 0: st.success("🎯 РЕКОМЕНДАЦИЯ: ПОКУПАТЬ")
        else: st.error("⚠️ РЕКОМЕНДАЦИЯ: ПРОДАВАТЬ")

    # СКРЫТЫЙ БЛОК: НОВОСТИ (только если нажать)
    with st.expander("🔍 Показать обоснование (Новости)"):
        try:
            news = asset_info.news
            if news:
                for n in news[:3]:
                    st.write(f"**{n.get('title', 'Новость')}**")
                    st.write(f"[Читать]({n.get('link', '#')})")
            else:
                st.write("Новостей нет.")
        except:
            st.write("Связь с новостями временно прервана.")
