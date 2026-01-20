import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time

# --- ИНТЕРФЕЙС И ГЛОБАЛЬНЫЙ СТИЛЬ ---
st.set_page_config(page_title="ABI Terminal", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    /* Стилизация вертикального списка */
    .stock-list {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #00ffcc33;
    }
    .metric-card {
        background: rgba(10, 15, 25, 0.95); border-left: 5px solid #00ffcc;
        padding: 20px; border-radius: 10px; margin-bottom: 10px;
    }
    h1, h2, h3 { color: #00ffcc !important; font-family: 'Courier New', monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- ЭКРАН ЗАГРУЗКИ (DINO НА БЕЛОМ) ---
if 'loaded' not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("""
            <div style="background-color: white; height: 100vh; width: 100vw; position: fixed; top: 0; left: 0; z-index: 9999; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                <h1 style="color: black !important; font-family: Arial; margin-bottom: 20px;">ABI TERMINAL STARTING...</h1>
                <img src="https://i.gifer.com/V96u.gif" width="250">
                <p style="color: #666; font-size: 18px; margin-top: 30px;">Синхронизация с мировыми биржами...</p>
            </div>
            """, unsafe_allow_html=True)
        time.sleep(2.5) 
    st.session_state.loaded = True
    placeholder.empty()

# --- ЛОГИКА ДАННЫХ (ТУРБО-ПАКЕТ) ---
MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC ADBE CRM AVGO QCOM PYPL",
    "RF (Россия)": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME NVTK.ME GMKN.ME TATN.ME CHMF.ME ALRS.ME MTSS.ME PLZL.ME MOEX.ME SNGS.ME",
    "KAZ (Казахстан)": "KCZ.L KMGZ.KZ HSBK.KZ KCELL.KZ NAC.KZ CCBN.KZ KZAP.KZ KEGC.KZ KZTK.KZ KZTO.KZ ASBN.KZ BAST.KZ",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD XRP-USD LINK-USD AVAX-USD DOGE-USD MATIC-USD TRX-USD LTC-USD"
}

@st.cache_data(ttl=300)
def get_fast_data(market_name):
    tickers = MARKETS[market_name]
    data = yf.download(tickers, period="1y", group_by='ticker', progress=False)
    # Загружаем курсы валют
    rates_data = yf.download(["RUB=X", "KZT=X"], period="1d", progress=False)['Close']
    r = {"₽": float(rates_data["RUB=X"].iloc[-1]), "₸": float(rates_data["KZT=X"].iloc[-1]), "$": 1.0}
    
    results = []
    for t in tickers.split():
        try:
            df = data[t].dropna()
            if df.empty: continue
            conv = r["₽"] if ".ME" in t else r["₸"] if (".KZ" in t or "KCZ" in t) else 1.0
            results.append({
                "ticker": t, 
                "price": float(df['Close'].iloc[-1]) / conv,
                "history": (df['Close'].values / conv)[-30:],
                "vol": float(df['Close'].pct_change().std()),
                "trend": (df['Close'].iloc[-1] - df['Close'].iloc[-15]) / conv / 15
            })
        except: continue
    return results, r

# --- ОСНОВНОЙ ИНТЕРФЕЙС ---
st.sidebar.title("🛡️ ABI CONTROL")
market_choice = st.sidebar.selectbox("ВЫБОР РЫНКА:", list(MARKETS.keys()))
currency_choice = st.sidebar.radio("ВАЛЮТА ТЕРМИНАЛА:", ["USD ($)", "RUB (₽)", "KZT (₸)"])
user_capital = st.sidebar.number_input("ВАШ КАПИТАЛ:", value=1000)

assets, rates = get_fast_data(market_choice)
curr_sym = currency_choice.split("(")[1][0]
rate_to_use = rates[curr_sym]

# РАЗДЕЛЕНИЕ НА КОЛОНКИ: Список (слева) и Анализ (справа)
col_list, col_main = st.columns([1, 3])

with col_list:
    st.subheader("📈 ТОП-15")
    # Формируем вертикальный список
    st.markdown('<div class="stock-list">', unsafe_allow_html=True)
    df_vertical = pd.DataFrame(assets)
    df_vertical["Цена"] = (df_vertical["price"] * rate_to_use).round(2)
    st.dataframe(df_vertical[["ticker", "Цена"]].set_index("ticker"), height=550, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_main:
    selected_ticker = st.selectbox("ВЫБЕРИТЕ АКТИВ ДЛЯ ПРОГНОЗА:", [a['ticker'] for a in assets])
    asset = next(a for a in assets if a['ticker'] == selected_ticker)
    
    p_now = asset['price'] * rate_to_use
    
    # Расчет прогноза
    np.random.seed(42)
    forecast = [p_now]
    for i in range(1, 15):
        noise = np.random.normal(0, p_now * asset['vol'] * 0.5)
        forecast.append(max(forecast[-1] + (asset['trend'] * rate_to_use) + noise, 0.01))

    # Сигналы и Метрики
    change_pct = ((forecast[-1]/p_now)-1)*100
    sig_color = "#00ffcc" if change_pct > 3 else "#ff4b4b" if change_pct < -3 else "#888888"
    
    m1, m2, m3 = st.columns(3)
    m1.markdown(f"<div class='metric-card'>ТЕКУЩАЯ ЦЕНА<br><h2>{p_now:,.2f} {curr_sym}</h2></div>", unsafe_allow_html=True)
    m2.markdown(f"<div class='metric-card'>ЦЕЛЬ (14 ДНЕЙ)<br><h2 style='color:{sig_color} !important;'>{forecast[-1]:,.2f} {curr_sym}</h2></div>", unsafe_allow_html=True)
    
    profit_amt = (forecast[-1] * (user_capital/p_now * rate_to_use)) - (user_capital * rate_to_use)
    m3.markdown(f"<div class='metric-card'>ВАШ ПРОФИТ<br><h2>{profit_amt:,.2f} {curr_sym}</h2></div>", unsafe_allow_html=True)

    # ИСПРАВЛЕННЫЙ ГРАФИК
    fig, ax = plt.subplots(figsize=(10, 4), facecolor='none')
    ax.set_facecolor('none')
    
    history_prices = [h * rate_to_use for h in asset['history']]
    ax.plot(range(len(history_prices)), history_prices, color='white', alpha=0.3, label="История")
    ax.plot(range(len(history_prices)-1, len(history_prices)+14), forecast, color=sig_color, linewidth=4, marker='o', markersize=6, label="ABI Forecast")
    
    ax.tick_params(colors='white')
    ax.grid(color='#222222', alpha=0.5)
    st.pyplot(fig)

    st.markdown(f"### Рекомендация: <span style='color:{sig_color}'>{'ПОКУПАТЬ' if change_pct > 3 else 'ПРОДАВАТЬ' if change_pct < -3 else 'УДЕРЖИВАТЬ'}</span>", unsafe_allow_html=True)
