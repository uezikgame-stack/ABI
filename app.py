import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from gnews import GNews
from datetime import datetime

# --- 1. СТИЛЬ И БРЕНДИНГ RILLET ---
st.set_page_config(page_title="Rillet", layout="wide")

# --- ЛОКАЛИЗАЦИЯ ---
lang = st.sidebar.radio("LANGUAGE / ЯЗЫК", ["EN", "RU"])
txt = {
    "EN": {
        "market": "MARKET", "currency": "CURRENCY", "price": "PRICE", "forecast": "FORECAST %",
        "select": "SELECT ASSET:", "current": "CURRENT PRICE", "target": "TARGET (7d)",
        "profit": "EST. PROFIT", "chart_title": "FORECAST CHART", "news_title": "INFO-FIELD ANALYSIS",
        "buy": "✅ STRONG BUY", "sell": "❌ SELL / HOLD", "hold": "⚖️ NEUTRAL", "no_news": "No news found.",
        "update": "Data updated", "signal": "FINAL SIGNAL",
        "brokers": "TOP BROKERS", "trust": "TRUST LEVEL", "details": "DETAILS",
        "history": "History", "founder": "Founder", "fact": "Fun Fact", "lawsuits": "Major Lawsuits"
    },
    "RU": {
        "market": "РЫНОК", "currency": "ВАЛЮТА", "price": "ЦЕНА", "forecast": "ПРОГНОЗ %",
        "select": "ВЫБЕРИ АКТИВ:", "current": "ТЕКУЩАЯ", "target": "ЦЕЛЬ (7д)",
        "profit": "ПРОФИТ (%)", "chart_title": "ГРАФИК ПРОГНОЗА", "news_title": "АНАЛИЗ ИНФОПОЛЯ",
        "buy": "✅ ПОКУПАТЬ", "sell": "❌ ПРОДАВАТЬ/ЖДАТЬ", "hold": "⚖️ УДЕРЖИВАТЬ", "no_news": "Новостей не найдено.",
        "update": "Обновление данных", "signal": "ИТОГОВЫЙ СИГНАЛ",
        "brokers": "ТОП БРОКЕРОВ", "trust": "УРОВЕНЬ ДОВЕРИЯ", "details": "ДЕТАЛИ",
        "history": "История", "founder": "Основатель", "fact": "Интересный факт", "lawsuits": "Крупные иски"
    }
}[lang]

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
    .stExpander { border: 1px solid #00ffcc !important; background: transparent !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. БАЗА ДАННЫХ ---
DB = {
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "NFLX", "GOOGL", "META", "INTC", "CRM", "AVGO", "QCOM", "PYPL", "TSM"],
    "CHINA": ["BABA", "TCEHY", "PDD", "JD", "BIDU", "NIO", "LI", "BYDDY", "BILI", "NTES", "GDS", "ZLAB", "KC", "IQ", "TME"],
    "EUROPE": ["ASML", "MC.PA", "VOW3.DE", "NESN.SW", "SIE.DE", "SAP.DE", "AIR.PA", "RMS.PA", "MBG.DE", "DHL.DE", "ALV.DE", "SAN.MC", "BMW.DE", "OR.PA", "BBVA.MC"],
    "KAZAKHSTAN": ["KCZ.L", "KMGZ.KZ", "HSBK.KZ", "KCELL.KZ", "NAC.KZ", "CCBN.KZ", "KEGC.KZ", "KZTK.KZ", "KZTO.KZ", "ASBN.KZ", "KSPI.KZ", "KCP.KZ", "KMGP.KZ", "BCKL.KZ", "KASE.KZ"],
    "RUSSIA": ["SBER.ME", "GAZP.ME", "LKOH.ME", "YNDX", "ROSN.ME", "MGNT.ME", "NVTK.ME", "GMKN.ME", "CHMF.ME", "PLZL.ME", "TATN.ME", "MTSS.ME", "AFLT.ME", "ALRS.ME", "VTBR.ME"]
}

BROKERS_DB = {
    "Interactive Brokers": {
        "trust": 99.2,
        "history": "Founded in 1978 as T.P. & Co. Pioneered electronic trading.",
        "founder": "Thomas Peterffy",
        "fact": "Peterffy is known as the father of digital trading.",
        "lawsuits": "Fined $38M in 2020 for AML (anti-money laundering) compliance failures."
    },
    "Freedom Finance": {
        "trust": 94.5,
        "history": "Part of Freedom Holding Corp, listed on NASDAQ.",
        "founder": "Timur Turlov",
        "fact": "The only broker from Central Asia listed on NASDAQ.",
        "lawsuits": "Under short-seller attacks (Hindenburg Research), but successfully passed audits."
    },
    "Tinkoff (RU)": {
        "trust": 88.5,
        "history": "Started as a credit card company, became a huge fintech ecosystem.",
        "founder": "Oleg Tinkov",
        "fact": "One of the world's largest digital banks without physical branches.",
        "lawsuits": "Heavy sanctions-related issues and ownership change in 2022-2023."
    },
    "Halyk Finance (KZ)": {
        "trust": 92.3,
        "history": "Investment arm of the largest bank in Kazakhstan.",
        "founder": "Halyk Bank Group",
        "fact": "Oldest financial institution in Kazakhstan with over 100 years of history.",
        "lawsuits": "Local regulatory fines for reporting delays, no major global fraud cases."
    }
}

def get_daily_key():
    return datetime.now().strftime("%Y-%m-%d")

@st.cache_data(ttl=86400)
def fetch_all(m_name, daily_key):
    try:
        tickers = DB[m_name]
        data = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', progress=False)
        rates_raw = yf.download(["RUB=X", "KZT=X", "EURUSD=X"], period="5d", progress=False)['Close']
        r_map = {"$": 1.0, "₽": 90.0, "₸": 485.0}
        try:
            r_map["₽"] = float(rates_raw["RUB=X"].dropna().iloc[-1])
            r_map["₸"] = float(rates_raw["KZT=X"].dropna().iloc[-1])
        except: pass
        eur_usd = float(rates_raw["EURUSD=X"].dropna().iloc[-1]) if not rates_raw["EURUSD=X"].dropna().empty else 1.08
        clean = []
        for t in tickers:
            try:
                df = data[t].dropna()
                if df.empty: continue
                base = "₽" if ".ME" in t or t == "YNDX" else ("₸" if ".KZ" in t or "KCZ" in t else ("€" if any(x in t for x in [".PA", ".DE", ".MC", ".SW"]) else "$"))
                p_now_usd = (float(df['Close'].iloc[-1]) * eur_usd) if base == "€" else (float(df['Close'].iloc[-1]) / r_map.get(base, 1.0))
                mu = df['Close'].pct_change().mean() or 0.0
                clean.append({"T": t, "P_USD": p_now_usd, "F_USD": p_now_usd * (1 + mu * 7), "AVG": mu, "STD": df['Close'].pct_change().std() or 0.02, "DF": df})
            except: continue
        return clean, r_map
    except: return [], {"$": 1.0, "₽": 90.0, "₸": 485.0}

@st.cache_data(ttl=86400)
def analyze_news(query, daily_key, l):
    try:
        gn = GNews(language='ru' if l == "RU" else 'en', period='7d', max_results=6)
        news = gn.get_news(f"{query} stock forecast" if l == "EN" else f"{query} акции прогноз")
        results = []
        pos_w = ['рост', 'вверх', 'покупать', 'profit', 'growth', 'buy', 'positive']
        neg_w = ['падение', 'вниз', 'продавать', 'loss', 'fall', 'sell', 'negative']
        for n in news:
            txt = n.get('title', '')
            sent = "NEUTRAL"
            if any(w in txt.lower() for w in pos_w): sent = "POSITIVE"
            elif any(w in txt.lower() for w in neg_w): sent = "NEGATIVE"
            results.append({"text": txt, "sent": sent, "src": n.get('publisher', {}).get('title', 'Media')})
        return results
    except: return []

# --- 3. ИНТЕРФЕЙС RILLET ---
st.sidebar.markdown('<div class="logo-text">RILLET</div>', unsafe_allow_html=True)

mode = st.sidebar.selectbox("MODE / РЕЖИМ", [txt["market"], txt["brokers"]])

if mode == txt["market"]:
    m_name = st.sidebar.selectbox(txt["market"], list(DB.keys()))
    c_choice = st.sidebar.radio(txt["currency"], ["USD ($)", "RUB (₽)", "KZT (₸)"])

    daily_token = get_daily_key()
    assets, rates = fetch_all(m_name, daily_token)
    sign = c_choice.split("(")[1][0]
    r_val = rates.get(sign, 1.0)

    if not assets:
        st.error("Data unavailable / Данные недоступны")
    else:
        df_main = pd.DataFrame(assets)
        df_main["PROFIT_EST"] = ((df_main["F_USD"] / df_main["P_USD"]) - 1) * 100
        df_main = df_main.sort_values("PROFIT_EST", ascending=False).reset_index(drop=True)
        view = df_main.copy()
        view[txt["price"]] = (view["P_USD"] * r_val).apply(lambda x: f"{x:,.2f} {sign}")
        view[txt["forecast"]] = view["PROFIT_EST"].apply(lambda x: f"{x:+.2f}%")
        st.dataframe(view[["T", txt["price"], txt["forecast"]]], use_container_width=True, height=250)
        st.divider()
        t_sel = st.selectbox(txt["select"], df_main["T"].tolist())
        item = next(x for x in assets if x['T'] == t_sel)
        p_now = item['P_USD'] * r_val
        if "f_pts" not in st.session_state or st.session_state.get("last_t") != t_sel:
            st.session_state.f_pts = [item['P_USD'] * (1 + np.random.normal(item['AVG'], item['STD'])) for _ in range(7)]
            st.session_state.last_t = t_sel
        f_prices = [p * r_val for p in st.session_state.f_pts]
        pct = ((f_prices[-1] / p_now) - 1) * 100
        clr = "#00ffcc" if pct > 0.5 else ("#ff4b4b" if pct < -0.5 else "#ffcc00")
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-card'>{txt['current']}<br><h3>{p_now:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'>{txt['target']}<br><h3>{f_prices[-1]:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card' style='border-color:{clr}'>{txt['profit']}<br><h3>{pct:+.2f}%</h3></div>", unsafe_allow_html=True)
        st.write(f"#### {txt['chart_title']} {t_sel}")
        hist = item['DF']['Close'].tail(15).values * r_val / (item['P_USD'] * r_val / p_now)
        st.line_chart(np.append(hist, f_prices), color="#00ffcc")
        st.divider()
        st.write(f"#### 🧠 {txt['news_title']} {t_sel}")
        news_data = analyze_news(t_sel, daily_token, lang)
        if news_data:
            n_col1, n_col2 = st.columns(2)
            for i, entry in enumerate(news_data):
                target_col = n_col1 if i % 2 == 0 else n_col2
                s_class = "bullish" if entry['sent'] == "POSITIVE" else ("bearish" if entry['sent'] == "NEGATIVE" else "")
                target_col.markdown(f"""
                <div class="analysis-card">
                    <p style="margin-bottom:5px;">{entry['text']}</p>
                    <span class="{s_class}">{entry['sent']}</span> | <span style="color:#888;">{entry['src']}</span>
                </div>
                """, unsafe_allow_html=True)
            pos = len([x for x in news_data if x['sent'] == "POSITIVE"])
            neg = len([x for x in news_data if x['sent'] == "NEGATIVE"])
            res_text = txt["buy"] if pos > neg else (txt["sell"] if neg > pos else txt["hold"])
            st.markdown(f"<h2 style='text-align:center; border:2px solid {clr}; padding:15px; border-radius:10px;'>{txt['signal']}: {res_text}</h2>", unsafe_allow_html=True)
        else:
            st.info(txt["no_news"])

elif mode == txt["brokers"]:
    st.write(f"## 🏛️ {txt['brokers']}")
    sorted_brokers = sorted(BROKERS_DB.items(), key=lambda x: x[1]['trust'], reverse=True)
    
    for broker, info in sorted_brokers:
        trust = info['trust']
        bar_color = "#00ffcc" if trust > 90 else "#ffcc00"
        
        st.markdown(f"""
        <div class="analysis-card" style="display: flex; justify-content: space-between; align-items: center; margin-bottom:0px; border-bottom:none; border-radius:10px 10px 0 0;">
            <div style="font-size: 20px; font-weight: bold;">{broker}</div>
            <div style="text-align: right;">
                <span style="font-size: 14px; color: #888;">{txt['trust']}</span><br>
                <span style="font-size: 24px; color: {bar_color}; font-weight: bold;">{trust}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander(txt["details"]):
            st.markdown(f"**📜 {txt['history']}:** {info['history']}")
            st.markdown(f"**👤 {txt['founder']}:** {info['founder']}")
            st.markdown(f"**💡 {txt['fact']}:** {info['fact']}")
            st.markdown(f"**⚖️ {txt['lawsuits']}:** {info['lawsuits']}")
            
        st.markdown(f"""
        <div style="background-color: #111; height: 5px; border-radius: 5px; margin-bottom: 25px;">
            <div style="background-color: {bar_color}; width: {trust}%; height: 100%; border-radius: 5px;"></div>
        </div>
        """, unsafe_allow_html=True)

st.caption(f"{txt['update']}: {get_daily_key()} 00:00")
