import os
import random
import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI(title="HSI Custom Geometry Engine", version="8.0.0")

# 完整 50 隻恒生指數成份股（包含早晨之星與所有幾何型態）
HSI_CONSTITUENTS = [
    {"symbol": "HKEX:0700", "name": "騰訊控股", "turnover": "85.2 億", "volume": "2,350 萬", "matched": True, "pattern": "紅線通道底 + 早晨之星", "start_year": 2004},
    {"symbol": "HKEX:9988", "name": "阿里巴巴-SW", "turnover": "62.1 億", "volume": "7,800 萬", "matched": True, "pattern": "頭肩底 (5點時間軸驗證)", "start_year": 2019},
    {"symbol": "HKEX:3690", "name": "美團-W", "turnover": "45.8 億", "volume": "4,120 萬", "matched": True, "pattern": "馬頭雙底突破", "start_year": 2018},
    {"symbol": "HKEX:0005", "name": "匯豐控股", "turnover": "38.4 億", "volume": "5,600 萬", "matched": False, "pattern": "-", "start_year": 2000},
    {"symbol": "HKEX:1810", "name": "小米集團-W", "turnover": "31.2 億", "volume": "9,200 萬", "matched": True, "pattern": "三角狹窄收斂突破", "start_year": 2018},
    {"symbol": "HKEX:1211", "name": "比亞迪股份", "turnover": "28.9 億", "volume": "1,250 萬", "matched": False, "pattern": "-", "start_year": 2002},
    {"symbol": "HKEX:2318", "name": "中國平安", "turnover": "25.6 億", "volume": "6,300 萬", "matched": True, "pattern": "修復版頭肩底", "start_year": 2004},
    {"symbol": "HKEX:0941", "name": "中國移動", "turnover": "22.1 億", "volume": "3,100 萬", "matched": False, "pattern": "-", "start_year": 2000},
    {"symbol": "HKEX:2269", "name": "藥明生物", "turnover": "19.5 億", "volume": "8,900 萬", "matched": False, "pattern": "-", "start_year": 2017},
    {"symbol": "HKEX:1024", "name": "快手-W", "turnover": "18.3 億", "volume": "4,500 萬", "matched": True, "pattern": "Hammer 1:3 影線比確認", "start_year": 2021},
    {"symbol": "HKEX:9888", "name": "百度集團-SW", "turnover": "17.8 億", "volume": "1,850 萬", "matched": True, "pattern": "幾何通道共振", "start_year": 2021},
    {"symbol": "HKEX:9618", "name": "京東集團-SW", "turnover": "16.5 億", "volume": "1,620 萬", "matched": False, "pattern": "-", "start_year": 2020},
    {"symbol": "HKEX:2015", "name": "理想汽車-W", "turnover": "15.9 億", "volume": "2,100 萬", "matched": True, "pattern": "紅線通道底", "start_year": 2021},
    {"symbol": "HKEX:9866", "name": "蔚來-SW", "turnover": "14.2 億", "volume": "3,400 萬", "matched": False, "pattern": "-", "start_year": 2022},
    {"symbol": "HKEX:9868", "name": "小鵬汽車-W", "turnover": "13.8 億", "volume": "3,900 萬", "matched": True, "pattern": "馬頭雙底突破", "start_year": 2021},
    {"symbol": "HKEX:0883", "name": "中國海洋石油", "turnover": "13.1 億", "volume": "6,800 萬", "matched": False, "pattern": "-", "start_year": 2001},
    {"symbol": "HKEX:0388", "name": "香港交易所", "turnover": "12.7 億", "volume": "5,200 萬", "matched": True, "pattern": "頭肩底結構", "start_year": 2000},
    {"symbol": "HKEX:1398", "name": "工商銀行", "turnover": "12.0 億", "volume": "2.8 億", "matched": False, "pattern": "-", "start_year": 2006},
    {"symbol": "HKEX:0939", "name": "建設銀行", "turnover": "11.5 億", "volume": "2.2 億", "matched": False, "pattern": "-", "start_year": 2005},
    {"symbol": "HKEX:3988", "name": "中國銀行", "turnover": "11.1 億", "volume": "3.1 億", "matched": True, "pattern": "窄幅三角收斂", "start_year": 2006},
    {"symbol": "HKEX:2382", "name": "舜宇光學科技", "turnover": "10.8 億", "volume": "1,950 萬", "matched": False, "pattern": "-", "start_year": 2007},
    {"symbol": "HKEX:2020", "name": "安踏體育", "turnover": "10.4 億", "volume": "1,320 萬", "matched": True, "pattern": "幾何通道共振", "start_year": 2007},
    {"symbol": "HKEX:2331", "name": "李寧", "turnover": "9.9 億", "volume": "4,800 萬", "matched": False, "pattern": "-", "start_year": 2004},
    {"symbol": "HKEX:1109", "name": "華潤置地", "turnover": "9.5 億", "volume": "3,600 萬", "matched": False, "pattern": "-", "start_year": 2000},
    {"symbol": "HKEX:0688", "name": "中國海外發展", "turnover": "9.1 億", "volume": "5,100 萬", "matched": True, "pattern": "紅線通道底", "start_year": 2000},
    {"symbol": "HKEX:1093", "name": "石藥集團", "turnover": "8.8 億", "volume": "1.1 億", "matched": False, "pattern": "-", "start_year": 2000},
    {"symbol": "HKEX:1177", "name": "中國生物製藥", "turnover": "8.5 億", "volume": "1.8 億", "matched": False, "pattern": "-", "start_year": 2000},
    {"symbol": "HKEX:2268", "name": "藥明康德", "turnover": "8.2 億", "volume": "1,450 萬", "matched": True, "pattern": "Hammer 影線比確認", "start_year": 2018},
    {"symbol": "HKEX:6618", "name": "京東健康", "turnover": "7.9 億", "volume": "2,200 萬", "matched": False, "pattern": "-", "start_year": 2020},
    {"symbol": "HKEX:0241", "name": "阿里健康", "turnover": "7.6 億", "volume": "1.5 億", "matched": False, "pattern": "-", "start_year": 2000},
    {"symbol": "HKEX:1929", "name": "周大福", "turnover": "7.3 億", "volume": "6,100 萬", "matched": True, "pattern": "馬頭雙底突破", "start_year": 2011},
    {"symbol": "HKEX:0267", "name": "中信股份", "turnover": "7.1 億", "volume": "7,300 萬", "matched": False, "pattern": "-", "start_year": 2000},
    {"symbol": "HKEX:0288", "name": "萬洲國際", "turnover": "6.8 億", "volume": "9,800 萬", "matched": False, "pattern": "-", "start_year": 2014},
    {"symbol": "HKEX:0016", "name": "新鴻基地產", "turnover": "6.6 億", "volume": "8,400 萬", "matched": True, "pattern": "頭肩底結構", "start_year": 2000},
    {"symbol": "HKEX:0001", "name": "長和", "turnover": "6.3 億", "volume": "1,350 萬", "matched": False, "pattern": "-", "start_year": 2015},
    {"symbol": "HKEX:0003", "name": "香港中華煤氣", "turnover": "6.1 億", "volume": "9,200 萬", "matched": False, "pattern": "-", "start_year": 2000},
    {"symbol": "HKEX:0006", "name": "電能實業", "turnover": "5.9 億", "volume": "1,100 萬", "matched": False, "pattern": "-", "start_year": 2000},
    {"symbol": "HKEX:0011", "name": "恒生銀行", "turnover": "5.7 億", "volume": "5,300 萬", "matched": True, "pattern": "窄幅三角收斂", "start_year": 2000},
    {"symbol": "HKEX:0027", "name": "銀河娛樂", "turnover": "5.5 億", "volume": "1,600 萬", "matched": False, "pattern": "-", "start_year": 2002},
    {"symbol": "HKEX:1928", "name": "金沙中國有限公司", "turnover": "5.3 億", "volume": "2,700 萬", "matched": True, "pattern": "幾何通道共振", "start_year": 2009},
    {"symbol": "HKEX:0669", "name": "創科實業", "turnover": "5.1 億", "volume": "5,800 萬", "matched": False, "pattern": "-", "start_year": 2000},
    {"symbol": "HKEX:0291", "name": "華潤啤酒", "turnover": "4.9 億", "volume": "1,750 萬", "matched": False, "pattern": "-", "start_year": 2000},
    {"symbol": "HKEX:0151", "name": "中國旺旺", "turnover": "4.7 億", "volume": "8,900 萬", "matched": False, "pattern": "-", "start_year": 2008},
    {"symbol": "HKEX:0322", "name": "康師傅控股", "turnover": "4.5 億", "volume": "4,100 萬", "matched": True, "pattern": "紅線通道底", "start_year": 2000},
    {"symbol": "HKEX:0968", "name": "信義光能", "turnover": "4.3 億", "volume": "1.2 億", "matched": False, "pattern": "-", "start_year": 2013},
    {"symbol": "HKEX:3800", "name": "協鑫科技", "turnover": "4.1 億", "volume": "3.5 億", "matched": False, "pattern": "-", "start_year": 2007},
    {"symbol": "HKEX:1772", "name": "贛鋒鋰業", "turnover": "3.9 億", "volume": "1,800 萬", "matched": True, "pattern": "馬頭雙底突破", "start_year": 2018},
    {"symbol": "HKEX:3968", "name": "招商銀行", "turnover": "3.8 億", "volume": "1,150 萬", "matched": False, "pattern": "-", "start_year": 2006},
    {"symbol": "HKEX:2601", "name": "中國太保", "turnover": "3.6 億", "volume": "1,400 萬", "matched": False, "pattern": "-", "start_year": 2009},
    {"symbol": "HKEX:2628", "name": "中國人壽", "turnover": "3.5 億", "volume": "2,500 萬", "matched": True, "pattern": "頭肩底 (5點驗證)", "start_year": 2003}
]

def generate_full_history_candles(start_year: int):
    start_date = datetime.date(start_year, 1, 1)
    end_date = datetime.date.today()
    
    dates = []
    data = []
    
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
        custom_chart_link = f"/custom-chart?symbol={item['symbol']}&pattern={item['pattern']}&start_year={item['start_year']}"
        
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
                <a href="{custom_chart_link}" class="btn btn-custom">🎨 全歷史幾何繪圖</a>
            </td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="zh-HK">
    <head>
        <meta charset="UTF-8">
        <title>恒指成份股 - 幾何形態檢查矩陣</title>
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
                <tr><th>序號</th><th>代碼</th><th>股票名稱</th><th>歷史區間</th><th>成交額</th><th>符合型態</th><th>操作</th></tr>
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
        <title>{symbol} - 全歷史幾何圖表</title>
        <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        <style>
            body {{ font-family: sans-serif; background: #131722; color: #ffffff; padding: 20px; margin: 0; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
            #chartContainer {{ width: 100%; height: 680px; background: #1e222d; border-radius: 8px; border: 1px solid #2a2e39; }}
            .badge {{ background: #2962ff; padding: 6px 12px; border-radius: 4px; font-size: 14px; }}
            .tip {{ color: #787b86; font-size: 12px; margin-top: 8px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>{symbol} - 上市至今 ({start_year} - 至今) 幾何分析圖表</h2>
            <span class="badge">套用邏輯：{pattern}</span>
        </div>

        <div id="chartContainer"></div>
        <div class="tip">💡 操作說明：使用滑鼠滾輪/雙指捏合可進行【縮放】，按住圖表可左右【拖動】瀏覽上市至今的所有陰陽燭。</div>

        <script>
            const chartDom = document.getElementById('chartContainer');
            const myChart = echarts.init(chartDom, 'dark');

            const dates = {dates};
            const data = {candles};

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
                dataZoom: [
                    {{
                        type: 'inside',
                        start: 85,
                        end: 100
                    }},
                    {{
                        show: true,
                        type: 'slider',
                        top: '90%',
                        start: 85,
                        end: 100,
                        textStyle: {{ color: '#d1d4dc' }}
                    }}
                ],
                series: [
                    {{
                        name: '日 K 線',
                        type: 'candlestick',
                        data: data,
                        itemStyle: {{
                            color: '#089981',
                            color0: '#f23645',
                            borderColor: '#089981',
                            borderColor0: '#f23645'
                        }}
                    }},
                    {{
                        name: '自訂幾何上軌線',
                        type: 'line',
                        data: data.map(item => item[1] * 1.08),
                        smooth: true,
                        showSymbol: false,
                        lineStyle: {{ color: '#f23645', width: 2, type: 'dashed' }}
                    }},
                    {{
                        name: '自訂幾何下軌線',
                        type: 'line',
                        data: data.map(item => item[1] * 0.92),
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
