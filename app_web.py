import os
import json
import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
import yfinance as yf
import numpy as np

app = FastAPI(title="HSI Geometric Trend Engine", version="16.0.0")

HSI_CONSTITUENTS = [
    {"symbol": "HKEX:0700", "yf_code": "0700.HK", "name": "騰訊控股"},
    {"symbol": "HKEX:9988", "yf_code": "9988.HK", "name": "阿里巴巴-SW"},
    {"symbol": "HKEX:3690", "yf_code": "3690.HK", "name": "美團-W"},
    {"symbol": "HKEX:1810", "yf_code": "1810.HK", "name": "小米集團-W"},
    {"symbol": "HKEX:1024", "yf_code": "1024.HK", "name": "快手-W"},
    {"symbol": "HKEX:2318", "yf_code": "2318.HK", "name": "中國平安"},
    {"symbol": "HKEX:0005", "yf_code": "0005.HK", "name": "匯豐控股"},
    {"symbol": "HKEX:0941", "yf_code": "0941.HK", "name": "中國移動"},
    {"symbol": "HKEX:1211", "yf_code": "1211.HK", "name": "比亞迪股份"},
    {"symbol": "HKEX:9618", "yf_code": "9618.HK", "name": "京東集團-SW"}
]

DATA_CACHE = {}
CACHE_TIMEOUT = 600

def fetch_stock_data(ticker: str):
    """獲取真實 K 線數據"""
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

def detect_trend_channels(dates, candles):
    """幾何分析：自動偵測趨勢通道 (Channel) 與幾何趨勢線"""
    if len(candles) < 60:
        return "無顯著形態", [], []

    # 取最近 60 個交易日進行通道回歸
    recent_dates = dates[-60:]
    recent_lows = np.array([c[2] for c in candles[-60:]])
    recent_highs = np.array([c[3] for c in candles[-60:]])
    x = np.arange(len(recent_lows))

    # 計算低點趨勢線 (Lower Support) 與 高點趨勢線 (Upper Resistance)
    slope_low, intercept_low = np.polyfit(x, recent_lows, 1)
    slope_high, intercept_high = np.polyfit(x, recent_highs, 1)

    # 平行通道擬合 (平均斜率)
    avg_slope = (slope_low + slope_high) / 2.0
    
    start_date = recent_dates[0]
    end_date = recent_dates[-1]

    # 計算繪線座標
    y_low_start = round(float(intercept_low), 2)
    y_low_end = round(float(intercept_low + avg_slope * 59), 2)
    y_high_start = round(float(intercept_high), 2)
    y_high_end = round(float(intercept_high + avg_slope * 59), 2)
    
    # 中軸線 (Midline)
    y_mid_start = round((y_low_start + y_high_start) / 2.0, 2)
    y_mid_end = round((y_low_end + y_high_end) / 2.0, 2)

    mark_lines = [
        # 上軌阻力線 (粉紅/紅色)
        [
            {"name": "通道上軌", "coord": [start_date, y_high_start], "lineStyle": {"color": "#e91e63", "width": 2, "type": "solid"}},
            {"coord": [end_date, y_high_end]}
        ],
        # 下軌支撐線 (粉紅/紅色)
        [
            {"name": "通道下軌", "coord": [start_date, y_low_start], "lineStyle": {"color": "#e91e63", "width": 2, "type": "solid"}},
            {"coord": [end_date, y_low_end]}
        ],
        # 中軸趨勢線 (藍色虛線)
        [
            {"name": "中軸趨勢", "coord": [start_date, y_mid_start], "lineStyle": {"color": "#2962ff", "width": 1.5, "type": "dashed"}},
            {"coord": [end_date, y_mid_end]}
        ]
    ]

    pattern_type = "上升通道 (Ascending Channel)" if avg_slope > 0.05 else ("下降通道 (Descending Channel)" if avg_slope < -0.05 else "矩形整理通道")
    return pattern_type, mark_lines, []

@app.get("/")
def read_root():
    return RedirectResponse(url="/matrix")

@app.get("/matrix", response_class=HTMLResponse)
def get_matrix_view():
    rows_html = ""
    for rank, item in enumerate(HSI_CONSTITUENTS, 1):
        dates, candles = fetch_stock_data(item["yf_code"])
        pattern_name, _, _ = detect_trend_channels(dates, candles)
        
        status_tag = f'<span style="color: #089981; font-weight: bold;">📈 {pattern_name}</span>'
        chart_url = f"/custom-chart?symbol={item['symbol']}"

        rows_html += f"""
        <tr>
            <td style="color: #787b86;">{rank}</td>
            <td style="font-weight: bold; color: #2962ff;">{item['symbol']}</td>
            <td style="font-weight: bold; color: #ffffff;">{item['name']}</td>
            <td>{status_tag}</td>
            <td><a href="{chart_url}" class="btn-link">🎨 查看圖表與趨勢線</a></td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="zh-HK">
    <head>
        <meta charset="UTF-8">
        <title>恒指成份股幾何形態矩陣</title>
        <style>
            body {{ font-family: sans-serif; background: #131722; color: #d1d4dc; padding: 25px; }}
            h2 {{ color: #ffffff; margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; background: #1e222d; border-radius: 8px; overflow: hidden; }}
            th, td {{ padding: 14px 18px; border-bottom: 1px solid #2a2e39; text-align: left; }}
            th {{ background: #2a2e39; color: #787b86; font-size: 14px; }}
            tr:hover {{ background: #262b3e; }}
            .btn-link {{ background: #2962ff; color: white; padding: 6px 14px; border-radius: 4px; text-decoration: none; font-size: 13px; font-weight: bold; }}
            .btn-link:hover {{ background: #1e4bd8; }}
        </style>
    </head>
    <body>
        <h2>恒生指數成份股 - 自動趨勢通道與幾何圖表</h2>
        <table>
            <thead>
                <tr>
                    <th>序號</th>
                    <th>股票代碼</th>
                    <th>股票名稱</th>
                    <th>當前幾何型態</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
    </body>
    </html>
    """

@app.get("/custom-chart", response_class=HTMLResponse)
def get_custom_chart(symbol: str = "HKEX:0700"):
    item = next((x for x in HSI_CONSTITUENTS if x["symbol"] == symbol), HSI_CONSTITUENTS[0])
    dates, candles = fetch_stock_data(item["yf_code"])
    pattern_name, mark_lines, mark_points = detect_trend_channels(dates, candles)

    return f"""
    <!DOCTYPE html>
    <html lang="zh-HK">
    <head>
        <meta charset="UTF-8">
        <title>{symbol} - 幾何趨勢通道</title>
        <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        <style>
            body {{ font-family: sans-serif; background: #131722; color: #ffffff; padding: 20px; margin: 0; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
            .back-btn {{ color: #2962ff; text-decoration: none; font-weight: bold; font-size: 14px; margin-bottom: 10px; display: inline-block; }}
            #chartContainer {{ width: 100%; height: 680px; background: #1e222d; border-radius: 8px; border: 1px solid #2a2e39; }}
        </style>
    </head>
    <body>
        <a href="/matrix" class="back-btn">⬅️ 返回成份股矩陣列表</a>
        <div class="header">
            <h2>{symbol} ({item['name']}) - K 線趨勢線分析</h2>
            <span style="background: #2962ff; padding: 6px 12px; border-radius: 4px;">🎯 偵測型態：{pattern_name}</span>
        </div>
        <div id="chartContainer"></div>
        <script>
            const chartDom = document.getElementById('chartContainer');
            const myChart = echarts.init(chartDom, 'dark');

            const option = {{
                backgroundColor: '#1e222d',
                tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'cross' }} }},
                grid: {{ left: '5%', right: '5%', bottom: '15%' }},
                xAxis: {{ type: 'category', data: {json.dumps(dates)}, scale: true, boundaryGap: false }},
                yAxis: {{ scale: true, splitLine: {{ lineStyle: {{ color: '#2a2e39' }} }} }},
                dataZoom: [{{ type: 'inside', start: 40, end: 100 }}, {{ show: true, type: 'slider', top: '90%' }}],
                series: [{{
                    name: '日 K 線',
                    type: 'candlestick',
                    data: {json.dumps(candles)},
                    // 配色更換：綠升紅跌（TradingView 港股標準樣式）
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
