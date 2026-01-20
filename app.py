import streamlit as st
import yfinance as yf
import pandas as pd

# --- 1. НАСТРОЙКИ И КИБЕР-СТИЛЬ ---
st.set_page_config(page_title="ABI Quantum", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #020508;
        background-image: 
            linear-gradient(rgba(0, 255, 204, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 255, 204, 0.05) 1px, transparent 1px);
        background-size: 30px 30px;
    }
    /* Стиль красной ячейки (как в твоем логе ошибок) */
    .error-box {
        background-color: rgba(255, 75, 75, 0.2);
        border: 1px solid #ff4b4b;
        padding: 15px;
        text-align: center;
        width: 100%;
        margin: 10px 0;
    }
    .metric-card {
        background: rgba(0, 0, 0, 0.9);
        border: 1px solid #00ffcc;
        padding: 20px;
        text-align: center;
    }
    h1, h2, h3, p, span, div, label { color: #00ffcc !important; }
    .stDataFrame { border: 1px solid #00ffcc !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. СЛОВАРЬ ЯЗЫКОВ ---
UI = {
    "RU": {
        "market": "РЫНОК", "curr": "ВАЛЮТА", "depo": "ДЕПОЗИТ", "lang": "ЯЗЫК",
        "top": "ВЕРТИКАЛЬНЫЙ ТОП АКТИВОВ", "select": "ВЫБЕРИ ДЛЯ ПРОГНОЗА:",
        "now": "СЕЙЧАС", "target": "ЦЕЛЬ (14д)", "profit": "ПРОФИТ",
        "buy": "ПОКУПАТЬ", "sell": "ПРОДАВАТЬ", "err": "СЕЙЧАС НЕ ДОСТУПЕН",
        "signal": "СИГНАЛ", "ticker": "ТИКЕР", "price": "ЦЕНА"
    },
    "EN": {
        "market": "MARKET", "curr": "CURRENCY", "depo": "CAPITAL", "lang": "LANGUAGE",
        "top": "VERTICAL TOP ASSETS", "select": "SELECT FOR FORECAST:",
        "now": "CURRENT", "target": "TARGET (14d)", "profit": "PROFIT",
        "buy": "BUY", "sell": "SELL", "err": "CURRENTLY UNAVAILABLE",
        "signal": "SIGNAL", "ticker": "TICKER", "price": "PRICE"
    }
}

MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX",
    "CHINA": "BABA BIDU JD PDD LI NIO TCEHY",
    "EUROPE": "ASML MC.PA VOW3.DE NESN.SW SIE.DE",
    "RF (Россия)": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME",
    "KAZ (Казахстан)": "KCZ.L KMGZ.KZ HSBK.KZ KCELL.KZ",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD"
}

@st.cache_data(ttl=300)
def load_data(m_name):
    try:
        tickers = MARKETS[m_name]
        data = yf.download(tickers, period="1mo", group_by='ticker', progress=False)
        rates = yf.download(["RUB=X", "KZT=X"], period="1d", progress=False)['Close']
        r_map = {"₽": float(rates["RUB=X"].iloc[-1]), "₸": float(rates["KZT=X"].iloc[-1]), "$": 1.0}
        
        results = []
        for t in tickers.split():
            try:
                df = data[t].dropna() if len(tickers.split()) > 1 else data.dropna()
                if df.empty: continue
                conv = r_map["₽"] if ".ME" in t else r_map["₸"] if (".KZ" in t or "KCZ" in t) else 1.0
                results.append({
                    "T": t, "P_USD": float(df['Close'].iloc[-1]) / conv,
                    "CH": (df['Close'].iloc[-1] / df['Close'].iloc[0] - 1)
                })
            except: continue
        return results, r_map
    except: return None, {}

# --- 3. ИНТЕРФЕЙС ---
ln = st.sidebar.radio("ЯЗЫК / LANGUAGE", ["RU", "EN"])
m_sel = st.sidebar.selectbox(UI[ln]["market"], list(MARKETS.keys()))
c_sel = st.sidebar.radio(UI[ln]["curr"], ["USD ($)", "RUB (₽)", "KZT (₸)"])
depo = st.sidebar.number_input(UI[ln]["depo"], value=1000)

assets, rates = load_data(m_sel)

if not assets:
    st.markdown(f"<div class='error-box'>{UI[ln]['err']}</div>", unsafe_allow_html=True)
else:
    sign = c_sel.split("(")[1][0]
    rate = rates.get(sign, 1.0)
    
    st.title(f"🚀 ABI: {m_sel}")
    
    # ВЕРТИКАЛЬНАЯ ТАБЛИЦА
    df_res = pd.DataFrame(assets)
    df_res[UI[ln]["price"]] = (df_res["P_USD"] * rate).round(2)
    st.subheader(UI[ln]["top"])
    st.dataframe(df_res[["T", UI[ln]["price"]]].set_index("T"), use_container_width=True)

    # АНАЛИЗ И КРАСНЫЙ ПРОФИТ
    sel_t = st.selectbox(UI[ln]["select"], [x['T'] for x in assets])
    item = next(x for x in assets if x['T'] == sel_t)
    p_now = item['P_USD'] * rate
    
    # Расчет (BTC на слив по дефолту)
    tr = -0.15 if "BTC" in sel_t else item['CH']
    p_target = p_now * (1 + tr)
    profit = (p_target * (depo/p_now)) - depo

    # ЛОГИКА ЦВЕТА: ЕСЛИ МИНУС — КРАСНАЯ ПЛАШКА КАК В ОШИБКЕ
    if profit < 0:
        st.markdown(f"""
            <div class='error-box'>
                <span style='font-size: 1.2em;'>{UI[ln]['profit']}: {profit:,.2f} {sign}</span><br>
                <strong>{UI[ln]['signal']}: {UI[ln]['sell']}</strong>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"<h2 style='text-align:center;'>{UI[ln]['signal']}: {UI[ln]['buy']}</h2>", unsafe_allow_html=True)

    # МЕТРИКИ
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'>{UI[ln]['now']}<br><h3>{p_now:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>{UI[ln]['target']}<br><h3>{p_target:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    
    # Если профит положительный, рисуем обычную карточку
    if profit >= 0:
        c3.markdown(f"<div class='metric-card'>{UI[ln]['profit']}<br><h3>{profit:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
