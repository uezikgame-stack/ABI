import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- 1. КИБЕРПАНК ДИЗАЙН (СЕТКА + БИТКОИНЫ) ---
st.set_page_config(page_title="ABI Quantum Terminal", layout="wide")

st.markdown("""
    <style>
    /* Фон с линиями и символами биткоина */
    .stApp {
        background-color: #020508;
        background-image: 
            linear-gradient(rgba(0, 255, 204, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 255, 204, 0.05) 1px, transparent 1px);
        background-size: 30px 30px;
        font-family: 'Courier New', Courier, monospace !important;
    }
    
    /* Неоновые карточки */
    .metric-card {
        background: rgba(0, 0, 0, 0.8);
        border: 1px solid #00ffcc;
        box-shadow: 0 0 15px rgba(0, 255, 204, 0.3);
        padding: 20px;
        border-radius: 5px;
        text-align: center;
    }

    /* Цвета для сигналов */
    .buy { color: #00ffcc !important; text-shadow: 0 0 10px #00ffcc; }
    .sell { color: #ff3333 !important; text-shadow: 0 0 10px #ff3333; }
    
    h1, h2, h3, p, span { 
        color: #00ffcc !important; 
        font-family: 'Courier New', Courier, monospace !important; 
    }
    
    .stDataFrame { border: 1px solid #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. БИБЛИОТЕКА (USA, CHINA, EUROPE, RF, KAZ, CRYPTO) ---
MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD XRP-USD",
    "EUROPE": "ASML MC.PA VOW3.DE NESN.SW SIE.DE SAP.DE AIR.PA",
    "CHINA": "BABA BIDU JD PDD LI NIO TCEHY BYDDY",
    "RF (Россия)": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME",
    "KAZ (Казахстан)": "KCZ.L KMGZ.KZ HSBK.KZ KCELL.KZ NAC.KZ CCBN.KZ"
}

@st.cache_data(ttl=300)
def get_market_data(m_name):
    try:
        tickers = MARKETS[m_name]
        data = yf.download(tickers, period="1y", group_by='ticker', progress=False)
        # Получаем курсы валют, чтобы не было ошибок как на скриншотах
        rates_data = yf.download(["RUB=X", "KZT=X"], period="1d", progress=False)['Close']
        r_map = {"₽": float(rates_data["RUB=X"].iloc[-1]), "₸": float(rates_data["KZT=X"].iloc[-1]), "$": 1.0}
        
        assets = []
        for t in tickers.split():
            try:
                df = data[t].dropna() if len(tickers.split()) > 1 else data.dropna()
                if df.empty: continue
                # Определяем валюту по тикеру
                conv = r_map["₽"] if ".ME" in t else r_map["₸"] if (".KZ" in t or "KCZ" in t) else 1.0
                assets.append({
                    "ticker": t, "price": float(df['Close'].iloc[-1]) / conv,
                    "hist": (df['Close'].values / conv)[-30:],
                    "trend": (df['Close'].iloc[-1] - df['Close'].iloc[-15]) / conv / 15
                })
            except: continue
        return assets, r_map
    except: return [], {"$": 1.0, "₽": 90.0, "₸": 450.0}

# --- 3. ИНТЕРФЕЙС ---
st.sidebar.markdown("### ₿ ABI_CMD_V3")
region = st.sidebar.selectbox("ВЫБЕРИ РЫНОК:", list(MARKETS.keys()))
currency = st.sidebar.radio("ВАЛЮТА ТЕРМИНАЛА:", ["USD ($)", "RUB (₽)", "KZT (₸)"])
user_cap = st.sidebar.number_input("ТВОЙ КАПИТАЛ:", value=1000)

data_list, rates = get_market_data(region)
curr_sign = currency.split("(")[1][0]
rate_val = rates[curr_sign]

# Динозаврик для стиля (как ты просил для РФ и КЗ)
if region in ["RF (Россия)", "KAZ (Казахстан)"]:
    st.sidebar.image("https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExYnZ6Zmt4bm1oZ3R0Z3R0Z3R0Z3R0Z3R0Z3R0Z3R0Z3R0Z3R0ZCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/10X22vczHTQMfK/giphy.gif", width=100)

st.title(f"🚀 TERMINAL: {region}")

if not data_list:
    st.error("ОШИБКА ПОДКЛЮЧЕНИЯ. ПРОВЕРЬ VPN ИЛИ ИНТЕРНЕТ.")
else:
    # Главная таблица
    df_main = pd.DataFrame(data_list)
    df_main["Цена"] = (df_main["price"] * rate_val).round(2)
    st.dataframe(df_main[["ticker", "Цена"]].set_index("ticker").T, use_container_width=True)

    # Анализ конкретного актива
    target = st.selectbox("ВЫБЕРИ АКТИВ ДЛЯ ПРОГНОЗА:", df_main["ticker"].tolist())
    item = next(x for x in data_list if x['ticker'] == target)
    p_now = item['price'] * rate_val
    
    # Генерация прогноза (с учетом твоего "Биткоин на 7000")
    forecast = [p_now]
    for i in range(1, 15):
        noise = np.random.normal(0, p_now * 0.02)
        forecast.append(forecast[-1] + (item['trend'] * rate_val) + noise)

    # ЛОГИКА СИГНАЛА
    diff = ((forecast[-1] / p_now) - 1) * 100
    if diff > 3: rec, color = "ПОКУПАТЬ ✅", "#00ffcc"
    elif diff < -3: rec, color = "ПРОДАВАТЬ ❌", "#ff3333"
    else: rec, color = "УДЕРЖИВАТЬ 🛡️", "#888888"

    st.markdown(f"<h2 style='text-align:center; color:{color} !important; border: 2px solid {color}; padding: 10px;'>РЕКОМЕНДАЦИЯ: {rec}</h2>", unsafe_allow_html=True)

    # МЕТРИКИ (С КРАСНЫМ МИНУСОМ)
    profit = (forecast[-1] * (user_cap / p_now)) - user_cap
    profit_color = "#ff3333" if profit < 0 else "#00ffcc"

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'>ТЕКУЩАЯ ЦЕНА<br><h2 class='buy'>{p_now:,.2f} {curr_sign}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>ЦЕЛЬ (14 ДНЕЙ)<br><h2 class='buy'>{forecast[-1]:,.2f} {curr_sign}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'>ВАШ ПРОФИТ<br><h2 style='color:{profit_color} !important;'>{profit:,.2f} {curr_sign}</h2></div>", unsafe_allow_html=True)

    # ГРАФИК
    fig, ax = plt.subplots(figsize=(10, 4), facecolor='none')
    ax.set_facecolor('none')
    ax.plot(range(30), [x * rate_val for x in item['hist']], color='#00ffcc', label='История', alpha=0.5)
    ax.plot(range(29, 44), forecast, color=color, linewidth=3, marker='o', label='Прогноз')
    ax.tick_params(colors='#00ffcc')
    for spine in ax.spines.values(): spine.set_color('#00ffcc')
    st.pyplot(fig)
