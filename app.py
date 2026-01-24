import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. СТИЛЬ (ПЛЫВУЩИЙ ФОН И КИБЕРПАНК) ---
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
    .dino-container {
        overflow: hidden; height: 300px; width: 100%; border-radius: 10px; border: 1px solid #ff4b4b;
    }
    .dino-container iframe { width: 100%; height: 500px; margin-top: -100px; filter: invert(1); }
    .metric-card { background: rgba(0, 0, 0, 0.9); border: 1px solid #00ffcc; padding: 15px; text-align: center; border-radius: 10px; }
    h1, h2, h3, p, span, label { color: #00ffcc !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ЯЗЫКИ И ДАННЫЕ ---
LANG = {
    "RU": {
        "market": "РЫНОК", "curr": "ВАЛЮТА", "top": "🔥 ТОП АКТИВОВ", "price": "ЦЕНА", "pred": "ПРОГНОЗ %",
        "sel": "ВЫБЕРИ ДЛЯ АНАЛИЗА:", "now": "ТЕКУЩАЯ", "target": "ЦЕЛЬ (7д)", "profit": "ПРОФИТ (%)",
        "chart": "ГРАФИК ПРОГНОЗА", "days": "РАЗБОР ПО ДНЯМ", "day_label": "День", "signal": "СИГНАЛ",
        "buy": "ПОКУПАТЬ", "sell": "ПРОДАВАТЬ", "hold": "УДЕРЖИВАТЬ",
        "err": "РЕГИОН ВРЕМЕННО НЕДОСТУПЕН", "dino_msg": "Пока данные грузятся, побей рекорд!"
    },
    "EN": {
        "market": "MARKET", "curr": "CURRENCY", "top": "🔥 TOP ASSETS", "price": "PRICE", "pred": "FORECAST %",
        "sel": "SELECT FOR ANALYSIS:", "now": "CURRENT", "target": "TARGET (7d)", "profit": "PROFIT (%)",
        "chart": "FORECAST CHART", "days": "DAILY BREAKDOWN", "day_label": "Day", "signal": "SIGNAL",
        "buy": "BUY", "sell": "SELL", "hold": "HOLD",
        "err": "REGION UNAVAILABLE", "dino_msg": "Beat the record while data is loading!"
    }
}

DB = {
    "CHINA (Китай)": ["BABA", "TCEHY", "PDD", "JD", "BIDU", "NIO", "LI", "BYDDY"],
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "NFLX", "GOOGL", "CRM"],
    "KAZ (Казахстан)": ["KCZ.L", "KMGZ.KZ", "HSBK.KZ", "KCELL.KZ", "NAC.KZ", "CCBN.KZ"],
    "RF (Россия)": ["SBER.ME", "GAZP.ME", "LKOH.ME", "YNDX", "ROSN.ME"]
}

@st.cache_data(ttl=300)
def fetch_all(m_name):
    try:
        tickers = DB[m_name]
        data = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', progress=False)
        rates_raw = yf.download(["RUB=X", "KZT=X"], period="1d", progress=False)['Close']
        
        # Безопасный маппинг курсов
        r_map = {"$": 1.0}
        r_map["₽"] = float(rates_raw["RUB=X"].iloc[-1]) if not rates_raw["RUB=X"].empty else 90.0
        r_map["₸"] = float(rates_raw["KZT=X"].iloc[-1]) if not rates_raw["KZT=X"].empty else 450.0
        
        clean = []
        for t in tickers:
            try:
                df = data[t].dropna() if t in data else pd.DataFrame()
                if df.empty: continue
                
                base = "₽" if ".ME" in t or t == "YNDX" else ("₸" if ".KZ" in t or "KCZ" in t else "$")
                p_now_usd = float(df['Close'].iloc[-1]) / r_map[base]
                
                mu = df['Close'].pct_change().mean()
                if np.isnan(mu) or np.isinf(mu): mu = 0.0
                
                clean.append({
                    "T": t, "P_USD": p_now_usd, "F_USD": p_now_usd * (1 + mu * 7),
                    "AVG": mu, "STD": df['Close'].pct_change().std() or 0.02, "DF": df
                })
            except: continue
        return clean, r_map
    except: return [], {"$": 1.0, "₽": 90.0, "₸": 450.0}

# --- 3. ИНТЕРФЕЙС ---
st.sidebar.title("ABI SETTINGS")
l_code = st.sidebar.radio("LANGUAGE / ЯЗЫК", ["RU", "EN"])
T = LANG[l_code]
m_name = st.sidebar.selectbox(T["market"], list(DB.keys()))
c_name = st.sidebar.radio(T["curr"], ["USD ($)", "RUB (₽)", "KZT (₸)"])

assets, rates = fetch_all(m_name)
st.title("🚀 ABI ANALITIC")

if not assets:
    st.markdown(f"""<div class='unified-card'><h2 style='color:#ff4b4b!important;'>⚠️ {T['err']}</h2><p>{T['dino_msg']}</p>
    <div class='dino-container'><iframe src='https://chromedino.com/' frameborder='0' scrolling='no'></iframe></div></div>""", unsafe_allow_html=True)
else:
    sign = c_name.split("(")[1][0]
    r_val = rates.get(sign, 1.0)

    # ТОП АКТИВОВ
    st.write(f"### {T['top']}")
    df = pd.DataFrame(assets)
    df["PROFIT_EST"] = ((df["F_USD"] / df["P_USD"].replace(0, 1)) - 1) * 100
    df = df.sort_values("PROFIT_EST", ascending=False).reset_index(drop=True)
    
    view = df.copy()
    view[T["price"]] = (view["P_USD"] * r_val).apply(lambda x: f"{x:,.2f} {sign}")
    view[T["pred"]] = view["PROFIT_EST"].apply(lambda x: f"{x:+.2f}%")
    st.dataframe(view[["T", T["price"], T["pred"]]], use_container_width=True, height=300)

    # ДЕТАЛИЗАЦИЯ
    st.divider()
    t_sel = st.selectbox(T["sel"], df["T"].tolist())
    item = next(x for x in assets if x['T'] == t_sel)

    # Фикс прогноза
    if "cache_t" not in st.session_state or st.session_state.cache_t != t_sel:
        st.session_state.f_pts = [item['P_USD'] * (1 + np.random.normal(item['AVG'], item['STD'])) for _ in range(7)]
        st.session_state.cache_t = t_sel

    p_now = item['P_USD'] * r_val
    f_prices = [p * r_val for p in st.session_state.f_pts]
    pct = ((f_prices[-1] / p_now) - 1) * 100 if p_now != 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'>{T['now']}<br><h3>{p_now:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>{T['target']}<br><h3>{f_prices[-1]:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    clr = "#00ffcc" if pct > 0.5 else ("#ff4b4b" if pct < -0.5 else "#ffcc00")
    c3.markdown(f"<div class='metric-card' style='border-color:{clr}'>{T['profit']}<br><h3>{pct:+.2f}%</h3></div>", unsafe_allow_html=True)

    # ГРАФИК И ТАБЛИЦА
    cg, ct = st.columns([2, 1])
    with cg:
        st.write(f"#### {T['chart']}")
        h_vals = (item['DF']['Close'].tail(15).values * r_val / (item['P_USD'] * r_val / p_now)) if p_now != 0 else np.zeros(15)
        st.line_chart(np.append(h_vals, f_prices), color="#00ffcc")
    with ct:
        st.write(f"#### {T['days']}")
        days_df = pd.DataFrame({
            T["day_label"]: [f"{T['day_label']} {i+1}" for i in range(7)],
            T["price"]: [f"{p:,.2f} {sign}" for p in f_prices]
        })
        st.dataframe(days_df, hide_index=True, use_container_width=True)

    res = "buy" if pct > 0.5 else ("sell" if pct < -0.5 else "hold")
    st.markdown(f"<h2 style='text-align:center; border:2px solid {clr}; padding:10px; border-radius:10px;'>{T['signal']}: {T[res]}</h2>", unsafe_allow_html=True)
