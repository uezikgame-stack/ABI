import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. СТИЛЬ (КИБЕРПАНК + ДВИЖУЩИЙСЯ ФОН) ---
st.set_page_config(page_title="ABI ANALITIC", layout="wide")
st.markdown("""
    <style>
    .stApp {
        background-color: #020508 !important;
        background-image: 
            linear-gradient(rgba(0, 255, 204, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 255, 204, 0.1) 1px, transparent 1px);
        background-size: 60px 60px;
        animation: moveGrid 20s linear infinite;
        color: #00ffcc;
    }
    @keyframes moveGrid { from { background-position: 0 0; } to { background-position: 60px 60px; } }
    .unified-card {
        background: rgba(0, 0, 0, 0.95); border: 2px solid #ff4b4b; border-radius: 15px;
        padding: 30px; text-align: center; box-shadow: 0 0 25px rgba(255, 75, 75, 0.3);
    }
    .dino-container {
        overflow: hidden; height: 250px; width: 100%;
        margin-top: 20px; border-radius: 10px; position: relative; background: #000;
        border: 1px solid #ff4b4b;
    }
    .dino-container iframe {
        position: absolute; top: -100px; left: 0; width: 100%; height: 450px;
        filter: invert(1) hue-rotate(180deg) contrast(1.2);
    }
    .metric-card { background: rgba(0, 0, 0, 0.9); border: 1px solid #00ffcc; padding: 15px; text-align: center; border-radius: 10px; }
    h1, h2, h3, span, label, p { color: #00ffcc !important; }
    [data-testid="stSidebar"] { background-color: rgba(10, 14, 20, 0.95) !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. СЛОВАРЬ ЯЗЫКОВ ---
LANG = {
    "RU": {
        "market": "РЫНОК", "curr": "ВАЛЮТА", "lang": "ЯЗЫК", "top": "🔥 ТОП АКТИВОВ",
        "price": "ЦЕНА", "pred": "ПРОГНОЗ %", "sel": "ВЫБЕРИ ДЛЯ АНАЛИЗА:",
        "now": "ТЕКУЩАЯ", "target": "ЦЕЛЬ (7д)", "profit": "ПРОФИТ (%)",
        "chart": "ГРАФИК ПРОГНОЗА", "days": "РАЗБОР ПО ДНЯМ", "day_label": "День",
        "buy": "ПОКУПАТЬ", "sell": "ПРОДАВАТЬ", "hold": "УДЕРЖИВАТЬ", "signal": "СИГНАЛ",
        "err": "РЕГИОН ВРЕМЕННО НЕДОСТУПЕН", "dino_msg": "Пока данные грузятся, побей рекорд!"
    },
    "EN": {
        "market": "MARKET", "curr": "CURRENCY", "lang": "LANGUAGE", "top": "🔥 TOP ASSETS",
        "price": "PRICE", "pred": "FORECAST %", "sel": "SELECT FOR ANALYSIS:",
        "now": "CURRENT", "target": "TARGET (7d)", "profit": "PROFIT (%)",
        "chart": "FORECAST CHART", "days": "DAILY BREAKDOWN", "day_label": "Day",
        "buy": "BUY", "sell": "SELL", "hold": "HOLD", "signal": "SIGNAL",
        "err": "REGION TEMPORARILY UNAVAILABLE", "dino_msg": "Beat the record while data is loading!"
    }
}

# --- 3. БИБЛИОТЕКА ---
DB = {
    "CHINA (Китай)": ["BABA", "TCEHY", "PDD", "JD", "BIDU", "NIO", "LI", "BYDDY", "BILI", "NTES", "GDS", "ZLAB", "KC", "IQ", "TME"],
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "NFLX", "GOOGL", "META", "INTC", "CRM", "AVGO", "QCOM", "PYPL", "TSM"],
    "KAZ (Казахстан)": ["KCZ.L", "KMGZ.KZ", "HSBK.KZ", "KCELL.KZ", "NAC.KZ", "CCBN.KZ", "KEGC.KZ", "KZTK.KZ", "KZTO.KZ", "ASBN.KZ", "KSPI.KZ", "KCP.KZ", "KMGP.KZ", "BCKL.KZ", "KASE.KZ"],
    "EUROPE": ["ASML", "MC.PA", "VOW3.DE", "NESN.SW", "SIE.DE", "SAP.DE", "AIR.PA", "RMS.PA", "MBG.DE", "DHL.DE", "ALV.DE", "SAN.MC", "BMW.DE", "OR.PA", "BBVA.MC"],
    "RF (Россия)": ["SBER.ME", "GAZP.ME", "LKOH.ME", "YNDX", "ROSN.ME", "MGNT.ME", "NVTK.ME", "GMKN.ME", "CHMF.ME", "PLZL.ME", "TATN.ME", "MTSS.ME", "AFLT.ME", "ALRS.ME", "VTBR.ME"]
}

@st.cache_data(ttl=300)
def load_data(m_name):
    try:
        tickers = DB[m_name]
        data = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', progress=False)
        rates_df = yf.download(["RUB=X", "KZT=X", "CNY=X"], period="1d", progress=False)['Close']
        r_map = {"₽": float(rates_df["RUB=X"].iloc[-1]), "$": 1.0, "₸": float(rates_df["KZT=X"].iloc[-1])}
        
        clean = []
        for t in tickers:
            try:
                df = data[t].dropna()
                if df.empty: continue
                b = "₽" if ".ME" in t or t == "YNDX" else ("₸" if ".KZ" in t or "KCZ" in t else "$")
                p_usd = float(df['Close'].iloc[-1]) / r_map[b]
                mu = df['Close'].pct_change().mean()
                if np.isnan(mu): mu = 0.0
                clean.append({"T": t, "P_USD": p_usd, "F_USD": p_usd*(1+mu*7), "AVG": mu, "STD": df['Close'].pct_change().std() or 0.02, "DF": df})
            except: continue
        return clean, r_map
    except: return None, None

# --- 4. ИНТЕРФЕЙС ---
st.sidebar.title("ABI SETTINGS")
l_sel = st.sidebar.radio("LANGUAGE / ЯЗЫК", ["RU", "EN"])
T = LANG[l_sel]

m_sel = st.sidebar.selectbox(T["market"], list(DB.keys()))
c_sel = st.sidebar.radio(T["curr"], ["USD ($)", "RUB (₽)", "KZT (₸)"])

assets, rates = load_data(m_sel)
st.title("🚀 ABI ANALITIC")

if not assets:
    st.markdown(f"""
        <div class="unified-card">
            <h1 style="color:#ff4b4b !important;">⚠️ {T['err']}</h1>
            <p>{T['dino_msg']}</p>
            <div class="dino-container">
                <iframe src="https://chromedino.com/" frameborder="0" scrolling="no"></iframe>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    sign = c_sel.split("(")[1][0]
    r_target = rates[sign]

    st.write(f"## {T['top']}")
    df_top = pd.DataFrame(assets)
    df_top["PROFIT_EST"] = ((df_top["F_USD"] / df_top["P_USD"]) - 1) * 100
    df_top = df_top.sort_values(by="PROFIT_EST", ascending=False).reset_index(drop=True)
    df_top.index += 1
    
    df_show = df_top.copy()
    df_show[T["price"]] = (df_show["P_USD"] * r_target).fillna(0).apply(lambda x: f"{x:,.2f} {sign}")
    df_show[T["pred"]] = df_show["PROFIT_EST"].fillna(0).apply(lambda x: f"{x:+.2f}%")
    st.dataframe(df_show[["T", T["price"], T["pred"]]], use_container_width=True, height=550)

    st.divider()
    t_name = st.selectbox(T["sel"], df_top["T"].tolist())
    item = next(x for x in assets if x['T'] == t_name)

    if "f_usd" not in st.session_state or st.session_state.get("last_t") != t_name:
        st.session_state.f_usd = [item['P_USD'] * (1 + np.random.normal(item['AVG'], item['STD'])) for _ in range(7)]
        st.session_state.last_t = t_name

    p_now = item['P_USD'] * r_target
    f_prices = [p * r_target for p in st.session_state.f_usd]
    profit_pct = ((f_prices[-1] / p_now) - 1) * 100 if p_now != 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'>{T['now']}<br><h3>{p_now:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>{T['target']}<br><h3>{f_prices[-1]:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    p_color = "#ff4b4b" if profit_pct < -0.7 else ("#00ffcc" if profit_pct > 0.7 else "#ffcc00")
    c3.markdown(f"<div class='metric-card' style='border: 1px solid {p_color};'>{T['profit']}<br><h3>{profit_pct:+.2f} %</h3></div>", unsafe_allow_html=True)

    col_graph, col_table = st.columns([2, 1])
    with col_graph:
        st.write(f"### {T['chart']}")
        hist_vals = (item['DF']['Close'].tail(15).values / (item['P_USD'] / p_now))
        st.line_chart(np.append(hist_vals, f_prices), color="#00ffcc")
    with col_table:
        st.write(f"### {T['days']}")
        forecast_df = pd.DataFrame({
            T["day_label"]: [f"{T['day_label']} {i+1}" for i in range(7)],
            T["price"]: [f"{p:,.2f} {sign}" for p in f_prices],
            " % ": [f"{((p/p_now)-1)*100:+.2f} %" if p_now != 0 else "0.00 %" for p in f_prices]
        })
        st.dataframe(forecast_df, hide_index=True, use_container_width=True)

    sig_key = "buy" if profit_pct > 0.7 else ("sell" if profit_pct < -0.7 else "hold")
    sig_c = "#00ffcc" if sig_key == "buy" else ("#ff4b4b" if sig_key == "sell" else "#ffcc00")
    st.markdown(f"<h2 style='text-align:center; color:{sig_c} !important; border: 2px solid {sig_c}; padding: 15px; border-radius: 10px;'>{T['signal']}: {T[sig_key]}</h2>", unsafe_allow_html=True)
