import os
import datetime
import numpy as np
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI(title="HSI Custom Geometry Engine", version="7.0.0")

HSI_CONSTITUENTS = [
    {"symbol": "HKEX:0700", "name": "騰訊控股", "turnover": "85.2 億", "volume": "2,350 萬", "matched": True, "pattern": "紅線通道底 + 早晨之星", "start_year": 2004},
    {"symbol": "HKEX:9988", "name": "阿里巴巴-SW", "turnover": "62.1 億", "volume": "7,800 萬", "matched": True, "pattern": "頭肩底 (5點時間軸驗證)", "start_year": 2019},
    {"symbol": "HKEX:3690", "name": "美團-W", "turnover": "45.8 億", "volume": "4,120 萬", "matched": True, "pattern": "馬頭雙底突破", "start_year": 2018},
    {"symbol": "HKEX:1810", "name": "小米集團-W", "turnover": "31.2 億", "volume": "9,200 萬", "matched": True, "pattern": "三角狹窄收斂突破", "start_year": 2018},
    {"symbol": "HKEX:2318", "name": "中國平安", "turnover": "25.6 億", "volume": "6,300 萬", "matched": True, "pattern": "修復版頭肩底", "start_year": 2004},
    {"symbol": "HKEX:1024", "name": "快手-W", "turnover": "18.3 億", "volume": "4,500 萬", "matched": True, "pattern": "Hammer 1:3 影線比確認", "start_year": 2021}
]

def generate_full_history_candles(start_year: int):
    """模擬產生自上市年份至今的所有每日陰陽燭數據"""
    start_date = datetime.date(start_year, 1, 1)
    end_date = datetime.date.today()
    
    dates = []
    data = [] # [Open, Close, Low, High]
    
    curr = start_date
    price = 100.0
    
    # 使用隨機走勢模擬歷史 K 線
    np.random.seed(42 + start_year)
    
    while curr <= end_date:
        if curr.weekday() < 5: # 僅交易日
            date_str = curr.strftime("%Y-%m-%d")
            dates.append(date_str)
            
            change = np.random.normal(0.05, 1.8)
            open_p = round(price, 2)
            close_p = round(max(5.0, price + change), 2)
            high_p = round(max(open_p, close_p) + abs(np.random.normal(0, 0.8)), 2)
            low_p = round(max(1.0, min(open_p, close_p) - abs(np.random.normal(0, 0.8))), 2)
            
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
        custom_chart_link = f"/custom-chart?symbol={item['symbol']}&pattern={item['pattern']}&start_year={item['start_year']}"
        rows_html += f"""
        <tr>
            <td style="color: #787b86;">{rank}</td>
            <td style="font-weight: bold; color: #2962ff;">{item['symbol']}</td>
            <td style="font-weight: bold; color: #ffffff;">{item['name']}</td>
            <td>上市年份 ({item['start_year']})</td>
            <td>{item['turnover']}</td>
            <td><span style="color: #089981; font-weight: bold;">✅ {item['pattern']}</span></td>
            <td>
                <a href="{custom_chart_link}" class="btn btn-custom">🎨 全歷史幾何圖表</a>
            </td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="zh-HK">
    <head>
        <meta charset="UTF-8">
        <title>全歷史幾何圖表矩陣</title>
        <style>
            body {{ font-family: sans-serif; background: #131722; color: #d1d4dc; padding: 20px; }}
            table {{ width: 100%; border-collapse: collapse; background: #1e222d; border-radius: 8px; }}
            th, td {{ padding: 12px 16px; border-bottom: 1px solid #2a2e39; }}
            th {{ background: #2a2e39; color: #787b86; }}
            .btn-custom {{ background: #9c27b0; color: white; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h2>恒生指數成份股 - 上市至今自訂幾何圖表</h2>
        <table>
            <thead>
                <tr><th>序號</th><th>代碼</th><th>股票名稱</th><th>上市歷史</th><th>成交額</th><th>符合型態</th><th>操作</th></tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
    </body>
    </html>
    """

@app.get("/custom-chart", response_class=HTMLResponse)
def get_custom_chart(symbol: str = "HKEX:0700", pattern: str = "幾何邏輯分析", start_year: int = 2004):
    dates, candles = generate_full_history_candles(start_year)

    return f"""
    <!DOCTYPE html>
    <html lang="zh-HK">
    <head>
        <meta charset="UTF-8">
        <title>{symbol} - 全歷史陰陽燭幾何繪圖</title>
        <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        <style>
            body {{ font-family: sans-serif; background: #131722; color: #ffffff; padding: 20px; margin: 0; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
            #chartContainer {{ width: 100%; height: 650px; background: #1e222d; border-radius: 8px; border: 1px solid #2a2e39; }}
            .badge {{ background: #2962ff; padding: 6px 12px; border-radius: 4px; font-size: 14px; }}
            .tip {{ color: #787b86; font-size: 12px; margin-top: 8px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>{symbol} - 上市至今 ({start_year} 年至今) 陰陽蠋繪圖</h2>
            <span class="badge">套用幾何邏輯：{pattern}</span>
        </div>

        <div id="chartContainer"></div>
        <div class="tip">💡 操作提示：使用滾輪或下方滑塊可隨意【縮放】與【拖拽】時間軸，瀏覽上市至今的所有陰陽燭。</div>

        <script>
            const chartDom = document.getElementById('chartContainer');
            const myChart = echarts.init(chartDom, 'dark');

            const dates = {dates};
            const data = {candles}; // [Open, Close, Low, High]

            const option = {{
                backgroundColor: '#1e222d',
                title: {{ text: '{symbol} 全歷史 K 線與自訂幾何通道', left: 10, textStyle: {{ color: '#d1d4dc', fontSize: 16 }} }},
                tooltip: {{
                    trigger: 'axis',
                    axisPointer: {{ type: 'cross' }}
                }},
                grid: {{ left: '5%', right: '5%', bottom: '15%' }},
                xAxis: {{
                    type: 'category',
                    data: dates,
                    scale: true,
                    boundaryGap: false,
                    axisLine: {{ onZero: false, lineStyle: {{ color: '#2a2e39' }} }},
                    splitLine: {{ show: false }},
                    axisLabel: {{ color: '#787b86' }}
                }},
                yAxis: {{
                    scale: true,
                    splitArea: {{ show: true, areaStyle: {{ color: ['rgba(30,34,45,0.3)', 'rgba(20,24,35,0.3)'] }} }},
                    splitLine: {{ lineStyle: {{ color: '#2a2e39' }} }},
                    axisLabel: {{ color: '#787b86' }}
                }},
                // 1. 支援滾輪與拖曳縮放（DataZoom）
                dataZoom: [
                    {{
                        type: 'inside', // 滾輪 / 雙指縮放
                        start: 80,      // 預設顯示最後 20% 的數據
                        end: 100
                    }},
                    {{
                        show: true,     // 下方時間軸滑塊
                        type: 'slider',
                        top: '90%',
                        start: 80,
                        end: 100,
                        textStyle: {{ color: '#d1d4dc' }}
                    }}
                ],
                series: [
                    // 2. 陰陽燭渲染
                    {{
                        name: '日 K 線',
                        type: 'candlestick',
                        data: data,
                        itemStyle: {{
                            color: '#089981',        // 陽線顏色
                            color0: '#f23645',       // 陰線顏色
                            borderColor: '#089981',
                            borderColor0: '#f23645'
                        }}
                    }},
                    // 3. 疊加自訂幾何線條（例如：自動趨勢通道/支撐線）
                    {{
                        name: '自訂幾何趨勢線',
                        type: 'line',
                        data: data.map((item, idx) => item[1] * 1.08), // 範例：動態幾何上軌
                        smooth: true,
                        showSymbol: false,
                        lineStyle: {{ color: '#f23645', width: 2, type: 'dashed' }}
                    }},
                    {{
                        name: '自訂幾何支撐線',
                        type: 'line',
                        data: data.map((item, idx) => item[1] * 0.92), // 範例：動態幾何下軌
                        smooth: true,
                        showSymbol: false,
                        lineStyle: {{ color: '#089981', width: 2, type: 'dashed' }}
                    }}
                ]
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
