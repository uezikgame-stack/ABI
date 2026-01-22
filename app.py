import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. КИБЕРПАНК СТИЛЬ (НЕОНОВЫЕ ЛИНИИ) ---
st.set_page_config(page_title="ABI ANALITIC", layout="wide")
st.markdown("""
    <style>
    /* Анимированный фон */
    .stApp {
        background: linear-gradient(135deg, #020508 25%, #050a10 50%, #020508 75%);
        background-size: 400% 400%;
        animation: gradientMove 15s ease infinite;
        color: #00ffcc;
        overflow: hidden;
    }
    
    /* Неоновые линии на фоне */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background: repeating-linear-gradient(
            0deg,
            transparent,
            transparent 50px,
            rgba(0, 255, 204, 0.03) 50px,
            rgba(0, 255, 204, 0.03) 51px
        );
        animation: linesMove 20s linear infinite;
        z-index: 0;
        pointer-events: none;
    }

    @keyframes gradientMove { 0% {background-position: 0% 50%} 50% {background-position: 100% 50%} 100% {background-position: 0% 50%} }
    @keyframes linesMove { from {transform: translateY(0);} to {transform: translateY(50px);} }

    .metric-card { background: rgba(0, 0, 0, 0.85); border: 1px solid #00ffcc; padding: 15px; text-align: center; min-height: 110px; position: relative; z-index: 1; }
    .error-card { background: rgba(255, 75, 75, 0.1); border: 1px solid #ff4b4b; padding: 25px; text-align: center; position: relative; z-index: 1; }
    h1, h2, h3, span, label, p { color: #00ffcc !important; }
    [data-testid="stSidebar"] { background-color: rgba(10, 14, 20, 0.95) !important; z-index: 2; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. РЫНКИ ---
DB = {
    "KAZ (Казахстан)": ["KCZ.L", "KMGZ.KZ", "HSBK.KZ", "KCELL.KZ", "NAC.KZ", "CCBN.KZ", "KEGC.KZ", "KZTK.KZ", "KZTO.KZ", "ASBN.KZ", "BAST.KZ", "KMCP.KZ", "KASE.KZ", "KZIP.KZ", "KZMZ.KZ"],
    "EUROPE": ["ASML", "MC.PA", "VOW3.DE", "NESN.SW", "SIE.DE", "SAP.DE", "AIR.PA", "RMS.PA", "MBG.DE", "DHL.DE", "SAN.MC", "ALV.DE", "CS.PA", "BBVA.MC", "OR.PA"],
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "NFLX", "GOOGL", "META", "INTC", "ADBE", "CRM", "AVGO", "QCOM", "PYPL"],
    "RF (Россия)": ["SBER.ME", "GAZP.ME", "LKOH.ME", "YNDX", "ROSN.ME", "MGNT.ME", "NVTK.ME", "GMKN.ME", "CHMF.ME", "PLZL.ME", "TATN.ME", "MTSS.ME", "ALRS.ME", "AFLT.ME", "MAGN.ME"],
    "CRYPTO": ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "DOGE-USD", "DOT-USD", "MATIC-USD", "LTC-USD", "SHIB-USD", "TRX-USD", "AVAX-USD", "UNI-USD", "LINK-USD"]
}

@st.cache_data(ttl=600)
def get_data_engine(m_name):
    try:
        tickers = DB[m_name]
        data = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', progress=False)
        rates_df = yf.download(["RUB=X", "KZT=X", "EURUSD=X"], period="1d", progress=False)['Close']
        r_map = {"₽": float(rates_df["RUB=X"].iloc[-1]), "$": 1.0, "₸": float(rates_df["KZT=X"].iloc[-1]), "EUR": float(rates_df["EURUSD=X"].iloc[-1])}
        
        clean = []
        for t in tickers:
            try:
                df = data[t].dropna()
                if df.empty: continue
                if any(x in t for x in [".ME", "YNDX"]): b = "₽"
                elif any(x in t for x in [".KZ", "KCZ"]): b = "₸"
                elif any(x in t for x in [".PA", ".DE", ".MC"]): b = "EUR"
                else: b = "$"
                curr_p = float(df['Close'].iloc[-1])
                p_usd = curr_p / r_map[b] if b != "EUR" else curr_p * r_map["EUR"]
                clean.append({"T": t, "P_USD": p_usd, "CH": (df['Close'].iloc[-1]/df['Close'].iloc[0]-1), "AVG": df['Close'].pct_change().mean(), "STD": df['Close'].pct_change().std(), "DF": df})
            except: continue
        return clean, r_map
    except: return None, None

# --- 3. ИНТЕРФЕЙС ---
st.sidebar.title("ABI SETTINGS")
m_sel = st.sidebar.selectbox("MARKET", list(DB.keys()))
c_sel = st.sidebar.radio("CURRENCY", ["USD ($)", "RUB (₽)", "KZT (₸)"])
cap_val = st.sidebar.number_input("CAPITAL", value=1000)

assets, rates = get_data_engine(m_sel)
st.title("🚀 ABI ANALITIC")

if not assets:
    # --- ИСПРАВЛЕННЫЙ БЛОК: ТОЛЬКО ДИНО (БЕЗ ЛИШНЕГО ТЕКСТА) ---
    st.markdown("""
        <div class='error-card'>
            <h1>⚠️ РЕГИОН ВРЕМЕННО НЕДОСТУПЕН</h1>
            <iframe src="https://chromedino.com/" frameborder="0" scrolling="no" width="100%" height="300" style="border:none; filter: invert(1); margin-top: 20px;"></iframe>
        </div>
    """, unsafe_allow_html=True)
else:
    sign = c_sel.split("(")[1][0]
    r_target = rates[sign]

    df_top = pd.DataFrame(assets)
    df_top["PRICE"] = (df_top["P_USD"] * r_target).apply(lambda x: f"{x:,.2f} {sign}")
    df_top = df_top.sort_values(by="CH", ascending=False).head(15).reset_index(drop=True)
    df_top.index += 1
    
    st.subheader(f"ТОП 15 АКТИВОВ ({sign})")
    st.dataframe(df_top[["T", "PRICE"]], use_container_width=True, height=450)

    t_name = st.selectbox("ВЫБЕРИ ДЛЯ АНАЛИЗА:", df_top["T"].tolist())
    item = next(x for x in assets if x['T'] == t_name)

    if "f_usd" not in st.session_state or st.session_state.get("last_t") != t_name:
        mu, sigma = item['AVG'], item['STD'] if item['STD'] > 0 else 0.015
        st.session_state.f_usd = [item['P_USD'] * (1 + np.random.normal(mu, sigma)) for _ in range(7)]
        st.session_state.last_t = t_name

    p_now = item['P_USD'] * r_target
    f_prices = [p * r_target for p in st.session_state.f_usd]
    final_profit_pct = ((f_prices[-1] / p_now) - 1) * 100

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'>ТЕКУЩАЯ<br><h3>{p_now:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>ЦЕЛЬ (7д)<br><h3>{f_prices[-1]:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    style = "error-card" if final_profit_pct < 0 else "metric-card"
    c3.markdown(f"<div class='{style}'>ПРОФИТ (%)<br><h3>{final_profit_pct:+.2f} %</h3></div>", unsafe_allow_html=True)

    st.divider()
    col_g, col_t = st.columns([2, 1])
    with col_g:
        hist = (item['DF']['Close'].tail(14).values / (item['P_USD'] / p_now))
        st.line_chart(np.append(hist, f_prices), color="#00ffcc")

    with col_t:
        table_df = pd.DataFrame({
            "ДЕНЬ": [f"День {i+1}" for i in range(7)],
            "ЦЕНА": [f"{p:,.2f} {sign}" for p in f_prices],
            "ПРОФИТ (%)": [f"{((p/p_now)-1)*100:+.2f} %" for p in f_prices]
        })
        st.write(f"### ПРОГНОЗ В {sign}")
        st.dataframe(table_df, hide_index=True, use_container_width=True)

    sig = "ПРОДАВАТЬ" if final_profit_pct < 0 else "ПОКУПАТЬ"
    st.markdown(f"<h2 style='text-align:center; color:{'#ff4b4b' if final_profit_pct < 0 else '#00ffcc'} !important; border: 2px solid;'>СИГНАЛ: {sig}</h2>", unsafe_allow_html=True)
