import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time

# --- НАСТРОЙКИ СТРАНИЦЫ (БЕЗ ФОНА) ---
st.set_page_config(page_title="ABI Quantum", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; } /* Возвращаем чистый темный фон */
    .metric-card {
        background: rgba(10, 15, 25, 0.95); border-left: 5px solid #00ffcc;
        padding: 20px; border-radius: 10px; margin-bottom: 10px;
    }
    .dino-container {
        background-color: white; border-radius: 20px; padding: 40px; 
        text-align: center; margin-top: 20px;
    }
    .recommendation-bar {
        text-align: center; padding: 20px; border-radius: 10px;
        font-size: 28px; font-weight: bold; margin-top: 20px;
        border: 2px solid;
    }
    h1, h2, h3 { color: #00ffcc !important; font-family: 'Courier New', monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- РЫНКИ (ЕВРОПА ВЕРНУЛАСЬ) ---
MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC ADBE CRM AVGO QCOM PYPL TSMC ASML BABA COST PEP NKE TM ORCL MCD DIS",
    "KAZ (Казахстан)": "KCZ.L KMGZ.KZ HSBK.KZ KCELL.KZ NAC.KZ CCBN.KZ KZAP.KZ KEGC.KZ KZTK.KZ KZTO.KZ ASBN.KZ BAST.KZ KMGD.KZ",
    "EUROPE": "ASML MC.PA VOW3.DE NESN.SW SIE.DE SAP.DE AIR.PA RMS.PA MBG.DE DHL.DE SAN.MC ALV.DE CS.PA BBVA.MC NOVO-B.CO",
    "RF (Россия)": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME NVTK.ME GMKN.ME TATN.ME CHMF.ME ALRS.ME MTSS.ME PLZL.ME MOEX.ME SNGS.ME MAGN.ME",
    "CHINA": "BABA BIDU JD PDD LI NIO TCEHY BYDDY XPEV NTES MCHI KWEB FUTU BILI VIPS KC TME IQ EH ZLAB GDS",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD XRP-USD LINK-USD AVAX-USD DOGE-USD MATIC-USD TRX-USD LTC-USD"
}

@st.cache_data(ttl=300)
def fetch_data(m_name):
    try:
        tickers = MARKETS[m_name]
        data = yf.download(tickers, period="1y", group_by='ticker', progress=False)
        rates = yf.download(["RUB=X", "KZT=X", "EURUSD=X"], period="1d", progress=False)['Close']
        r_map = {
            "₽": float(rates["RUB=X"].iloc[-1]), 
            "₸": float(rates["KZT=X"].iloc[-1]), 
            "$": 1.0
        }
        
        res = []
        for t in tickers.split():
            try:
                df = data[t].dropna() if len(tickers.split()) > 1 else data.dropna()
                if df.empty: continue
                # Конвертация для Европы, РФ и Казахстана
                conv = r_map["₽"] if ".ME" in t else r_map["₸"] if (".KZ" in t or "KCZ" in t) else 1.0
                res.append({
                    "Asset": t, "p_usd": float(df['Close'].iloc[-1]) / conv,
                    "hist": (df['Close'].values / conv)[-30:],
                    "vol": float(df['Close'].pct_change().std()),
                    "trend": (df['Close'].iloc[-1] - df['Close'].iloc[-15]) / conv / 15
                })
            except: continue
        return res, r_map
    except:
        return [], {}

# --- ПАНЕЛЬ УПРАВЛЕНИЯ ---
st.sidebar.title("🛡️ ABI CONTROL")
m_sel = st.sidebar.selectbox("ВЫБОР РЕГИОНА:", list(MARKETS.keys()))
c_sel = st.sidebar.radio("ВАЛЮТА:", ["USD ($)", "RUB (₽)", "KZT (₸)"])
cap = st.sidebar.number_input("КАПИТАЛ:", value=1000)

assets, rates = fetch_data(m_sel)

# --- ГЛАВНЫЙ ЭКРАН ---
if not assets:
    # ДИНОЗАВРИК, ЕСЛИ ДАННЫХ НЕТ (ФИКС ОШИБОК ИЗ СКРИНШОТОВ)
    st.markdown(f"""
        <div class="dino-container">
            <h1 style="color: black !important;">ДАННЫЕ ПО {m_sel} НЕ НАЙДЕНЫ</h1>
            <img src="https://i.gifer.com/V96u.gif" width="300">
            <p style="color: #666; font-size: 20px; font-weight: bold; margin-top: 20px;">ДИНОЗАВРИК ГРУСТИТ, НО ЖДЕТ ОБНОВЛЕНИЯ...</p>
        </div>
    """, unsafe_allow_html=True)
else:
    c_sym = c_sel.split("(")[1][0]
    r_val = rates[c_sym]
    
    st.title(f"🚀 TOP-25: {m_sel}")
    
    # 1. ТОП-25 (НУМЕРОВАННЫЙ И ЧИТАЕМЫЙ)
    df_top = pd.DataFrame(assets).head(25)
    df_top["Цена"] = (df_top["p_usd"] * r_val).round(2)
    df_top.index = np.arange(1, len(df_top) + 1)
    df_top.index.name = "№"
    st.dataframe(df_top[["Asset", "Цена"]], height=350, use_container_width=True)

    st.divider()

    # 2. АНАЛИЗ
    target = st.selectbox("ВЫБЕРИТЕ АКТИВ:", df_top["Asset"].tolist())
    item = next(a for a in assets if a['Asset'] == target)
    p_now = item['p_usd'] * r_val
    
    np.random.seed(42)
    forecast = [p_now]
    for _ in range(1, 15):
        noise = np.random.normal(0, p_now * item['vol'] * 0.5)
        forecast.append(max(forecast[-1] + (item['trend'] * r_val) + noise, 0.01))

    diff = ((forecast[-1]/p_now)-1)*100
    clr = "#00ffcc" if diff > 2 else "#ff4b4b" if diff < -2 else "#888888"
    sig = "ПОКУПАТЬ" if diff > 2 else "ПРОДАВАТЬ" if diff < -2 else "УДЕРЖИВАТЬ"

    col1, col2, col3 = st.columns(3)
    col1.markdown(f"<div class='metric-card'>СЕЙЧАС<br><h2>{p_now:,.2f} {c_sym}</h2></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='metric-card'>ЦЕЛЬ (14Д)<br><h2 style='color:{clr} !important;'>{forecast[-1]:,.2f} {c_sym}</h2></div>", unsafe_allow_html=True)
    
    gain = (forecast[-1] * (cap/p_now * r_val)) - (cap * r_mult if 'r_mult' in locals() else cap * r_val)
    col3.markdown(f"<div class='metric-card'>ПРОФИТ<br><h2>{gain:,.2f} {c_sym}</h2></div>", unsafe_allow_html=True)

    # ГРАФИК
    fig, ax = plt.subplots(figsize=(12, 4), facecolor='none')
    ax.set_facecolor('none')
    ax.plot(range(30), [x * r_val for x in item['hist']], color='white', alpha=0.3)
    ax.plot(range(29, 44), forecast, color=clr, linewidth=4, marker='o')
    ax.tick_params(colors='white')
    st.pyplot(fig)

    # СИГНАЛ
    st.markdown(f"""
        <div class="recommendation-bar" style="color: {clr}; border-color: {clr};">
            РЕКОМЕНДАЦИЯ: {sig}
        </div>
    """, unsafe_allow_html=True)
