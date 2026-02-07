import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

# --- 1. СТИЛЬ И БРЕНДИНГ RILLET ---
st.set_page_config(page_title="Rillet", layout="wide")
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
    
    .logo-text {
        font-size: 42px;
        font-weight: bold;
        text-align: center;
        color: #00ffcc;
        border-bottom: 2px solid #00ffcc;
        margin-bottom: 20px;
    }
    .news-card {
        background: rgba(0, 255, 204, 0.05);
        border-left: 5px solid #00ffcc;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 5px;
    }
    .loss-tracker {
        background: rgba(255, 75, 75, 0.1);
        border: 1px solid #ff4b4b;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        margin-top: 20px;
    }
    .unified-card {
        background: rgba(0, 0, 0, 0.95); border: 2px solid #ff4b4b; border-radius: 15px;
        padding: 30px; text-align: center;
    }
    .dino-container {
        overflow: hidden; height: 300px; width: 100%; border-radius: 10px; border: 1px solid #ff4b4b;
    }
    .dino-container iframe { width: 100%; height: 500px; margin-top: -100px; filter: invert(1); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. БАЗА ДАННЫХ ---
DB = {
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "NFLX", "GOOGL", "META", "INTC", "CRM", "AVGO", "QCOM", "PYPL", "TSM"],
    "CHINA (Китай)": ["BABA", "TCEHY", "PDD", "JD", "BIDU", "NIO", "LI", "BYDDY", "BILI", "NTES", "GDS", "ZLAB", "KC", "IQ", "TME"],
    "EUROPE": ["ASML", "MC.PA", "VOW3.DE", "NESN.SW", "SIE.DE", "SAP.DE", "AIR.PA", "RMS.PA", "MBG.DE", "DHL.DE", "ALV.DE", "SAN.MC", "BMW.DE", "OR.PA", "BBVA.MC"],
    "KAZ (Казахстан)": ["KCZ.L", "KMGZ.KZ", "HSBK.KZ", "KCELL.KZ", "NAC.KZ", "CCBN.KZ", "KEGC.KZ", "KZTK.KZ", "KZTO.KZ", "ASBN.KZ", "KSPI.KZ", "KCP.KZ", "KMGP.KZ", "BCKL.KZ", "KASE.KZ"],
    "RF (Россия)": ["SBER.ME", "GAZP.ME", "LKOH.ME", "YNDX", "ROSN.ME", "MGNT.ME", "NVTK.ME", "GMKN.ME", "CHMF.ME", "PLZL.ME", "TATN.ME", "MTSS.ME", "AFLT.ME", "ALRS.ME", "VTBR.ME"]
}

LANG = {
    "RU": {
        "market": "РЫНОК", "curr": "ВАЛЮТА", "top": "🔥 ТОП АКТИВОВ", "price": "ЦЕНА", "pred": "ПРОГНОЗ %",
        "sel": "ВЫБЕРИ ДЛЯ АНАЛИЗА:", "now": "ТЕКУЩАЯ", "target": "ЦЕЛЬ (7д)", "profit": "ПРОФИТ (%)",
        "chart": "ГРАФИК ПРОГНОЗА", "days": "РАЗБОР ПО ДНЯМ", "day_label": "День", "signal": "СИГНАЛ",
        "buy": "ПОКУПАТЬ", "sell": "ПРОДАВАТЬ", "hold": "УДЕРЖИВАТЬ",
        "err": "РЕГИОН ВРЕМЕННО НЕДОСТУПЕН", "dino_msg": "Пока данные грузятся, побей рекорд!",
        "tab_an": "Аналитика", "tab_news": "Новости рынка",
        "loss_title": "ПОТЕРИ ИНВЕСТОРОВ В МИРЕ", "loss_sub": "с момента открытия приложения"
    },
    "EN": {
        "market": "MARKET", "curr": "CURRENCY", "top": "🔥 TOP ASSETS", "price": "PRICE", "pred": "FORECAST %",
        "sel": "SELECT FOR ANALYSIS:", "now": "CURRENT", "target": "TARGET (7d)", "profit": "PROFIT (%)",
        "chart": "FORECAST CHART", "days": "DAILY BREAKDOWN", "day_label": "Day", "signal": "SIGNAL",
        "buy": "BUY", "sell": "SELL", "hold": "HOLD",
        "err": "REGION UNAVAILABLE", "dino_msg": "Beat the record while data is loading!",
        "tab_an": "Analytics", "tab_news": "Market News",
        "loss_title": "GLOBAL INVESTOR LOSSES", "loss_sub": "since you opened this app"
    }
}

@st.cache_data(ttl=300)
def fetch_all(m_name):
    try:
        tickers = DB[m_name]
        data = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', progress=False)
        rates_raw = yf.download(["RUB=X", "KZT=X", "EURUSD=X"], period="5d", progress=False)['Close']
        r_map = {"$": 1.0}
        r_map["₽"] = float(rates_raw["RUB=X"].dropna().iloc[-1
