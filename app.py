import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. СТИЛЬ ШЭФА (КИБЕРПАНК) ---
st.set_page_config(page_title="ABI ANALITIC", layout="wide")
st.markdown("""
    <style>
    .stApp {
        background-color: #020508 !important;
        background-image: 
            linear-gradient(rgba(0, 255, 204, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 255, 204, 0.1) 1px, transparent 1px);
        background-size: 50px 50px;
        animation: moveGrid 15s linear infinite;
    }
    @keyframes moveGrid { from { background-position: 0 0; } to { background-position: 50px 50px; } }

    .unified-card {
        background: rgba(0, 0, 0, 0.95); border: 2px solid #ff4b4b; border-radius: 15px;
        padding: 30px; text-align: center; box-shadow: 0 0 25px rgba(255, 75, 75, 0.3);
    }

    .dino-crop {
        overflow: hidden; height: 180px; width: 100%;
        margin-top: 20px; border-radius: 8px; position: relative; background: black;
    }
    .dino-crop iframe {
        position: absolute; top: -105px; left: 0; width: 100%; height: 400px;
        filter: invert(1) hue-rotate(180deg) contrast(1.4);
    }

    .metric-card { background: rgba(0, 0, 0, 0.9); border: 1px solid #00ffcc; padding: 15px; text-align: center; border-radius: 10px; }
    h1, h2, h3, span, label, p { color: #00ffcc !important; }
    [data-testid="stSidebar"] { background-color: rgba(10, 14, 20, 0.95) !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ГЛОБАЛЬНАЯ БИБЛИОТЕКА ---
DB = {
    "CHINA (Китай)": ["BABA", "TCEHY", "PDD", "JD", "BIDU", "NIO", "LI", "BYDDY", "BILI", "NTES"],
    "KAZ (Казахстан)": ["KCZ.L", "KMGZ.KZ", "HSBK.KZ", "KCELL.KZ", "NAC.KZ", "CCBN.KZ", "KEGC.KZ", "KZTK.KZ", "KZTO.KZ"],
    "EUROPE": ["ASML", "MC.PA", "VOW3.DE", "NESN.SW", "SIE.DE", "SAP.DE", "AIR.PA", "RMS.PA", "MBG.DE", "DHL.DE"],
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "NFLX", "GOOGL", "META", "INTC", "CRM"],
    "RF (Россия)": ["SBER.ME", "GAZP.ME", "LKOH.ME", "YNDX", "ROSN.ME", "MGNT.ME", "NVTK.ME", "GMKN.ME"],
    "CRYPTO": ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "DOGE-USD"]
}

@st.cache_data(ttl=300)
def load_data(m_name):
    try:
        tickers = DB[m_name]
        data = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', progress=False)
        rates_df = yf.download(["RUB=X", "KZT=X", "CNY=X"], period="1d", progress=False)['Close']
        r_map = {"₽": float(rates_df["RUB=X"].iloc[-1]), "$": 1.0, "₸": float(rates_df["KZT=X"].iloc[-1]), "¥": float(rates_df["CNY=X"].iloc[-1])}
        
        clean = []
        for t in tickers:
            try:
                df = data[t].dropna()
                if df.empty: continue
                b = "₽" if ".ME" in t or t == "YNDX" else ("₸" if ".KZ" in t or "KCZ" in t else "$")
                p_usd = float(df['Close'].iloc[-1]) / r_map[b]
                # Считаем примерный прогноз для сортировки ТОПа
                mu, sigma = df['Close'].pct_change().mean(), (df['Close'].pct_change().std() or 0.02)
                f_usd = p_usd * (1 + mu * 7) # Упрощенный прогноз для рейтинга
                clean.append({"T": t, "P_USD": p_usd, "F_USD": f_usd, "AVG": mu, "STD": sigma, "DF": df})
            except: continue
        return clean, r_map
    except: return None, None

# --- 3. ИНТЕРФЕЙС ---
st.sidebar.title("ABI SETTINGS")
m_sel = st.sidebar.selectbox("MARKET", list(DB.keys()))
c_sel = st.sidebar.radio("CURRENCY", ["USD ($)", "RUB (₽)", "KZT (₸)"])

assets, rates = load_data(m_sel)
st.title("🚀 ABI ANALITIC")

if not assets:
    st.markdown(f"""<div class="unified-card"><h1>⚠️ {m_sel} ВРЕМЕННО НЕДОСТУПЕН</h1><div class="dino-crop"><iframe src="https://chromedino.com/" frameborder="0" scrolling="no"></iframe></div></div>""", unsafe_allow_html=True)
else:
    sign = c_sel.split("(")[1][0]
    r_target = rates[sign]

    # --- ТОП АКТИВОВ (ЛУЧШИЕ НАВЕРХ) ---
    st.write("## 🔥 ТОП АКТИВОВ")
    df_top = pd.DataFrame(assets)
    df_top["PROFIT_EST"] = ((df_top["F_USD"] / df_top["P_USD"]) - 1) * 100
    df_top = df_top.sort_values(by="PROFIT_EST", ascending=False).reset_index(drop=True)
    df_top.index += 1 # Цифры сверху (нумерация с 1)
    
    # Форматируем для таблицы
    df_show = df_top.copy()
    df_show["ЦЕНА"] = (df_show["P_USD"] * r_target).apply(lambda x: f"{x:,.2f} {sign}")
    df_show["ПРОГНОЗ %"] = df_show["PROFIT_EST"].apply(lambda x: f"{x:+.2f}%")
    
    st.dataframe(df_show[["T", "ЦЕНА", "ПРОГНОЗ %"]], use_container_width=True, height=250)

    # Выбор актива для детального разбора
    t_name = st.selectbox("ВЫБЕРИ ДЛЯ ДЕТАЛЬНОГО АНАЛИЗА:", df_top["T"].tolist())
    item = next(x for x in assets if x['T'] == t_name)

    # Прогноз на 7 дней
    if "f_usd" not in st.session_state or st.session_state.get("last_t") != t_name:
        st.session_state.f_usd = [item['P_USD'] * (1 + np.random.normal(item['AVG'], item['STD'])) for _ in range(7)]
        st.session_state.last_t = t_name

    p_now = item['P_USD'] * r_target
    f_prices = [p * r_target for p in st.session_state.f_usd]
    profit_pct = ((f_prices[-1] / p_now) - 1) * 100

    # МЕТРИКИ
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'>ТЕКУЩАЯ<br><h3>{p_now:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>ЦЕЛЬ (7д)<br><h3>{f_prices[-1]:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    p_color = "#ff4b4b" if profit_pct < -0.7 else ("#00ffcc" if profit_pct > 0.7 else "#ffcc00")
    c3.markdown(f"<div class='metric-card' style='border: 1px solid {p_color};'>ПРОФИТ (%)<br><h3>{profit_pct:+.2f} %</h3></div>", unsafe_allow_html=True)

    st.divider()

    # РАЗБОР ПО ДНЯМ
    col_graph, col_table = st.columns([2, 1])
    with col_graph:
        st.write("### ГРАФИК ПРОГНОЗА")
        hist_vals = (item['DF']['Close'].tail(15).values / (item['P_USD'] / p_now))
        st.line_chart(np.append(hist_vals, f_prices), color="#00ffcc")

    with col_table:
        st.write("### РАЗБОР ПО ДНЯМ")
        forecast_df = pd.DataFrame({
            "ДЕНЬ": [f"День {i+1}" for i in range(7)],
            "ЦЕНА": [f"{p:,.2f} {sign}" for p in f_prices],
            "ПРОФИТ": [f"{((p/p_now)-1)*100:+.2f} %" for p in f_prices]
        })
        st.dataframe(forecast_df, hide_index=True, use_container_width=True)

    # СИГНАЛ
    if profit_pct > 0.7: sig_t, sig_c = "ПОКУПАТЬ", "#00ffcc"
    elif profit_pct < -0.7: sig_t, sig_c = "ПРОДАВАТЬ", "#ff4b4b"
    else: sig_t, sig_c = "УДЕРЖИВАТЬ", "#ffcc00"

    st.markdown(f"<h2 style='text-align:center; color:{sig_c} !important; border: 2px solid {sig_c}; padding: 15px; border-radius: 10px;'>СИГНАЛ: {sig_t}</h2>", unsafe_allow_html=True)
