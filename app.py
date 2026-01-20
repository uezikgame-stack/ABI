import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- LUXURY DESIGN ---
st.set_page_config(page_title="ABI Terminal", layout="wide")
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), 
                    url('https://images.unsplash.com/photo-1639762681485-074b7f938ba0?q=80&w=2232&auto=format&fit=crop');
        background-size: cover; background-attachment: fixed;
    }
    div[data-testid="metric-container"] {
        background: rgba(10, 10, 15, 0.9); border: 1px solid #00ffcc;
        padding: 20px; border-radius: 15px; backdrop-filter: blur(10px);
    }
    .signal-box {
        padding: 20px; border-radius: 15px; text-align: center;
        font-weight: bold; font-size: 24px; margin: 10px 0;
        border: 2px solid #00ffcc; background: rgba(0, 255, 204, 0.1);
    }
    h1, h3 { color: #00ffcc !important; text-shadow: 0 0 10px #00ffcc; }
    .nav-menu {
        display: flex; justify-content: space-around;
        background: rgba(0, 255, 204, 0.1); padding: 10px;
        border-radius: 10px; border: 1px solid rgba(0, 255, 204, 0.3);
        margin-bottom: 25px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- MENU ---
st.markdown('<div class="nav-menu"><span style="color: #00ffcc;">🏠 ТЕРМИНАЛ</span><span style="color: #888;">📈 АНАЛИТИКА</span><span style="color: #888;">🎓 ОБУЧЕНИЕ</span></div>', unsafe_allow_html=True)

st.title("🛡️ ABI: GLOBAL QUANTUM TERMINAL")

# --- SIDEBAR ---
st.sidebar.header("🏦 Настройки")
budget_base = st.sidebar.number_input("Ваш капитал ($)", value=1000, step=100)
currency = st.sidebar.radio("Валюта:", ["USD ($)", "RUB (₽)", "KZT (₸)"])

@st.cache_data(ttl=3600)
def get_rates():
    try:
        r = yf.download(["RUB=X", "KZT=X"], period="1d", progress=False)['Close'].iloc[-1]
        return {"₽": float(r["RUB=X"]), "₸": float(r["KZT=X"]), "$": 1.0}
    except:
        return {"₽": 91.5, "₸": 485.0, "$": 1.0}

rates = get_rates()
curr_sym = currency.split("(")[1][0]
rate_to_use = rates[curr_sym]

st.sidebar.header("🌍 Рынки")
market = st.sidebar.selectbox("Регион:", ["USA", "RF (Россия)", "KAZ (Казахстан)", "CHINA (Китай)", "EUROPE (Европа)", "CRYPTO"])

# Максимально полный список акций
MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC ADBE CRM AVGO QCOM PYPL BABA JD NIO",
    "RF (Россия)": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME NVTK.ME GMKN.ME TATN.ME CHMF.ME ALRS.ME MTSS.ME",
    "KAZ (Казахстан)": "KCZ.L KMGZ.KZ HSBK.KZ KCELL.KZ NAC.KZ CCBN.KZ KZAP.KZ",
    "CHINA (Китай)": "BABA BIDU JD PDD LI NIO TCEHY BYDDY",
    "EUROPE (Европа)": "ASML MC.PA VOW3.DE NESN.SW SIE.DE SAP.DE AIR.PA",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD XRP-USD"
}

@st.cache_data(ttl=300)
def load_data(tickers):
    # Пытаемся загрузить данные по одному, чтобы не терять весь список
    results = []
    for t in tickers.split():
        try:
            ticker_obj = yf.Ticker(t)
            df = ticker_obj.history(period="1y")
            if df.empty: continue
            
            p_raw = float(df['Close'].iloc[-1])
            p_usd = p_raw / (rates["₽"] if ".ME" in t else rates["₸"] if (".KZ" in t or "KCZ" in t) else 1)
            results.append({
                "ticker": t, "p_usd": p_usd, 
                "vol": float(df['Close'].pct_change().std()),
                "trend": (df['Close'].iloc[-1] - df['Close'].iloc[-15])/15,
                "history_usd": (df['Close'].values / (rates["₽"] if ".ME" in t else rates["₸"] if (".KZ" in t or "KCZ" in t) else 1))[-25:]
            })
        except: continue
    return results

assets = load_data(MARKETS[market])

if not assets:
    # Тот самый Динозаврик, если данных нет
    st.markdown("<h1 style='text-align: center; font-size: 100px;'>🦖</h1>", unsafe_allow_html=True)
    st.error("Упс! Биржа временно недоступна. Попробуйте другой регион или обновите страницу.")
else:
    df_view = pd.DataFrame(assets)
    df_view["Цена"] = (df_view["p_usd"] * rate_to_use).round(2)
    st.dataframe(df_view[["ticker", "Цена"]].rename(columns={"Цена": f"Цена ({curr_sym})"}), use_container_width=True)

    st.divider()
    selected = st.selectbox("ВЫБЕРИТЕ АКТИВ:", df_view["ticker"].tolist())

    if selected:
        asset = next(item for item in assets if item["ticker"] == selected)
        p_now = asset['p_usd'] * rate_to_use
        
        np.random.seed(42)
        forecast = [p_now]
        for i in range(1, 15):
            noise = np.random.normal(0, p_now * asset['vol'] * 0.4)
            val = forecast[-1] + (asset['trend'] * (rate_to_use / 10) * (0.85**i)) + noise
            forecast.append(max(val, 0.01))

        # СИСТЕМА СИГНАЛОВ
        change_pct = ((forecast[-1] / p_now) - 1) * 100
        if change_pct > 5: sig_text, sig_col, sig_hold = "🚀 СИЛЬНАЯ ПОКУПКА", "#00ffcc", "7-14 дней"
        elif change_pct < -5: sig_text, sig_col, sig_hold = "🆘 СРОЧНО ПРОДАВАТЬ", "#ff4b4b", "Выходить сейчас"
        else: sig_text, sig_col, sig_hold = "⚖️ НЕЙТРАЛЬНО", "#888888", "Наблюдать"

        st.markdown(f'<div class="signal-box" style="color: {sig_col}; border-color: {sig_col};">РЕКОМЕНДАЦИЯ: {sig_text}<br><span style="font-size: 16px; color: white;">Рекомендуемый срок: {sig_hold}</span></div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("СЕЙЧАС", f"{p_now:,.2f} {curr_sym}")
        c2.metric("ПРОГНОЗ (14Д)", f"{forecast[-1]:,.2f} {curr_sym}", f"{change_pct:+.2f}%")
        profit = (forecast[-1] * (budget_base/p_now * rate_to_use)) - (budget_base * rate_to_use)
        c3.metric("ПРОФИТ", f"{profit:,.2f} {curr_sym}")

        fig, ax = plt.subplots(figsize=(12, 4), facecolor='none')
        ax.set_facecolor('none')
        h_disp = [h * rate_to_use for h in asset['history_usd']]
        ax.plot(h_disp, color='#444444', alpha=0.6, label="История")
        ax.plot(range(len(h_disp)-1, len(h_disp)+15), forecast, marker='o', color=sig_col, linewidth=3, label="ABI Forecast")
        ax.tick_params(colors='white')
        st.pyplot(fig)
