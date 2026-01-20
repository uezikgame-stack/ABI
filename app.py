import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- КОНФИГ И СТИЛИ ---
st.set_page_config(page_title="ABI Quantum", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(0, 0, 0, 0.85), rgba(0, 0, 0, 0.85)), 
                    url('https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJueXNoeXF6eXF6eXF6eXF6eXF6eXF6eXF6eXF6eXF6eCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3o7TKMGpxxcaOXYT6w/giphy.gif');
        background-size: cover;
    }
    .metric-card {
        background: rgba(15, 20, 30, 0.95); border: 1px solid #00ffcc33;
        padding: 25px; border-radius: 15px; border-left: 5px solid #00ffcc;
    }
    .google-dino-box {
        background: #f7f7f7; border-radius: 15px; padding: 60px; 
        text-align: center; border: 3px solid #ddd; color: #535353;
        margin: 20px auto; max-width: 900px;
    }
    h1, h2, h3 { color: #00ffcc !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ПОЛНАЯ БАЗА ТИКЕРОВ ---
MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC ADBE CRM AVGO QCOM PYPL TSMC ASML COST PEP NKE TM ORCL MCD DIS",
    "RF (Россия)": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME NVTK.ME GMKN.ME TATN.ME CHMF.ME ALRS.ME MTSS.ME PLZL.ME MOEX.ME",
    "KAZ (Казахстан)": "KCZ.L KMGZ.KZ HSBK.KZ KCELL.KZ NAC.KZ CCBN.KZ KZAP.KZ KEGC.KZ KZTK.KZ KZTO.KZ ASBN.KZ BAST.KZ",
    "CHINA": "BABA BIDU JD PDD LI NIO TCEHY BYDDY XPEV NTES MCHI KWEB FUTU BILI VIPS KC TME IQ EH ZLAB",
    "EUROPE": "ASML MC.PA VOW3.DE NESN.SW SIE.DE SAP.DE AIR.PA RMS.PA MBG.DE DHL.DE SAN.MC ALV.DE CS.PA BBVA.MC",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD XRP-USD LINK-USD AVAX-USD DOGE-USD MATIC-USD"
}

@st.cache_data(ttl=300)
def fetch_quantum_data(m_name):
    try:
        tickers = MARKETS[m_name]
        data = yf.download(tickers, period="1y", group_by='ticker', progress=False)
        rates = yf.download(["RUB=X", "KZT=X"], period="1d", progress=False)['Close']
        r_map = {"₽": float(rates["RUB=X"].iloc[-1]), "₸": float(rates["KZT=X"].iloc[-1]), "$": 1.0}
        
        final_list = []
        for t in tickers.split():
            try:
                df = data[t].dropna() if len(tickers.split()) > 1 else data.dropna()
                if df.empty: continue
                conv = r_map["₽"] if ".ME" in t else r_map["₸"] if (".KZ" in t or "KCZ" in t) else 1.0
                final_list.append({
                    "Asset": t, "p_usd": float(df['Close'].iloc[-1]) / conv,
                    "hist": (df['Close'].values / conv)[-30:],
                    "vol": float(df['Close'].pct_change().std()),
                    "trend": (df['Close'].iloc[-1] - df['Close'].iloc[-15]) / conv / 15
                })
            except: continue
        return final_list, r_map
    except: return [], {}

# --- ИНТЕРФЕЙС УПРАВЛЕНИЯ ---
st.sidebar.title("🛡️ ABI CONTROL")
m_choice = st.sidebar.selectbox("ВЫБОР РЫНКА:", list(MARKETS.keys()))
c_choice = st.sidebar.radio("ВАЛЮТА ТЕРМИНАЛА:", ["USD ($)", "RUB (₽)", "KZT (₸)"])
cap_input = st.sidebar.number_input("ВАШ КАПИТАЛ:", value=1000)

assets, rates = fetch_quantum_data(m_choice)

# --- ГЛАВНЫЙ МОДУЛЬ ---
if not assets:
    # ОРИГИНАЛЬНЫЙ ДИНОЗАВР ДЛЯ КЗ, РФ И ОСТАЛЬНЫХ
    st.markdown(f"""
        <div class="google-dino-box">
            <img src="https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExYnZ6Zmt4bm1oZ3R0Z3R0Z3R0Z3R0Z3R0Z3R0Z3R0Z3R0Z3R0ZCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/10X22vczHTQMfK/giphy.gif" width="250">
            <h2 style="color: #535353 !important; margin-top: 20px;">НЕТ ДАННЫХ ПО РЕГИОНУ: {m_choice}</h2>
            <p style="font-size: 18px; color: #666;">Попробуйте сменить провайдера или выбрать другой актив. Динозаврик ждет сигнала...</p>
            <p style="color: #bbb; font-size: 14px; margin-top: 20px;">STATUS_CODE: EMPTY_DATA_RESPONSE</p>
        </div>
    """, unsafe_allow_html=True)
else:
    c_sign = c_choice.split("(")[1][0]
    curr_rate = rates[c_sign]
    
    st.title(f"🚀 GLOBAL TERMINAL: {m_choice}")
    
    # 1. ТОП-25 СИСТЕМЫ
    df_assets = pd.DataFrame(assets).head(25)
    df_assets["Цена"] = (df_assets["p_usd"] * curr_rate).round(2)
    df_assets.index = np.arange(1, len(df_assets) + 1)
    st.dataframe(df_assets[["Asset", "Цена"]], height=350, use_container_width=True)

    # 2. ДЕТАЛЬНЫЙ АНАЛИЗ
    sel_ticker = st.selectbox("ВЫБЕРИТЕ АКТИВ ДЛЯ ПРОГНОЗА:", df_assets["Asset"].tolist())
    target_data = next(a for a in assets if a['Asset'] == sel_ticker)
    price_now = target_data['p_usd'] * curr_rate
    
    np.random.seed(42)
    forecast_line = [price_now]
    for _ in range(1, 15):
        noise = np.random.normal(0, price_now * target_data['vol'] * 0.5)
        forecast_line.append(max(forecast_line[-1] + (target_data['trend'] * curr_rate) + noise, 0.01))

    # --- ЛОГИКА ЦВЕТА (ПРОФИТ КРАСНЫЙ ПРИ МИНУСЕ) ---
    total_profit = (forecast_line[-1] * (cap_input/price_now * curr_rate)) - (cap_input * curr_rate)
    
    # Жесткий фикс цвета профита
    p_color = "#ff4b4b" if total_profit < 0 else "#00ffcc" 
    
    diff_pct = ((forecast_line[-1]/price_now)-1)*100
    sig_color = "#00ffcc" if diff_pct > 2 else "#ff4b4b" if diff_pct < -2 else "#888888"

    col1, col2, col3 = st.columns(3)
    col1.markdown(f"<div class='metric-card'>ТЕКУЩАЯ ЦЕНА<br><h2>{price_now:,.2f} {c_sign}</h2></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='metric-card'>ЦЕЛЬ (14 ДНЕЙ)<br><h2 style='color:{sig_color} !important;'>{forecast_line[-1]:,.2f} {c_sign}</h2></div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='metric-card'>ВАШ ПРОФИТ<br><h2 style='color:{p_color} !important;'>{total_profit:,.2f} {c_sign}</h2></div>", unsafe_allow_html=True)

    # ГРАФИК
    fig, ax = plt.subplots(figsize=(12, 4), facecolor='none')
    ax.set_facecolor('none')
    ax.plot(range(30), [x * curr_rate for x in target_data['hist']], color='white', alpha=0.2)
    ax.plot(range(29, 44), forecast_line, color=sig_color, linewidth=4, marker='o')
    ax.tick_params(colors='white')
    st.pyplot(fig)
