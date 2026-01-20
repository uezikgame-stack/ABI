import streamlit as st
import yfinance as yf
import pandas as pd

# --- 1. ТЕРМИНАЛЬНЫЙ ДИЗАЙН ---
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
    /* Стандартные карточки */
    .metric-card {
        background: rgba(0, 0, 0, 0.9);
        border: 1px solid #00ffcc;
        padding: 20px;
        text-align: center;
        height: 120px;
    }
    /* КРАСНАЯ КАРТОЧКА (Стиль ошибки из твоего скриншота) */
    .error-card {
        background: rgba(255, 75, 75, 0.25) !important;
        border: 1px solid #ff4b4b !important;
        padding: 20px;
        text-align: center;
        height: 120px;
    }
    h1, h2, h3, p, span, div, label { color: #00ffcc !important; }
    .stDataFrame { border: 1px solid #00ffcc !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ЛОКАЛИЗАЦИЯ ---
UI = {
    "RU": {
        "market": "РЫНОК", "curr": "ВАЛЮТА", "depo": "КАПИТАЛ", "lang": "ЯЗЫК",
        "top": "ВЕРТИКАЛЬНЫЙ ТОП АКТИВОВ", "select": "ВЫБЕРИ ДЛЯ ПРОГНОЗА:",
        "now": "ТЕКУЩАЯ ЦЕНА", "target": "ЦЕЛЬ (14 ДНЕЙ)", "profit": "ВАШ ПРОФИТ",
        "buy": "ПОКУПАТЬ", "sell": "ПРОДАВАТЬ", "err": "НЕТ ДАННЫХ", "signal": "СИГНАЛ"
    },
    "EN": {
        "market": "MARKET", "curr": "CURRENCY", "depo": "CAPITAL", "lang": "LANGUAGE",
        "top": "VERTICAL TOP ASSETS", "select": "SELECT FOR FORECAST:",
        "now": "CURRENT PRICE", "target": "TARGET (14d)", "profit": "YOUR PROFIT",
        "buy": "BUY", "sell": "SELL", "err": "NO DATA", "signal": "SIGNAL"
    }
}

MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META",
    "CHINA": "BABA BIDU JD PDD LI NIO TCEHY BYDDY XPEV",
    "EUROPE": "ASML MC.PA VOW3.DE NESN.SW SIE.DE SAP.DE",
    "RF (Россия)": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME",
    "KAZ (Казахстан)": "KCZ.L KMGZ.KZ HSBK.KZ KCELL.KZ NAC.KZ CCBN.KZ",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD XRP-USD"
}

@st.cache_data(ttl=300)
def load_data(m_name):
    try:
        tickers = MARKETS[m_name]
        data = yf.download(tickers, period="1mo", group_by='ticker', progress=False)
        rates = yf.download(["RUB=X", "KZT=X"], period="1d", progress=False)['Close']
        r_map = {"₽": float(rates["RUB=X"].iloc[-1]), "₸": float(rates["KZT=X"].iloc[-1]), "$": 1.0}
        res = []
        for t in tickers.split():
            try:
                df = data[t].dropna() if len(tickers.split()) > 1 else data.dropna()
                if df.empty: continue
                conv = r_map["₽"] if ".ME" in t else r_map["₸"] if (".KZ" in t or "KCZ" in t) else 1.0
                res.append({"T": t, "P": float(df['Close'].iloc[-1]) / conv, "CH": (df['Close'].iloc[-1]/df['Close'].iloc[0]-1)})
            except: continue
        return res, r_map
    except: return None, {}

# --- 3. ИНТЕРФЕЙС ---
ln = st.sidebar.radio("ЯЗЫК / LANGUAGE", ["RU", "EN"])
m_sel = st.sidebar.selectbox(UI[ln]["market"], list(MARKETS.keys()))
c_sel = st.sidebar.radio(UI[ln]["curr"], ["USD ($)", "RUB (₽)", "KZT (₸)"])
depo = st.sidebar.number_input(UI[ln]["depo"], value=1000)

assets, rates = load_data(m_sel)

if not assets:
    st.subheader(UI[ln]["err"])
else:
    sign = c_sel.split("(")[1][0]
    rate = rates.get(sign, 1.0)
    
    st.title(f"🚀 TERMINAL: {m_sel}")
    
    # ТАБЛИЦА (Вертикальная)
    df_v = pd.DataFrame(assets)
    df_v["PRICE"] = (df_v["P"] * rate).round(2)
    st.dataframe(df_v[["T", "PRICE"]].set_index("T"), use_container_width=True, height=300)

    # ВЫБОР И РАСЧЕТ
    target_t = st.selectbox(UI[ln]["select"], df_v["T"].tolist())
    item = next(x for x in assets if x['T'] == target_t)
    p_now = item['P'] * rate
    tr = -0.12 if "BTC" in target_t else item['CH'] # Медвежий BTC
    p_target = p_now * (1 + tr)
    profit = (p_target * (depo/p_now)) - depo

    # СИГНАЛ
    sig_text = UI[ln]["sell"] if tr < -0.02 else UI[ln]["buy"]
    p_color = "#ff4b4b" if profit < 0 else "#00ffcc"
    st.markdown(f"<h2 style='text-align:center; border:1px solid {p_color}; padding:10px;'>{UI[ln]['signal']}: {sig_text}</h2>", unsafe_allow_html=True)

    # --- ТРИ КАРТОЧКИ В ОДИН РЯД ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"<div class='metric-card'>{UI[ln]['now']}<br><h3>{p_now:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"<div class='metric-card'>{UI[ln]['target']}<br><h3>{p_target:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    
    with col3:
        # Если минус — применяем стиль красной ошибки
        style = "error-card" if profit < 0 else "metric-card"
        txt_color = "#ffffff" if profit < 0 else "#00ffcc"
        st.markdown(f"""
            <div class='{style}'>
                {UI[ln]['profit']}<br>
                <h3 style='color: {txt_color} !important;'>{profit:,.2f} {sign}</h3>
            </div>
            """, unsafe_allow_html=True)
