import os
import json
import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
import yfinance as yf
import numpy as np

app = FastAPI(title="HSI Full Matrix Pattern Engine", version="15.0.0")

# 恒生指數核心成份股代表清單 (可隨意擴充)
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

# 全域快取與冷卻時間設定 (10分鐘快取)
DATA_CACHE = {}
CACHE_TIMEOUT = 600

def fetch_stock_data(ticker: str):
    """獲取單隻股票真實 K 線數據 (帶快取)"""
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

def analyze_pattern(dates, candles):
    """幾何形態辨識引擎：有形態才繪製，無形態回傳空標註"""
    if len(candles) < 90:
        return "無顯著形態", [], []

    lows = [c[2] for c in candles]
    highs = [c[3] for c in candles]

    # 取近 120 日數據計算頭肩底
    w_len = min(120, len(candles))
    sub_lows = lows[-w_len:]
    head_rel = int(np.argmin(sub_lows))
    head_idx = len(candles) - w_len + head_rel
    p_head = lows[head_idx]

    if 20 <= head_rel <= w_len - 20:
        # 左肩與右肩極值尋找
        l_range = lows[max(0, head_idx - 40):head_idx - 10]
        r_range = lows[head_idx + 10:min(len(lows), head_idx + 40)]
        
        if l_range and r_range:
            ls_idx = max(0, head_idx - 40) + int(np.argmin(l_range))
            rs_idx = head_idx + 10 + int(np.argmin(r_range))
            p_ls, p_rs = lows[ls_idx], lows[rs_idx]

            # 幾何條件校驗：頭部顯著低於兩肩
            if p_head < p_ls * 0.97 and p_head < p_rs * 0.97 and abs(p_ls - p_rs) / min(p_ls, p_rs) <= 0.12:
                v1_idx = ls_idx + int(np.argmax(highs[ls_idx:head_idx]))
                v2_idx = head_idx + int(np.argmax(highs[head_idx:rs_idx]))
                p_v1, p_v2 = highs[v1_idx], highs[v2_idx]

                mark_lines = [[
                    {"name": "頸線 (Neckline)", "coord": [dates[v1_idx], p_v1], "lineStyle": {"color": "#2962ff", "width": 2}},
                    {"coord": [dates[min(len(dates)-1, rs_idx + 25)], p_v2]}
                ]]

                mark_points = [
                    {"name": "左肩", "coord": [dates[ls_idx], p_ls], "value": "左肩", "itemStyle": {"color": "#089981"}},
                    {"name": "頭部", "coord": [dates[head_idx], p_head], "value": "頭部", "itemStyle": {"color": "#f23645"}},
                    {"name": "右肩", "coord": [dates[rs_idx], p_rs], "value": "右肩", "itemStyle": {"color": "#089981"}}
                ]

                return "標準頭肩底形態", mark_lines, mark_points

    return "無顯著形態", [], []

@app.get("/")
def read_root():
    return RedirectResponse(url="/matrix")

@app.get("/matrix", response_class=HTMLResponse)
def get_matrix_view():
    """主頁：恒指成份股幾何形態矩陣面板"""
    rows_html = ""
    for rank, item in enumerate(HSI_CONSTITUENTS, 1):
        dates, candles = fetch_stock_data(item["yf_code"])
        pattern_name, _, _ = analyze_pattern(dates, candles)
        
        status_tag = f'<span style="color: #089981; font-weight: bold;">✅ {pattern_name}</span>' if pattern_name != "無顯著形態" else '<span style="color: #787b86;">⚪ 無顯著形態</span>'
        chart_url = f"/custom-chart?symbol={item['symbol']}"

        rows_html += f"""
        <tr>
            <td style="color: #787b86;">{rank}</td>
            <td style="font-weight: bold; color: #2962ff;">{item['symbol']}</td>
            <td style="font-weight: bold; color: #ffffff;">{item['name']}</td>
            <td>{status_tag}</td>
            <td>
                <a href="{chart_url}" class="btn-link">🎨 查看圖表與趨勢線</a>
            </td>
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
        <h2>恒生指數成份股 - 自動幾何形態監測矩陣</h2>
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
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </body>
    </html>
    """

@app.get("/custom-chart", response_class=HTMLResponse)
def get_custom_chart(symbol: str = "HKEX:9988"):
    """單隻股票詳情 K 線圖"""
    item = next((x for x in HSI_CONSTITUENTS if x["symbol"] == symbol), HSI_CONSTITUENTS[0])
    dates, candles = fetch_stock_data(item["yf_code"])
    pattern_name, mark_lines, mark_points = analyze_pattern(dates, candles)

    badge = f'<span style="background: #2962ff; padding: 6px 12px; border-radius: 4px;">🎯 偵測型態：{pattern_name}</span>' if pattern_name != "無顯著形態" else '<span style="background: #363a45; color: #9194a1; padding: 6px 12px; border-radius: 4px;">⚪ 無顯著幾何形態</span>'

    return f"""
    <!DOCTYPE html>
    <html lang="zh-HK">
    <head>
        <meta charset="UTF-8">
        <title>{symbol} - K線幾何圖表</title>
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
            <h2>{symbol} ({item['name']}) - K 線圖分析</h2>
            {badge}
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
                dataZoom: [{{ type: 'inside', start: 50, end: 100 }}, {{ show: true, type: 'slider', top: '90%' }}],
                series: [{{
                    name: '日 K 線',
                    type: 'candlestick',
                    data: {json.dumps(candles)},
                    itemStyle: {{ color: '#089981', color0: '#f23645', borderColor: '#089981', borderColor0: '#f23645' }},
                    markLine: {{ symbol: ['none', 'none'], data: {json.dumps(mark_lines)} }},
                    markPoint: {{ data: {json.dumps(mark_points)}, symbol: 'pin', symbolSize: 40 }}
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
