import os
import json
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI(title="Quant Matrix Engine", version="3.0.0")

# 模擬的形態掃描結果數據矩陣
PATTERNS_MATRIX = [
    {
        "symbol": "HKEX:9988",
        "name": "阿里巴巴",
        "timeframe": "1D",
        "pattern": "頭肩底 (綠色正宗結構)",
        "type": "CHART_PATTERN",
        "status": "已驗證 (5點時間軸通過)",
        "score": "95%"
    },
    {
        "symbol": "HKEX:0700",
        "name": "騰訊控股",
        "timeframe": "1D",
        "pattern": "早晨之星 + 紅線通道底",
        "type": "CANDLESTICK",
        "status": "觸發買入點",
        "score": "88%"
    },
    {
        "symbol": "HKEX:3690",
        "name": "美團",
        "timeframe": "4H",
        "pattern": "馬頭 (雙底)",
        "type": "CHART_PATTERN",
        "status": "突破頸線中",
        "score": "82%"
    }
]

def get_tv_url(symbol: str, interval: str) -> str:
    formatted_symbol = symbol.replace(":", "%3A")
    return f"https://www.tradingview.com/chart/?symbol={formatted_symbol}&interval={interval}"

@app.get("/")
def root():
    return RedirectResponse(url="/matrix")

# 1. 形態指標檢查矩陣表格（之前個表，右側加上雙按鈕功能）
@app.get("/matrix", response_class=HTMLResponse)
def get_matrix_view():
    rows_html = ""
    for item in PATTERNS_MATRIX:
        tv_link = get_tv_url(item["symbol"], item["timeframe"])
        custom_chart_link = f"/custom-chart?symbol={item['symbol']}&interval={item['timeframe']}"
        
        rows_html += f"""
        <tr>
            <td style="font-weight: bold; color: #2962ff;">{item['symbol']}</td>
            <td>{item['name']}</td>
            <td><span class="badge">{item['timeframe']}</span></td>
            <td><span class="pattern-tag">{item['pattern']}</span></td>
            <td style="color: #089981; font-weight: bold;">{item['status']}</td>
            <td>{item['score']}</td>
            <td class="action-cell">
                <a href="{custom_chart_link}" target="_blank" class="btn btn-custom">🎨 自訂繪圖板</a>
                <a href="{tv_link}" target="_blank" class="btn btn-tv">📈 TradingView ↗</a>
            </td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="zh-HK">
    <head>
        <meta charset="UTF-8">
        <title>形態與指標檢查矩陣</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, Arial, sans-serif; background: #131722; color: #d1d4dc; padding: 20px; }}
            h2 {{ margin-bottom: 16px; color: #ffffff; }}
            table {{ width: 100%; border-collapse: collapse; background: #1e222d; border-radius: 8px; overflow: hidden; }}
            th, td {{ padding: 14px 16px; text-align: left; border-bottom: 1px solid #2a2e39; }}
            th {{ background: #2a2e39; color: #787b86; font-size: 13px; uppercase; }}
            tr:hover {{ background: #262b3e; }}
            .badge {{ background: #2a2e39; padding: 2px 6px; border-radius: 4px; font-size: 12px; }}
            .pattern-tag {{ color: #f6c343; font-weight: bold; }}
            .action-cell {{ display: flex; gap: 8px; }}
            .btn {{ padding: 6px 12px; border-radius: 4px; text-decoration: none; font-size: 13px; font-weight: bold; }}
            .btn-custom {{ background: #9c27b0; color: white; }}
            .btn-custom:hover {{ background: #ab47bc; }}
            .btn-tv {{ background: #2962ff; color: white; }}
            .btn-tv:hover {{ background: #1e53e5; }}
        </style>
    </head>
    <body>
        <h2>全套量化幾何形態與指標檢查矩陣</h2>
        <table>
            <thead>
                <tr>
                    <th>代碼</th>
                    <th>名稱</th>
                    <th>週期</th>
                    <th>識別形態/指標</th>
                    <th>狀態</th>
                    <th>信心度</th>
                    <th>操作（開新版面）</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </body>
    </html>
    """
    return html

# 2. 根據自訂邏輯繪製指標的獨立圖表頁面
@app.get("/custom-chart", response_class=HTMLResponse)
def get_custom_chart(symbol: str = "HKEX:9988", interval: str = "D"):
    tv_url = get_tv_url(symbol, interval)
    
    # 測試用 K 棒數據[span_1](start_span)[span_1](end_span)
    candle_data = [
        {"time": "2026-07-20", "open": 140.0, "high": 142.5, "low": 138.0, "close": 139.5},
        {"time": "2026-07-21", "open": 139.5, "high": 140.0, "low": 122.0, "close": 125.0},
        {"time": "2026-07-22", "open": 125.0, "high": 138.5, "low": 124.0, "close": 137.0},
        {"time": "2026-07-23", "open": 137.0, "high": 137.5, "low": 112.0, "close": 115.0},
        {"time": "2026-07-24", "open": 115.0, "high": 136.5, "low": 114.5, "close": 135.0},
        {"time": "2026-07-25", "open": 135.0, "high": 135.5, "low": 123.0, "close": 126.0},
        {"time": "2026-07-28", "open": 126.0, "high": 141.0, "low": 125.5, "close": 139.5},
    ]
    
    channel_bot = [{"time": "2026-07-20", "value": 112.0}, {"time": "2026-07-28", "value": 120.0}][span_2](start_span)[span_2](end_span)
    channel_top = [{"time": "2026-07-20", "value": 138.0}, {"time": "2026-07-28", "value": 146.0}][span_3](start_span)[span_3](end_span)

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
            #chart {{ width: 100%; height: 600px; border-radius: 8px; border: 1px solid #2a2e39; }}
            .btn-tv {{ background: #2962ff; color: white; padding: 8px 16px; border-radius: 4px; text-decoration: none; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>自訂幾何邏輯畫圖版面 ({symbol})</h2>
            <a href="{tv_url}" target="_blank" class="btn-tv">切換至 TradingView 原生頁面 ↗</a>
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
            botSeries.setData({json.dumps(channel_bot)});
            
            const topSeries = chart.addLineSeries({{ color: '#ff0000', lineWidth: 2 }});
            topSeries.setData({json.dumps(channel_top)});

            candleSeries.setMarkers([
                {{ time: '2026-07-21', position: 'belowBar', color: '#e91e63', shape: 'circle', text: 'LS' }},
                {{ time: '2026-07-23', position: 'belowBar', color: '#9c27b0', shape: 'arrowUp', text: 'HEAD' }},
                {{ time: '2026-07-25', position: 'belowBar', color: '#e91e63', shape: 'circle', text: 'RS' }}
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
