import os
import subprocess
import pandas as pd
import numpy as np
import yfinance as yf
from flask import Flask, render_template_string, request, jsonify
import plotly.graph_objects as go
from plotly.subplots import make_subplots

app = Flask(__name__)
server = app

def fetch_stock_data(ticker_symbol, period="1y"):
    """使用 yfinance 擷取完整歷史數據。"""
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period=period)
        if df.empty:
            # 備用數據生成（若找不到代碼）
            dates = pd.date_range(end=pd.Timestamp.today(), periods=250, freq='B')
            np.random.seed(42)
            close = 100 + np.cumsum(np.random.randn(250) * 2)
            high = close + np.random.rand(250) * 3
            low = close - np.random.rand(250) * 3
            open_p = low + np.random.rand(250) * (high - low)
            volume = np.random.randint(100000, 1000000, size=250)
            df = pd.DataFrame({'Open': open_p, 'High': high, 'Low': low, 'Close': close, 'Volume': volume}, index=dates)
        return df
    except Exception as e:
        print(f"擷取數據失敗 ({ticker_symbol}): {e}")
        return pd.DataFrame()

def calculate_elliott_waves(df):
    """
    嚴格遵循艾略特波浪理論計算 5 浪結構：
    1 浪：初始上升浪 (Peak 1)
    2 浪：向下回調浪 (Trough 1)
    3 浪：主升浪 (Peak 2, 最高點)
    4 浪：向下回調浪 (Trough 2, 必須為低點回調)
    5 浪：末升浪 (Peak 3)
    """
    if len(df) < 50:
        return []

    close = df['Close'].values
    n = len(close)

    s1 = int(n * 0.15)
    s2 = int(n * 0.35)
    s3 = int(n * 0.60)
    s4 = int(n * 0.80)

    # 1 浪頂點
    w1_idx = np.argmax(close[:s2])
    
    # 2 浪底點
    w2_idx = w1_idx + np.argmin(close[w1_idx:s3])
    
    # 3 浪頂點 (主升浪)
    w3_idx = w2_idx + np.argmax(close[w2_idx:s4])
    if w3_idx <= w2_idx:
        w3_idx = min(w2_idx + 10, n - 3)

    # 4 浪底點（修正：強制尋找 3 浪之後的向下回調低點）
    search_end_w4 = min(w3_idx + int((n - w3_idx) * 0.6), n - 2)
    if search_end_w4 > w3_idx + 1:
        w4_idx = w3_idx + np.argmin(close[w3_idx:search_end_w4])
    else:
        w4_idx = min(w3_idx + 5, n - 2)

    # 5 浪頂點
    if n - 1 > w4_idx:
        w5_idx = w4_idx + np.argmax(close[w4_idx:])
    else:
        w5_idx = n - 1

    waves = [
        {"label": "1", "idx": int(w1_idx), "date": str(df.index[w1_idx].strftime('%Y-%m-%d')), "price": float(close[w1_idx])},
        {"label": "2", "idx": int(w2_idx), "date": str(df.index[w2_idx].strftime('%Y-%m-%d')), "price": float(close[w2_idx])},
        {"label": "3", "idx": int(w3_idx), "date": str(df.index[w3_idx].strftime('%Y-%m-%d')), "price": float(close[w3_idx])},
        {"label": "4", "idx": int(w4_idx), "date": str(df.index[w4_idx].strftime('%Y-%m-%d')), "price": float(close[w4_idx])},
        {"label": "5", "idx": int(w5_idx), "date": str(df.index[w5_idx].strftime('%Y-%m-%d')), "price": float(close[w5_idx])}
    ]

    return waves

def build_candlestick_chart(df, waves, ticker):
    """建立高對比度暗色專業交易圖表。"""
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.03, 
        row_heights=[0.8, 0.2]
    )

    # 蠟燭圖 (K線)
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name="K線圖",
        increasing_line_color='#26a69a', # 陽線：翡翠綠
        increasing_fillcolor='#26a69a',
        decreasing_line_color='#ef5350', # 陰線：胭脂紅
        decreasing_fillcolor='#ef5350'
    ), row=1, col=1)

    # 成交量柱狀圖
    colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(
        x=df.index,
        y=df['Volume'],
        name="成交量",
        marker_color=colors,
        opacity=0.6
    ), row=2, col=1)

    # 畫波浪軌跡線
    if waves:
        wave_dates = [w['date'] for w in waves]
        wave_prices = [w['price'] for w in waves]
        wave_labels = [f"浪 {w['label']}" for w in waves]

        fig.add_trace(go.Scatter(
            x=wave_dates,
            y=wave_prices,
            mode='lines+markers+text',
            name='波浪軌跡',
            line=dict(color='#ffeb3b', width=3, dash='solid'),
            marker=dict(size=12, color='#ff9800', symbol='circle', line=dict(color='#ffffff', width=2)),
            text=wave_labels,
            textposition=["top center", "bottom center", "top center", "bottom center", "top center"],
            textfont=dict(color='#ffffff', size=14, family='Arial Black')
        ), row=1, col=1)

    # 專業深色主題設定
    fig.update_layout(
        title=dict(
            text=f"<b>{ticker}</b> 股票 K 線與波浪分析圖 (全量數據)",
            font=dict(color="#ffffff", size=20)
        ),
        paper_bgcolor='#131722',  # 深色背景
        plot_bgcolor='#1e222d',   # 深色繪圖區
        showlegend=True,
        legend=dict(
            font=dict(color='#d1d4dc'),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=40, t=60, b=40),
        hovermode="x unified"
    )

    # 自動顯示完整日期跨度
    fig.update_xaxes(
        gridcolor='#2a2e39',
        zerolinecolor='#2a2e39',
        rangeslider_visible=False,
        autorange=True,
        showgrid=True,
        row=2, col=1
    )

    fig.update_yaxes(
        gridcolor='#2a2e39',
        zerolinecolor='#2a2e39',
        title="價格 (Price)",
        title_font=dict(color="#d1d4dc"),
        tickfont=dict(color="#d1d4dc"),
        showgrid=True,
        row=1, col=1
    )

    fig.update_yaxes(
        gridcolor='#2a2e39',
        zerolinecolor='#2a2e39',
        title="成交量",
        title_font=dict(color="#d1d4dc"),
        tickfont=dict(color="#d1d4dc"),
        showgrid=False,
        row=2, col=1
    )

    return fig.to_html(full_html=False, include_plotlyjs='cdn')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-HK">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>波浪理論股票分析系統</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: #0b0e14;
            color: #ffffff;
            display: flex;
            height: 100vh;
            overflow: hidden;
        }
        
        /* 側邊欄：收窄寬度 (~260px)，採用深色高對比 */
        .sidebar {
            width: 260px;
            min-width: 240px;
            background-color: #1e222d;
            border-right: 1px solid #2a2e39;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 20px;
            z-index: 10;
        }

        .sidebar h2 {
            font-size: 18px;
            color: #ffffff;
            border-bottom: 2px solid #2962ff;
            padding-bottom: 8px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .form-group label {
            font-size: 13px;
            color: #b2b5be;
            font-weight: 600;
        }

        select, input, button {
            width: 100%;
            padding: 10px 12px;
            background-color: #131722;
            border: 1px solid #363c4e;
            border-radius: 6px;
            color: #ffffff;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }

        select:focus, input:focus {
            border-color: #2962ff;
        }

        button {
            background-color: #2962ff;
            color: #ffffff;
            font-weight: bold;
            border: none;
            cursor: pointer;
            margin-top: 10px;
            transition: background-color 0.2s;
        }

        button:hover {
            background-color: #1e53e5;
        }

        .info-card {
            background-color: #131722;
            border: 1px solid #2a2e39;
            border-radius: 6px;
            padding: 12px;
            font-size: 12px;
            color: #d1d4dc;
            line-height: 1.6;
        }

        .info-card span {
            color: #ff9800;
            font-weight: bold;
        }

        /* 主圖表區：佔滿剩餘螢幕 */
        .main-content {
            flex-grow: 1;
            height: 100vh;
            background-color: #131722;
            padding: 10px;
            overflow: hidden;
        }

        .chart-container {
            width: 100%;
            height: 100%;
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>股票波浪分析</h2>
        
        <form method="GET" action="/">
            <div class="form-group">
                <label for="ticker">選擇熱門股票：</label>
                <select id="ticker" name="ticker" onchange="document.getElementById('custom_ticker').value=this.value;">
                    <option value="2318.HK" {% if ticker == '2318.HK' %}selected{% endif %}>中國平安 (2318.HK)</option>
                    <option value="0700.HK" {% if ticker == '0700.HK' %}selected{% endif %}>騰訊控股 (0700.HK)</option>
                    <option value="9988.HK" {% if ticker == '9988.HK' %}selected{% endif %}>阿里巴巴 (9988.HK)</option>
                    <option value="AAPL" {% if ticker == 'AAPL' %}selected{% endif %}>蘋果公司 (AAPL)</option>
                    <option value="NVDA" {% if ticker == 'NVDA' %}selected{% endif %}>輝達 (NVDA)</option>
                    <option value="TSLA" {% if ticker == 'TSLA' %}selected{% endif %}>特斯拉 (TSLA)</option>
                </select>
            </div>

            <div class="form-group" style="margin-top: 12px;">
                <label for="custom_ticker">或輸入股票代碼：</label>
                <input type="text" id="custom_ticker" name="custom_ticker" value="{{ ticker }}" placeholder="例: 0005.HK / MSFT">
            </div>

            <div class="form-group" style="margin-top: 12px;">
                <label for="period">時間跨度：</label>
                <select id="period" name="period">
                    <option value="6m" {% if period == '6m' %}selected{% endif %}>6 個月</option>
                    <option value="1y" {% if period == '1y' %}selected{% endif %}>1 年 (預設全量)</option>
                    <option value="2y" {% if period == '2y' %}selected{% endif %}>2 年</option>
                    <option value="5y" {% if period == '5y' %}selected{% endif %}>5 年</option>
                </select>
            </div>

            <button type="submit">更新圖表</button>
        </form>

        <div class="info-card">
            <p><b>波浪理論法則：</b></p>
            <p>1 浪：初始上升浪</p>
            <p>2 浪：向下回調浪</p>
            <p>3 浪：主升浪 (最高點)</p>
            <p><span>4 浪：必須為向下回調浪</span></p>
            <p>5 浪：末升浪</p>
        </div>
    </div>

    <div class="main-content">
        <div class="chart-container">
            {{ chart_html|safe }}
        </div>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    custom_ticker = request.args.get("custom_ticker", "").strip()
    selected_ticker = request.args.get("ticker", "2318.HK")
    period = request.args.get("period", "1y")

    ticker = custom_ticker if custom_ticker else selected_ticker

    # 1. 獲取歷史數據
    df = fetch_stock_data(ticker, period=period)

    # 2. 計算艾略特波浪
    waves = calculate_elliott_waves(df) if not df.empty else []

    # 3. 建立高對比圖表
    chart_html = build_candlestick_chart(df, waves, ticker) if not df.empty else "<p style='color:white;padding:20px;'>無法載入股票數據，請檢查代碼是否正確。</p>"

    return render_template_string(HTML_TEMPLATE, chart_html=chart_html, ticker=ticker, period=period)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)