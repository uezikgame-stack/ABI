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
    .metric-card {
        background: rgba(10, 15, 25, 0.95); border-left: 5px solid #00ffcc;
        padding: 20px; border-radius: 10px; margin-bottom: 10px;
    }
    .stock-box {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid #00ffcc33; border-radius: 10px;
        padding: 15px; margin-bottom: 20px;
    }
    h1, h2, h3 { color: #00ffcc !important; font-family: 'Courier New', monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- ЭКРАН ЗАГРУЗКИ (DINO НА БЕЛОМ) ---
# Используем session_state, чтобы динозаврик мелькал только при смене рынка
if 'last_market' not in st.session_state:
    st.session_state.last_market = None

def show_dino():
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("""
            <div style="background-color: white; height: 100vh; width: 100vw; position: fixed; top: 0; left: 0; z-index: 9999; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                <h1 style="color: black !important; font-family: Arial; margin-bottom: 20px;">ABI QUANTUM LOADING...</h1>
                <img src="https://i.gifer.com/V96u.gif" width="250">
                <p style="color: #666; font-size: 18px; margin-top: 30px;">Анализируем глобальные тренды...</p>
            </div>
            """, unsafe_allow_html=True)
        time.sleep(2)
    placeholder.empty()

# --- СПИСОК РЕГИОНОВ (ПОЛНЫЙ ТОП-25) ---
MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC ADBE CRM AVGO QCOM PYPL TSMC ASML BABA COST PEP NKE TM ORCL MCD DIS",
    "RF (Россия)": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME NVTK.ME GMKN.ME TATN.ME CHMF.ME ALRS.ME MTSS.ME PLZL.ME MOEX.ME SNGS.ME MAGN.ME AFLT.ME RTKM.ME FEES.ME CBOM.ME",
    "KAZ (Казахстан)": "KCZ.L KMGZ.KZ HSBK.KZ KCELL.KZ NAC.KZ CCBN.KZ KZAP.KZ KEGC.KZ KZTK.KZ KZTO.KZ ASBN.KZ BAST.KZ",
    "CHINA": "BABA BIDU JD PDD LI NIO TCEHY BYDDY XPEV NTES MCHI KWEB FUTU BILI VIPS KC TME IQ EH ZLAB GDS",
    "EUROPE": "ASML MC.PA VOW3.DE NESN.SW SIE.DE SAP.DE AIR.PA RMS.PA MBG.DE DHL.DE SAN.MC ALV.DE CS.PA BBVA.MC NOVO-B.CO",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD XRP-USD LINK-USD AVAX-USD DOGE-USD MATIC-USD TRX-USD LTC-USD UNI-USD SHIB-USD NEAR-USD"
}

@st.cache_data(ttl=300)
def get_market_data(m_name):
    tickers = MARKETS[m_name]
    data = yf.download(tickers, period="1y", group_by='ticker', progress=False)
    rates_raw = yf.download(["RUB=X", "KZT=X"], period="1d", progress=False)['Close']
    r_map = {"₽": float(rates_raw["RUB=X"].iloc[-1]), "₸": float(rates_raw["KZT=X"].iloc[-1]), "$": 1.0}
    
    results = []
    for t in tickers.split():
        try:
            # Обработка структуры yfinance для одного или нескольких тикеров
            df = data[t].dropna() if len(tickers.split()) > 1 else data.dropna()
            if df.empty: continue
            
            is_rub, is_kzt = ".ME" in t, (".KZ" in t or "KCZ" in t)
            conv = r_map["₽"] if is_rub else r_map["₸"] if is_kzt else 1.0
            
            results.append({
                "ticker": t,
                "price_usd": float(df['Close'].iloc[-1]) / conv,
                "history_usd": (df['Close'].values / conv)[-30:],
                "vol": float(df['Close'].pct_change().std()),
                "trend": (df['Close'].iloc[-1] - df['Close'].iloc[-15]) / conv / 15
            })
        except: continue
    return results, r_map

# --- SIDEBAR ---
st.sidebar.title("🛡️ ABI CONTROL")
market_choice = st.sidebar.selectbox("ВЫБОР РЕГИОНА:", list(MARKETS.keys()))
if market_choice != st.session_state.last_market:
    show_dino()
    st.session_state.last_market = market_choice

currency_choice = st.sidebar.radio("ВАЛЮТА:", ["USD ($)", "RUB (₽)", "KZT (₸)"])
user_capital = st.sidebar.number_input("ВАШ КАПИТАЛ:", value=1000)

assets, rates = get_market_data(market_choice)
curr_sym = currency_choice.split("(")[1][0]
rate_mult = rates[curr_sym]

# --- ОСНОВНОЙ ИНТЕРФЕЙС ---
st.title(f"🚀 TERMINAL: {market_choice}")

if assets:
    # 1. ВЕРТИКАЛЬНЫЙ ТОП-25 НАД ВЫБОРОМ
    st.markdown(f"### 📊 TOP-25 ASSETS ({market_choice})")
    with st.container():
        df_display = pd.DataFrame(assets)
        df_display["Цена"] = (df_display["price_usd"] * rate_mult).round(2)
        # Показываем вертикальную таблицу с прокруткой
        st.dataframe(df_display[["ticker", "Цена"]].set_index("ticker"), height=300, use_container_width=True)

    st.divider()

    # 2. ВЫБОР АКТИВА И АНАЛИЗ
    selected_ticker = st.selectbox("ВЫБЕРИТЕ АКТИВ ДЛЯ ДЕТАЛЬНОГО ПРОГНОЗА:", [a['ticker'] for a in assets])
    asset = next(a for a in assets if a['ticker'] == selected_ticker)
    
    p_now = asset['price_usd'] * rate_mult
    
    # Прогноз (Fix axis size)
    np.random.seed(42)
    forecast = [p_now]
    for _ in range(1, 15):
        noise = np.random.normal(0, p_now * asset['vol'] * 0.5)
        forecast.append(max(forecast[-1] + (asset['trend'] * rate_mult) + noise, 0.01))

    # Метрики
    chg = ((forecast[-1]/p_now)-1)*100
    res_color = "#00ffcc" if chg > 2 else "#ff4b4b" if chg < -2 else "#888888"
    
    m1, m2, m3 = st.columns(3)
    m1.markdown(f"<div class='metric-card'>ТЕКУЩАЯ<br><h2>{p_now:,.2f} {curr_sym}</h2></div>", unsafe_allow_html=True)
    m2.markdown(f"<div class='metric-card'>ПРОГНОЗ (14Д)<br><h2 style='color:{res_color} !important;'>{forecast[-1]:,.2f} {curr_sym}</h2></div>", unsafe_allow_html=True)
    
    profit = (forecast[-1] * (user_capital/p_now * rate_mult)) - (user_capital * rate_mult)
    m3.markdown(f"<div class='metric-card'>ПРОФИТ<br><h2>{profit:,.2f} {curr_sym}</h2></div>", unsafe_allow_html=True)

    # ГРАФИК (БЕЗ ОШИБОК)
    fig, ax = plt.subplots(figsize=(12, 5), facecolor='none')
    ax.set_facecolor('none')
    
    h_data = [x * rate_mult for x in asset['history_usd']]
    # История
    ax.plot(range(len(h_data)), h_data, color='white', alpha=0.3, label="История")
    # Прогноз (стыкуем с последней точкой истории)
    ax.plot(range(len(h_data)-1, len(h_data)+14), forecast, color=res_color, linewidth=4, marker='o', markersize=6, label="ABI Forecast")
    
    ax.tick_params(colors='white')
    ax.grid(color='#222222', alpha=0.3)
    st.pyplot(fig)
    
    st.markdown(f"<h2 style='text-align:center; color:{res_color} !important;'>РЕКОМЕНДАЦИЯ: {'BUY' if chg > 2 else 'SELL' if chg < -2 else 'HOLD'}</h2>", unsafe_allow_html=True)
