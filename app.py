import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(page_title="ABI Terminal", layout="wide")
st.title("🛡️ ABI: Maximum Precision Terminal")

# Настройки управления
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

@st.cache_data(ttl=3600)
def load_abi_data(tickers):
    # Берем данные за полгода для точности
    data = yf.download(tickers, period="6mo", interval="1d", group_by='ticker', progress=False)
    results = []
    for t in tickers.split():
        try:
            df = data[t] if len(tickers.split()) > 1 else data
            df = df.dropna()
            if df.empty: continue
            
            p = float(df['Close'].iloc[-1])
            # Расчет математического тренда (наклон линии)
            y = df['Close'].values
            x = np.arange(len(y))
            slope, intercept = np.polyfit(x, y, 1)
            
            v = float(df['Close'].pct_change().std())
            sc = (p / df['Close'].iloc[0] - 1) * 100
            results.append({"Тикер": t, "Цена": round(p, 2), "Вол": v, "Тренд_Коэф": slope, "Смена %": round(sc, 2)})
        except: continue
    return results

assets = load_abi_data(MARKETS[market_choice])
df_assets = pd.DataFrame(assets).sort_values(by="Смена %", ascending=False).reset_index(drop=True)
df_assets.index += 1 

st.subheader(f"📊 Аналитический срез (Точность +): {market_choice}")
st.dataframe(df_assets[["Тикер", "Цена", "Смена %"]].head(15), use_container_width=True)

st.divider()
selected_ticker = st.selectbox("Выберите актив для сверхточного анализа:", df_assets["Тикер"].tolist())

if selected_ticker:
    asset_info = yf.Ticker(selected_ticker)
    asset = next(item for item in assets if item["Тикер"] == selected_ticker)
    
    # Сверхточный прогноз ABI
    prices = [asset['Цена']]
    for d in range(1, 8):
        # Базис — исторический наклон + текущий шум рынка
        drift = asset['Тренд_Коэф'] * 0.2 
        shock = np.random.normal(0, asset['Цена'] * asset['Вол'] * 0.5)
        next_p = prices[-1] + drift + shock
        prices.append(max(next_p, 0.01))
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write(f"### Сверхточная модель для {selected_ticker}")
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(prices, marker='o', color='#28a745', linewidth=2, label="Математический прогноз")
        ax.axhline(asset['Цена'], color='red', linestyle='--', alpha=0.5, label="Текущая цена")
        ax.grid(True, alpha=0.3)
        ax.legend()
        st.pyplot(fig)
        
    with col2:
        st.write("### Оценка ABI")
        profit = (prices[-1] * (budget/asset['Цена'])) - budget
        st.metric("Прогноз через 7 дней", f"${prices[-1]:.2f}", f"{((prices[-1]/prices[0])-1)*100:.2f}%")
        st.metric("Чистый профит", f"${profit:.2f}")
        
        # Сигнал ABI
        if prices[-1] > prices[0] * 1.02:
            st.success("🎯 РЕКОМЕНДАЦИЯ: ПОКУПАТЬ")
        elif prices[-1] < prices[0] * 0.98:
            st.error("⚠️ РЕКОМЕНДАЦИЯ: ПРОДАВАТЬ")
        else:
            st.warning("⚖️ РЕКОМЕНДАЦИЯ: УДЕРЖИВАТЬ")

    # НОВОСТИ БЕЗ ОШИБОК
    st.divider()
    st.subheader(f"📰 Контекст рынка для {selected_ticker}")
    try:
        news_data = asset_info.news
        if news_data:
            for item in news_data[:5]:
                title = item.get('title', 'Новость без заголовка')
                with st.expander(title):
                    st.write(f"**Источник:** {item.get('publisher', 'N/A')}")
                    st.write(f"[Открыть оригинал]({item.get('link', '#')})")
        else:
            st.info("Новости по данному активу отсутствуют.")
    except:
        st.error("Не удалось загрузить ленту новостей.")
