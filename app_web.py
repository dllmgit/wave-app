import os
import json
import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
import yfinance as yf
import numpy as np

import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
import yfinance as yf
import numpy as np

app = FastAPI(title="HSI Geometric & Candlestick Engine", version="19.0.0")

HSI_FULL_LIST = [
    {"symbol": "HKEX:0700", "yf_code": "0700.HK", "name": "騰訊控股"},
    {"symbol": "HKEX:9988", "yf_code": "9988.HK", "name": "阿里巴巴-SW"},
    {"symbol": "HKEX:3690", "yf_code": "3690.HK", "name": "美團-W"},
    {"symbol": "HKEX:1810", "yf_code": "1810.HK", "name": "小米集團-W"},
    {"symbol": "HKEX:0005", "yf_code": "0005.HK", "name": "匯豐控股"},
    {"symbol": "HKEX:0941", "yf_code": "0941.HK", "name": "中國移動"},
    {"symbol": "HKEX:1211", "yf_code": "1211.HK", "name": "比亞迪股份"},
    {"symbol": "HKEX:2318", "yf_code": "2318.HK", "name": "中國平安"},
    {"symbol": "HKEX:1024", "yf_code": "1024.HK", "name": "快手-W"},
    {"symbol": "HKEX:9618", "yf_code": "9618.HK", "name": "京東集團-SW"},
    {"symbol": "HKEX:0388", "yf_code": "0388.HK", "name": "香港交易所"},
    {"symbol": "HKEX:0823", "yf_code": "0823.HK", "name": "領展房產基金"},
    {"symbol": "HKEX:2269", "yf_code": "2269.HK", "name": "藥明生物"},
    {"symbol": "HKEX:2015", "yf_code": "2015.HK", "name": "理想汽車-W"}
]

DATA_CACHE = {}
CACHE_TIMEOUT = 600

def fetch_stock_data(ticker: str):
    now = datetime.datetime.now()
    if ticker in DATA_CACHE:
        entry = DATA_CACHE[ticker]
        if (now - entry["time"]).total_seconds() < CACHE_TIMEOUT:
            return entry["dates"], entry["candles"]

    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y", interval="1d")
        if df.empty:
            return [], []

        dates = [d.strftime("%Y-%m-%d") for d in df.index]
        candles = []
        for _, row in df.iterrows():
            candles.append([
                round(float(row['Open']), 2),
                round(float(row['Close']), 2),
                round(float(row['Low']), 2),
                round(float(row['High']), 2)
            ])

        DATA_CACHE[ticker] = {"time": now, "dates": dates, "candles": candles}
        return dates, candles
    except Exception:
        if ticker in DATA_CACHE:
            return DATA_CACHE[ticker]["dates"], DATA_CACHE[ticker]["candles"]
        return [], []

def find_pivots(candles, window=3):
    """尋找真實的波峰 (Pivot Highs) 與波谷 (Pivot Lows)"""
    highs = [c[3] for c in candles]
    lows = [c[2] for c in candles]
    n = len(candles)
    
    pivot_highs = []
    pivot_lows = []

    for i in range(window, n - window):
        # 判斷是否為區域最高點
        if all(highs[i] >= highs[i - k] for k in range(1, window + 1)) and \
           all(highs[i] >= highs[i + k] for k in range(1, window + 1)):
            pivot_highs.append((i, highs[i]))
            
        # 判斷是否為區域最低點
        if all(lows[i] <= lows[i - k] for k in range(1, window + 1)) and \
           all(lows[i] <= lows[i + k] for k in range(1, window + 1)):
            pivot_lows.append((i, lows[i]))

    return pivot_highs, pivot_lows

def detect_candlestick_patterns(candles):
    """陰陽燭形態邏輯判斷"""
    if len(candles) < 3:
        return []

    patterns = []
    curr = candles[-1]
    prev = candles[-2]

    o, c, l, h = curr[0], curr[1], curr[2], curr[3]
    body = abs(c - o)
    shade = h - l
    
    if shade > 0 and body / shade <= 0.1:
        patterns.append({"name": "十字星 (Doji)", "color": "#ffb74d"})

    lower_shadow = min(o, c) - l
    upper_shadow = h - max(o, c)
    if body > 0 and lower_shadow >= 2 * body and upper_shadow <= body * 0.5:
        patterns.append({"name": "鎚頭線 (Hammer)", "color": "#089981"})

    if prev[1] < prev[0] and c > o and o <= prev[1] and c >= prev[0]:
        patterns.append({"name": "陽線吞噬 (Bullish Engulfing)", "color": "#2962ff"})

    return patterns

def calculate_pivot_channel(dates, candles):
    """嚴謹的 Pivot 切線 + 相同斜率平行平移通道"""
    if len(candles) < 60:
        return "數據不足", [], []

    recent_dates = dates[-60:]
    recent_candles = candles[-60:]
    recent_highs = np.array([c[3] for c in recent_candles])
    recent_lows = np.array([c[2] for c in recent_candles])
    x = np.arange(60)

    p_highs, p_lows = find_pivots(recent_candles, window=3)

    mark_lines = []
    slope = 0.0

    # 優先嘗試用兩個顯著 Pivot Highs 作為上軌阻力線
    if len(p_highs) >= 2:
        idx1, h1 = p_highs[-2]
        idx2, h2 = p_highs[-1]
        slope = (h2 - h1) / (idx2 - idx1)
        intercept_high = h1 - slope * idx1

        # 確保上軌壓在所有 High 之上或精準貼合
        diff_high = recent_highs - (slope * x + intercept_high)
        intercept_high += np.max(diff_high)

        # 下軌：相同斜率平行下移至最低 Low
        intercept_low = np.min(recent_lows - slope * x)

        start_date, end_date = recent_dates[0], recent_dates[-1]
        
        y_high_start = round(float(intercept_high), 2)
        y_high_end = round(float(intercept_high + slope * 59), 2)
        y_low_start = round(float(intercept_low), 2)
        y_low_end = round(float(intercept_low + slope * 59), 2)

        mark_lines = [
            [
                {"name": "波峰阻力線", "coord": [start_date, y_high_start], "lineStyle": {"color": "#e91e63", "width": 2}},
                {"coord": [end_date, y_high_end]}
            ],
            [
                {"name": "波谷支撐線", "coord": [start_date, y_low_start], "lineStyle": {"color": "#2196f3", "width": 2}},
                {"coord": [end_date, y_low_end]}
            ]
        ]
    elif len(p_lows) >= 2: # 備用方案：若頂點不夠，改用底點連線平行上移
        idx1, l1 = p_lows[-2]
        idx2, l2 = p_lows[-1]
        slope = (l2 - l1) / (idx2 - idx1)
        intercept_low = l1 - slope * idx1

        diff_low = recent_lows - (slope * x + intercept_low)
        intercept_low += np.min(diff_low)

        intercept_high = np.max(recent_highs - slope * x)

        start_date, end_date = recent_dates[0], recent_dates[-1]

        mark_lines = [
            [
                {"name": "波峰阻力線", "coord": [start_date, round(float(intercept_high), 2)], "lineStyle": {"color": "#e91e63", "width": 2}},
                {"coord": [end_date, round(float(intercept_high + slope * 59), 2)]}
            ],
            [
                {"name": "波谷支撐線", "coord": [start_date, round(float(intercept_low), 2)], "lineStyle": {"color": "#2196f3", "width": 2}},
                {"coord": [end_date, round(float(intercept_low + slope * 59), 2)]}
            ]
        ]

    channel_name = "上升通道" if slope > 0.03 else ("下降通道" if slope < -0.03 else "橫向通道")
    return channel_name, mark_lines, []

@app.get("/")
def read_root():
    return RedirectResponse(url="/custom-chart?symbol=HKEX:0700")

@app.get("/custom-chart", response_class=HTMLResponse)
def get_custom_chart(symbol: str = "HKEX:0700"):
    clean_code = symbol.upper().replace("HKEX:", "").replace(".HK", "").zfill(4)
    yf_code = f"{clean_code}.HK"
    display_symbol = f"HKEX:{clean_code}"

    matched = next((x for x in HSI_FULL_LIST if clean_code in x["symbol"]), None)
    stock_name = matched["name"] if matched else "自訂股票"

    dates, candles = fetch_stock_data(yf_code)
    channel_name, mark_lines, _ = calculate_pivot_channel(dates, candles)
    candlestick_patterns = detect_candlestick_patterns(candles)

    options_html = ""
    for item in HSI_FULL_LIST:
        selected = "selected" if clean_code in item["symbol"] else ""
        options_html += f'<option value="{item["symbol"]}" {selected}>{item["symbol"]} - {item["name"]}</option>'

    pattern_tags_html = ""
    for p in candlestick_patterns:
        pattern_tags_html += f'<span style="background: {p["color"]}; padding: 4px 8px; border-radius: 4px; margin-left: 6px; font-size: 12px;">🕯️ {p["name"]}</span>'

    return f"""
    <!DOCTYPE html>
    <html lang="zh-HK">
    <head>
        <meta charset="UTF-8">
        <title>{display_symbol} - 幾何與陰陽燭圖表</title>
        <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        <style>
            body {{ font-family: sans-serif; background: #131722; color: #ffffff; padding: 20px; margin: 0; }}
            .toolbar {{ display: flex; gap: 15px; align-items: center; background: #1e222d; padding: 12px 20px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #2a2e39; }}
            select, input, button {{ background: #2a2e39; color: #ffffff; border: 1px solid #363a45; padding: 8px 12px; border-radius: 4px; outline: none; }}
            button {{ background: #2962ff; font-weight: bold; cursor: pointer; border: none; }}
            button:hover {{ background: #1e4bd8; }}
            #chartContainer {{ width: 100%; height: 680px; background: #1e222d; border-radius: 8px; border: 1px solid #2a2e39; }}
        </style>
    </head>
    <body>
        <div class="toolbar">
            <label>快速選擇成份股：</label>
            <select onchange="location.href='/custom-chart?symbol=' + this.value">
                {options_html}
            </select>
            
            <label style="margin-left: 15px;">或手動輸入代碼：</label>
            <input type="text" id="symbolInput" placeholder="例如：0005 或 9988" value="{clean_code}" style="width: 120px;">
            <button onclick="searchSymbol()">搜尋載入</button>
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <h2>{display_symbol} ({stock_name}) - K 線幾何分析</h2>
            <div>
                <span style="background: #2962ff; padding: 6px 12px; border-radius: 4px; font-size: 13px;">📐 通道：{channel_name}</span>
                {pattern_tags_html}
            </div>
        </div>

        <div id="chartContainer"></div>

        <script>
            function searchSymbol() {{
                const val = document.getElementById('symbolInput').value.trim();
                if (val) {{
                    location.href = '/custom-chart?symbol=' + val;
                }}
            }}

            const chartDom = document.getElementById('chartContainer');
            const myChart = echarts.init(chartDom, 'dark');

            const option = {{
                backgroundColor: '#1e222d',
                tooltip: {{ 
                    trigger: 'axis', 
                    axisPointer: {{ type: 'cross' }},
                    position: [60, 15],
                    backgroundColor: 'rgba(30, 34, 45, 0.9)',
                    borderColor: '#2a2e39',
                    padding: [4, 8],
                    textStyle: {{ color: '#d1d4dc', fontSize: 12 }},
                    formatter: function (params) {{
                        if (!params || !params[0] || !params[0].data) return '';
                        const date = params[0].name;
                        const data = params[0].data;
                        return `<span style="color:#787b86;">${{date}}</span> &nbsp;|&nbsp; 開: <b>${{data[1]}}</b> &nbsp; 高: <b>${{data[4]}}</b> &nbsp; 低: <b>${{data[3]}}</b> &nbsp; 收: <b>${{data[2]}}</b>`;
                    }}
                }},
                grid: {{ left: '5%', right: '5%', bottom: '15%' }},
                xAxis: {{ type: 'category', data: {json.dumps(dates)}, scale: true, boundaryGap: false }},
                yAxis: {{ scale: true, splitLine: {{ lineStyle: {{ color: '#2a2e39' }} }} }},
                dataZoom: [{{ type: 'inside', start: 40, end: 100 }}, {{ show: true, type: 'slider', top: '90%' }}],
                series: [{{
                    name: '日 K 線',
                    type: 'candlestick',
                    data: {json.dumps(candles)},
                    itemStyle: {{ 
                        color: '#089981', 
                        color0: '#f23645', 
                        borderColor: '#089981', 
                        borderColor0: '#f23645' 
                    }},
                    markLine: {{ 
                        symbol: ['none', 'none'], 
                        data: {json.dumps(mark_lines)} 
                    }}
                }}]
            }};
            myChart.setOption(option);
            window.addEventListener('resize', myChart.resize);
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app_web:app", host="0.0.0.0", port=port, reload=True)

import yfinance as yf
import numpy as np

app = FastAPI(title="HSI Geometric & Candlestick Engine", version="18.0.0")

# 完整恒指核心成份股選單 (80+ 隻可自由選擇，亦支援手動輸入代碼)
HSI_FULL_LIST = [
    {"symbol": "HKEX:0700", "yf_code": "0700.HK", "name": "騰訊控股"},
    {"symbol": "HKEX:9988", "yf_code": "9988.HK", "name": "阿里巴巴-SW"},
    {"symbol": "HKEX:3690", "yf_code": "3690.HK", "name": "美團-W"},
    {"symbol": "HKEX:1810", "yf_code": "1810.HK", "name": "小米集團-W"},
    {"symbol": "HKEX:0005", "yf_code": "0005.HK", "name": "匯豐控股"},
    {"symbol": "HKEX:0941", "yf_code": "0941.HK", "name": "中國移動"},
    {"symbol": "HKEX:1211", "yf_code": "1211.HK", "name": "比亞迪股份"},
    {"symbol": "HKEX:2318", "yf_code": "2318.HK", "name": "中國平安"},
    {"symbol": "HKEX:1024", "yf_code": "1024.HK", "name": "快手-W"},
    {"symbol": "HKEX:9618", "yf_code": "9618.HK", "name": "京東集團-SW"},
    {"symbol": "HKEX:0388", "yf_code": "0388.HK", "name": "香港交易所"},
    {"symbol": "HKEX:0823", "yf_code": "0823.HK", "name": "領展房產基金"},
    {"symbol": "HKEX:2269", "yf_code": "2269.HK", "name": "藥明生物"},
    {"symbol": "HKEX:2015", "yf_code": "2015.HK", "name": "理想汽車-W"}
]

DATA_CACHE = {}
CACHE_TIMEOUT = 600

def fetch_stock_data(ticker: str):
    """獲取 K 線數據 (帶快取)"""
    now = datetime.datetime.now()
    if ticker in DATA_CACHE:
        entry = DATA_CACHE[ticker]
        if (now - entry["time"]).total_seconds() < CACHE_TIMEOUT:
            return entry["dates"], entry["candles"]

    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y", interval="1d")
        if df.empty:
            return [], []

        dates = [d.strftime("%Y-%m-%d") for d in df.index]
        candles = []
        for _, row in df.iterrows():
            candles.append([
                round(float(row['Open']), 2),
                round(float(row['Close']), 2),
                round(float(row['Low']), 2),
                round(float(row['High']), 2)
            ])

        DATA_CACHE[ticker] = {"time": now, "dates": dates, "candles": candles}
        return dates, candles
    except Exception:
        if ticker in DATA_CACHE:
            return DATA_CACHE[ticker]["dates"], DATA_CACHE[ticker]["candles"]
        return [], []

def detect_candlestick_patterns(candles):
    """第二點：陰陽燭形態判斷 (Hammer / Engulfing / Doji)"""
    if len(candles) < 2:
        return []

    patterns = []
    curr = candles[-1] # [Open, Close, Low, High]
    prev = candles[-2]

    o, c, l, h = curr[0], curr[1], curr[2], curr[3]
    body = abs(c - o)
    shade = h - l
    
    # 1. 十字星 (Doji)
    if shade > 0 and body / shade <= 0.1:
        patterns.append({"name": "十字星 (Doji)", "color": "#ffb74d"})

    # 2. 錘頭線 (Hammer - 底部下影線長)
    lower_shadow = min(o, c) - l
    upper_shadow = h - max(o, c)
    if body > 0 and lower_shadow >= 2 * body and upper_shadow <= body * 0.5:
        patterns.append({"name": "鎚頭線 (Hammer)", "color": "#089981"})

    # 3. 陽包陰 / 陽線吞噬 (Bullish Engulfing)
    if prev[1] < prev[0] and c > o: # 前陰後陽
        if o <= prev[1] and c >= prev[0]:
            patterns.append({"name": "陽線吞噬 (Bullish Engulfing)", "color": "#2962ff"})

    return patterns

def calculate_pivot_channel(dates, candles):
    """第一點：根據真實高點斜率劃線，並平行下移至最低點"""
    if len(candles) < 60:
        return "無顯著通道", [], []

    recent_dates = dates[-60:]
    recent_highs = np.array([c[3] for c in candles[-60:]])
    recent_lows = np.array([c[2] for c in candles[-60:]])
    x = np.arange(60)

    # 找出區間內兩個最顯著的高點 (Pivot Highs) 計算真實頂部斜率
    sorted_high_indices = np.argsort(recent_highs)[-10:] # 前 10 大高點中選兩點
    sorted_high_indices = np.sort(sorted_high_indices)
    
    idx1, idx2 = sorted_high_indices[0], sorted_high_indices[-1]
    if idx1 == idx2:
        idx1, idx2 = 0, 59

    # 1. 計算頂點連線斜率
    slope = (recent_highs[idx2] - recent_highs[idx1]) / (idx2 - idx1)
    intercept_high = recent_highs[idx1] - slope * idx1

    # 2. 平行向下移動：以相同斜率往下壓到最底部的 K 線 Low
    intercept_low = np.min(recent_lows - slope * x)

    # 繪線座標計算
    start_date, end_date = recent_dates[0], recent_dates[-1]
    y_high_start = round(float(intercept_high), 2)
    y_high_end = round(float(intercept_high + slope * 59), 2)
    y_low_start = round(float(intercept_low), 2)
    y_low_end = round(float(intercept_low + slope * 59), 2)

    mark_lines = [
        [
            {"name": "頂點阻力線", "coord": [start_date, y_high_start], "lineStyle": {"color": "#e91e63", "width": 2}},
            {"coord": [end_date, y_high_end]}
        ],
        [
            {"name": "平行底線 (最低點)", "coord": [start_date, y_low_start], "lineStyle": {"color": "#2196f3", "width": 2}},
            {"coord": [end_date, y_low_end]}
        ]
    ]

    channel_name = "上升通道" if slope > 0.05 else ("下降通道" if slope < -0.05 else "橫向通道")
    return channel_name, mark_lines, []

@app.get("/")
def read_root():
    return RedirectResponse(url="/custom-chart?symbol=HKEX:0700")

@app.get("/custom-chart", response_class=HTMLResponse)
def get_custom_chart(symbol: str = "HKEX:0700"):
    # 處理手動輸入 (例如輸入 0005 自動補全為 HKEX:0005 / 0005.HK)
    clean_code = symbol.upper().replace("HKEX:", "").replace(".HK", "").zfill(4)
    yf_code = f"{clean_code}.HK"
    display_symbol = f"HKEX:{clean_code}"

    # 尋找名稱
    matched = next((x for x in HSI_FULL_LIST if clean_code in x["symbol"]), None)
    stock_name = matched["name"] if matched else "自訂股票"

    dates, candles = fetch_stock_data(yf_code)
    channel_name, mark_lines, _ = calculate_pivot_channel(dates, candles)
    candlestick_patterns = detect_candlestick_patterns(candles)

    # 下拉選單 HTML
    options_html = ""
    for item in HSI_FULL_LIST:
        selected = "selected" if clean_code in item["symbol"] else ""
        options_html += f'<option value="{item["symbol"]}" {selected}>{item["symbol"]} - {item["name"]}</option>'

    # 陰陽燭標籤 HTML
    pattern_tags_html = ""
    for p in candlestick_patterns:
        pattern_tags_html += f'<span style="background: {p["color"]}; padding: 4px 8px; border-radius: 4px; margin-left: 6px; font-size: 12px;">🕯️ {p["name"]}</span>'

    return f"""
    <!DOCTYPE html>
    <html lang="zh-HK">
    <head>
        <meta charset="UTF-8">
        <title>{display_symbol} - 幾何與陰陽燭圖表</title>
        <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        <style>
            body {{ font-family: sans-serif; background: #131722; color: #ffffff; padding: 20px; margin: 0; }}
            .toolbar {{ display: flex; gap: 15px; align-items: center; background: #1e222d; padding: 12px 20px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #2a2e39; }}
            select, input, button {{ background: #2a2e39; color: #ffffff; border: 1px solid #363a45; padding: 8px 12px; border-radius: 4px; outline: none; }}
            button {{ background: #2962ff; font-weight: bold; cursor: pointer; border: none; }}
            button:hover {{ background: #1e4bd8; }}
            #chartContainer {{ width: 100%; height: 680px; background: #1e222d; border-radius: 8px; border: 1px solid #2a2e39; }}
        </style>
    </head>
    <body>
        <!-- 第三點：輸入框 + 下拉選單 -->
        <div class="toolbar">
            <label>快速選擇成份股：</label>
            <select onchange="location.href='/custom-chart?symbol=' + this.value">
                {options_html}
            </select>
            
            <label style="margin-left: 15px;">或手動輸入代碼：</label>
            <input type="text" id="symbolInput" placeholder="例如：0005 或 9988" value="{clean_code}" style="width: 120px;">
            <button onclick="searchSymbol()">搜尋載入</button>
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <h2>{display_symbol} ({stock_name}) - K 線幾何分析</h2>
            <div>
                <span style="background: #2962ff; padding: 6px 12px; border-radius: 4px; font-size: 13px;">📐 通道：{channel_name}</span>
                {pattern_tags_html}
            </div>
        </div>

        <div id="chartContainer"></div>

        <script>
            function searchSymbol() {{
                const val = document.getElementById('symbolInput').value.trim();
                if (val) {{
                    location.href = '/custom-chart?symbol=' + val;
                }}
            }}

            const chartDom = document.getElementById('chartContainer');
            const myChart = echarts.init(chartDom, 'dark');

            const option = {{
                backgroundColor: '#1e222d',
                tooltip: {{ 
                    trigger: 'axis', 
                    axisPointer: {{ type: 'cross' }},
                    position: [60, 15], // 第一點：提示框固定左上角橫向展示
                    backgroundColor: 'rgba(30, 34, 45, 0.9)',
                    borderColor: '#2a2e39',
                    padding: [4, 8],
                    textStyle: {{ color: '#d1d4dc', fontSize: 12 }},
                    formatter: function (params) {{
                        if (!params || !params[0] || !params[0].data) return '';
                        const date = params[0].name;
                        const data = params[0].data;
                        return `<span style="color:#787b86;">${{date}}</span> &nbsp;|&nbsp; 開: <b>${{data[1]}}</b> &nbsp; 高: <b>${{data[4]}}</b> &nbsp; 低: <b>${{data[3]}}</b> &nbsp; 收: <b>${{data[2]}}</b>`;
                    }}
                }},
                grid: {{ left: '5%', right: '5%', bottom: '15%' }},
                xAxis: {{ type: 'category', data: {json.dumps(dates)}, scale: true, boundaryGap: false }},
                yAxis: {{ scale: true, splitLine: {{ lineStyle: {{ color: '#2a2e39' }} }} }},
                dataZoom: [{{ type: 'inside', start: 40, end: 100 }}, {{ show: true, type: 'slider', top: '90%' }}],
                series: [{{
                    name: '日 K 線',
                    type: 'candlestick',
                    data: {json.dumps(candles)},
                    itemStyle: {{ 
                        color: '#089981', 
                        color0: '#f23645', 
                        borderColor: '#089981', 
                        borderColor0: '#f23645' 
                    }},
                    markLine: {{ 
                        symbol: ['none', 'none'], 
                        data: {json.dumps(mark_lines)} 
                    }}
                }}]
            }};
            myChart.setOption(option);
            window.addEventListener('resize', myChart.resize);
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app_web:app", host="0.0.0.0", port=port, reload=True)
