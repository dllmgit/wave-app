import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI(title="HSI Custom Geometry Engine", version="6.0.0")

HSI_CONSTITUENTS = [
    {"symbol": "HKEX:0700", "name": "騰訊控股", "turnover": "85.2 億", "volume": "2,350 萬", "matched": True, "pattern": "紅線通道底 + 早晨之星"},
    {"symbol": "HKEX:9988", "name": "阿里巴巴-SW", "turnover": "62.1 億", "volume": "7,800 萬", "matched": True, "pattern": "頭肩底 (5點時間軸驗證)"},
    {"symbol": "HKEX:3690", "name": "美團-W", "turnover": "45.8 億", "volume": "4,120 萬", "matched": True, "pattern": "馬頭雙底突破"},
    {"symbol": "HKEX:1810", "name": "小米集團-W", "turnover": "31.2 億", "volume": "9,200 萬", "matched": True, "pattern": "三角狹窄收斂突破"},
    {"symbol": "HKEX:2318", "name": "中國平安", "turnover": "25.6 億", "volume": "6,300 萬", "matched": True, "pattern": "修復版頭肩底"},
    {"symbol": "HKEX:1024", "name": "快手-W", "turnover": "18.3 億", "volume": "4,500 萬", "matched": True, "pattern": "Hammer 1:3 影線比確認"}
]

@app.get("/")
def read_root():
    return RedirectResponse(url="/matrix")

@app.get("/matrix", response_class=HTMLResponse)
def get_matrix_view():
    rows_html = ""
    for rank, item in enumerate(HSI_CONSTITUENTS, 1):
        custom_chart_link = f"/custom-chart?symbol={item['symbol']}&pattern={item['pattern']}"
        rows_html += f"""
        <tr>
            <td style="color: #787b86;">{rank}</td>
            <td style="font-weight: bold; color: #2962ff;">{item['symbol']}</td>
            <td style="font-weight: bold; color: #ffffff;">{item['name']}</td>
            <td>{item['turnover']}</td>
            <td>{item['volume']}</td>
            <td><span style="color: #089981; font-weight: bold;">✅ {item['pattern']}</span></td>
            <td>
                <a href="{custom_chart_link}" class="btn btn-custom">🎨 執行自訂幾何繪圖</a>
            </td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="zh-HK">
    <head>
        <meta charset="UTF-8">
        <title>幾何形態矩陣</title>
        <style>
            body {{ font-family: sans-serif; background: #131722; color: #d1d4dc; padding: 20px; }}
            table {{ width: 100%; border-collapse: collapse; background: #1e222d; border-radius: 8px; }}
            th, td {{ padding: 12px 16px; border-bottom: 1px solid #2a2e39; }}
            th {{ background: #2a2e39; color: #787b86; }}
            .btn-custom {{ background: #9c27b0; color: white; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h2>恒生指數成份股 - 自訂幾何邏輯監控</h2>
        <table>
            <thead>
                <tr><th>序號</th><th>代碼</th><th>股票名稱</th><th>成交額</th><th>成交量</th><th>符合型態</th><th>操作</th></tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
    </body>
    </html>
    """

@app.get("/custom-chart", response_class=HTMLResponse)
def get_custom_chart(symbol: str = "HKEX:2318", pattern: str = "自訂幾何邏輯"):
    return f"""
    <!DOCTYPE html>
    <html lang="zh-HK">
    <head>
        <meta charset="UTF-8">
        <title>自訂幾何繪圖 - {symbol}</title>
        <style>
            body {{ font-family: sans-serif; background: #131722; color: #ffffff; padding: 20px; margin: 0; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
            #chartCanvas {{ background: #1e222d; border-radius: 8px; border: 1px solid #2a2e39; width: 100%; height: 500px; }}
            .badge {{ background: #2962ff; padding: 4px 10px; border-radius: 4px; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>{symbol} - 自訂幾何圖表渲染器</h2>
            <span class="badge">套用邏輯：{pattern}</span>
        </div>

        <canvas id="chartCanvas" width="1000" height="500"></canvas>

        <script>
            const canvas = document.getElementById('chartCanvas');
            const ctx = canvas.getContext('2d');

            // 模擬 K 線數據 (Open, High, Low, Close)
            const candles = [
                {{o: 100, h: 105, l: 98, c: 103}},
                {{o: 103, h: 108, l: 101, c: 102}},
                {{o: 102, h: 104, l: 95, c: 96}},
                {{o: 96, h: 99, l: 92, c: 94}},
                {{o: 94, h: 101, l: 93, c: 100}},
                {{o: 100, h: 107, l: 99, c: 106}},
                {{o: 106, h: 112, l: 105, c: 110}},
                {{o: 110, h: 115, l: 108, c: 114}},
                {{o: 114, h: 118, l: 112, c: 113}},
                {{o: 113, h: 122, l: 113, c: 120}},
            ];

            const padding = 50;
            const chartWidth = canvas.width - padding * 2;
            const chartHeight = canvas.height - padding * 2;
            const candleWidth = chartWidth / candles.length;

            // 1. 繪製背景網格
            ctx.strokeStyle = '#2a2e39';
            ctx.lineWidth = 1;
            for(let i = 0; i <= 5; i++) {{
                let y = padding + (chartHeight / 5) * i;
                ctx.beginPath();
                ctx.moveTo(padding, y);
                ctx.lineTo(canvas.width - padding, y);
                ctx.stroke();
            }}

            // 2. 繪製 K 線
            candles.forEach((c, idx) => {{
                let x = padding + idx * candleWidth + candleWidth / 2;
                let isGreen = c.c >= c.o;
                
                // 價格映身至 Canvas 座標
                let yHigh = padding + chartHeight - ((c.h - 90) / 35) * chartHeight;
                let yLow = padding + chartHeight - ((c.l - 90) / 35) * chartHeight;
                let yOpen = padding + chartHeight - ((c.o - 90) / 35) * chartHeight;
                let yClose = padding + chartHeight - ((c.c - 90) / 35) * chartHeight;

                // 畫影線
                ctx.strokeStyle = isGreen ? '#089981' : '#f23645';
                ctx.beginPath();
                ctx.moveTo(x, yHigh);
                ctx.lineTo(x, yLow);
                ctx.stroke();

                // 畫實體
                ctx.fillStyle = isGreen ? '#089981' : '#f23645';
                ctx.fillRect(x - 12, Math.min(yOpen, yClose), 24, Math.abs(yClose - yOpen) || 2);
            }});

            // 3. 執行自訂幾何圖形邏輯繪製（範例：自動繪製通道線與突破點）
            // 上軌趨勢線 (紅線)
            ctx.strokeStyle = '#f23645';
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.moveTo(padding + 20, 200);
            ctx.lineTo(canvas.width - padding - 20, 80);
            ctx.stroke();

            // 下軌支撐線 (綠線)
            ctx.strokeStyle = '#089981';
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.moveTo(padding + 20, 420);
            ctx.lineTo(canvas.width - padding - 20, 260);
            ctx.stroke();

            // 自訂標示：幾何訊號觸發點
            ctx.fillStyle = '#ffeb3b';
            ctx.font = 'bold 14px Arial';
            ctx.fillText('★ 幾何形態突破點', canvas.width - 220, 70);
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app_web:app", host="0.0.0.0", port=port, reload=True)
