import os
import json
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI(title="Quant Top 50 Matrix Engine", version="4.0.0")

# 模擬港股成交額/成交量 Top 50 數據與形態掃描結果
TOP_50_STOCKS = [
    {"symbol": "HKEX:0700", "name": "騰訊控股", "turnover": "85.2 億", "volume": "2,350 萬", "matched": True, "pattern": "紅線通道底 + 早晨之星"},
    {"symbol": "HKEX:9988", "name": "阿里巴巴-SW", "turnover": "62.1 億", "volume": "7,800 萬", "matched": True, "pattern": "頭肩底 (5點時間軸驗證)"},
    {"symbol": "HKEX:3690", "name": "美團-W", "turnover": "45.8 億", "volume": "4,120 萬", "matched": True, "pattern": "馬頭雙底突破"},
    {"symbol": "HKEX:0005", "name": "匯豐控股", "turnover": "38.4 億", "volume": "5,600 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:1810", "name": "小米集團-W", "turnover": "31.2 億", "volume": "9,200 萬", "matched": True, "pattern": "三角狹窄收斂突破"},
    {"symbol": "HKEX:1211", "name": "比亞迪股份", "turnover": "28.9 億", "volume": "1,250 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:2318", "name": "中國平安", "turnover": "25.6 億", "volume": "6,300 萬", "matched": True, "pattern": "修復版頭肩底 (左肩平衡)"},
    {"symbol": "HKEX:0941", "name": "中國移動", "turnover": "22.1 億", "volume": "3,100 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:2269", "name": "藥明生物", "turnover": "19.5 億", "volume": "8,900 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:1024", "name": "快手-W", "turnover": "18.3 億", "volume": "4,500 萬", "matched": True, "pattern": "Hammer 1:3 影線比確認"},
]

# 補充生成至 50 隻股票樣板
for i in range(11, 51):
    TOP_50_STOCKS.append({
        "symbol": f"HKEX:{9000+i:04d}",
        "name": f"熱門標的-{i}",
        "turnover": f"{18.0 - i*0.3:.1f} 億",
        "volume": f"{4000 - i*60:,} 萬",
        "matched": (i % 3 == 0),
        "pattern": "幾何通道共振" if (i % 3 == 0) else "-"
    })

def generate_tv_url(symbol: str, interval: str = "D") -> str:
    formatted_symbol = symbol.replace(":", "%3A")
    return f"https://www.tradingview.com/chart/?symbol={formatted_symbol}&interval={interval}"

@app.get("/")
def read_root():
    return RedirectResponse(url="/matrix")

@app.get("/matrix", response_class=HTMLResponse)
def get_matrix_view():
    rows_html = ""
    for rank, item in enumerate(TOP_50_STOCKS, 1):
        tv_link = generate_tv_url(item["symbol"])
        custom_chart_link = f"/custom-chart?symbol={item['symbol']}"
        
        match_icon = f'<span style="color: #089981; font-weight: bold; font-size: 16px;">✅ {item["pattern"]}</span>' if item["matched"] else '<span style="color: #5d606b;">❌ 未符合</span>'
        
        rows_html += f"""
        <tr>
            <td style="color: #787b86;">{rank}</td>
            <td style="font-weight: bold; color: #2962ff;">{item['symbol']}</td>
            <td style="font-weight: bold; color: #ffffff;">{item['name']}</td>
            <td>{item['turnover']}</td>
            <td>{item['volume']}</td>
            <td>{match_icon}</td>
            <td>
                <a href="{custom_chart_link}" target="_blank" class="btn btn-custom">🎨 自訂幾何圖表</a>
            </td>
            <td>
                <a href="{tv_link}" target="_blank" class="btn btn-tv">📈 TradingView ↗</a>
            </td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-HK">
    <head>
        <meta charset="UTF-8">
        <title>Top 50 成交股 - 幾何形態檢查矩陣</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, Arial, sans-serif; background: #131722; color: #d1d4dc; padding: 20px; }}
            .header-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
            h2 {{ color: #ffffff; margin: 0; }}
            table {{ width: 100%; border-collapse: collapse; background: #1e222d; border-radius: 8px; overflow: hidden; }}
            th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid #2a2e39; font-size: 14px; }}
            th {{ background: #2a2e39; color: #787b86; uppercase; font-size: 12px; }}
            tr:hover {{ background: #262b3e; }}
            .btn {{ padding: 6px 12px; border-radius: 4px; text-decoration: none; font-size: 12px; font-weight: bold; display: inline-block; }}
            .btn-custom {{ background: #9c27b0; color: white; }}
            .btn-custom:hover {{ background: #ab47bc; }}
            .btn-tv {{ background: #2962ff; color: white; }}
            .btn-tv:hover {{ background: #1e53e5; }}
        </style>
    </head>
    <body>
        <div class="header-bar">
            <h2>前 50 隻最大成交額/量股票 - 幾何形態即時監控</h2>
        </div>
        <table>
            <thead>
                <tr>
                    <th>排名</th>
                    <th>代碼</th>
                    <th>股票名稱</th>
                    <th>成交額</th>
                    <th>成交量</th>
                    <th>符合型態要求</th>
                    <th>自訂繪圖（根據你的邏輯）</th>
                    <th>TradingView 官方跳轉</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </body>
    </html>
    """
    return html_content

@app.get("/custom-chart", response_class=HTMLResponse)
def get_custom_chart(symbol: str = "HKEX:9988"):
    tv_url = generate_tv_url(symbol)
    
    # 根據你的邏輯繪製畫線的 K 線數據與通道座標
    candle_data = [
        {"time": "2026-08-01", "open": 100, "high": 105, "low": 98, "close": 102},
        {"time": "2026-08-02", "open": 102, "high": 108, "low": 101, "close": 106},
        {"time": "2026-08-03", "open": 106, "high": 112, "low": 105, "close": 110},
        {"time": "2026-08-04", "open": 110, "high": 115, "low": 108, "close": 114},
        {"time": "2026-08-05", "open": 114, "high": 120, "low": 113, "close": 118},
    ]
    
    red_channel_bot = [{"time": "2026-08-01", "value": 98}, {"time": "2026-08-05", "value": 113}]
    red_channel_top = [{"time": "2026-08-01", "value": 105}, {"time": "2026-08-05", "value": 120}]

    html = f"""
    <!DOCTYPE html>
    <html lang="zh-HK">
    <head>
        <meta charset="UTF-8">
        <title>自訂邏輯圖表 - {symbol}</title>
        <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
        <style>
            body {{ font-family: Arial, sans-serif; background: #131722; color: #d1d4dc; padding: 16px; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }}
            #chart {{ width: 100%; height: 650px; border-radius: 8px; border: 1px solid #2a2e39; }}
            .btn-tv {{ background: #2962ff; color: white; padding: 8px 16px; border-radius: 4px; text-decoration: none; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>{symbol} - 依據自訂幾何邏輯自動繪圖</h2>
            <a href="{tv_url}" target="_blank" class="btn-tv">切換至 TradingView 原生圖表 ↗</a>
        </div>
        <div id="chart"></div>
        <script>
            const chart = LightweightCharts.createChart(document.getElementById('chart'), {{
                layout: {{ backgroundColor: '#131722', textColor: '#d1d4dc' }},
                grid: {{ vertLines: {{ color: '#2a2e39' }}, horzLines: {{ color: '#2a2e39' }} }}
            }});
            const candleSeries = chart.addCandlestickSeries();
            candleSeries.setData({json.dumps(candle_data)});
            
            const botSeries = chart.addLineSeries({{ color: '#ff0000', lineWidth: 2 }});
            botSeries.setData({json.dumps(red_channel_bot)});
            
            const topSeries = chart.addLineSeries({{ color: '#ff0000', lineWidth: 2 }});
            topSeries.setData({json.dumps(red_channel_top)});

            candleSeries.setMarkers([
                {{ time: '2026-08-01', position: 'belowBar', color: '#089981', shape: 'arrowUp', text: '通道底觸發' }},
                {{ time: '2026-08-05', position: 'aboveBar', color: '#e91e63', shape: 'arrowDown', text: '通道頂阻力' }}
            ]);
        </script>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app_web:app", host="0.0.0.0", port=port, reload=True)
