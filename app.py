import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time

# --- НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(page_title="ABI Terminal", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    /* Стиль для полноценного отображения названий */
    .stDataFrame div[data-testid="stTable"] { width: 100%; }
    .metric-card {
        background: rgba(10, 15, 25, 0.95); border-left: 5px solid #00ffcc;
        padding: 20px; border-radius: 10px; margin-bottom: 10px;
    }
    h1, h2, h3 { color: #00ffcc !important; font-family: 'Courier New', monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- ВОЗВРАЩЕНИЕ ДИНОЗАВРИКА (ФИКСИРОВАННЫЙ ЛОАДЕР) ---
# Теперь он будет появляться ВСЕГДА при инициализации или смене рынка
def run_dino_loader():
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("""
            <div style="background-color: white; height: 100vh; width: 100vw; position: fixed; top: 0; left: 0; z-index: 9999; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                <h1 style="color: black !important; font-family: 'Courier New', monospace; margin-bottom: 20px;">ABI QUANTUM LOADING...</h1>
                <img src="https://i.gifer.com/V96u.gif" width="300">
                <p style="color: #444; font-size: 20px; margin-top: 30px; font-weight: bold;">ПОДГОТОВКА ДАННЫХ ТОП-25...</p>
            </div>
            """, unsafe_allow_html=True)
        time.sleep(3) # Увеличил время, чтобы ты успел насладиться динозавриком
    placeholder.empty()

if 'first_run' not in st.session_state:
    run_dino_loader()
    st.session_state.first_run = True

# --- РЫНКИ (ТОП-25) ---
MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC ADBE CRM AVGO QCOM PYPL TSMC ASML BABA COST PEP NKE TM ORCL MCD DIS",
    "RF (Россия)": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME NVTK.ME GMKN.ME TATN.ME CHMF.ME ALRS.ME MTSS.ME PLZL.ME MOEX.ME SNGS.ME MAGN.ME AFLT.ME RTKM.ME FEES.ME CBOM.ME AFKS.ME LENT.ME VTBR.ME GAZP.ME TRNFP.ME",
    "CHINA": "BABA BIDU JD PDD LI NIO TCEHY BYDDY XPEV NTES MCHI KWEB FUTU BILI VIPS KC TME IQ EH ZLAB GDS LI ANGI TAL EDU",
    "EUROPE": "ASML MC.PA VOW3.DE NESN.SW SIE.DE SAP.DE AIR.PA RMS.PA MBG.DE DHL.DE SAN.MC ALV.DE CS.PA BBVA.MC NOVO-B.CO LVMUY AD.AS",
    "KAZ (Казахстан)": "KCZ.L KMGZ.KZ HSBK.KZ KCELL.KZ NAC.KZ CCBN.KZ KZAP.KZ KEGC.KZ KZTK.KZ KZTO.KZ ASBN.KZ BAST.KZ KMGD.KZ",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD XRP-USD LINK-USD AVAX-USD DOGE-USD MATIC-USD TRX-USD LTC-USD UNI-USD SHIB-USD NEAR-USD ATOM-USD"
}

@st.cache_data(ttl=300)
def fetch_data(m_name):
    tickers = MARKETS[m_name]
    data = yf.download(tickers, period="1y", group_by='ticker', progress=False)
    rates = yf.download(["RUB=X", "KZT=X"], period="1d", progress=False)['Close']
    r_map = {"₽": float(rates["RUB=X"].iloc[-1]), "₸": float(rates["KZT=X"].iloc[-1]), "$": 1.0}
    
    res = []
    for t in tickers.split():
        try:
            df = data[t].dropna() if len(tickers.split()) > 1 else data.dropna()
            if df.empty: continue
            is_rub, is_kzt = ".ME" in t, (".KZ" in t or "KCZ" in t)
            conv = r_map["₽"] if is_rub else r_map["₸"] if is_kzt else 1.0
            res.append({
                "Asset": t,
                "Price_USD": float(df['Close'].iloc[-1]) / conv,
                "History": (df['Close'].values / conv)[-30:],
                "Vol": float(df['Close'].pct_change().std()),
                "Trend": (df['Close'].iloc[-1] - df['Close'].iloc[-15]) / conv / 15
            })
        except: continue
    return res, r_map

# --- БОКОВАЯ ПАНЕЛЬ ---
st.sidebar.title("🛡️ ABI CONTROL")
m_select = st.sidebar.selectbox("РЕГИОН:", list(MARKETS.keys()))

# Если сменили регион — запускаем динозавра
if 'last_m' not in st.session_state or st.session_state.last_m != m_select:
    run_dino_loader()
    st.session_state.last_m = m_select

c_select = st.sidebar.radio("ВАЛЮТА:", ["USD ($)", "RUB (₽)", "KZT (₸)"])
capital = st.sidebar.number_input("КАПИТАЛ:", value=1000)

assets, rates_map = fetch_data(m_select)
curr_char = c_select.split("(")[1][0]
rate = rates_map[curr_char]

# --- ГЛАВНЫЙ ЭКРАН ---
st.title(f"🚀 TOP-25: {m_select}")

if assets:
    # 1. ЧЕТКИЙ НУМЕРОВАННЫЙ ТОП
    st.markdown("### 🏆 РЕЙТИНГ АКТИВОВ")
    df_top = pd.DataFrame(assets).head(25)
    df_top["Цена"] = (df_top["Price_USD"] * rate).round(2)
    
    # Добавляем номера (1, 2, 3...)
    df_top.index = np.arange(1, len(df_top) + 1)
    df_top.index.name = "№"
    
    # Показываем таблицу (увеличил высоту, чтобы названия не жались)
    st.dataframe(df_top[["Asset", "Цена"]], height=400, use_container_width=True)

    st.divider()

    # 2. АНАЛИЗ
    target = st.selectbox("ВЫБЕРИТЕ ИЗ ТОПА ДЛЯ ПРОГНОЗА:", df_top["Asset"].tolist())
    item = next(a for a in assets if a['Asset'] == target)
    
    p_now = item['Price_USD'] * rate
    np.random.seed(42)
    forecast = [p_now]
    for _ in range(1, 15):
        noise = np.random.normal(0, p_now * item['Vol'] * 0.5)
        forecast.append(max(forecast[-1] + (item['Trend'] * rate) + noise, 0.01))

    # Виджеты
    diff = ((forecast[-1]/p_now)-1)*100
    clr = "#00ffcc" if diff > 2 else "#ff4b4b" if diff < -2 else "gray"
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'>ЦЕНА<br><h2>{p_now:,.2f} {curr_char}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>ЦЕЛЬ 14Д<br><h2 style='color:{clr} !important;'>{forecast[-1]:,.2f} {curr_char}</h2></div>", unsafe_allow_html=True)
    
    gain = (forecast[-1] * (capital/p_now * rate)) - (capital * rate)
    c3.markdown(f"<div class='metric-card'>ВАШ ПРОФИТ<br><h2>{gain:,.2f} {curr_char}</h2></div>", unsafe_allow_html=True)

    # ГРАФИК
    fig, ax = plt.subplots(figsize=(12, 4), facecolor='none')
    ax.set_facecolor('none')
    h_vals = [x * rate for x in item['History']]
    ax.plot(range(len(h_vals)), h_vals, color='white', alpha=0.3)
    ax.plot(range(len(h_vals)-1, len(h_vals)+14), forecast, color=clr, linewidth=4, marker='o')
    ax.tick_params(colors='white')
    st.pyplot(fig)
