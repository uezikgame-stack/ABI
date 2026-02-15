import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from gnews import GNews
from datetime import datetime, timedelta
import xgboost as xgb

# --- 1. НАСТРОЙКИ И СТИЛЬ ---
st.set_page_config(page_title="Rillet ML Full", layout="wide")

lang = st.sidebar.radio("ЯЗЫК / LANGUAGE", ["RU", "EN"])
txt = {
    "RU": {
        "market": "АНАЛИЗ РЫНКА", "select": "ВЫБЕРИ АКТИВ:", "current": "ТЕКУЩАЯ ЦЕНА",
        "target": "ПРОГНОЗ (7 ДНЕЙ)", "profit": "ОЖИДАЕМЫЙ ДОХОД", "chart": "ДИНАМИКА И ML ПРОГНОЗ ПО ДНЯМ",
        "news": "НОВОСТИ ПО АКТИВУ", "signal": "СИГНАЛ", "buy": "ПОКУПАТЬ", "sell": "ПРОДАВАТЬ",
        "hold": "ЖДАТЬ", "brokers": "ТОП-15 БРОКЕРОВ", "trust": "ДОВЕРИЕ", "details": "ДЕТАЛИ"
    },
    "EN": {
        "market": "MARKET ANALYSIS", "select": "SELECT ASSET:", "current": "CURRENT PRICE",
        "target": "FORECAST (7 DAYS)", "profit": "EST. PROFIT", "chart": "DAILY DYNAMICS & ML FORECAST",
        "news": "ASSET SPECIFIC NEWS", "signal": "SIGNAL", "buy": "BUY", "sell": "SELL",
        "hold": "HOLD", "brokers": "TOP 15 BROKERS", "trust": "TRUST", "details": "DETAILS"
    }
}[lang]

st.markdown("""<style>
    .stApp { background-color: #020508; color: #00ffcc; }
    .metric-card { background: rgba(0, 255, 204, 0.05); border: 1px solid #00ffcc; padding: 20px; border-radius: 12px; text-align: center; }
    .news-card { background: rgba(255, 255, 255, 0.03); border-left: 3px solid #00ffcc; padding: 10px; margin-bottom: 5px; }
    h1, h2, h3, p, span, label { color: #00ffcc !important; }
</style>""", unsafe_allow_html=True)

# --- 2. БАЗА ДАННЫХ (БРОКЕРЫ И КИТАЙ) ---
DB = {
    "CHINA": ["BABA", "TCEHY", "PDD", "JD", "BIDU", "NIO", "LI", "BYDDY", "BILI", "NTES"],
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "NFLX", "GOOGL"],
    "RUSSIA": ["SBER.ME", "GAZP.ME", "LKOH.ME", "YNDX", "ROSN.ME"],
    "KAZAKHSTAN": ["KMGZ.KZ", "HSBK.KZ", "KSPI.KZ", "KASE.KZ"]
}

BROKERS_LIST = {
    "Interactive Brokers": {"trust": 99.2, "lic": "SEC, FCA", "fees": "Low", "desc": "Лидер мирового рынка."},
    "Fidelity": {"trust": 98.5, "lic": "FINRA", "fees": "$0", "desc": "Надежность и пенсионные планы."},
    "Charles Schwab": {"trust": 98.0, "lic": "SEC", "fees": "$0", "desc": "Крупнейший брокер США."},
    "Saxo Bank": {"trust": 96.0, "lic": "Danish FSA", "fees": "High", "desc": "Европейский стандарт."},
    "Freedom Finance": {"trust": 94.5, "lic": "SEC, AFSA", "fees": "Mid", "desc": "Доступ к IPO и рынку СНГ."},
    "Swissquote": {"trust": 95.5, "lic": "FINMA", "fees": "High", "desc": "Швейцарский банк."},
    "Vantage": {"trust": 93.8, "lic": "ASIC", "fees": "Low", "desc": "Лучший ECN брокер."},
    "E*TRADE": {"trust": 93.0, "lic": "SEC", "fees": "$0", "desc": "Часть Morgan Stanley."},
    "Pepperstone": {"trust": 92.5, "lic": "FCA", "fees": "Spreads", "desc": "Скорость исполнения."},
    "Exante": {"trust": 91.2, "lic": "CySEC", "fees": "0.02%", "desc": "Единый счет на все рынки."},
    "Webull": {"trust": 90.0, "lic": "SEC", "fees": "$0", "desc": "Отличные графики."},
    "Tiger Brokers": {"trust": 89.5, "lic": "MAS", "fees": "Low", "desc": "Лидер Азии."},
    "Robinhood": {"trust": 88.0, "lic": "SEC", "fees": "$0", "desc": "Для нового поколения."},
    "AvaTrade": {"trust": 87.5, "lic": "CBI", "fees": "Spreads", "desc": "Фокус на CFD."},
    "BlackRock": {"trust": 99.8, "lic": "Global", "fees": "Inst.", "desc": "Мировой гигант."}
}

# --- 3. ЯДРО (ML + НОВОСТИ) ---
def get_daily_forecast(df):
    try:
        d = df[['Close']].copy()
        d['lag'] = d['Close'].shift(1)
        d['ma'] = d['Close'].rolling(5).mean()
        d = d.dropna()
        model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.05)
        model.fit(d[['lag', 'ma']], d['Close'])
        
        preds = []
        last_p = d['Close'].iloc[-1]
        last_m = d['ma'].iloc[-1]
        for _ in range(7):
            p = model.predict(np.array([[last_p, last_m]]))[0]
            preds.append(p)
            last_p = p
        return preds
    except: return None

def fetch_asset_news(ticker, l):
    try:
        gn = GNews(language='ru' if l == "RU" else 'en', max_results=4, period='7d')
        return gn.get_news(f"{ticker} stock")
    except: return []

# --- 4. ИНТЕРФЕЙС ---
st.sidebar.markdown("<h1 style='text-align:center;'>RILLET ML</h1>", unsafe_allow_html=True)
menu = st.sidebar.selectbox("МЕНЮ", [txt["market"], txt["brokers"]])

if menu == txt["market"]:
    market_sec = st.sidebar.selectbox("СЕКТОР", list(DB.keys()))
    ticker = st.selectbox(txt["select"], DB[market_sec])
    
    # Загрузка данных
    df_raw = yf.download(ticker, period="6mo", interval="1d", progress=False, auto_adjust=True)
    
    if not df_raw.empty:
        if isinstance(df_raw.columns, pd.MultiIndex): df_raw.columns = df_raw.columns.get_level_values(0)
        df = df_raw[['Close']].dropna()
        
        with st.spinner('Анализ нейросетью...'):
            forecast = get_daily_forecast(df)
            news = fetch_asset_news(ticker, lang)
        
        if forecast:
            p_now = float(df['Close'].iloc[-1])
            p_fut = float(forecast[-1])
            pct = ((p_fut / p_now) - 1) * 100
            
            # Метрики
            col1, col2, col3 = st.columns(3)
            col1.markdown(f"<div class='metric-card'>{txt['current']}<br><h2>{p_now:,.2f} $</h2></div>", unsafe_allow_html=True)
            col2.markdown(f"<div class='metric-card'>{txt['target']}<br><h2>{p_fut:,.2f} $</h2></div>", unsafe_allow_html=True)
            color = "#00ffcc" if pct > 0 else "#ff4b4b"
            col3.markdown(f"<div class='metric-card' style='border-color:{color}'>{txt['profit']}<br><h2>{pct:+.2f}%</h2></div>", unsafe_allow_html=True)
            
            # Построение графика по дням
            st.write(f"### 📈 {txt['chart']} {ticker}")
            last_dates = df.index[-30:]
            future_dates = [last_dates[-1] + timedelta(days=i) for i in range(1, 8)]
            
            hist_series = pd.Series(df['Close'].tail(30).values, index=last_dates)
            fore_series = pd.Series(forecast, index=future_dates)
            
            full_df = pd.DataFrame({"History": hist_series, "ML Forecast": fore_series})
            st.line_chart(full_df)
            
            # Блок новостей по конкретной акции
            st.write(f"### 📰 {txt['news']} ({ticker})")
            if news:
                for n in news:
                    st.markdown(f"<div class='news-card'><b>{n['title']}</b><br><small>{n['published date']}</small></div>", unsafe_allow_html=True)
            else:
                st.write("Новостей по данному тикеру пока нет.")

elif menu == txt["brokers"]:
    st.write(f"## 🏛️ {txt['brokers']}")
    for name, info in BROKERS_LIST.items():
        with st.expander(f"{name} — {txt['trust']}: {info['trust']}%"):
            st.write(f"**Лицензии:** {info['lic']}")
            st.write(f"**Комиссии:** {info['fees']}")
            st.write(f"**Описание:** {info['desc']}")

st.caption(f"Rillet ML Core 2026 | Обновлено: {datetime.now().strftime('%H:%M:%S')}")
