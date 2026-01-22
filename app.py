import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. КИБЕРПАНК СТИЛЬ ШЭФА ---
st.set_page_config(page_title="ABI ANALITIC", layout="wide")
st.markdown("""
    <style>
    .stApp {
        background-color: #020508 !important;
        background-image: 
            linear-gradient(rgba(0, 255, 204, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 255, 204, 0.1) 1px, transparent 1px);
        background-size: 50px 50px;
        animation: moveGrid 15s linear infinite;
        color: #00ffcc;
    }
    @keyframes moveGrid { from { background-position: 0 0; } to { background-position: 50px 50px; } }

    .unified-card {
        background: rgba(0, 0, 0, 0.95);
        border: 2px solid #ff4b4b;
        border-radius: 15px;
        padding: 30px;
        text-align: center;
        margin-top: 20px;
        box-shadow: 0 0 25px rgba(255, 75, 75, 0.3);
    }

    .dino-crop {
        overflow: hidden;
        height: 180px;
        width: 100%;
        margin-top: 20px;
        border-radius: 8px;
        position: relative;
        background: black;
    }
    .dino-crop iframe {
        position: absolute;
        top: -105px; 
        left: 0;
        width: 100%;
        height: 400px;
        filter: invert(1) hue-rotate(180deg) contrast(1.4);
    }

    .metric-card { background: rgba(0, 0, 0, 0.9); border: 1px solid #00ffcc; padding: 15px; text-align: center; border-radius: 10px; }
    h1, h2, h3, span, label, p { color: #00ffcc !important; }
    [data-testid="stSidebar"] { background-color: rgba(10, 14, 20, 0.95) !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ДАННЫЕ ---
DB = {
    "KAZ (Казахстан)": ["KCZ.L", "KMGZ.KZ", "HSBK.KZ", "KCELL.KZ", "NAC.KZ", "CCBN.KZ", "KEGC.KZ", "KZTK.KZ", "KZTO.KZ"],
    "EUROPE": ["ASML", "MC.PA", "VOW3.DE", "NESN.SW", "SIE.DE", "SAP.DE", "AIR.PA", "RMS.PA"],
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "NFLX", "GOOGL"],
    "RF (Россия)": ["SBER.ME", "GAZP.ME", "LKOH.ME", "YNDX", "ROSN.ME", "MGNT.ME"],
    "CRYPTO": ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD"]
}

@st.cache_data(ttl=300)
def load_data(m_name):
    try:
        tickers = DB[m_name]
        data = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', progress=False)
        rates_df = yf.download(["RUB=X", "KZT=X"], period="1d", progress=False)['Close']
        r_map = {"₽": float(rates_df["RUB=X"].iloc[-1]), "$": 1.0, "₸": float(rates_df["KZT=X"].iloc[-1])}
        
        clean = []
        for t in tickers:
            try:
                df = data[t].dropna()
                if df.empty: continue
                b = "₽" if ".ME" in t or t == "YNDX" else ("₸" if ".KZ" in t or "KCZ" in t else "$")
                curr_p = float(df['Close'].iloc[-1])
                p_usd = curr_p / r_map[b]
                clean.append({"T": t, "P_USD": p_usd, "CH": (df['Close'].iloc[-1]/df['Close'].iloc[0]-1), "AVG": df['Close'].pct_change().mean(), "STD": df['Close'].pct_change().std(), "DF": df})
            except: continue
        return clean, r_map
    except: return None, None

# --- 3. ИНТЕРФЕЙС ШЭФА ---
st.sidebar.title("ABI SETTINGS")
m_sel = st.sidebar.selectbox("MARKET", list(DB.keys()))
c_sel = st.sidebar.radio("CURRENCY", ["USD ($)", "RUB (₽)", "KZT (₸)"])

assets, rates = load_data(m_sel)
st.title("🚀 ABI ANALITIC")

if not assets:
    st.markdown(f"""<div class="unified-card"><h1>⚠️ {m_sel} ВРЕМЕННО НЕДОСТУПЕН</h1><div class="dino-crop"><iframe src="https://chromedino.com/" frameborder="0" scrolling="no"></iframe></div></div>""", unsafe_allow_html=True)
else:
    sign = c_sel.split("(")[1][0]
    r_target = rates[sign]

    df_top = pd.DataFrame(assets)
    df_top["PRICE"] = (df_top["P_USD"] * r_target).apply(lambda x: f"{x:,.2f} {sign}")
    df_top = df_top.sort_values(by="CH", ascending=False).reset_index(drop=True)
    
    st.dataframe(df_top[["T", "PRICE"]], use_container_width=True, height=250)

    t_name = st.selectbox("ВЫБЕРИ ДЛЯ АНАЛИЗА:", df_top["T"].tolist())
    item = next(x for x in assets if x['T'] == t_name)

    if "f_usd" not in st.session_state or st.session_state.get("last_t") != t_name:
        mu, sigma = item['AVG'], item['STD'] if item['STD'] > 0 else 0.02
        st.session_state.f_usd = [item['P_USD'] * (1 + np.random.normal(mu, sigma)) for _ in range(7)]
        st.session_state.last_t = t_name

    p_now = item['P_USD'] * r_target
    f_prices = [p * r_target for p in st.session_state.f_usd]
    profit_pct = ((f_prices[-1] / p_now) - 1) * 100

    # МЕТРИКИ
    col1, col2, col3 = st.columns(3)
    col1.markdown(f"<div class='metric-card'>ТЕКУЩАЯ<br><h3>{p_now:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='metric-card'>ЦЕЛЬ (7д)<br><h3>{f_prices[-1]:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    
    # Цвет рамки для профита
    p_color = "#ff4b4b" if profit_pct < -0.5 else ("#00ffcc" if profit_pct > 0.5 else "#ffcc00")
    col3.markdown(f"<div class='metric-card' style='border: 1px solid {p_color};'>ПРОФИТ (%)<br><h3>{profit_pct:+.2f} %</h3></div>", unsafe_allow_html=True)

    st.divider()
    # ГРАФИК
    hist_vals = (item['DF']['Close'].tail(14).values / (item['P_USD'] / p_now))
    st.line_chart(np.append(hist_vals, f_prices), color="#00ffcc")

    # ЛОГИКА СИГНАЛА ОТ ШЭФА
    if profit_pct > 0.5:
        sig_text, sig_color = "ПОКУПАТЬ", "#00ffcc"
    elif profit_pct < -0.5:
        sig_text, sig_color = "ПРОДАВАТЬ", "#ff4b4b"
    else:
        sig_text, sig_color = "УДЕРЖИВАТЬ", "#ffcc00" # Желтый для нейтрала

    st.markdown(f"<h2 style='text-align:center; color:{sig_color} !important; border: 2px solid {sig_color}; padding: 10px; border-radius: 10px;'>СИГНАЛ: {sig_text}</h2>", unsafe_allow_html=True)
