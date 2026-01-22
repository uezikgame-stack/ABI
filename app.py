import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. СТИЛЬ ОТ ШЭФА (НЕОН + ЕДИНАЯ РАМКА) ---
st.set_page_config(page_title="ABI ANALITIC", layout="wide")
st.markdown("""
    <style>
    /* Анимированная неоновая сетка на фоне */
    .stApp {
        background-color: #020508 !important;
        background-image: 
            linear-gradient(rgba(0, 255, 204, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 255, 204, 0.1) 1px, transparent 1px);
        background-size: 50px 50px;
        animation: moveGrid 15s linear infinite;
        color: #00ffcc;
    }
    @keyframes moveGrid {
        from { background-position: 0 0; }
        to { background-position: 50px 50px; }
    }

    /* ЕДИНАЯ РАМКА ДЛЯ ОШИБКИ И ИГРЫ */
    .unified-card {
        background: rgba(0, 0, 0, 0.95);
        border: 2px solid #ff4b4b;
        border-radius: 15px;
        padding: 30px;
        text-align: center;
        margin-top: 20px;
        box-shadow: 0 0 25px rgba(255, 75, 75, 0.3);
    }

    /* Очистка игрового поля Дино */
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
        top: -105px; /* Убираем текст сверху */
        left: 0;
        width: 100%;
        height: 400px;
        filter: invert(1) hue-rotate(180deg) contrast(1.4);
    }

    .metric-card { background: rgba(0, 0, 0, 0.9); border: 1px solid #00ffcc; padding: 15px; text-align: center; }
    h1, h2, h3, span, label, p { color: #00ffcc !important; }
    [data-testid="stSidebar"] { background-color: rgba(10, 14, 20, 0.95) !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ЛОГИКА ДАННЫХ ---
DB = {
    "KAZ (Казахстан)": ["KCZ.L", "KMGZ.KZ", "HSBK.KZ", "KCELL.KZ", "NAC.KZ", "CCBN.KZ", "KEGC.KZ", "KZTK.KZ", "KZTO.KZ", "ASBN.KZ", "BAST.KZ", "KMCP.KZ", "KASE.KZ", "KZIP.KZ", "KZMZ.KZ"],
    "EUROPE": ["ASML", "MC.PA", "VOW3.DE", "NESN.SW", "SIE.DE", "SAP.DE", "AIR.PA", "RMS.PA", "MBG.DE", "DHL.DE", "SAN.MC", "ALV.DE", "CS.PA", "BBVA.MC", "OR.PA"],
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "NFLX", "GOOGL", "META", "INTC", "ADBE", "CRM", "AVGO", "QCOM", "PYPL"],
    "RF (Россия)": ["SBER.ME", "GAZP.ME", "LKOH.ME", "YNDX", "ROSN.ME", "MGNT.ME", "NVTK.ME", "GMKN.ME", "CHMF.ME", "PLZL.ME", "TATN.ME", "MTSS.ME", "ALRS.ME", "AFLT.ME", "MAGN.ME"],
    "CRYPTO": ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "DOGE-USD", "DOT-USD"]
}

@st.cache_data(ttl=600)
def get_data_engine(m_name):
    try:
        tickers = DB[m_name]
        data = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', progress=False)
        rates_df = yf.download(["RUB=X", "KZT=X", "EURUSD=X"], period="1d", progress=False)['Close']
        r_map = {"₽": float(rates_df["RUB=X"].iloc[-1]), "$": 1.0, "₸": float(rates_df["KZT=X"].iloc[-1]), "EUR": float(rates_df["EURUSD=X"].iloc[-1])}
        
        clean = []
        for t in tickers:
            try:
                df = data[t].dropna()
                if df.empty: continue
                if any(x in t for x in [".ME", "YNDX"]): b = "₽"
                elif any(x in t for x in [".KZ", "KCZ"]): b = "₸"
                elif any(x in t for x in [".PA", ".DE", ".MC"]): b = "EUR"
                else: b = "$"
                curr_p = float(df['Close'].iloc[-1])
                p_usd = curr_p / r_map[b] if b != "EUR" else curr_p * r_map["EUR"]
                clean.append({"T": t, "P_USD": p_usd, "CH": (df['Close'].iloc[-1]/df['Close'].iloc[0]-1), "AVG": df['Close'].pct_change().mean(), "STD": df['Close'].pct_change().std(), "DF": df})
            except: continue
        return clean, r_map
    except: return None, None

# --- 3. ИНТЕРФЕЙС ---
st.sidebar.title("ABI SETTINGS")
m_sel = st.sidebar.selectbox("MARKET", list(DB.keys()))
c_sel = st.sidebar.radio("CURRENCY", ["USD ($)", "RUB (₽)", "KZT (₸)"])

assets, rates = get_data_engine(m_sel)
st.title("🚀 ABI ANALITIC")

if not assets:
    # --- ЕДИНАЯ РАМКА С ОБНОВЛЕННЫМ ТЕКСТОМ ---
    st.markdown(f"""
        <div class="unified-card">
            <h1>⚠️ {m_sel} ВРЕМЕННО НЕДОСТУПЕН</h1>
            <div class="dino-crop">
                <iframe src="https://chromedino.com/" frameborder="0" scrolling="no"></iframe>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    sign = c_sel.split("(")[1][0]
    r_target = rates[sign]
    
    # ... (остальная часть кода для отображения графиков и прогнозов) ...
    st.success("Данные загружены, шэф!")
