import os
import json
import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
import yfinance as yf
import numpy as np

app = FastAPI(title="HSI Pattern Detection Engine", version="13.0.0")

# 恒指成份股列表
HSI_CONSTITUENTS = [
    {"symbol": "HKEX:9988", "yf_code": "9988.HK", "name": "阿里巴巴-SW"},
    {"symbol": "HKEX:0700", "yf_code": "0700.HK", "name": "騰訊控股"},
    {"symbol": "HKEX:3690", "yf_code": "3690.HK", "name": "美團-W"},
    {"symbol": "HKEX:1810", "yf_code": "1810.HK", "name": "小米集團-W"},
    {"symbol": "HKEX:0005", "yf_code": "0005.HK", "name": "匯豐控股"}
]

def fetch_real_candles(ticker: str):
    """獲取真實港股日 K 線數據"""
    df = yf.download(ticker, period="1y", interval="1d")
    if df.empty:
        return [], []
    
    dates = [d.strftime("%Y-%m-%d") for d in df.index]
    candles = []
    for idx, row in df.iterrows():
        open_p = float(row['Open'])
        close_p = float(row['Close'])
        low_p = float(row['Low'])
        high_p = float(row['High'])
        candles.append([round(open_p, 2), round(close_p, 2), round(low_p, 2), round(high_p, 2)])
    return dates, candles

def detect_patterns(dates, candles):
    """
    形態偵測邏輯：
    1. 優先檢測標準頭肩底
    2. 若不符合幾何條件，則判定為「無顯著形態」
    """
    if len(candles) < 90:
        return "無顯著形態", [], []

    lows = [c[2] for c in candles]
    highs = [c[3] for c in candles]

    # 取最近 120 天的窗口進行幾何分析
    window_len = min(120, len(candles))
    sub_lows = lows[-window_len:]
    
    # 尋找全區間最低點作為潛在「頭部」
    head_rel_idx = int(np.argmin(sub_lows))
    head_idx = len(candles) - window_len + head_rel_idx
    p_head = lows[head_idx]

    # 頭部不能太接近圖表邊界（左右必須留有足夠天數形成雙肩）
    if head_rel_idx < 20 or head_rel_idx > window_len - 20:
        return "無顯著形態", [], []

    # 尋找左肩 (頭部左側 15~40 天內的局部低點)
    left_start = max(0, head_idx - 40)
    left_end = head_idx - 10
    if left_end <= left_start:
        return "無顯著形態", [], []
    ls_rel_idx = int(np.argmin(lows[left_start:left_end]))
    ls_idx = left_start + ls_rel_idx
    p_ls = lows[ls_idx]

    # 尋找右肩 (頭部右側 10~40 天內的局部低點)
    right_start = head_idx + 10
    right_end = min(len(lows), head_idx + 40)
    if right_end <= right_start:
        return "無顯著形態", [], []
    rs_rel_idx = int(np.argmin(lows[right_start:right_end]))
    rs_idx = right_start + rs_rel_idx
    p_rs = lows[rs_idx]

    # 嚴格幾何門檻校驗：
    # 1. 頭部必須顯著低於左肩與右肩（至少低 3%）
    # 2. 左右肩高度差不能太大（不超過 10%）
    if not (p_head < p_ls * 0.97 and p_head < p_rs * 0.97):
        return "無顯著形態", [], []
    if abs(p_ls - p_rs) / min(p_ls, p_rs) > 0.10:
        return "無顯著形態", [], []

    # 計算兩肩之間的反彈高點以連接頸線
    v1_idx = ls_idx + int(np.argmax(highs[ls_idx:head_idx]))
    v2_idx = head_idx + int(np.argmax(highs[head_idx:rs_idx]))
    p_v1 = highs[v1_idx]
    p_v2 = highs[v2_idx]

    mark_lines = [[
        {"name": "頸線 (Neckline)", "coord": [dates[v1_idx], p_v1], "lineStyle": {"color": "#2962ff", "width": 2, "type": "solid"}},
        {"coord": [dates[min(len(dates)-1, rs_idx + 25)], p_v2]}
    ]]

    mark_points = [
        {"name": "左肩", "coord": [dates[ls_idx], p_ls], "value": "左肩", "itemStyle": {"color": "#089981"}},
        {"name": "頭部", "coord": [dates[head_idx], p_head], "value": "頭部", "itemStyle": {"color": "#f23645"}},
        {"name": "右肩", "coord": [dates[rs_idx], p_rs], "value": "右肩", "itemStyle": {"color": "#089981"}}
    ]

    return "標準頭肩底形態", mark_lines, mark_points

@app.get("/")
def read_root():
    return RedirectResponse(url="/custom-chart?symbol=HKEX:9988")

@app.get("/custom-chart", response_class=HTMLResponse)
def get_custom_chart(symbol: str = "HKEX:9988"):
    item = next((x for x in HSI_CONSTITUENTS if x["symbol"] == symbol), HSI_CONSTITUENTS[0])
    
    dates, candles = fetch_real_candles(item["yf_code"])
    pattern_name, mark_lines, mark_points = detect_patterns(dates, candles)

    dates_json = json.dumps(dates)
    candles_json = json.dumps(candles)
    mark_lines_json = json.dumps(mark_lines)
    mark_points_json = json.dumps(mark_points)

    status_badge = f'<span style="background: #2962ff; padding: 6px 12px; border-radius: 4px;">🎯 偵測型態：{pattern_name}</span>' if pattern_name != "無顯著形態" else '<span style="background: #363a45; color: #9194a1; padding: 6px 12px; border-radius: 4px;">⚪ 當前無顯著幾何形態</span>'

    return f"""
    <!DOCTYPE html>
    <html lang="zh-HK">
    <head>
        <meta charset="UTF-8">
        <title>{symbol} - 幾何圖表分析</title>
        <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        <style>
            body {{ font-family: sans-serif; background: #131722; color: #ffffff; padding: 20px; margin: 0; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
            #chartContainer {{ width: 100%; height: 680px; background: #1e222d; border-radius: 8px; border: 1px solid #2a2e39; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>{symbol} ({item['name']}) - K 線圖分析</h2>
            {status_badge}
        </div>
        <div id="chartContainer"></div>
        <script>
            const chartDom = document.getElementById('chartContainer');
            const myChart = echarts.init(chartDom, 'dark');

            const option = {{
                backgroundColor: '#1e222d',
                tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'cross' }} }},
                grid: {{ left: '5%', right: '5%', bottom: '15%' }},
                xAxis: {{ type: 'category', data: {dates_json}, scale: true, boundaryGap: false }},
                yAxis: {{ scale: true, splitLine: {{ lineStyle: {{ color: '#2a2e39' }} }} }},
                dataZoom: [{{ type: 'inside', start: 50, end: 100 }}, {{ show: true, type: 'slider', top: '90%' }}],
                series: [{{
                    name: '日 K 線',
                    type: 'candlestick',
                    data: {candles_json},
                    itemStyle: {{ color: '#089981', color0: '#f23645', borderColor: '#089981', borderColor0: '#f23645' }},
                    markLine: {{ symbol: ['none', 'none'], data: {mark_lines_json} }},
                    markPoint: {{ data: {mark_points_json}, symbol: 'pin', symbolSize: 40 }}
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
