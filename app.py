import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit.components.v1 as components

# --- LUXURY TURBO DESIGN ---
st.set_page_config(page_title="ABI Terminal", layout="wide")
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.9), rgba(0,0,0,0.9)), 
                    url('https://images.unsplash.com/photo-1611974717482-98252c00bc20?q=80&w=2070');
        background-size: cover; background-attachment: fixed;
    }
    .main-nav {
        display: flex; gap: 20px; background: rgba(0, 255, 204, 0.05);
        padding: 15px; border-radius: 15px; border: 1px solid #00ffcc33; margin-bottom: 20px;
    }
    .metric-card {
        background: rgba(10, 15, 25, 0.95); border-left: 5px solid #00ffcc;
        padding: 20px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,255,204,0.1);
    }
    h1, h2, h3 { color: #00ffcc !important; font-family: 'Courier New', monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- ОТДЕЛЬНЫЙ ИНТЕРФЕЙС МЕНЮ ---
tab1, tab2 = st.tabs(["🚀 ТЕРМИНАЛ", "🦖 ИГРОВАЯ КОНСОЛЬ"])

with tab2:
    st.markdown("### 🎮 ABI GAMING ZONE")
    components.iframe("https://wayou.github.io/t-rex-runner/", height=400)

with tab1:
    st.title("🛡️ ABI: QUANTUM TURBO TERMINAL")

    # --- SIDEBAR: FAST CONFIG ---
    st.sidebar.header("🏦 Capital Settings")
    budget = st.sidebar.number_input("Капитал", value=1000)
    currency = st.sidebar.radio("Валюта:", ["USD ($)", "RUB (₽)", "KZT (₸)"])
    
    market = st.sidebar.selectbox("Регион (Топ-15):", ["USA", "RF (Россия)", "KAZ (Казахстан)", "CHINA", "EUROPE", "CRYPTO"])

    # --- ТУРБО-ЗАГРУЗКА ДАННЫХ ---
    MARKETS = {
        "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC ADBE CRM AVGO QCOM PYPL",
        "RF (Россия)": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME NVTK.ME GMKN.ME TATN.ME CHMF.ME ALRS.ME MTSS.ME PLZL.ME MOEX.ME SNGS.ME",
        "KAZ (Казахстан)": "KCZ.L KMGZ.KZ HSBK.KZ KCELL.KZ NAC.KZ CCBN.KZ KZAP.KZ KEGC.KZ KZTK.KZ KZTO.KZ ASBN.KZ BAST.KZ",
        "CHINA": "BABA BIDU JD PDD LI NIO TCEHY BYDDY XPEV NTES MCHI KWEB FUTU BILI VIPS",
        "EUROPE": "ASML MC.PA VOW3.DE NESN.SW SIE.DE SAP.DE AIR.PA RMS.PA MBG.DE DHL.DE SAN.MC ALV.DE CS.PA BBVA.MC",
        "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD XRP-USD LINK-USD AVAX-USD DOGE-USD MATIC-USD TRX-USD LTC-USD"
    }

    @st.cache_data(ttl=300)
    def fast_load(market_name):
        tickers = MARKETS[market_name]
        # Загружаем всё одним махом для скорости
        data = yf.download(tickers, period="1y", group_by='ticker', progress=False)
        
        # Курсы валют
        rates_data = yf.download(["RUB=X", "KZT=X"], period="1d", progress=False)['Close']
        r = {"₽": float(rates_data["RUB=X"].iloc[-1]), "₸": float(rates_data["KZT=X"].iloc[-1]), "$": 1.0}
        
        results = []
        for t in tickers.split():
            try:
                df = data[t].dropna()
                if df.empty: continue
                
                curr_price = float(df['Close'].iloc[-1])
                # Фикс конвертации
                conv = r["₽"] if ".ME" in t else r["₸"] if (".KZ" in t or "KCZ" in t) else 1.0
                p_usd = curr_price / conv
                
                results.append({
                    "ticker": t, "p_usd": p_usd,
                    "history": (df['Close'].values / conv)[-30:],
                    "vol": float(df['Close'].pct_change().std()),
                    "trend": (df['Close'].iloc[-1] - df['Close'].iloc[-15]) / conv / 15
                })
            except: continue
        return results, r

    with st.spinner('Подключаюсь к квантовым серверам...'):
        assets, rates = fast_load(market)
        curr_sym = currency.split("(")[1][0]
        rate_to_use = rates[curr_sym]

    if assets:
        df_view = pd.DataFrame(assets)
        df_view["Цена"] = (df_view["p_usd"] * rate_to_use).round(2)
        
        st.dataframe(df_view[["ticker", "Цена"]].set_index("ticker").T, use_container_width=True)

        selected = st.selectbox("ВЫБЕРИТЕ АКТИВ:", [a['ticker'] for a in assets])
        asset = next(a for a in assets if a['ticker'] == selected)
        
        # --- ПРОГНОЗ 14 ДНЕЙ (БЕЗ ОШИБОК) ---
        p_now = asset['p_usd'] * rate_to_use
        np.random.seed(42)
        forecast = [p_now]
        for i in range(1, 15):
            change = (asset['trend'] * rate_to_use) + np.random.normal(0, p_now * asset['vol'] * 0.5)
            forecast.append(max(forecast[-1] + change, 0.01))

        # ИНТЕРФЕЙС МЕТРИК
        chg = ((forecast[-1]/p_now)-1)*100
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f"<div class='metric-card'>💸 ЦЕНА<br><h2>{p_now:,.2f} {curr_sym}</h2></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='metric-card'>🎯 ЦЕЛЬ<br><h2>{forecast[-1]:,.2f} {curr_sym}</h2><small>{chg:+.2f}%</small></div>", unsafe_allow_html=True)
        with c3: 
            prof = (forecast[-1] * (budget/p_now * rate_to_use)) - (budget * rate_to_use)
            st.markdown(f"<div class='metric-card'>💰 ПРОФИТ<br><h2>{prof:,.2f} {curr_sym}</h2></div>", unsafe_allow_html=True)

        # --- СТАБИЛЬНЫЙ ГРАФИК ---
        fig, ax = plt.subplots(figsize=(12, 4), facecolor='none')
        ax.set_facecolor('none')
        h_vals = [x * rate_to_use for x in asset['history']]
        
        # Х-оси без нахлеста
        ax.plot(range(len(h_vals)), h_vals, color='gray', alpha=0.5, label="История")
        ax.plot(range(len(h_vals)-1, len(h_vals)+14), forecast, color='#00ffcc', linewidth=3, marker='o', label="ABI PRO")
        
        ax.tick_params(colors='white')
        st.pyplot(fig)
