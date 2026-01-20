import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time

# --- ИНТЕРФЕЙС И СТИЛЬ ---
st.set_page_config(page_title="ABI Terminal", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .metric-card {
        background: rgba(10, 15, 25, 0.95); border-left: 5px solid #00ffcc;
        padding: 20px; border-radius: 10px; margin-bottom: 10px;
    }
    .top-table { margin-bottom: 30px; border: 1px solid #00ffcc33; border-radius: 10px; }
    h1, h2, h3 { color: #00ffcc !important; font-family: 'Courier New', monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- БЕЛЫЙ ЗАГРУЗЧИК С ДИНОЗАВРИКОМ ---
if 'initialized' not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("""
            <div style="background-color: white; height: 100vh; width: 100vw; position: fixed; top: 0; left: 0; z-index: 9999; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                <h1 style="color: black !important; font-family: Arial;">ABI QUANTUM BOOTING...</h1>
                <img src="https://i.gifer.com/V96u.gif" width="200">
                <p style="color: #666; margin-top: 20px;">Загрузка Топ-25 мировых активов...</p>
            </div>
            """, unsafe_allow_html=True)
        time.sleep(2.5)
    st.session_state.initialized = True
    placeholder.empty()

# --- ПОЛНЫЙ СПИСОК РЕГИОНОВ (ТОП-25) ---
MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC ADBE CRM AVGO QCOM PYPL TSMC ASML BABA COST PEP NKE TM ORCL MCD",
    "RF (Россия)": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME NVTK.ME GMKN.ME TATN.ME CHMF.ME ALRS.ME MTSS.ME PLZL.ME MOEX.ME SNGS.ME MAGN.ME TRNFP.ME CBOM.ME AFLT.ME PIKK.ME FEES.ME HYDR.ME AFKS.ME RTKM.ME LENT.ME",
    "KAZ (Казахстан)": "KCZ.L KMGZ.KZ HSBK.KZ KCELL.KZ NAC.KZ CCBN.KZ KZAP.KZ KEGC.KZ KZTK.KZ KZTO.KZ ASBN.KZ BAST.KZ KMGD.KZ",
    "CHINA": "BABA BIDU JD PDD LI NIO TCEHY BYDDY XPEV NTES MCHI KWEB FUTU BILI VIPS KC TME IQ EH ZLAB GDS LI ANGI",
    "EUROPE": "ASML MC.PA VOW3.DE NESN.SW SIE.DE SAP.DE AIR.PA RMS.PA MBG.DE DHL.DE SAN.MC ALV.DE CS.PA BBVA.MC NOVO-B.CO LVMUY",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD XRP-USD LINK-USD AVAX-USD DOGE-USD MATIC-USD TRX-USD LTC-USD UNI-USD SHIB-USD BCH-USD NEAR-USD ATOM-USD XMR-USD XLM-USD ALGO-USD"
}

@st.cache_data(ttl=300)
def load_market_data(m_name):
    tickers = MARKETS[m_name]
    raw_data = yf.download(tickers, period="1y", group_by='ticker', progress=False)
    # Актуальные курсы
    rates_raw = yf.download(["RUB=X", "KZT=X"], period="1d", progress=False)['Close']
    r_map = {"₽": float(rates_raw["RUB=X"].iloc[-1]), "₸": float(rates_raw["KZT=X"].iloc[-1]), "$": 1.0}
    
    final_list = []
    for t in tickers.split():
        try:
            node = raw_data[t].dropna()
            if node.empty: continue
            # Конвертация в USD для базы
            is_rub, is_kzt = ".ME" in t, (".KZ" in t or "KCZ" in t)
            c_val = r_map["₽"] if is_rub else r_map["₸"] if is_kzt else 1.0
            
            final_list.append({
                "ticker": t,
                "p_base": float(node['Close'].iloc[-1]) / c_val,
                "history": (node['Close'].values / c_val)[-30:],
                "vol": float(node['Close'].pct_change().std()),
                "trend": (node['Close'].iloc[-1] - node['Close'].iloc[-15]) / c_val / 15
            })
        except: continue
    return final_list, r_map

# --- SIDEBAR ---
st.sidebar.title("🛡️ ABI CONTROL")
sel_market = st.sidebar.selectbox("ВЫБОР РЕГИОНА:", list(MARKETS.keys()))
sel_curr = st.sidebar.radio("ВАЛЮТА:", ["USD ($)", "RUB (₽)", "KZT (₸)"])
capital = st.sidebar.number_input("ВАШ КАПИТАЛ:", value=1000)

assets, rates = load_market_data(sel_market)
curr_tag = sel_curr.split("(")[1][0]
rate_mult = rates[curr_tag]

# --- ГЛАВНЫЙ ИНТЕРФЕЙС ---
st.title(f"📊 TOP-25 ASSETS: {sel_market}")

if assets:
    # 1. ТОП-25 НАД ВЫБОРОМ АКТИВА
    df_top = pd.DataFrame(assets).head(25)
    df_top["Цена"] = (df_top["p_base"] * rate_mult).round(2)
    st.dataframe(df_top[["ticker", "Цена"]].set_index("ticker").T, use_container_width=True)

    st.divider()

    # 2. ВЫБОР И АНАЛИЗ
    target_ticker = st.selectbox("ВЫБЕРИТЕ АКТИВ ИЗ СПИСКА ВЫШЕ:", [a['ticker'] for a in assets])
    active_asset = next(a for a in assets if a['ticker'] == target_ticker)
    
    p_now = active_asset['p_base'] * rate_mult
    
    # Расчет прогноза (Fix ValueError)
    np.random.seed(42)
    prediction = [p_now]
    for _ in range(1, 15):
        noise = np.random.normal(0, p_now * active_asset['vol'] * 0.5)
        prediction.append(max(prediction[-1] + (active_asset['trend'] * rate_mult) + noise, 0.01))

    # Визуализация
    chg_pct = ((prediction[-1]/p_now)-1)*100
    res_color = "#00ffcc" if chg_pct > 3 else "#ff4b4b" if chg_pct < -3 else "#888888"
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'>СЕЙЧАС<br><h2>{p_now:,.2f} {curr_tag}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>ЦЕЛЬ (14Д)<br><h2 style='color:{res_color} !important;'>{prediction[-1]:,.2f} {curr_tag}</h2></div>", unsafe_allow_html=True)
    
    my_profit = (prediction[-1] * (capital/p_now * rate_mult)) - (capital * rate_mult)
    c3.markdown(f"<div class='metric-card'>ПРИБЫЛЬ<br><h2>{my_profit:,.2f} {curr_tag}</h2></div>", unsafe_allow_html=True)

    # График
    fig, ax = plt.subplots(figsize=(12, 4), facecolor='none')
    ax.set_facecolor('none')
    h_prices = [h * rate_mult for h in active_asset['history']]
    
    ax.plot(range(len(h_prices)), h_prices, color='white', alpha=0.3)
    ax.plot(range(len(h_prices)-1, len(h_prices)+14), prediction, color=res_color, linewidth=4, marker='o')
    
    ax.tick_params(colors='white')
    st.pyplot(fig)
    
    st.markdown(f"<h2 style='text-align:center; color:{res_color} !important;'>РЕКОМЕНДАЦИЯ: {'BUY' if chg_pct > 3 else 'SELL' if chg_pct < -3 else 'HOLD'}</h2>", unsafe_allow_html=True)
