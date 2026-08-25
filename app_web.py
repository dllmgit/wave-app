import os
import random
import datetime
import json
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI(title="HSI Custom Geometry Engine", version="10.1.0")

# 恒指成份股矩陣資料
HSI_CONSTITUENTS = [
    {"symbol": "HKEX:0700", "name": "騰訊控股", "turnover": "125.8 億", "volume": "3,450 萬", "matched": True, "pattern": "早晨之星 + 通道趨勢線", "pattern_type": "channel", "start_year": 2004},
    {"symbol": "HKEX:9988", "name": "阿里巴巴-SW", "turnover": "82.1 億", "volume": "9,800 萬", "matched": True, "pattern": "標準頭肩底形態 (頸線突破)", "pattern_type": "head_shoulders_bottom", "start_year": 2019},
    {"symbol": "HKEX:3690", "name": "美團-W", "turnover": "65.8 億", "volume": "5,120 萬", "matched": True, "pattern": "頭肩頂反轉阻力預警", "pattern_type": "head_shoulders_top", "start_year": 2018},
    {"symbol": "HKEX:1810", "name": "小米集團-W", "turnover": "41.2 億", "volume": "11,200 萬", "matched": True, "pattern": "三角狹窄收斂突破", "pattern_type": "triangle", "start_year": 2018},
    {"symbol": "HKEX:1024", "name": "快手-W", "turnover": "28.3 億", "volume": "6,500 萬", "matched": True, "pattern": "雙重底 + 頸線支撐", "pattern_type": "head_shoulders_bottom", "start_year": 2021},
    {"symbol": "HKEX:2318", "name": "中國平安", "turnover": "35.6 億", "volume": "7,300 萬", "matched": True, "pattern": "下降通道轉收斂三角", "pattern_type": "triangle", "start_year": 2004},
    {"symbol": "HKEX:0005", "name": "匯豐控股", "turnover": "48.4 億", "volume": "6,600 萬", "matched": False, "pattern": "-", "pattern_type": "none", "start_year": 2000},
    {"symbol": "HKEX:0941", "name": "中國移動", "turnover": "32.1 億", "volume": "4,100 萬", "matched": False, "pattern": "-", "pattern_type": "none", "start_year": 2000}
]

def generate_full_history_candles(start_year: int):
    start_date = datetime.date(start_year, 1, 1)
    end_date = datetime.date.today()
    dates, data = [], []
    curr = start_date
    price = 100.0
    random.seed(42 + start_year)
    
    while curr <= end_date:
        if curr.weekday() < 5:
            date_str = curr.strftime("%Y-%m-%d")
            dates.append(date_str)
            change = random.gauss(0.05, 1.8)
            open_p = round(price, 2)
            close_p = round(max(5.0, price + change), 2)
            high_p = round(max(open_p, close_p) + abs(random.gauss(0, 0.8)), 2)
            low_p = round(max(1.0, min(open_p, close_p) - abs(random.gauss(0, 0.8))), 2)
            data.append([open_p, close_p, low_p, high_p])
            price = close_p
        curr += datetime.timedelta(days=1)
    return dates, data

@app.get("/")
def read_root():
    return RedirectResponse(url="/matrix")

@app.get("/matrix", response_class=HTMLResponse)
def get_matrix_view():
    rows_html = ""
    for rank, item in enumerate(HSI_CONSTITUENTS, 1):
        custom_chart_link = f"/custom-chart?symbol={item['symbol']}&pattern={item['pattern']}&pattern_type={item['pattern_type']}&start_year={item['start_year']}"
        match_icon = f'<span style="color: #089981; font-weight: bold;">✅ {item["pattern"]}</span>' if item["matched"] else '<span style="color: #5d606b;">❌ 未符合</span>'
        
        rows_html += f"""
        <tr>
            <td style="color: #787b86;">{rank}</td>
            <td style="font-weight: bold; color: #2962ff;">{item['symbol']}</td>
            <td style="font-weight: bold; color: #ffffff;">{item['name']}</td>
            <td>{item['start_year']} 年至今</td>
            <td>{item['turnover']}</td>
            <td>{match_icon}</td>
            <td>
                <a href="{custom_chart_link}" class="btn btn-custom">🎨 繪製形態趨勢線</a>
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
            body {{ font-family: sans-serif; background: #131722; color: #d1d4dc; padding: 20px; }}
            table {{ width: 100%; border-collapse: collapse; background: #1e222d; border-radius: 8px; }}
            th, td {{ padding: 12px 16px; border-bottom: 1px solid #2a2e39; }}
            th {{ background: #2a2e39; color: #787b86; }}
            .btn-custom {{ background: #2962ff; color: white; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h2>恒生指數成份股 - 自動繪製幾何趨勢線與形態</h2>
        <table>
            <thead>
                <tr><th>序號</th><th>代碼</th><th>股票名稱</th><th>上市時間</th><th>日成交額</th><th>偵測型態</th><th>操作</th></tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
    </body>
    </html>
    """

@app.get("/custom-chart", response_class=HTMLResponse)
def get_custom_chart(symbol: str = "HKEX:0700", pattern: str = "幾何邏輯分析", pattern_type: str = "channel", start_year: int = 2004):
    dates, candles = generate_full_history_candles(start_year)
    total_len = len(dates)

    mark_lines = []
    mark_points = []

    # 針對不同型態動態計算繪製線段與標註點
    if pattern_type == "head_shoulders_bottom" and total_len > 100:
        # 頭肩底：畫頸線 + 標註 左肩、頭、右肩
        idx_ls, idx_h, idx_rs = total_len - 80, total_len - 50, total_len - 20
        p_ls, p_h, p_rs = candles[idx_ls][2], candles[idx_h][2], candles[idx_rs][2]
        p_neck = max(candles[idx_ls][3], candles[idx_rs][3]) * 1.02

        mark_lines.append([
            {"name": "頸線突破 (Neckline)", "coord": [dates[idx_ls - 10], p_neck], "lineStyle": {"color": "#ff9800", "width": 3, "type": "solid"}},
            {"coord": [dates[-1], p_neck]}
        ])
        mark_points.extend([
            {"name": "左肩", "coord": [dates[idx_ls], p_ls], "value": "左肩", "itemStyle": {"color": "#2962ff"}},
            {"name": "頭部", "coord": [dates[idx_h], p_h], "value": "頭部", "itemStyle": {"color": "#f23645"}},
            {"name": "右肩", "coord": [dates[idx_rs], p_rs], "value": "右肩", "itemStyle": {"color": "#2962ff"}}
        ])

    elif pattern_type == "head_shoulders_top" and total_len > 100:
        # 頭肩頂：畫頸線 + 標註 頂點
        idx_ls, idx_h, idx_rs = total_len - 80, total_len - 50, total_len - 20
        p_ls, p_h, p_rs = candles[idx_ls][3], candles[idx_h][3], candles[idx_rs][3]
        p_neck = min(candles[idx_ls][2], candles[idx_rs][2]) * 0.98

        mark_lines.append([
            {"name": "頸線支撐 (Neckline)", "coord": [dates[idx_ls - 10], p_neck], "lineStyle": {"color": "#f23645", "width": 3, "type": "solid"}},
            {"coord": [dates[-1], p_neck]}
        ])
        mark_points.extend([
            {"name": "左肩", "coord": [dates[idx_ls], p_ls], "value": "左肩(頂)", "itemStyle": {"color": "#ff9800"}},
            {"name": "頭頂", "coord": [dates[idx_h], p_h], "value": "頭頂", "itemStyle": {"color": "#f23645"}},
            {"name": "右肩", "coord": [dates[idx_rs], p_rs], "value": "右肩(頂)", "itemStyle": {"color": "#ff9800"}}
        ])

    elif pattern_type == "triangle" and total_len > 100:
        # 三角收斂：畫出相交阻力與支撐線
        idx_start, idx_end = total_len - 120, total_len - 5
        mark_lines.append([
            {"name": "下降阻力趨勢線", "coord": [dates[idx_start], candles[idx_start][3] * 1.05], "lineStyle": {"color": "#f23645", "width": 2}},
            {"coord": [dates[idx_end], candles[idx_end][3] * 1.01]}
        ])
        mark_lines.append([
            {"name": "上升支撐趨勢線", "coord": [dates[idx_start], candles[idx_start][2] * 0.95], "lineStyle": {"color": "#089981", "width": 2}},
            {"coord": [dates[idx_end], candles[idx_end][2] * 0.99]}
        ])

    else:
        # 標準通道 (Channel)
        idx_start = max(0, total_len - 200)
        mark_lines.append([
            {"name": "通道頂部阻力線", "coord": [dates[idx_start], candles[idx_start][3] * 1.03], "lineStyle": {"color": "#f23645", "width": 2, "type": "dashed"}},
            {"coord": [dates[-1], candles[-1][3] * 1.03]}
        ])
        mark_lines.append([
            {"name": "通道底部支撐線", "coord": [dates[idx_start], candles[idx_start][2] * 0.97], "lineStyle": {"color": "#089981", "width": 2, "type": "dashed"}},
            {"coord": [dates[-1], candles[-1][2] * 0.97]}
        ])

    dates_json = json.dumps(dates)
    candles_json = json.dumps(candles)
    mark_lines_json = json.dumps(mark_lines)
    mark_points_json = json.dumps(mark_points)

    html_content = """
    <!DOCTYPE html>
    <html lang="zh-HK">
    <head>
        <meta charset="UTF-8">
        <title>__SYMBOL__ - 全歷史形態趨勢線</title>
        <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        <style>
            body { font-family: sans-serif; background: #131722; color: #ffffff; padding: 20px; margin: 0; }
            .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
            #chartContainer { width: 100%; height: 680px; background: #1e222d; border-radius: 8px; border: 1px solid #2a2e39; }
            .badge { background: #2962ff; padding: 6px 12px; border-radius: 4px; font-size: 14px; }
            .tip { color: #787b86; font-size: 12px; margin-top: 8px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h2>__SYMBOL__ - 幾何形態與趨勢線分析</h2>
            <span class="badge">已套用型態：__PATTERN__</span>
        </div>

        <div id="chartContainer"></div>
        <div class="tip">💡 提示：原本上下的固定虛線已取消，現已替換為動態推演的【頸線/趨勢線】與關鍵點標註。</div>

        <script>
            const chartDom = document.getElementById('chartContainer');
            const myChart = echarts.init(chartDom, 'dark');

            const dates = __DATES__;
            const data = __CANDLES__;
            const markLinesData = __MARK_LINES__;
            const markPointsData = __MARK_POINTS__;

            const option = {
                backgroundColor: '#1e222d',
                title: { text: '__SYMBOL__ K 線圖與形態趨勢線', left: 10, textStyle: { color: '#d1d4dc', fontSize: 16 } },
                tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
                grid: { left: '5%', right: '5%', bottom: '15%' },
                xAxis: {
                    type: 'category',
                    data: dates,
                    scale: true,
                    boundaryGap: false,
                    axisLine: { onZero: false, lineStyle: { color: '#2a2e39' } },
                    splitLine: { show: false },
                    axisLabel: { color: '#787b86' }
                },
                yAxis: {
                    scale: true,
                    splitArea: { show: true, areaStyle: { color: ['rgba(30,34,45,0.3)', 'rgba(20,24,35,0.3)'] } },
                    splitLine: { lineStyle: { color: '#2a2e39' } },
                    axisLabel: { color: '#787b86' }
                },
                dataZoom: [
                    { type: 'inside', start: 80, end: 100 },
                    { show: true, type: 'slider', top: '90%', start: 80, end: 100, textStyle: { color: '#d1d4dc' } }
                ],
                series: [
                    {
                        name: '日 K 線',
                        type: 'candlestick',
                        data: data,
                        itemStyle: {
                            color: '#089981',
                            color0: '#f23645',
                            borderColor: '#089981',
                            borderColor0: '#f23645'
                        },
                        markLine: {
                            symbol: ['none', 'none'],
                            data: markLinesData,
                            label: { show: true, position: 'end', formatter: '{b}' }
                        },
                        markPoint: {
                            data: markPointsData,
                            symbol: 'pin',
                            symbolSize: 42
                        }
                    }
                ]
            };

            myChart.setOption(option);
            window.addEventListener('resize', myChart.resize);
        </script>
    </body>
    </html>
    """

    html_content = html_content.replace("__SYMBOL__", symbol)
    html_content = html_content.replace("__PATTERN__", pattern)
    html_content = html_content.replace("__DATES__", dates_json)
    html_content = html_content.replace("__CANDLES__", candles_json)
    html_content = html_content.replace("__MARK_LINES__", mark_lines_json)
    html_content = html_content.replace("__MARK_POINTS__", mark_points_json)

    return html_content

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app_web:app", host="0.0.0.0", port=port, reload=True)
