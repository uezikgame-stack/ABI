import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from gnews import GNews
from datetime import datetime, timedelta

# --- БИБЛИОТЕКИ МАШИННОГО ОБУЧЕНИЯ ---
import xgboost as xgb
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error

# --- 1. СТИЛЬ И БРЕНДИНГ RILLET ---
st.set_page_config(page_title="Rillet ML", layout="wide")

# --- ЛОКАЛИЗАЦИЯ ---
lang = st.sidebar.radio("LANGUAGE / ЯЗЫК", ["EN", "RU"])
txt = {
    "EN": {
        "market": "MARKET", "currency": "CURRENCY", "price": "PRICE", "forecast": "FORECAST %",
        "select": "SELECT ASSET:", "current": "CURRENT PRICE", "target": "TARGET (7d ML)",
        "profit": "EST. PROFIT", "chart_title": "XGBOOST ML FORECAST", "news_title": "INFO-FIELD ANALYSIS",
        "buy": "✅ STRONG BUY", "sell": "❌ SELL / HOLD", "hold": "⚖️ NEUTRAL", "no_news": "No news found.",
        "update": "Data updated", "signal": "FINAL SIGNAL",
        "brokers": "TOP BROKERS", "trust": "TRUST LEVEL", "details": "DETAILS",
        "history": "History", "founder": "Founder", "fact": "Fun Fact", "lawsuits": "Major Lawsuits",
        "license": "License", "fees": "Commissions", "withdraw": "Withdrawal"
    },
    "RU": {
        "market": "РЫНОК", "currency": "ВАЛЮТА", "price": "ЦЕНА", "forecast": "ПРОГНОЗ %",
        "select": "ВЫБЕРИ АКТИВ:", "current": "ТЕКУЩАЯ", "target": "ЦЕЛЬ (7д ML)",
        "profit": "ПРОФИТ (%)", "chart_title": "ПРОГНОЗ ML (XGBOOST)", "news_title": "АНАЛИЗ ИНФОПОЛЯ",
        "buy": "✅ ПОКУПАТЬ", "sell": "❌ ПРОДАВАТЬ/ЖДАТЬ", "hold": "⚖️ УДЕРЖИВАТЬ", "no_news": "Новостей не найдено.",
        "update": "Обновление данных", "signal": "ИТОГОВЫЙ СИГНАЛ",
        "brokers": "ТОП БРОКЕРОВ", "trust": "УРОВЕНЬ ДОВЕРИЯ", "details": "ДЕТАЛИ",
        "history": "История", "founder": "Основатель", "fact": "Интересный факт", "lawsuits": "Крупные иски",
        "license": "Лицензия", "fees": "Комиссии", "withdraw": "Вывод"
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
    .info-tag { background: #00ffcc22; padding: 2px 8px; border-radius: 5px; font-size: 0.8em; margin-right: 5px; border: 1px solid #00ffcc44; color: #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. БАЗА ДАННЫХ ---
DB = {
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "GOOGL", "META"],
    "EUROPE": ["ASML", "MC.PA", "SAP.DE", "AIR.PA", "BMW.DE"],
    "RUSSIA": ["SBER.ME", "GAZP.ME", "LKOH.ME", "YNDX", "ROSN.ME"],
    "KAZAKHSTAN": ["KMGZ.KZ", "HSBK.KZ", "KSPI.KZ", "KASE.KZ"]
}

raw_brokers = {
    "Interactive Brokers": {
        "trust": 99.2, "founder": "Thomas Peterffy", "license": "SEC, FINRA, FCA", "fees": "0.005$/sh", "withdraw": "1-3d",
        "history": {"EN": "Pioneered electronic trading.", "RU": "Пионеры электронного трейдинга."},
        "fact": {"EN": "Father of digital trading.", "RU": "Основатель — отец цифровой торговли."},
        "lawsuits": {"EN": "Fined in 2020 (AML).", "RU": "Штраф в 2020 за пробелы в AML."}
    },
    "Freedom Finance": {
        "trust": 94.5, "founder": "Timur Turlov", "license": "SEC, CySEC, AFSA", "fees": "0.02%", "withdraw": "Instant",
        "history": {"EN": "NASDAQ listed holding.", "RU": "Единственный брокер из СНГ на NASDAQ."},
        "fact": {"EN": "Leader in Central Asia.", "RU": "Лидер рынка в Центральной Азии."},
        "lawsuits": {"EN": "Cleared Hindenburg audit.", "RU": "Прошли аудит после атаки шорт-селлеров."}
    },
     "Tinkoff (RU)": {
        "trust": 88.5, "founder": "Oleg Tinkov", "license": "CBR (RU)", "fees": "0.025%+", "withdraw": "Instant",
        "history": {"EN": "Digital-first ecosystem.", "RU": "Крупнейшая инвестиционная соцсеть в РФ."},
        "fact": {"EN": "Zero physical branches.", "RU": "Цифровой банк без отделений."},
        "lawsuits": {"EN": "Sanction changes.", "RU": "Санкционные изменения."}
    }
    # (Остальные брокеры скрыты для краткости, но логика работает для всех)
}

# --- 3. ЯДРО МАШИННОГО ОБУЧЕНИЯ (XGBOOST) ---

def create_features(df):
    """Создает новые признаки (Feature Engineering) для ML модели"""
    df = df.copy()
    # Лаги (вчерашняя цена, позавчерашняя...)
    df['lag_1'] = df['Close'].shift(1)
    df['lag_2'] = df['Close'].shift(2)
    df['lag_3'] = df['Close'].shift(3)
    
    # Скользящие средние (тренды)
    df['SMA_5'] = df['Close'].rolling(window=5).mean().shift(1)
    df['SMA_20'] = df['Close'].rolling(window=20).mean().shift(1)
    
    # Волатильность (стандартное отклонение за неделю)
    df['Vol_5'] = df['Close'].rolling(window=5).std().shift(1)
    
    # Удаляем пустые значения, появившиеся из-за сдвигов (shift/rolling)
    df.dropna(inplace=True)
    return df

@st.cache_resource # Кэшируем модель и предсказания
def forecast_xgboost(ticker_df, days_ahead=7):
    """Обучает модель XGBoost и делает рекурсивный прогноз"""
    
    # 1. Подготовка данных с новыми признаками
    ml_df = create_features(ticker_df)
    
    if len(ml_df) < 30: return None, None # Недостаточно данных для ML

    features = ['lag_1', 'lag_2', 'lag_3', 'SMA_5', 'SMA_20', 'Vol_5']
    target = 'Close'

    X = ml_df[features]
    y = ml_df[target]

    # 2. Инициализация и обучение модели XGBoost
    # Используем параметры для быстрой регрессии
    model = xgb.XGBRegressor(
        objective='reg:squarederror',
        n_estimators=100,     # Количество деревьев
        learning_rate=0.1,    # Скорость обучения
        max_depth=3,          # Глубина деревьев (чтобы не переобучиться)
        random_state=42,
        n_jobs=-1             # Использовать все ядра процессора
    )
    
    model.fit(X, y)

    # 3. Рекурсивный прогноз на 7 дней вперед
    future_predictions = []
    # Берем последнюю известную строку данных как старт для прогноза
    current_features = X.iloc[-1:].copy() 
    current_close = y.iloc[-1]
    
    for _ in range(days_ahead):
        # Предсказываем следующий день
        pred = model.predict(current_features)[0]
        future_predictions.append(pred)
        
        # Обновляем признаки для следующего шага (имитируем, что наступило завтра)
        # Это упрощенная рекурсия для демонстрации:
        # Сдвигаем лаги: lag_2 становится lag_3, lag_1 становится lag_2, а предсказание становится lag_1
        new_row = current_features.copy()
        new_row['lag_3'] = new_row['lag_2']
        new_row['lag_2'] = new_row['lag_1']
        new_row['lag_1'] = pred # Используем предсказание как "вчерашнюю" цену для следующего шага
        
        # (Для SMA и Vol мы пока оставим старые значения для упрощения рекурсии в демке, 
        # в продакшене их нужно пересчитывать)
        current_features = new_row

    return future_predictions, model

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_daily_key(): return datetime.now().strftime("%Y-%m-%d-%H") # Обновление каждый час

@st.cache_data(ttl=3600) # Кэш на 1 час
def fetch_data_for_ml(t):
    try:
        # Берем данных побольше (6 месяцев) для обучения ML
        df = yf.download(t, period="6mo", interval="1d", progress=False)
        return df['Close'].dropna().to_frame()
    except: return None

@st.cache_data(ttl=3600)
def get_rates():
    try:
        raw = yf.download(["RUB=X", "KZT=X", "EURUSD=X"], period="5d", progress=False)['Close']
        return {
            "$": 1.0,
            "₽": float(raw["RUB=X"].dropna().iloc[-1]),
            "₸": float(raw["KZT=X"].dropna().iloc[-1]),
            "€_rate": float(raw["EURUSD=X"].dropna().iloc[-1])
        }
    except: return {"$": 1.0, "₽": 90.0, "₸": 485.0, "€_rate": 1.08}

@st.cache_data(ttl=86400)
def analyze_news_simple(query, l):
    try:
        gn = GNews(language='ru' if l == "RU" else 'en', period='7d', max_results=4)
        news = gn.get_news(f"{query} stock")
        pos = 0; neg = 0
        for n in news:
            txt_n = n.get('title', '').lower()
            if any(w in txt_n for w in ['рост', 'up', 'profit', 'buy']): pos+=1
            if any(w in txt_n for w in ['падение', 'down', 'loss', 'sell']): neg+=1
        return txt["buy"] if pos > neg else (txt["sell"] if neg > pos else txt["hold"])
    except: return txt["hold"]

# --- 4. ИНТЕРФЕЙС RILLET ML ---
st.sidebar.markdown('<div class="logo-text">RILLET ML</div>', unsafe_allow_html=True)
mode = st.sidebar.selectbox("MODE / РЕЖИМ", [txt["market"], txt["brokers"]])

if mode == txt["market"]:
    m_name = st.sidebar.selectbox(txt["market"], list(DB.keys()))
    c_choice = st.sidebar.radio(txt["currency"], ["USD ($)", "RUB (₽)", "KZT (₸)"])
    sign = c_choice.split("(")[1][0]
    
    rates = get_rates()
    r_val = rates.get(sign, 1.0)
    
    t_sel = st.selectbox(txt["select"], DB[m_name])
    
    # --- ЗАПУСК ML ПАЙПЛАЙНА ---
    df_raw = fetch_data_for_ml(t_sel)
    
    if df_raw is not None and not df_raw.empty:
        # Определение базовой валюты актива для конвертации
        base_currency = "$"
        if "ME" in t_sel or t_sel == "YNDX": base_currency = "₽"
        elif "KZ" in t_sel: base_currency = "₸"
        elif ".DE" in t_sel or ".PA" in t_sel: base_currency = "€"

        # Конвертация цены в выбранную валюту
        price_converter = 1.0
        if base_currency == "€": price_converter = rates["€_rate"] * r_val
        elif base_currency != sign: price_converter = r_val / rates.get(base_currency, 1.0)

        p_now_raw = df_raw['Close'].iloc[-1]
        p_now_display = p_now_raw * price_converter
        
        # Обучение и прогноз
        with st.spinner(f'Training XGBoost model for {t_sel}...'):
            f_raw, model = forecast_xgboost(df_raw, days_ahead=7)
            
        if f_raw:
            f_prices_display = [p * price_converter for p in f_raw]
            target_price = f_prices_display[-1]
            pct = ((target_price / p_now_display) - 1) * 100
            clr = "#00ffcc" if pct > 0.5 else ("#ff4b4b" if pct < -0.5 else "#ffcc00")

            # Метрики
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"<div class='metric-card'>{txt['current']}<br><h3>{p_now_display:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='metric-card'>{txt['target']}<br><h3>{target_price:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='metric-card' style='border-color:{clr}'>{txt['profit']}<br><h3>{pct:+.2f}%</h3></div>", unsafe_allow_html=True)

            # График ML
            st.write(f"#### {txt['chart_title']} {t_sel}")
            hist_data = df_raw['Close'].tail(30).values * price_converter
            chart_data = np.append(hist_data, f_prices_display)
            st.line_chart(chart_data, color="#00ffcc")
            
            # Простой сигнал новостей
            news_signal = analyze_news_simple(t_sel, lang)
            st.markdown(f"<h5 style='text-align:center;'>{txt['news_title']} Signal: {news_signal}</h5>", unsafe_allow_html=True)
            
        else:
            st.error("Not enough data for ML training.")
    else:
        st.error("Data unavailable.")


elif mode == txt["brokers"]:
    # (Код раздела брокеров остается прежним, для краткости не дублирую весь список)
    st.write(f"## 🏛️ {txt['brokers']}")
    sorted_brokers = sorted(raw_brokers.items(), key=lambda x: x[1]['trust'], reverse=True)
    for b_name, b_info in sorted_brokers:
        trust = b_info['trust']; bar_clr = "#00ffcc" if trust > 90 else ("#ffcc00" if trust > 85 else "#ff4b4b")
        st.markdown(f"""
        <div class="analysis-card" style="margin-bottom:0px; border-bottom:none;">
            <div style="display:flex; justify-content:space-between;">
                <b>{b_name}</b> <span style="color:{b_clr}">{t_val}% TRUST</span>
            </div>
            <div style="margin-top:10px;">
                <span class="info-tag">⚖️ {b_info['license']}</span>
                <span class="info-tag">💰 {b_info['fees']}</span>
                <span class="info-tag">⏱️ {b_info['withdraw']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        with st.expander(txt["details"]):
            st.write(f"**{txt['history']}:** {b_info['history'][lang]}")
            st.write(f"**{txt['founder']}:** {b_info['founder']}")
            st.write(f"**{txt['fact']}:** {b_info['fact'][lang]}")
            st.markdown(f"**{txt['lawsuits']}:** <span style='color:#ff4b4b;'>{b_info['lawsuits'][lang]}</span>", unsafe_allow_html=True)
        st.markdown(f"<div style='background:#111; height:3px; margin-bottom:20px;'><div style='background:{b_clr}; width:{t_val}%; height:100%;'></div></div>", unsafe_allow_html=True)

st.caption(f"{txt['update']} (ML Core): {get_daily_key()}")
