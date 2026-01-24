import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. ОРИГИНАЛЬНЫЙ СТИЛЬ (КИБЕРПАНК) ---
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
        padding: 30px; text-align: center;
    }
    .metric-card { background: rgba(0, 0, 0, 0.9); border: 1px solid #00ffcc; padding: 15px; text-align: center; border-radius: 10px; }
    h1, h2, h3, p, span, label { color: #00ffcc !important; }
    [data-testid="stSidebar"] { background-color: rgba(10, 14, 20, 0.95) !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. СЛОВАРЬ (RU/EN) ---
LANG = {
    "RU": {
        "market": "РЫНОК", "curr": "ВАЛЮТА", "top": "🔥 ТОП АКТИВОВ", "price": "ЦЕНА", "pred": "ПРОГНОЗ %",
        "sel": "ВЫБЕРИ ДЛЯ АНАЛИЗА:", "now": "ТЕКУЩАЯ", "target": "ЦЕЛЬ (7д)", "profit": "ПРОФИТ (%)",
        "chart": "ГРАФИК ПРОГНОЗА", "days": "РАЗБОР ПО ДНЯМ", "day_label": "День", "signal": "СИГНАЛ",
        "buy": "ПОКУПАТЬ", "sell": "ПРОДАВАТЬ", "hold": "УДЕРЖИВАТЬ"
    },
    "EN": {
        "market": "MARKET", "curr": "CURRENCY", "top": "🔥 TOP ASSETS", "price": "PRICE", "pred": "FORECAST %",
        "sel": "SELECT FOR ANALYSIS:", "now": "CURRENT", "target": "TARGET (7d)", "profit": "PROFIT (%)",
        "chart": "FORECAST CHART", "days": "DAILY BREAKDOWN", "day_label": "Day", "signal": "SIGNAL",
        "buy": "BUY", "sell": "SELL", "hold": "HOLD"
    }
}

# --- 3. БАЗА ДАННЫХ ---
DB = {
    "CHINA": ["BABA", "TCEHY", "PDD", "JD", "BIDU", "NIO", "LI", "BYDDY"],
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "NFLX", "GOOGL", "CRM"],
    "KAZ (Казахстан)": ["KCZ.L", "KMGZ.KZ", "HSBK.KZ", "KCELL.KZ", "NAC.KZ", "CCBN.KZ"],
    "RF (Россия)": ["SBER.ME", "GAZP.ME", "LKOH.ME", "YNDX", "ROSN.ME"]
}

@st.cache_data(ttl=300)
def load_data(m_name):
    tickers = DB[m_name]
    data = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', progress=False)
    rates_raw = yf.download(["RUB=X", "KZT=X"], period="1d", progress=False)['Close']
    
    # Расчет курсов валют
    r_map = {"$": 1.0}
    r_map["₽"] = float(rates_raw["RUB=X"].iloc[-1]) if not rates_raw["RUB=X"].empty else 90.0
    r_map["₸"] = float(rates_raw["KZT=X"].iloc[-1]) if not rates_raw["KZT=X"].empty else 450.0
    
    clean = []
    for t in tickers:
        try:
            df = data[t].dropna()
            if df.empty: continue
            
            # Определение базовой валюты тикера
            base = "₽" if ".ME" in t or t == "YNDX" else ("₸" if ".KZ" in t or "KCZ" in t else "$")
            p_usd = float(df['Close'].iloc[-1]) / r_map[base]
            
            mu = df['Close'].pct_change().mean()
            if np.isnan(mu): mu = 0.0
            
            clean.append({
                "T": t, "P_USD": p_usd, "F_USD": p_usd * (1 + mu * 7),
                "AVG": mu, "STD": df['Close'].pct_change().std() or 0.02, "DF": df
            })
        except: continue
    return clean, r_map

# --- 4. ИНТЕРФЕЙС ---
st.sidebar.title("ABI SETTINGS")
l_sel = st.sidebar.radio("LANGUAGE / ЯЗЫК", ["RU", "EN"])
T = LANG[l_sel]
m_sel = st.sidebar.selectbox(T["market"], list(DB.keys()))
c_sel = st.sidebar.radio(T["curr"], ["USD ($)", "RUB (₽)", "KZT (₸)"])

assets, rates = load_data(m_sel)
st.title("🚀 ABI ANALITIC")

if assets:
    sign = c_sel.split("(")[1][0]
    r_target = rates[sign]

    # ТОП АКТИВОВ
    st.write(f"## {T['top']}")
    df_top = pd.DataFrame(assets)
    df_top["PROFIT_EST"] = ((df_top["F_USD"] / df_top["P_USD"]) - 1) * 100
    df_top = df_top.sort_values(by="PROFIT_EST", ascending=False).reset_index(drop=True)
    
    df_show = df_top.copy()
    df_show[T["price"]] = (df_show["P_USD"] * r_target).apply(lambda x: f"{x:,.2f} {sign}")
    df_show[T["pred"]] = df_show["PROFIT_EST"].apply(lambda x: f"{x:+.2f}%")
    st.dataframe(df_show[["T", T["price"], T["pred"]]], use_container_width=True)

    # ДЕТАЛЬНЫЙ АНАЛИЗ
    st.divider()
    t_name = st.selectbox(T["sel"], df_top["T"].tolist())
    item = next(x for x in assets if x['T'] == t_name)

    p_now = item['P_USD'] * r_target
    f_price = item['F_USD'] * r_target
    profit_pct = item['PROFIT_EST']

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'>{T['now']}<br><h3>{p_now:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>{T['target']}<br><h3>{f_price:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'>{T['profit']}<br><h3>{profit_pct:+.2f} %</h3></div>", unsafe_allow_html=True)

    # ГРАФИК
    st.write(f"### {T['chart']}")
    hist_vals = (item['DF']['Close'].tail(15).values * r_target / (item['P_USD'] * r_target / p_now))
    st.line_chart(hist_vals, color="#00ffcc")

    # СИГНАЛ
    sig_key = "buy" if profit_pct > 0.7 else ("sell" if profit_pct < -0.7 else "hold")
    st.markdown(f"<h2 style='text-align:center; border: 2px solid #00ffcc; padding: 15px;'>{T['signal']}: {T[sig_key]}</h2>", unsafe_allow_html=True)
