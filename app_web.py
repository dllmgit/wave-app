import os
import pandas as pd
import numpy as np
import yfinance as yf
from flask import Flask, render_template_string, request
import plotly.graph_objects as go
from plotly.subplots import make_subplots

app = Flask(__name__)
server = app  # 供 Gunicorn 載入使用

def fetch_stock_data(ticker_symbol, period="max"):
    """使用 yfinance 擷取完整歷史數據 (預設上市至今所有時間)。"""
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period=period)
        if df.empty:
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

# -----------------------------------------------------------------------------
# 1. 陰陽燭指標計算（單支及組合形態）
# -----------------------------------------------------------------------------
def detect_candlestick_patterns(df):
    patterns = []
    n = len(df)
    if n < 3:
        return patterns

    for i in range(2, n):
        # 當前燭 (i)
        o0, c0, h0, l0 = df['Open'].iloc[i], df['Close'].iloc[i], df['High'].iloc[i], df['Low'].iloc[i]
        date0 = str(df.index[i].strftime('%Y-%m-%d'))
        body0 = abs(c0 - o0)
        u_shadow0 = h0 - max(o0, c0)
        l_shadow0 = min(o0, c0) - l0
        body_effective0 = max(body0, (h0 - l0) * 0.05)

        # 前一支燭 (i-1)
        o1, c1, h1, l1 = df['Open'].iloc[i-1], df['Close'].iloc[i-1], df['High'].iloc[i-1], df['Low'].iloc[i-1]
        date1 = str(df.index[i-1].strftime('%Y-%m-%d'))
        body1 = abs(c1 - o1)

        # 前兩支燭 (i-2)
        o2, c2, h2, l2 = df['Open'].iloc[i-2], df['Close'].iloc[i-2], df['High'].iloc[i-2], df['Low'].iloc[i-2]
        body2 = abs(c2 - o2)

        # --- 單支燭形態 ---
        # 錘頭 (Hammer): 下影線 >= 燭身 * 3
        if l_shadow0 >= body_effective0 * 3 and u_shadow0 <= body_effective0 * 0.5:
            patterns.append({"type": "Hammer", "label": "錘頭", "date": date0, "price": l0, "color": "#00e676"})
        # 倒轉錘頭 (Inverted Hammer): 上影線 >= 燭身 * 3
        elif u_shadow0 >= body_effective0 * 3 and l_shadow0 <= body_effective0 * 0.5:
            patterns.append({"type": "Inverted Hammer", "label": "倒轉錘頭", "date": date0, "price": h0, "color": "#ff5252"})

        # --- 兩支燭組合形態 ---
        # 底部身懷六甲 (Bullish Harami): 前長陰燭，後小陽/陰燭完全包在第一支實體內
        if c1 < o1 and body1 > (h1 - l1) * 0.5 and max(o0, c0) <= o1 and min(o0, c0) >= c1:
            patterns.append({"type": "Bullish Harami", "label": "底部身懷六甲", "date": date0, "price": l0, "color": "#00e676"})

        # 頂部身懷六甲 (Bearish Harami): 前長陽燭，後小陽/陰燭完全包在第一支實體內
        if c1 > o1 and body1 > (h1 - l1) * 0.5 and max(o0, c0) <= c1 and min(o0, c0) >= o1:
            patterns.append({"type": "Bearish Harami", "label": "頂部身懷六甲", "date": date0, "price": h0, "color": "#ff1744"})

        # 曙光初現 (Piercing Line): 前陰燭，後陽燭低開，且收盤價穿過前一陰燭實體中點以上
        if c1 < o1 and c0 > o0 and o0 < l1 and c0 > (o1 + c1) / 2 and c0 < o1:
            patterns.append({"type": "Piercing Line", "label": "曙光初現", "date": date0, "price": l0, "color": "#00e676"})

        # 烏雲蓋頂 (Dark Cloud Cover): 前陽燭，後陰燭高開，且收盤價穿過前一陽燭實體中點以下
        if c1 > o1 and c0 < o0 and o0 > h1 and c0 < (o1 + c1) / 2 and c0 > o1:
            patterns.append({"type": "Dark Cloud Cover", "label": "烏雲蓋頂", "date": date0, "price": h0, "color": "#ff1744"})

        # --- 三支燭組合形態 ---
        # 早晨之星 (Morning Star): 1長陰燭 + 2小實體(星線) + 3長陽燭(深入第1支實體)
        if c2 < o2 and body2 > (h2 - l2) * 0.4 and body1 < body2 * 0.3 and c0 > o0 and c0 > (o2 + c2) / 2:
            patterns.append({"type": "Morning Star", "label": "早晨之星", "date": date0, "price": l0, "color": "#00e676"})

        # 黃昏之星 (Evening Star): 1長陽燭 + 2小實體(星線) + 3長陰燭(深入第1支實體)
        if c2 > o2 and body2 > (h2 - l2) * 0.4 and body1 < body2 * 0.3 and c0 < o0 and c0 < (o2 + c2) / 2:
            patterns.append({"type": "Evening Star", "label": "黃昏之星", "date": date0, "price": h0, "color": "#ff1744"})

    return patterns

# -----------------------------------------------------------------------------
# 2. 頭肩頂 / 頭肩底 識別 (兩肩高寬比 0.5 - 1.5)
# -----------------------------------------------------------------------------
def detect_head_and_shoulders(df):
    results = []
    close = df['Close'].values
    n = len(close)
    if n < 30:
        return results

    pivots_high, pivots_low = [], []
    for i in range(2, n - 2):
        if close[i] > close[i-1] and close[i] > close[i-2] and close[i] > close[i+1] and close[i] > close[i+2]:
            pivots_high.append((i, close[i]))
        if close[i] < close[i-1] and close[i] < close[i-2] and close[i] < close[i+1] and close[i] < close[i+2]:
            pivots_low.append((i, close[i]))

    # 頭肩頂
    for i in range(len(pivots_high) - 2):
        ls_idx, ls_price = pivots_high[i]
        h_idx, h_price = pivots_high[i+1]
        rs_idx, rs_price = pivots_high[i+2]
        if h_price > ls_price and h_price > rs_price:
            h_ratio = rs_price / ls_price if ls_price > 0 else 0
            w_ratio = (rs_idx - h_idx) / (h_idx - ls_idx) if (h_idx - ls_idx) > 0 else 0
            if 0.5 <= h_ratio <= 1.5 and 0.5 <= w_ratio <= 1.5:
                results.append({
                    "type": "Head & Shoulders",
                    "points": [
                        {"date": str(df.index[ls_idx].strftime('%Y-%m-%d')), "price": float(ls_price), "label": "左肩"},
                        {"date": str(df.index[h_idx].strftime('%Y-%m-%d')), "price": float(h_price), "label": "頭部"},
                        {"date": str(df.index[rs_idx].strftime('%Y-%m-%d')), "price": float(rs_price), "label": "右肩"}
                    ],
                    "color": "#ff3d00"
                })

    # 頭肩底
    for i in range(len(pivots_low) - 2):
        ls_idx, ls_price = pivots_low[i]
        h_idx, h_price = pivots_low[i+1]
        rs_idx, rs_price = pivots_low[i+2]
        if h_price < ls_price and h_price < rs_price:
            h_ratio = rs_price / ls_price if ls_price > 0 else 0
            w_ratio = (rs_idx - h_idx) / (h_idx - ls_idx) if (h_idx - ls_idx) > 0 else 0
            if 0.5 <= h_ratio <= 1.5 and 0.5 <= w_ratio <= 1.5:
                results.append({
                    "type": "Inverse Head & Shoulders",
                    "points": [
                        {"date": str(df.index[ls_idx].strftime('%Y-%m-%d')), "price": float(ls_price), "label": "倒左肩"},
                        {"date": str(df.index[h_idx].strftime('%Y-%m-%d')), "price": float(h_price), "label": "倒頭部"},
                        {"date": str(df.index[rs_idx].strftime('%Y-%m-%d')), "price": float(rs_price), "label": "倒右肩"}
                    ],
                    "color": "#00e676"
                })

    return results

# -----------------------------------------------------------------------------
# 3. 上升平行通道 (底線兩點，定位點 P3 在中間)
# -----------------------------------------------------------------------------
def calculate_parallel_channel(df):
    close = df['Close'].values
    n = len(close)
    if n < 40:
        return None

    p1_idx = np.argmin(close[:int(n * 0.4)])
    p2_idx = int(n * 0.6) + np.argmin(close[int(n * 0.6):])

    if p1_idx >= p2_idx or (p2_idx - p1_idx) < 10:
        return None

    mid_close = close[p1_idx+1 : p2_idx]
    if len(mid_close) == 0:
        return None

    p3_idx = p1_idx + 1 + np.argmax(mid_close)

    x1, y1 = p1_idx, close[p1_idx]
    x2, y2 = p2_idx, close[p2_idx]
    m = (y2 - y1) / (x2 - x1)

    c_bottom = y1 - m * x1
    c_top = close[p3_idx] - m * p3_idx

    x_start, x_end = 0, n - 1
    return {
        "bottom_line": {
            "dates": [str(df.index[x_start].strftime('%Y-%m-%d')), str(df.index[x_end].strftime('%Y-%m-%d'))],
            "prices": [m * x_start + c_bottom, m * x_end + c_bottom]
        },
        "top_line": {
            "dates": [str(df.index[x_start].strftime('%Y-%m-%d')), str(df.index[x_end].strftime('%Y-%m-%d'))],
            "prices": [m * x_start + c_top, m * x_end + c_top]
        },
        "anchor_p3": {
            "date": str(df.index[p3_idx].strftime('%Y-%m-%d')),
            "price": float(close[p3_idx])
        }
    }

# -----------------------------------------------------------------------------
# 4. 艾略特波浪計算
# -----------------------------------------------------------------------------
def calculate_elliott_waves(df):
    if len(df) < 50:
        return []
    close = df['Close'].values
    n = len(close)

    s1, s2, s3, s4 = int(n * 0.15), int(n * 0.35), int(n * 0.60), int(n * 0.80)
    w1_idx = np.argmax(close[:s2])
    w2_idx = w1_idx + np.argmin(close[w1_idx:s3])
    w3_idx = w2_idx + np.argmax(close[w2_idx:s4])
    if w3_idx <= w2_idx:
        w3_idx = min(w2_idx + 10, n - 3)

    search_end_w4 = min(w3_idx + int((n - w3_idx) * 0.6), n - 2)
    w4_idx = w3_idx + np.argmin(close[w3_idx:search_end_w4]) if search_end_w4 > w3_idx + 1 else min(w3_idx + 5, n - 2)
    w5_idx = w4_idx + np.argmax(close[w4_idx:]) if n - 1 > w4_idx else n - 1

    return [
        {"label": "1", "date": str(df.index[w1_idx].strftime('%Y-%m-%d')), "price": float(close[w1_idx])},
        {"label": "2", "date": str(df.index[w2_idx].strftime('%Y-%m-%d')), "price": float(close[w2_idx])},
        {"label": "3", "date": str(df.index[w3_idx].strftime('%Y-%m-%d')), "price": float(close[w3_idx])},
        {"label": "4", "date": str(df.index[w4_idx].strftime('%Y-%m-%d')), "price": float(close[w4_idx])},
        {"label": "5", "date": str(df.index[w5_idx].strftime('%Y-%m-%d')), "price": float(close[w5_idx])}
    ]

# -----------------------------------------------------------------------------
# 5. 繪製 Plotly 圖表（支援開關選項）
# -----------------------------------------------------------------------------
def build_candlestick_chart(df, waves, candle_patterns, hs_patterns, channel, ticker, show_options):
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.03, 
        row_heights=[0.8, 0.2]
    )

    # K 線圖
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name="K線圖",
        increasing_line_color='#26a69a', increasing_fillcolor='#26a69a',
        decreasing_line_color='#ef5350', decreasing_fillcolor='#ef5350'
    ), row=1, col=1)

    # 成交量
    colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'], name="成交量", marker_color=colors, opacity=0.6
    ), row=2, col=1)

    # 1. 艾略特波浪
    if show_options.get('show_waves') and waves:
        fig.add_trace(go.Scatter(
            x=[w['date'] for w in waves], y=[w['price'] for w in waves],
            mode='lines+markers+text', name='波浪軌跡',
            line=dict(color='#ffeb3b', width=3),
            marker=dict(size=10, color='#ff9800'),
            text=[f"浪 {w['label']}" for w in waves],
            textposition="top center", textfont=dict(color='#ffffff', size=13)
        ), row=1, col=1)

    # 2. 陰陽燭指標
    if show_options.get('show_candlestick') and candle_patterns:
        for p in candle_patterns[-15:]:
            fig.add_trace(go.Scatter(
                x=[p['date']], y=[p['price']],
                mode='markers+text', name=p['label'],
                marker=dict(size=11, color=p['color'], symbol='diamond'),
                text=[p['label']], textposition="bottom center" if "底部" in p['label'] or "曙光" in p['label'] or "早晨" in p['label'] or "錘頭" in p['label'] else "top center",
                textfont=dict(color=p['color'], size=11),
                showlegend=False
            ), row=1, col=1)

    # 3. 頭肩頂/頭肩底
    if show_options.get('show_hs') and hs_patterns:
        for hs in hs_patterns:
            pts = hs['points']
            fig.add_trace(go.Scatter(
                x=[pt['date'] for pt in pts], y=[pt['price'] for pt in pts],
                mode='lines+markers+text', name=hs['type'],
                line=dict(color=hs['color'], width=2, dash='dot'),
                marker=dict(size=10, color=hs['color']),
                text=[pt['label'] for pt in pts], textposition="top center",
                textfont=dict(color=hs['color'], size=12)
            ), row=1, col=1)

    # 4. 平行通道
    if show_options.get('show_channel') and channel:
        fig.add_trace(go.Scatter(
            x=channel['bottom_line']['dates'], y=channel['bottom_line']['prices'],
            mode='lines', name='通道底線', line=dict(color='#2962ff', width=2)
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=channel['top_line']['dates'], y=channel['top_line']['prices'],
            mode='lines', name='通道頂線', line=dict(color='#2962ff', width=2, dash='dash')
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=[channel['anchor_p3']['date']], y=[channel['anchor_p3']['price']],
            mode='markers+text', name='通道定位點(P3)',
            marker=dict(size=10, color='#e91e63', symbol='star'),
            text=["P3 定位"], textposition="top center", textfont=dict(color='#e91e63', size=11)
        ), row=1, col=1)

    fig.update_layout(
        title=dict(text=f"<b>{ticker}</b> 多功能形態分析圖", font=dict(color="#ffffff", size=18)),
        paper_bgcolor='#131722', plot_bgcolor='#1e222d', showlegend=True,
        legend=dict(font=dict(color='#d1d4dc'), orientation="h", y=1.02, x=1, xanchor="right"),
        margin=dict(l=50, r=40, t=60, b=40), hovermode="x unified"
    )

    fig.update_xaxes(gridcolor='#2a2e39', zerolinecolor='#2a2e39', autorange=True, showgrid=True, row=2, col=1)
    fig.update_yaxes(gridcolor='#2a2e39', zerolinecolor='#2a2e39', title="價格", title_font=dict(color="#d1d4dc"), tickfont=dict(color="#d1d4dc"), showgrid=True, row=1, col=1)
    fig.update_yaxes(gridcolor='#2a2e39', zerolinecolor='#2a2e39', title="成交量", title_font=dict(color="#d1d4dc"), tickfont=dict(color="#d1d4dc"), showgrid=False, row=2, col=1)

    return fig.to_html(full_html=False, include_plotlyjs='cdn')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-HK">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>股票多指標圖表分析系統</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; background-color: #0b0e14; color: #ffffff; display: flex; height: 100vh; overflow: hidden; }
        .sidebar { width: 300px; min-width: 270px; background-color: #1e222d; border-right: 1px solid #2a2e39; padding: 20px; display: flex; flex-direction: column; gap: 16px; overflow-y: auto; }
        .sidebar h2 { font-size: 18px; color: #ffffff; border-bottom: 2px solid #2962ff; padding-bottom: 8px; }
        .form-group { display: flex; flex-direction: column; gap: 6px; }
        .form-group label { font-size: 13px; color: #b2b5be; font-weight: 600; }
        select, input, button { width: 100%; padding: 10px; background-color: #131722; border: 1px solid #363c4e; border-radius: 6px; color: #ffffff; font-size: 14px; outline: none; }
        button { background-color: #2962ff; color: #ffffff; font-weight: bold; border: none; cursor: pointer; margin-top: 10px; }
        button:hover { background-color: #1e53e5; }
        
        .checkbox-group {
            background-color: #131722;
            border: 1px solid #2a2e39;
            border-radius: 6px;
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .checkbox-group h4 { color: #2962ff; font-size: 13px; border-bottom: 1px solid #2a2e39; padding-bottom: 4px; }
        .checkbox-item { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #d1d4dc; cursor: pointer; }
        .checkbox-item input[type="checkbox"] { width: auto; cursor: pointer; }

        .main-content { flex-grow: 1; height: 100vh; background-color: #131722; padding: 10px; overflow: hidden; }
        .chart-container { width: 100%; height: 100%; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>多指標圖表系統</h2>
        
        <form method="GET" action="/">
            <div class="form-group">
                <label for="ticker">熱門股票：</label>
                <select id="ticker" name="ticker" onchange="document.getElementById('custom_ticker').value=this.value;">
                    <option value="2318.HK" {% if ticker == '2318.HK' %}selected{% endif %}>中國平安 (2318.HK)</option>
                    <option value="0700.HK" {% if ticker == '0700.HK' %}selected{% endif %}>騰訊控股 (0700.HK)</option>
                    <option value="9988.HK" {% if ticker == '9988.HK' %}selected{% endif %}>阿里巴巴 (9988.HK)</option>
                    <option value="AAPL" {% if ticker == 'AAPL' %}selected{% endif %}>蘋果公司 (AAPL)</option>
                    <option value="NVDA" {% if ticker == 'NVDA' %}selected{% endif %}>輝達 (NVDA)</option>
                    <option value="TSLA" {% if ticker == 'TSLA' %}selected{% endif %}>特斯拉 (TSLA)</option>
                </select>
            </div>

            <div class="form-group">
                <label for="custom_ticker">股票代碼：</label>
                <input type="text" id="custom_ticker" name="custom_ticker" value="{{ ticker }}" placeholder="例: 0005.HK">
            </div>

            <div class="form-group">
                <label for="period">時間跨度：</label>
                <select id="period" name="period">
                    <option value="max" {% if period == 'max' %}selected{% endif %}>全部 (上市至今)</option>
                    <option value="5y" {% if period == '5y' %}selected{% endif %}>5 年</option>
                    <option value="2y" {% if period == '2y' %}selected{% endif %}>2 年</option>
                    <option value="1y" {% if period == '1y' %}selected{% endif %}>1 年</option>
                </select>
            </div>

            <div class="checkbox-group">
                <h4>顯示指標選項：</h4>
                <label class="checkbox-item">
                    <input type="checkbox" name="show_waves" value="1" {% if show_options.show_waves %}checked{% endif %}> 艾略特波浪 (1-5浪)
                </label>
                <label class="checkbox-item">
                    <input type="checkbox" name="show_candlestick" value="1" {% if show_options.show_candlestick %}checked{% endif %}> 陰陽燭形態 (身懷六甲/晨昏星/曙光/烏雲)
                </label>
                <label class="checkbox-item">
                    <input type="checkbox" name="show_hs" value="1" {% if show_options.show_hs %}checked{% endif %}> 頭肩頂 / 頭肩底
                </label>
                <label class="checkbox-item">
                    <input type="checkbox" name="show_channel" value="1" {% if show_options.show_channel %}checked{% endif %}> 平行通道
                </label>
            </div>

            <button type="submit">更新圖表</button>
        </form>
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
    period = request.args.get("period", "max")

    show_options = {
        "show_waves": request.args.get("show_waves") == "1" if request.args else True,
        "show_candlestick": request.args.get("show_candlestick") == "1" if request.args else True,
        "show_hs": request.args.get("show_hs") == "1" if request.args else True,
        "show_channel": request.args.get("show_channel") == "1" if request.args else True,
    }

    ticker = custom_ticker if custom_ticker else selected_ticker

    df = fetch_stock_data(ticker, period=period)

    if not df.empty:
        waves = calculate_elliott_waves(df)
        candle_patterns = detect_candlestick_patterns(df)
        hs_patterns = detect_head_and_shoulders(df)
        channel = calculate_parallel_channel(df)
        chart_html = build_candlestick_chart(df, waves, candle_patterns, hs_patterns, channel, ticker, show_options)
    else:
        chart_html = "<p style='color:white;padding:20px;'>無法載入股票數據。</p>"

    return render_template_string(HTML_TEMPLATE, chart_html=chart_html, ticker=ticker, period=period, show_options=show_options)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)