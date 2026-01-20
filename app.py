import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Настройка страницы ABI
st.set_page_config(page_title="ABI Terminal", layout="wide")
st.title("🛡️ ABI: Intelligence Terminal")

# Панель управления ABI
st.sidebar.header("ABI Control Panel")
budget = st.sidebar.number_input("Ваш капитал ($)", value=1000, step=100)
market_choice = st.sidebar.selectbox("Выберите рынок", ["USA", "RF", "CRYPTO", "CHINA", "GOODS"])

# Обновленная база активов
MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC ADBE CRM AVGO QCOM TXN",
    "RF": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME NVTK.ME GMKN.ME TATN.ME MTSS.ME",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD XRP-USD LINK-USD AVAX-USD DOGE-USD UNI-USD",
    "CHINA": "BABA BIDU JD PDD LI NIO TCEHY NTES XPEV BYDDY",
    "GOODS": "GC=F SI=F PL=F HG=F PA=F CL=F NG=F BZ=F ZW=F ZC=F"
}

@st.cache_data(ttl=3600)
def load_abi_data(tickers):
    data = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', progress=False)
    results = []
    for t in tickers.split():
        try:
            df = data[t] if len(tickers.split()) > 1 else data
            if df.empty or np.isnan(df['Close'].iloc[-1]): continue
            p = float(df['Close'].iloc[-1])
            v = float(df['Close'].pct_change().std()) * 0.15 
            sc = (p / df['Close'].iloc[0] - 1) * 100
            results.append({"Тикер": t, "Цена": round(p, 2), "Вол": v, "Тренд %": round(sc, 2)})
        except: continue
    return results

# Загрузка данных
tickers = MARKETS[market_choice]
assets = load_abi_data(tickers)
df_assets = pd.DataFrame(assets).sort_values(by="Тренд %", ascending=False).reset_index(drop=True)
df_assets.index += 1 

st.subheader(f"📊 Аналитический срез: {market_choice}")
st.dataframe(df_assets[["Тикер", "Цена", "Тренд %"]].head(15), use_container_width=True)

st.divider()
selected_ticker = st.selectbox("Выберите актив для анализа ABI:", df_assets["Тикер"].tolist())

if selected_ticker:
    asset_info = yf.Ticker(selected_ticker)
    asset = next(item for item in assets if item["Тикер"] == selected_ticker)
    
    # Блок прогноза
    prices = [asset['Цена']]
    for d in range(1, 8):
        change = (asset['Trend %'] if 'Trend %' in asset else 0 * 0.0001) + np.random.normal(0, asset['Вол'])
        prices.append(prices[-1] * (1 + change))
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write(f"### График модели для {selected_ticker}")
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(prices, marker='o', color='#007bff', linewidth=2, label="Прогноз ABI")
        ax.grid(True, alpha=0.3)
        ax.legend()
        st.pyplot(fig)
        
    with col2:
        st.write("### Оценка профита")
        profit = (prices[-1] * (budget/asset['Цена'])) - budget
        st.metric("Ожидаемая прибыль", f"${profit:.2f}", f"{((prices[-1]/prices[0])-1)*100:.2f}%")
        risk = "Низкий" if asset['Вол'] < 0.015 else "Средний" if asset['Вол'] < 0.03 else "Высокий"
        st.info(f"💡 Риск: **{risk}**")

    # НОВЫЙ БЛОК: НОВОСТИ ABI
    st.divider()
    st.subheader(f"📰 Почему {selected_ticker} в движении: Заголовки")
    
    news = asset_info.news
    if news:
        for item in news[:5]: # Показываем 5 последних новостей
            with st.expander(item['title']):
                st.write(f"**Источник:** {item['publisher']}")
                st.write(f"**Ссылка:** [Читать подробнее]({item['link']})")
                # Пытаемся определить время публикации
                try:
                    date = datetime.fromtimestamp(item['providerPublishTime']).strftime('%Y-%m-%d %H:%M')
                    st.caption(f"Опубликовано: {date}")
                except: pass
    else:
        st.write("Для данного тикера свежих новостей не найдено.")
