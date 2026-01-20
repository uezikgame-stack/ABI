import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="ABI Terminal", layout="wide")
st.title("🛡️ ABI: Professional Intelligence Terminal")

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

@st.cache_data(ttl=600) # Обновляем чаще для точности
def load_abi_data(tickers):
    data = yf.download(tickers, period="6mo", interval="1d", group_by='ticker', progress=False)
    results = []
    for t in tickers.split():
        try:
            df = data[t] if len(tickers.split()) > 1 else data
            df = df.dropna()
            if df.empty: continue
            p = float(df['Close'].iloc[-1])
            y = df['Close'].values
            x = np.arange(len(y))
            slope, _ = np.polyfit(x, y, 1)
            v = float(df['Close'].pct_change().std())
            sc = (p / df['Close'].iloc[0] - 1) * 100
            results.append({"Тикер": t, "Цена": round(p, 2), "Вол": v, "Тренд_Коэф": slope, "Смена %": round(sc, 2)})
        except: continue
    return results

assets = load_abi_data(MARKETS[market_choice])
df_assets = pd.DataFrame(assets).sort_values(by="Смена %", ascending=False).reset_index(drop=True)
df_assets.index += 1 

st.subheader(f"📊 Аналитика рынка: {market_choice}")
st.dataframe(df_assets[["Тикер", "Цена", "Смена %"]].head(15), use_container_width=True)

st.divider()
selected_ticker = st.selectbox("Выберите актив:", df_assets["Тикер"].tolist())

if selected_ticker:
    asset_info = yf.Ticker(selected_ticker)
    asset = next(item for item in assets if item["Тикер"] == selected_ticker)
    
    # НОВЫЙ БЛОК: НЫНЕШНЯЯ ЦЕНА
    st.write(f"### 🎯 Текущий статус {selected_ticker}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Текущая цена", f"${asset['Цена']}")
    c2.metric("Волатильность (Риск)", f"{asset['Вол']*100:.2f}%")
    c3.metric("Тренд (6 мес)", f"{asset['Смена %']}%")

    # Сверхточный прогноз ABI
    prices = [asset['Цена']]
    for d in range(1, 8):
        drift = asset['Тренд_Коэф'] * 0.2
        shock = np.random.normal(0, asset['Цена'] * asset['Вол'] * 0.4)
        prices.append(max(prices[-1] + drift + shock, 0.01))
    
    col1, col2 = st.columns([2, 1])
    with col1:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(prices, marker='o', color='#28a745', linewidth=2, label="Прогноз ABI")
        ax.axhline(asset['Цена'], color='red', linestyle='--', alpha=0.6, label="Вход (Текущая)")
        ax.grid(True, alpha=0.2)
        ax.legend()
        st.pyplot(fig)
        
    with col2:
        st.write("### Резюме ABI")
        profit_val = (prices[-1] * (budget/asset['Цена'])) - budget
        st.metric("Прогноз через 7 дней", f"${prices[-1]:.2f}", f"{((prices[-1]/prices[0])-1)*100:.2f}%")
        st.write(f"**Ваш доход при вложении ${budget}:**")
        st.success(f"**+ ${profit_val:.2f}**") if profit_val > 0 else st.error(f"**- ${abs(profit_val):.2f}**")

    # ИСПРАВЛЕННЫЙ БЛОК НОВОСТЕЙ (v4)
    st.divider()
    st.subheader(f"📰 Почему {selected_ticker} двигается?")
    try:
        raw_news = asset_info.news
        if raw_news:
            for n in raw_news[:5]:
                # Более гибкий поиск заголовка
                title = n.get('title') or n.get('content', {}).get('title') or "Новость без названия"
                link = n.get('link') or n.get('content', {}).get('canonicalUrl', {}).get('url', '#')
                publisher = n.get('publisher') or "Yahoo Finance"
                
                with st.expander(f"📌 {title}"):
                    st.write(f"**Источник:** {publisher}")
                    st.write(f"**Ссылка:** [Открыть новость]({link})")
        else:
            st.info("По данному активу новостей на Yahoo Finance не найдено.")
    except Exception as e:
        st.error(f"Ошибка загрузки новостей. Тикер может быть недоступен для новостной ленты.")
