import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from gnews import GNews
from datetime import datetime

# --- 1. СТИЛЬ И БРЕНДИНГ RILLET ---
st.set_page_config(page_title="Rillet", layout="wide")
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
    .metric-card { background: rgba(0, 0, 0, 0.9); border: 1px solid #00ffcc; padding: 15px; text-align: center; border-radius: 10px; }
    h1, h2, h3, p, span, label { color: #00ffcc !important; }
    .logo-text { font-size: 42px; font-weight: bold; text-align: center; color: #00ffcc; border-bottom: 2px solid #00ffcc; margin-bottom: 20px; }
    .analysis-card { background: rgba(0, 255, 204, 0.05); border: 1px solid #00ffcc; padding: 15px; margin-bottom: 10px; border-radius: 10px; }
    .bullish { color: #00ffcc !important; font-weight: bold; }
    .bearish { color: #ff4b4b !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. БАЗА ДАННЫХ ---
DB = {
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "NFLX", "GOOGL", "META", "INTC", "CRM", "AVGO", "QCOM", "PYPL", "TSM"],
    "CHINA (Китай)": ["BABA", "TCEHY", "PDD", "JD", "BIDU", "NIO", "LI", "BYDDY", "BILI", "NTES", "GDS", "ZLAB", "KC", "IQ", "TME"],
    "EUROPE": ["ASML", "MC.PA", "VOW3.DE", "NESN.SW", "SIE.DE", "SAP.DE", "AIR.PA", "RMS.PA", "MBG.DE", "DHL.DE", "ALV.DE", "SAN.MC", "BMW.DE", "OR.PA", "BBVA.MC"],
    "KAZ (Казахстан)": ["KCZ.L", "KMGZ.KZ", "HSBK.KZ", "KCELL.KZ", "NAC.KZ", "CCBN.KZ", "KEGC.KZ", "KZTK.KZ", "KZTO.KZ", "ASBN.KZ", "KSPI.KZ", "KCP.KZ", "KMGP.KZ", "BCKL.KZ", "KASE.KZ"],
    "RF (Россия)": ["SBER.ME", "GAZP.ME", "LKOH.ME", "YNDX", "ROSN.ME", "MGNT.ME", "NVTK.ME", "GMKN.ME", "CHMF.ME", "PLZL.ME", "TATN.ME", "MTSS.ME", "AFLT.ME", "ALRS.ME", "VTBR.ME"]
}

LANG = {
    "RU": {
        "market": "РЫНОК", "curr": "ВАЛЮТА", "sel": "ВЫБЕРИ АКТИВ:", "price": "ЦЕНА", "pred_pct": "ПРОГНОЗ %",
        "now": "ТЕКУЩАЯ", "target": "ЦЕЛЬ (7д)", "profit": "ПРОФИТ (%)", "chart": "ГРАФИК ПРОГНОЗА",
        "logic_title": "🧠 АНАЛИЗ ИНФОПОЛЯ", "sent_label": "МНЕНИЕ", "src_label": "Источник",
        "buy": "✅ ПОКУПАТЬ", "sell": "❌ ПРОДАВАТЬ/ЖДАТЬ", "hold": "⚖️ УДЕРЖИВАТЬ", "final": "ИТОГОВЫЙ СИГНАЛ",
        "pos": "ПОЗИТИВ", "neg": "НЕГАТИВ", "neut": "НЕЙТРАЛЬНО", "upd": "Обновление данных"
    },
    "EN": {
        "market": "MARKET", "curr": "CURRENCY", "sel": "SELECT ASSET:", "price": "PRICE", "pred_pct": "FORECAST %",
        "now": "CURRENT", "target": "TARGET (7d)", "profit": "PROFIT (%)", "chart": "FORECAST CHART",
        "logic_title": "🧠 INFO-FIELD ANALYSIS", "sent_label": "SENTIMENT", "src_label": "Source",
        "buy": "✅ BUY", "sell": "❌ SELL/WAIT", "hold": "⚖️ HOLD", "final": "FINAL SIGNAL",
        "pos": "POSITIVE", "neg": "NEGATIVE", "neut": "NEUTRAL", "upd": "Data updated"
    }
}

def get_daily_key():
    return datetime.now().strftime("%Y-%m-%d")

@st.cache_data(ttl=86400)
def fetch_all(m_name, daily_key):
    tickers = DB[m_name]
    data = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', progress=False)
    rates_raw = yf.download(["RUB=X", "KZT=X", "EURUSD=X"], period="5d", progress=False)['Close']
    r_map = {"$": 1.0}
    r_map["₽"] = float(rates_raw["RUB=X"].dropna().iloc[-1]) if not rates_raw["RUB=X"].dropna().empty else 90.0
    r_map["₸"] = float(rates_raw["KZT=X"].dropna().iloc[-1]) if not rates_raw["KZT=X"].dropna().empty else 485.0
    eur_usd = float(rates_raw["EURUSD=X"].dropna().iloc[-1]) if not rates_raw["EURUSD=X"].dropna().empty else 1.08
    
    clean = []
    for t in tickers:
        try:
            df = data[t].dropna()
            if df.empty:
                t].dropna()
            if df.empty: continue
            base = "₽" if ".ME" in t or t == "YNDX" else ("₸" if ".KZ" in t or "KCZ" in t else ("€" if any(x in t for x in [".PA", ".DE", ".MC", ".SW"]) else "$"))
            p_now_usd = (float(df['Close'].iloc[-1]) * eur_usd) if base == "€" else (float(df['Close'].iloc[-1]) / r_map.get(base, 1.0))
            mu = df['Close'].pct_change().mean() or 0.0
            clean.append({"T": t, "P_USD": p_now_usd, "F_USD": p_now_usd * (1 + mu * 7), "AVG": mu, "STD": df['Close'].pct_change().std() or 0.02, "DF": df})
        except: continue
    return clean, r_map

@st.cache_data(ttl=86400)
def analyze_news(query, l_code, daily_key):
    try:
        gn = GNews(language='ru' if l_code == 'RU' else 'en', country='RU' if l_code == 'RU' else 'US', period='7d', max_results=6)
        news = gn.get_news(f"{query} stock forecast")
        results = []
        pos_w = ['рост', 'вверх', 'покупать', 'прибыль', 'growth', 'buy', 'bullish', 'up']
        neg_w = ['падение', 'вниз', 'продавать', 'убыток', 'fall', 'sell', 'bearish', 'down']
        for n in news:
            txt = n.get('title', '')
            sent = "neut"
            if any(w in txt.lower() for w in pos_w): sent = "pos"
            elif any(w in txt.lower() for w in neg_w): sent = "neg"
            results.append({"text": txt, "sent": sent, "src": n.get('publisher', {}).get('title', 'Media')})
        return results
    except: return []

# --- 3. ИНТЕРФЕЙС RILLET ---
st.sidebar.markdown('<div class="logo-text">RILLET</div>', unsafe_allow_html=True)
l_code = st.sidebar.radio("LANGUAGE / ЯЗЫК", ["RU", "EN"])
T = LANG[l_code]

m_choice = st.sidebar.selectbox(T["market"], list(DB.keys()))
c_choice = st.sidebar.radio(T["curr"], ["USD ($)", "RUB (₽)", "KZT (₸)"])

daily_token = get_daily_key()
assets, rates = fetch_all(m_choice, daily_token)
sign = c_choice.split("(")[1][0]
r_val = rates.get(sign, 1.0)

if assets:
    df_main = pd.DataFrame(assets)
    df_main["PROFIT_EST"] = ((df_main["F_USD"] / df_main["P_USD"]) - 1) * 100
    df_main = df_main.sort_values("PROFIT_EST", ascending=False).reset_index(drop=True)
    
    view = df_main.copy()
    view[T["price"]] = (view["P_USD"] * r_val).apply(lambda x: f"{x:,.2f} {sign}")
    view[T["pred_pct"]] = view["PROFIT_EST"].apply(lambda x: f"{x:+.2f}%")
    st.dataframe(view[["T", T["price"], T["pred_pct"]]], use_container_width=True, height=250)

    st.divider()
    t_sel = st.selectbox(T["sel"], df_main["T"].tolist())
    item = next(x for x in assets if x['T'] == t_sel)

    p_now = item['P_USD'] * r_val
    if "f_pts" not in st.session_state or st.session_state.get("last_t") != t_sel:
        st.session_state.f_pts = [item['P_USD'] * (1 + np.random.normal(item['AVG'], item['STD'])) for _ in range(7)]
        st.session_state.last_t = t_sel

    f_prices = [p * r_val for p in st.session_state.f_pts]
    pct = ((f_prices[-1] / p_now) - 1) * 100
    clr = "#00ffcc" if pct > 0.5 else ("#ff4b4b" if pct < -0.5 else "#ffcc00")

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'>{T['now']}<br><h3>{p_now:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>{T['target']}<br><h3>{f_prices[-1]:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card' style='border-color:{clr}'>{T['profit']}<br><h3>{pct:+.2f}%</h3></div>", unsafe_allow_html=True)

    st.write(f"#### {T['chart']} {t_sel}")
    hist = item['DF']['Close'].tail(15).values * r_val / (item['P_USD'] * r_val / p_now)
    st.line_chart(np.append(hist, f_prices), color="#00ffcc")

    st.divider()
    st.write(f"#### {T['logic_title']} {t_sel}")
    news_data = analyze_news(t_sel, l_code, daily_token)
    
    if news_data:
        n1, n2 = st.columns(2)
        for i, entry in enumerate(news_data):
            col = n1 if i % 2 == 0 else n2
            s_class = "bullish" if entry['sent'] == "pos" else ("bearish" if entry['sent'] == "neg" else "")
            col.markdown(f"""
            <div class="analysis-card">
                <p style=
            "margin-bottom:5px;">{entry['text']}</p>
                <span class="{s_class}">{T["sent_label"]}: {T[entry['sent']]}</span> | <span style="color:#888;">{entry['src']}</span>
            </div>
            """, unsafe_allow_html=True)
        
        pos = len([x for x in news_data if x['sent'] == "pos"])
        neg = len([x for x in news_data if x['sent'] == "neg"])
        res_key = "buy" if pos > neg else ("sell" if neg > pos else "hold")
        st.markdown(f"<h2 style='text-align:center; border:2px solid {clr}; padding:15px; border-radius:10px;'>{T['final']}: {T[res_key]}</h2>", unsafe_allow_html=True)

st.caption(f"{T['upd']}: {daily_token} 00:00")
