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
    
    .logo-text {
        font-size: 42px; font-weight: bold; text-align: center; color: #00ffcc;
        border-bottom: 2px solid #00ffcc; margin-bottom: 20px;
    }
    .analysis-card {
        background: rgba(0, 255, 204, 0.05);
        border: 1px solid #00ffcc;
        padding: 20px;
        margin-bottom: 15px;
        border-radius: 10px;
    }
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

# Кэширование на сутки (обновление в 00:00)
def get_daily_key():
    return datetime.now().strftime("%Y-%m-%d")

@st.cache_data(ttl=86400)
def fetch_market_data(m_name, daily_key):
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
            if df.empty: continue
            base = "₽" if ".ME" in t or t == "YNDX" else ("₸" if ".KZ" in t or "KCZ" in t else ("€" if any(x in t for x in [".PA", ".DE", ".MC", ".SW"]) else "$"))
            p_now_usd = (float(df['Close'].iloc[-1]) * eur_usd) if base == "€" else (float(df['Close'].iloc[-1]) / r_map.get(base, 1.0))
            mu = df['Close'].pct_change().mean() or 0.0
            clean.append({"T": t, "P_USD": p_now_usd, "F_USD": p_now_usd * (1 + mu * 7), "AVG": mu, "STD": df['Close'].pct_change().std() or 0.02, "DF": df})
        except: continue
    return clean, r_map

@st.cache_data(ttl=86400)
def analyze_news_text(query, daily_key):
    try:
        # Берем новости на русском для лучшего понимания контекста
        gn = GNews(language='ru', country='RU', period='7d', max_results=8)
        news = gn.get_news(f"{query} акции прогноз аналитика")
        
        summaries = []
        for n in news:
            title = n.get('title', '')
            # Извлекаем "настроение" из заголовка (простой алгоритм)
            sentiment = "НЕЙТРАЛЬНО"
            pos_words = ['рост', 'вверх', 'покупать', 'рекорд', 'прибыль', 'позитив', 'цель повышена']
            neg_words = ['падение', 'вниз', 'продавать', 'убыток', 'негатив', 'обвал', 'риск']
            
            if any(w in title.lower() for w in pos_words): sentiment = "ПОЗИТИВ"
            if any(w in title.lower() for w in neg_words): sentiment = "НЕГАТИВ"
            
            summaries.append({
                "text": title,
                "sentiment": sentiment,
                "source": n.get('publisher', {}).get('title', 'СМИ')
            })
        return summaries
    except: return []

# --- 3. ИНТЕРФЕЙС ---
st.sidebar.markdown('<div class="logo-text">RILLET</div>', unsafe_allow_html=True)
market = st.sidebar.selectbox("РЫНОК", list(DB.keys()))
currency = st.sidebar.radio("ВАЛЮТА", ["USD ($)", "RUB (₽)", "KZT (₸)"])

daily_token = get_daily_key()
assets, rates = fetch_market_data(market, daily_token)
sign = currency.split("(")[1][0]
r_val = rates.get(sign, 1.0)

st.title("🚀 RILLET ИНТЕЛЛЕКТ")

tab_data, tab_logic = st.tabs(["📊 ЦИФРЫ", "🧠 ТЕКСТОВЫЙ АНАЛИЗ"])

with tab_data:
    if assets:
        # Твой оригинальный код отображения
        df = pd.DataFrame(assets)
        df["PROFIT_EST"] = ((df["F_USD"] / df["P_USD"]) - 1) * 100
        df = df.sort_values("PROFIT_EST", ascending=False).reset_index(drop=True)
        st.dataframe(df[["T", "P_USD", "PROFIT_EST"]], use_container_width=True)
        t_sel = st.selectbox("ВЫБЕРИ АКТИВ ДЛЯ РАЗБОРА:", df["T"].tolist())
        
        # Расчет цен
        item = next(x for x in assets if x['T'] == t_sel)
        p_now = item['P_USD'] * r_val
        
        c1, c2 = st.columns(2)
        c1.metric("ТЕКУЩАЯ", f"{p_now:,.2f} {sign}")
        c2.metric("ПРОГНОЗ (7д)", f"{item['F_USD']*r_val:,.2f} {sign}", f"{((item['F_USD']/item['P_USD'])-1)*100:+.2f}%")
    else:
        st.error("Данные недоступны")
        t_sel = None

with tab_logic:
    if t_sel:
        st.write(f"### 🧠 Почему стоит (или нет) брать {t_sel}?")
        with st.spinner('Анализирую инфополе...'):
            logic_data = analyze_news_text(t_sel, daily_token)
        
        if logic_data:
            for entry in logic_data:
                s_class = "bullish" if entry['sentiment'] == "ПОЗИТИВ" else ("bearish" if entry['sentiment'] == "НЕГАТИВ" else "")
                st.markdown(f"""
                <div class="analysis-card">
                    <p style="font-size:1.1em; margin-bottom:5px;">{entry['text']}</p>
                    <span class="{s_class}">МНЕНИЕ: {entry['sentiment']}</span> | 
                    <span style="color:#888;">Источник: {entry['source']}</span>
                </div>
                """, unsafe_allow_html=True)
            
            # Итоговый вывод
            pos_count = len([x for x in logic_data if x['sentiment'] == "ПОЗИТИВ"])
            neg_count = len([x for x in logic_data if x['sentiment'] == "НЕГАТИВ"])
            
            st.divider()
            if pos_count > neg_count:
                st.success(f"✅ ИТОГ: Инфополе за {t_sel} преимущественно позитивное. Математика подтверждает покупку.")
            elif neg_count > pos_count:
                st.error(f"❌ ИТОГ: В новостях много негатива по {t_sel}. Высокий риск, лучше подождать.")
            else:
                st.warning(f"⚖️ ИТОГ: Новости по {t_sel} противоречивы. Решение за техническими индикаторами.")
        else:
            st.info("По этому активу сегодня нет критических новостей. Опирайтесь на график.")

st.caption(f"Автоматическое обновление базы: сегодня в 00:00 ({daily_token})")
