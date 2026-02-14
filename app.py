import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from gnews import GNews
from datetime import datetime

# --- 1. СТИЛЬ И БРЕНДИНГ RILLET ---
st.set_page_config(page_title="Rillet", layout="wide")

# --- ЛОКАЛИЗАЦИЯ (ИСПРАВЛЕНО, СЭР) ---
lang = st.sidebar.radio("LANGUAGE / ЯЗЫК", ["EN", "RU"])
txt = {
    "EN": {
        "market": "MARKET", "currency": "CURRENCY", "price": "PRICE", "forecast": "FORECAST %",
        "select": "SELECT ASSET:", "current": "CURRENT PRICE", "target": "TARGET (7d)",
        "profit": "EST. PROFIT", "chart_title": "FORECAST CHART", "news_title": "INFO-FIELD ANALYSIS",
        "buy": "✅ STRONG BUY", "sell": "❌ SELL / HOLD", "hold": "⚖️ NEUTRAL", "no_news": "No news found.",
        "update": "Data updated", "signal": "FINAL SIGNAL",
        "brokers": "TOP BROKERS", "trust": "TRUST LEVEL", "details": "DETAILS",
        "history": "History", "founder": "Founder", "fact": "Fun Fact", "lawsuits": "Major Lawsuits",
        "license": "License", "fees": "Commissions", "withdraw": "Withdrawal", "assets": "Available Assets"
    },
    "RU": {
        "market": "РЫНОК", "currency": "ВАЛЮТА", "price": "ЦЕНА", "forecast": "ПРОГНОЗ %",
        "select": "ВЫБЕРИ АКТИВ:", "current": "ТЕКУЩАЯ", "target": "ЦЕЛЬ (7д)",
        "profit": "ПРОФИТ (%)", "chart_title": "ГРАФИК ПРОГНОЗА", "news_title": "АНАЛИЗ ИНФОПОЛЯ",
        "buy": "✅ ПОКУПАТЬ", "sell": "❌ ПРОДАВАТЬ/ЖДАТЬ", "hold": "⚖️ УДЕРЖИВАТЬ", "no_news": "Новостей не найдено.",
        "update": "Обновление данных", "signal": "ИТОГОВЫЙ СИГНАЛ",
        "brokers": "ТОП БРОКЕРОВ", "trust": "УРОВЕНЬ ДОВЕРИЯ", "details": "ДЕТАЛИ",
        "history": "История", "founder": "Основатель", "fact": "Интересный факт", "lawsuits": "Крупные иски",
        "license": "Лицензия", "fees": "Комиссии", "withdraw": "Вывод", "assets": "Активы"
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
    .info-tag { background: #00ffcc22; padding: 2px 8px; border-radius: 5px; font-size: 0.8em; margin-right: 5px; border: 1px solid #00ffcc44; color: #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. БАЗА ДАННЫХ АКТИВОВ ---
DB = {
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "NFLX", "GOOGL", "META", "INTC", "CRM", "AVGO", "QCOM", "PYPL", "TSM"],
    "CHINA": ["BABA", "TCEHY", "PDD", "JD", "BIDU", "NIO", "LI", "BYDDY", "BILI", "NTES", "GDS", "ZLAB", "KC", "IQ", "TME"],
    "EUROPE": ["ASML", "MC.PA", "VOW3.DE", "NESN.SW", "SIE.DE", "SAP.DE", "AIR.PA", "RMS.PA", "MBG.DE", "DHL.DE", "ALV.DE", "SAN.MC", "BMW.DE", "OR.PA", "BBVA.MC"],
    "KAZAKHSTAN": ["KCZ.L", "KMGZ.KZ", "HSBK.KZ", "KCELL.KZ", "NAC.KZ", "CCBN.KZ", "KEGC.KZ", "KZTK.KZ", "KZTO.KZ", "ASBN.KZ", "KSPI.KZ", "KCP.KZ", "KMGP.KZ", "BCKL.KZ", "KASE.KZ"],
    "RUSSIA": ["SBER.ME", "GAZP.ME", "LKOH.ME", "YNDX", "ROSN.ME", "MGNT.ME", "NVTK.ME", "GMKN.ME", "CHMF.ME", "PLZL.ME", "TATN.ME", "MTSS.ME", "AFLT.ME", "ALRS.ME", "VTBR.ME"]
}

# --- БАЗА ДАННЫХ 10 БРОКЕРОВ (С ПЕРЕВОДОМ ВНУТРИ) ---
raw_brokers = {
    "Interactive Brokers": {
        "trust": 99.2, "founder": "Thomas Peterffy", "license": "SEC, FINRA, FCA", "fees": "0.005$/sh", "withdraw": "1-3d", "assets": "Stocks, Options, Futures",
        "history": {"EN": "Started in 1978. Pioneered electronic trading.", "RU": "Основан в 1978. Пионеры электронного трейдинга."},
        "fact": {"EN": "Father of digital trading.", "RU": "Основатель считается отцом цифровой торговли."},
        "lawsuits": {"EN": "Fined $38M in 2020 (AML).", "RU": "Штраф $38 млн в 2020 за пробелы в AML."}
    },
    "Freedom Finance": {
        "trust": 94.5, "founder": "Timur Turlov", "license": "SEC, CySEC, AFSA", "fees": "0.02%", "withdraw": "Instant", "assets": "Stocks, IPO, Bonds",
        "history": {"EN": "Listed on NASDAQ.", "RU": "Единственный брокер из СНГ с листингом на NASDAQ."},
        "fact": {"EN": "Dominate CIS market.", "RU": "Лидер рынка в Центральной Азии."},
        "lawsuits": {"EN": "Cleared after Hindenburg attack.", "RU": "Прошли аудит после атаки шорт-селлеров."}
    },
    "Charles Schwab": {
        "trust": 98.1, "founder": "Charles Schwab", "license": "SEC, FINRA", "fees": "0$ (USA)", "withdraw": "2-3d", "assets": "Stocks, ETF",
        "history": {"EN": "First discounter in 1975.", "RU": "Сделали трейдинг доступным для масс с 1975."},
        "fact": {"EN": "Bought TD Ameritrade.", "RU": "Купили конкурента TD Ameritrade за $26 млрд."},
        "lawsuits": {"EN": "187M$ fine for robo-fees.", "RU": "Штраф $187 млн за скрытые комиссии."}
    },
    "Fidelity": {
        "trust": 98.8, "founder": "Edward Johnson", "license": "SEC, FINRA", "fees": "0$", "withdraw": "1-3d", "assets": "Stocks, Crypto",
        "history": {"EN": "Asset giant since 1946.", "RU": "Гигант управления активами с 1946 года."},
        "fact": {"EN": "4 trillion under management.", "RU": "Управляют капиталом более $4 трлн."},
        "lawsuits": {"EN": "401k plan fee disputes.", "RU": "Судебные иски по пенсионным планам."}
    },
    "Tinkoff (RU)": {
        "trust": 88.5, "founder": "Oleg Tinkov", "license": "CBR (RU)", "fees": "0.025%+", "withdraw": "Instant", "assets": "RU Stocks, Currency",
        "history": {"EN": "Mobile-first ecosystem.", "RU": "Создали крупнейшую инвестиционную соцсеть в РФ."},
        "fact": {"EN": "Zero physical branches.", "RU": "Самый большой цифровой банк без отделений."},
        "lawsuits": {"EN": "Sanction ownership changes.", "RU": "Санкционные изменения владельцев в 2022."}
    },
    "Halyk Finance (KZ)": {
        "trust": 92.3, "founder": "Halyk Bank", "license": "AFSA, ARDFM", "fees": "0.02%+", "withdraw": "1d", "assets": "KASE, AIX, Global",
        "history": {"EN": "Part of 100-yr old bank.", "RU": "Инвестиционное крыло старейшего банка РК."},
        "fact": {"EN": "National pension manager.", "RU": "Управляет активами нацфондов."},
        "lawsuits": {"EN": "Minor reporting fines.", "RU": "Мелкие административные штрафы."}
    },
    "Saxo Bank": {
        "trust": 96.7, "founder": "Kim Fournais", "license": "FSA, FCA", "fees": "Commission", "withdraw": "1-2d", "assets": "Forex, CFDs",
        "history": {"EN": "Danish bank since 1992.", "RU": "Лидер онлайн-торговли в Европе с 1992."},
        "fact": {"EN": "First tech platform in EU.", "RU": "Первыми ввели торговый софт в Дании."},
        "lawsuits": {"EN": "Liquidity risk fines.", "RU": "Претензии по рискам ликвидности."}
    },
    "Swissquote": {
        "trust": 97.4, "founder": "Marc Bürki", "license": "FINMA", "fees": "Premium", "withdraw": "1-2d", "assets": "Stocks, Crypto",
        "history": {"EN": "Leading Swiss online bank.", "RU": "Ведущий онлайн-банк Швейцарии."},
        "fact": {"EN": "Public on SIX Exchange.", "RU": "Торгуется на швейцарской бирже."},
        "lawsuits": {"EN": "2015 SNB losses.", "RU": "Убытки от скачка франка в 2015."}
    },
    "E*TRADE": {
        "trust": 95.0, "founder": "William Porter", "license": "SEC, FINRA", "fees": "0$", "withdraw": "2-3d", "assets": "Stocks, Savings",
        "history": {"EN": "First online trade ever.", "RU": "Первыми провели онлайн-сделку в истории."},
        "fact": {"EN": "Famous 'Baby' ads.", "RU": "Знамениты рекламой с младенцем."},
        "lawsuits": {"EN": "Data protection fines.", "RU": "Штрафы за утечки данных."}
    },
    "Robinhood": {
        "trust": 85.2, "founder": "Vlad Tenev", "license": "SEC, FINRA", "fees": "0$", "withdraw": "3d", "assets": "Stocks, Options",
        "history": {"EN": "Democratizing finance.", "RU": "Основан для 'демократизации' биржи."},
        "fact": {"EN": "Zero fee trendsetter.", "RU": "Ввели моду на нулевые комиссии."},
        "lawsuits": {"EN": "70M$ systemic failure fine.", "RU": "Штраф $70 млн за сбои в 2021."}
    }
}

# --- 3. ФУНКЦИИ ---
def get_daily_key(): return datetime.now().strftime("%Y-%m-%d")

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
            txt_n = n.get('title', ''); sent = "NEUTRAL"
            if any(w in txt_n.lower() for w in pos_w): sent = "POSITIVE"
            elif any(w in txt_n.lower() for w in neg_w): sent = "NEGATIVE"
            results.append({"text": txt_n, "sent": sent, "src": n.get('publisher', {}).get('title', 'Media')})
        return results
    except: return []

# --- 4. ИНТЕРФЕЙС ---
st.sidebar.markdown('<div class="logo-text">RILLET</div>', unsafe_allow_html=True)
mode = st.sidebar.selectbox("MODE / РЕЖИМ", [txt["market"], txt["brokers"]])

if mode == txt["market"]:
    m_name = st.sidebar.selectbox(txt["market"], list(DB.keys()))
    c_choice = st.sidebar.radio(txt["currency"], ["USD ($)", "RUB (₽)", "KZT (₸)"])
    daily_token = get_daily_key()
    assets, rates = fetch_all(m_name, daily_token)
    sign = c_choice.split("(")[1][0]; r_val = rates.get(sign, 1.0)
    if not assets: st.error("Data unavailable / Данные недоступны")
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
        pct = ((f_prices[-1] / p_now) - 1) * 100; clr = "#00ffcc" if pct > 0.5 else ("#ff4b4b" if pct < -0.5 else "#ffcc00")
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-card'>{txt['current']}<br><h3>{p_now:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'>{txt['target']}<br><h3>{f_prices[-1]:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card' style='border-color:{clr}'>{txt['profit']}<br><h3>{pct:+.2f}%</h3></div>", unsafe_allow_html=True)
        st.write(f"#### {txt['chart_title']} {t_sel}")
        hist = item['DF']['Close'].tail(15).values * r_val / (item['P_USD'] * r_val / p_now)
        st.line_chart(np.append(hist, f_prices), color="#00ffcc")
        st.divider(); st.write(f"#### 🧠 {txt['news_title']} {t_sel}")
        news_data = analyze_news(t_sel, daily_token, lang)
        if news_data:
            n_col1, n_col2 = st.columns(2)
            for i, entry in enumerate(news_data):
                target_col = n_col1 if i % 2 == 0 else n_col2
                s_class = "bullish" if entry['sent'] == "POSITIVE" else ("bearish" if entry['sent'] == "NEGATIVE" else "")
                target_col.markdown(f"<div class='analysis-card'><p style='margin-bottom:5px;'>{entry['text']}</p><span class='{s_class}'>{entry['sent']}</span> | <span style='color:#888;'>{entry['src']}</span></div>", unsafe_allow_html=True)
            pos, neg = len([x for x in news_data if x['sent'] == "POSITIVE"]), len([x for x in news_data if x['sent'] == "NEGATIVE"])
            res_text = txt["buy"] if pos > neg else (txt["sell"] if neg > pos else txt["hold"])
            st.markdown(f"<h2 style='text-align:center; border:2px solid {clr}; padding:15px; border-radius:10px;'>{txt['signal']}: {res_text}</h2>", unsafe_allow_html=True)
        else: st.info(txt["no_news"])

elif mode == txt["brokers"]:
    st.write(f"## 🏛️ {txt['brokers']}")
    sorted_brokers = sorted(raw_brokers.items(), key=lambda x: x[1]['trust'], reverse=True)
    for b_name, b_info in sorted_brokers:
        trust = b_info['trust']; bar_clr = "#00ffcc" if trust > 90 else ("#ffcc00" if trust > 85 else "#ff4b4b")
        st.markdown(f"""
        <div class="analysis-card" style="margin-bottom:0px; border-bottom:none; border-radius:10px 10px 0 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-size: 20px; font-weight: bold;">{b_name}</div>
                <div style="text-align: right;">
                    <span style="font-size: 14px; color: #888;">{txt['trust']}</span><br>
                    <span style="font-size: 24px; color: {bar_clr}; font-weight: bold;">{trust}%</span>
                </div>
            </div>
            <div style="margin-top:10px;">
                <span class="info-tag">⚖️ {b_info['license']}</span>
                <span class="info-tag">💰 {b_info['fees']}</span>
                <span class="info-tag">⏱️ {b_info['withdraw']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        with st.expander(txt["details"]):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**📜 {txt['history']}:** {b_info['history'][lang]}")
                st.markdown(f"**👤 {txt['founder']}:** {b_info['founder']}")
                st.markdown(f"**🏗️ {txt['assets']}:** {b_info['assets']}")
            with col_b:
                st.markdown(f"**💡 {txt['fact']}:** {b_info['fact'][lang]}")
                st.markdown(f"**⚖️ {txt['lawsuits']}:** <span style='color:#ff4b4b;'>{b_info['lawsuits'][lang]}</span>", unsafe_allow_html=True)
        st.markdown(f"""<div style="background-color: #111; height: 5px; border-radius: 5px; margin-bottom: 25px;"><div style="background-color: {bar_clr}; width: {trust}%; height: 100%; border-radius: 5px;"></div></div>""", unsafe_allow_html=True)

st.caption(f"{txt['update']}: {get_daily_key()} 00:00")
