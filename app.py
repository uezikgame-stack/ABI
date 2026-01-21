import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. ИНТЕРФЕЙС ---
st.set_page_config(page_title="ABI ANALITIC", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #020508; color: #00ffcc; }
    .metric-card { background: rgba(0, 0, 0, 0.9); border: 1px solid #00ffcc; padding: 15px; text-align: center; height: 110px; }
    .error-card { background: rgba(255, 75, 75, 0.25); border: 1px solid #ff4b4b; padding: 15px; text-align: center; height: 110px; }
    h1, h2, h3, span, label, p { color: #00ffcc !important; }
    .stDataFrame { border: 1px solid #00ffcc !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ЛОКАЛИЗАЦИЯ ---
UI = {
    "RU": {
        "market": "РЫНОК", "curr": "ВАЛЮТА", "depo": "КАПИТАЛ", "top": "РЕЙТИНГ АКТИВОВ (ТОП 15)",
        "select": "ВЫБЕРИ ДЛЯ АНАЛИЗА:", "now": "ТЕКУЩАЯ", "target": "ЦЕЛЬ (7д)", "profit": "ПРОФИТ",
        "signal": "СИГНАЛ", "buy": "ПОКУПАТЬ", "sell": "ПРОДАВАТЬ", "day": "ДЕНЬ", "price": "ЦЕНА", "forecast": "АНАЛИЗ: ИСТОРИЯ И ПРОГНОЗ"
    },
    "EN": {
        "market": "MARKET", "curr": "CURRENCY", "depo": "CAPITAL", "top": "ASSET RATING (TOP 15)",
        "select": "SELECT FOR ANALYSIS:", "now": "CURRENT", "target": "TARGET (7d)", "profit": "PROFIT",
        "signal": "SIGNAL", "buy": "BUY", "sell": "SELL", "day": "DAY", "price": "PRICE", "forecast": "ANALYSIS: HISTORY & FORECAST"
    }
}

# --- 3. БАЗА АКТИВОВ ---
DB = {
    "KAZ (Казахстан)": ["KCZ.L", "KMGZ.KZ", "HSBK.KZ", "KCELL.KZ", "NAC.KZ", "CCBN.KZ", "KEGC.KZ", "KZTK.KZ", "KZTO.KZ", "ASBN.KZ", "BAST.KZ", "KMCP.KZ", "KASE.KZ", "KZIP.KZ", "KZMZ.KZ"],
    "EUROPE": ["ASML", "MC.PA", "VOW3.DE", "NESN.SW", "SIE.DE", "SAP.DE", "AIR.PA", "RMS.PA", "MBG.DE", "DHL.DE", "SAN.MC", "ALV.DE", "CS.PA", "BBVA.MC", "OR.PA"],
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "NFLX", "GOOGL", "META", "INTC", "ADBE", "CRM", "AVGO", "QCOM", "PYPL"],
    "CHINA": ["BABA", "BIDU", "JD", "PDD", "LI", "NIO", "TCEHY", "BYDDY", "XPEV", "NTES", "MCHI", "KWEB", "FUTU", "BILI", "VIPS"],
    "RF (Россия)": ["SBER.ME", "GAZP.ME", "LKOH.ME", "YNDX", "ROSN.ME", "MGNT.ME", "NVTK.ME", "GMKN.ME", "TATN.ME", "CHMF.ME", "ALRS.ME", "MTSS.ME", "NLMK.ME", "PLZL.ME", "VTBR.ME"],
    "CRYPTO": ["BTC-USD", "ETH-USD", "SOL-USD", "DOT-USD", "ADA-USD", "XRP-USD", "LINK-USD", "AVAX-USD", "DOGE-USD", "MATIC-USD", "TRX-USD", "LTC-USD", "SHIB-USD", "BCH-USD", "NEAR-USD"]
}

@st.cache_data(ttl=600)
def get_global_data(m_name):
    tickers = DB[m_name]
    data = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', progress=False)
    rates_df = yf.download(["RUB=X", "KZT=X", "EURUSD=X"], period="1d", progress=False)['Close']
    
    r_map = {
        "₽": float(rates_df["RUB=X"].iloc[-1]), 
        "$": 1.0, 
        "₸": float(rates_df["KZT=X"].iloc[-1]),
        "EUR": float(rates_df["EURUSD=X"].iloc[-1])
    }
    
    clean_assets = []
    for t in tickers:
        try:
            df = data[t].dropna()
            if df.empty: continue
            
            # Определяем исходную валюту акции
            if ".ME" in t: base = "₽"
            elif ".KZ" in t or "KCZ" in t: base = "₸"
            elif ".PA" in t or ".DE" in t or ".MC" in t: base = "EUR"
            else: base = "$"
            
            # Конвертируем всё в USD для универсального хранения
            last_val = float(df['Close'].iloc[-1])
            p_usd = last_val / r_map[base] if base != "EUR" else last_val * r_map["EUR"]
            
            returns = df['Close'].pct_change().dropna()
            clean_assets.append({
                "T": t, "P_USD": p_usd, "AVG": returns.mean(), "STD": returns.std(), 
                "CH": (df['Close'].iloc[-1]/df['Close'].iloc[0]-1), "DF": df, "BASE": base
            })
        except: continue
    return clean_assets, r_map

# --- 4. ЛОГИКА ТЕРМИНАЛА ---
ln = st.sidebar.radio("LANGUAGE", ["RU", "EN"])
m_sel = st.sidebar.selectbox(UI[ln]["market"], list(DB.keys()))
c_sel = st.sidebar.radio(UI[ln]["curr"], ["USD ($)", "RUB (₽)", "KZT (₸)"])
capital = st.sidebar.number_input(UI[ln]["depo"], value=1000)

assets, all_rates = get_global_data(m_sel)
sign = c_sel.split("(")[1][0]
target_rate = all_rates[sign]

st.title("🚀 ABI ANALITIC")

if assets:
    # ТАБЛИЦА ТОП-15 (СОРТИРОВКА + КОНВЕРТАЦИЯ)
    df_top = pd.DataFrame(assets)
    df_top["PRICE"] = (df_top["P_USD"] * target_rate).round(2)
    df_top = df_top.sort_values(by="CH", ascending=False).reset_index(drop=True)
    df_top.index += 1
    
    st.subheader(UI[ln]["top"])
    st.dataframe(df_top[["T", "PRICE"]], use_container_width=True, height=455)

    # АНАЛИЗ ВЫБРАННОГО АКТИВА
    target_t = st.selectbox(UI[ln]["select"], df_top["T"].tolist())
    item = next(x for x in assets if x['T'] == target_t)
    
    # ТЕКУЩАЯ ЦЕНА В ВЫБРАННОЙ ВАЛЮТЕ
    price_now = item['P_USD'] * target_rate
    mu, sigma = item['AVG'], item['STD'] if item['STD'] > 0 else 0.02
    
    # ГЕНЕРАЦИЯ ПРОГНОЗА
    future_prices = []
    temp_p = price_now
    for _ in range(7):
        temp_p *= (1 + np.random.normal(mu, sigma))
        future_prices.append(temp_p)
    
    # ТОЧНЫЙ РАСЧЕТ ПРОФИТА В ДЕНЬГАХ
    # Формула: (Цена_Будущая - Цена_Сейчас) * (Капитал / Цена_Сейчас)
    daily_profits = [(p - price_now) * (capital / price_now) for p in future_prices]

    # МЕТРИКИ (КАРТОЧКИ)
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'>{UI[ln]['now']}<br><h3>{price_now:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>{UI[ln]['target']}<br><h3>{future_prices[-1]:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    
    final_profit = daily_profits[-1]
    card_style = "error-card" if final_profit < 0 else "metric-card"
    c3.markdown(f"<div class='{card_style}'>{UI[ln]['profit']}<br><h3>{final_profit:,.2f} {sign}</h3></div>", unsafe_allow_html=True)

    # ГРАФИК И ТАБЛИЦА
    st.divider()
    col_chart, col_table = st.columns([2, 1])
    
    with col_chart:
        st.subheader(UI[ln]["forecast"])
        # Синхронизация истории с текущей валютой
        hist_p = (item['DF']['Close'].tail(14).values / (item['P_USD'] / price_now)) 
        st.line_chart(np.append(hist_p, future_prices), color="#00ffcc")

    with col_table:
        dates = [(datetime.now() + timedelta(days=i)).strftime('%d.%m') for i in range(1, 8)]
        breakdown = pd.DataFrame({
            UI[ln]["day"]: dates,
            UI[ln]["price"]: [f"{p:,.2f}" for p in future_prices],
            UI[ln]["profit"]: [f"{pr:,.2f} {sign}" for pr in daily_profits]
        })
        st.table(breakdown)

    sig_text = UI[ln]["sell"] if final_profit < 0 else UI[ln]["buy"]
    st.markdown(f"<h2 style='text-align:center; color:{'#ff4b4b' if final_profit < 0 else '#00ffcc'} !important; border: 2px solid;'>{UI[ln]['signal']}: {sig_text}</h2>", unsafe_allow_html=True)
