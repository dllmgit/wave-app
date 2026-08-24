from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json

app = FastAPI()

def generate_tradingview_url(symbol: str = "HKEX:9988", interval: str = "D") -> str:
    """動態生成對應標的與週期之 TradingView 官方跳轉連結"""
    formatted_symbol = symbol.replace(":", "%3A")
    return f"https://www.tradingview.com/chart/?symbol={formatted_symbol}&interval={interval}"

@app.get("/chart", response_class=HTMLResponse)
def get_chart_view():
    symbol = "HKEX:9988"
    interval = "D"
    tv_url = generate_tradingview_url(symbol, interval)

    # 模擬 K 棒與後端 C++ / Python 計算出的紅線通道及形態座標
    candle_data = [
        {"time": "2026-08-01", "open": 110, "high": 115, "low": 108, "close": 112},
        {"time": "2026-08-02", "open": 112, "high": 120, "low": 111, "close": 118},
        {"time": "2026-08-03", "open": 118, "high": 125, "low": 116, "close": 122},
        {"time": "2026-08-04", "open": 122, "high": 124, "low": 115, "close": 116},
        {"time": "2026-08-05", "open": 116, "high": 130, "low": 115, "close": 128},
    ]

    # 後端精確算出的紅線通道座標 (底線與頂線)
    channel_bot = [
        {"time": "2026-08-01", "value": 108},
        {"time": "2026-08-05", "value": 115}
    ]
    channel_top = [
        {"time": "2026-08-01", "value": 120},
        {"time": "2026-08-05", "value": 128}
    ]

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>自訂精確圖表分析 - {symbol}</title>
        <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #131722; color: #d1d4dc; }}
            #header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
            #chart-container {{ width: 100%; height: 600px; }}
            .tv-btn {{
                background-color: #2962ff; color: white; padding: 10px 18px;
                text-decoration: none; border-radius: 4px; font-weight: bold;
            }}
            .tv-btn:hover {{ background-color: #1e53e5; }}
        </style>
    </head>
    <body>
        <div id="header">
            <h2>自訂幾何邏輯圖表 ({symbol})</h2>
            <a href="{tv_url}" target="_blank" class="tv-btn">開啟 TradingView 原生圖表 ↗</a>
        </div>
        <div id="chart-container"></div>

        <script>
            const chart = LightweightCharts.createChart(document.getElementById('chart-container'), {{
                layout: {{ backgroundColor: '#131722', textColor: '#d1d4dc' }},
                grid: {{ vertLines: {{ color: '#2B2B43' }}, horzLines: {{ color: '#2B2B43' }} }}
            }});

            // 1. 繪製 K 線
            const candlestickSeries = chart.addCandlestickSeries({{
                upColor: '#089981', downColor: '#f23645',
                borderUpColor: '#089981', borderDownColor: '#f23645',
                wickUpColor: '#089981', wickDownColor: '#f23645'
            }});
            candlestickSeries.setData({json.dumps(candle_data)});

            // 2. 繪製自訂精確紅線通道 (底線)
            const botSeries = chart.addLineSeries({{ color: '#ff0000', lineWidth: 2 }});
            botSeries.setData({json.dumps(channel_bot)});

            // 3. 繪製自訂精確紅線通道 (頂線)
            const topSeries = chart.addLineSeries({{ color: '#ff0000', lineWidth: 2 }});
            topSeries.setData({json.dumps(channel_top)});

            // 4. 標註自訂形態 (例：修復版頭肩底、早晨之星)
            candlestickSeries.setMarkers([
                {{ time: '2026-08-01', position: 'belowBar', color: '#e91e63', shape: 'arrowUp', text: 'LS (左肩)' }},
                {{ time: '2026-08-04', position: 'belowBar', color: '#9c27b0', shape: 'arrowUp', text: 'HEAD (頭部)' }},
                {{ time: '2026-08-05', position: 'belowBar', color: '#e91e63', shape: 'arrowUp', text: 'RS (右肩 - 驗證通過)' }}
            ]);
        </script>
    </body>
    </html>
    """
    return html_content
