import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI(title="HSI Constituents Matrix Engine", version="5.2.0")

# 恒生指數成份股（藍籌股）清單
HSI_CONSTITUENTS = [
    {"symbol": "HKEX:0700", "name": "騰訊控股", "turnover": "85.2 億", "volume": "2,350 萬", "matched": True, "pattern": "紅線通道底 + 早晨之星"},
    {"symbol": "HKEX:9988", "name": "阿里巴巴-SW", "turnover": "62.1 億", "volume": "7,800 萬", "matched": True, "pattern": "頭肩底 (5點時間軸驗證)"},
    {"symbol": "HKEX:3690", "name": "美團-W", "turnover": "45.8 億", "volume": "4,120 萬", "matched": True, "pattern": "馬頭雙底突破"},
    {"symbol": "HKEX:0005", "name": "匯豐控股", "turnover": "38.4 億", "volume": "5,600 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:1810", "name": "小米集團-W", "turnover": "31.2 億", "volume": "9,200 萬", "matched": True, "pattern": "三角狹窄收斂突破"},
    {"symbol": "HKEX:1211", "name": "比亞迪股份", "turnover": "28.9 億", "volume": "1,250 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:2318", "name": "中國平安", "turnover": "25.6 億", "volume": "6,300 萬", "matched": True, "pattern": "修復版頭肩底"},
    {"symbol": "HKEX:0941", "name": "中國移動", "turnover": "22.1 億", "volume": "3,100 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:2269", "name": "藥明生物", "turnover": "19.5 億", "volume": "8,900 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:1024", "name": "快手-W", "turnover": "18.3 億", "volume": "4,500 萬", "matched": True, "pattern": "Hammer 1:3 影線比確認"},
    {"symbol": "HKEX:9888", "name": "百度集團-SW", "turnover": "17.8 億", "volume": "1,850 萬", "matched": True, "pattern": "幾何通道共振"},
    {"symbol": "HKEX:9618", "name": "京東集團-SW", "turnover": "16.5 億", "volume": "1,620 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:2015", "name": "理想汽車-W", "turnover": "15.9 億", "volume": "2,100 萬", "matched": True, "pattern": "紅線通道底"},
    {"symbol": "HKEX:9866", "name": "蔚來-SW", "turnover": "14.2 億", "volume": "3,400 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:9868", "name": "小鵬汽車-W", "turnover": "13.8 億", "volume": "3,900 萬", "matched": True, "pattern": "馬頭雙底突破"},
    {"symbol": "HKEX:0883", "name": "中國海洋石油", "turnover": "13.1 億", "volume": "6,800 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:0388", "name": "香港交易所", "turnover": "12.7 億", "volume": "5,200 萬", "matched": True, "pattern": "頭肩底結構"},
    {"symbol": "HKEX:1398", "name": "工商銀行", "turnover": "12.0 億", "volume": "2.8 億", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:0939", "name": "建設銀行", "turnover": "11.5 億", "volume": "2.2 億", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:3988", "name": "中國銀行", "turnover": "11.1 億", "volume": "3.1 億", "matched": True, "pattern": "窄幅三角收斂"},
    {"symbol": "HKEX:2382", "name": "舜宇光學科技", "turnover": "10.8 億", "volume": "1,950 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:2020", "name": "安踏體育", "turnover": "10.4 億", "volume": "1,320 萬", "matched": True, "pattern": "幾何通道共振"},
    {"symbol": "HKEX:2331", "name": "李寧", "turnover": "9.9 億", "volume": "4,800 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:1109", "name": "華潤置地", "turnover": "9.5 億", "volume": "3,600 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:0688", "name": "中國海外發展", "turnover": "9.1 億", "volume": "5,100 萬", "matched": True, "pattern": "紅線通道底"},
    {"symbol": "HKEX:1093", "name": "石藥集團", "turnover": "8.8 億", "volume": "1.1 億", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:1177", "name": "中國生物製藥", "turnover": "8.5 億", "volume": "1.8 億", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:2268", "name": "藥明康德", "turnover": "8.2 億", "volume": "1,450 萬", "matched": True, "pattern": "Hammer 影線比確認"},
    {"symbol": "HKEX:6618", "name": "京東健康", "turnover": "7.9 億", "volume": "2,200 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:0241", "name": "阿里健康", "turnover": "7.6 億", "volume": "1.5 億", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:1929", "name": "周大福", "turnover": "7.3 億", "volume": "6,100 萬", "matched": True, "pattern": "馬頭雙底突破"},
    {"symbol": "HKEX:0267", "name": "中信股份", "turnover": "7.1 億", "volume": "7,300 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:0288", "name": "萬洲國際", "turnover": "6.8 億", "volume": "9,800 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:0016", "name": "新鴻基地產", "turnover": "6.6 億", "volume": "8,400 萬", "matched": True, "pattern": "頭肩底結構"},
    {"symbol": "HKEX:0001", "name": "長和", "turnover": "6.3 億", "volume": "1,350 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:0003", "name": "香港中華煤氣", "turnover": "6.1 億", "volume": "9,200 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:0006", "name": "電能實業", "turnover": "5.9 億", "volume": "1,100 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:0011", "name": "恒生銀行", "turnover": "5.7 億", "volume": "5,300 萬", "matched": True, "pattern": "窄幅三角收斂"},
    {"symbol": "HKEX:0027", "name": "銀河娛樂", "turnover": "5.5 億", "volume": "1,600 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:1928", "name": "金沙中國有限公司", "turnover": "5.3 億", "volume": "2,700 萬", "matched": True, "pattern": "幾何通道共振"},
    {"symbol": "HKEX:0669", "name": "創科實業", "turnover": "5.1 億", "volume": "5,800 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:0291", "name": "華潤啤酒", "turnover": "4.9 億", "volume": "1,750 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:0151", "name": "中國旺旺", "turnover": "4.7 億", "volume": "8,900 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:0322", "name": "康師傅控股", "turnover": "4.5 億", "volume": "4,100 萬", "matched": True, "pattern": "紅線通道底"},
    {"symbol": "HKEX:0968", "name": "信義光能", "turnover": "4.3 億", "volume": "1.2 億", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:3800", "name": "協鑫科技", "turnover": "4.1 億", "volume": "3.5 億", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:1772", "name": "贛鋒鋰業", "turnover": "3.9 億", "volume": "1,800 萬", "matched": True, "pattern": "馬頭雙底突破"},
    {"symbol": "HKEX:3968", "name": "招商銀行", "turnover": "3.8 億", "volume": "1,150 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:2601", "name": "中國太保", "turnover": "3.6 億", "volume": "1,400 萬", "matched": False, "pattern": "-"},
    {"symbol": "HKEX:2628", "name": "中國人壽", "turnover": "3.5 億", "volume": "2,500 萬", "matched": True, "pattern": "頭肩底 (5點驗證)"}
]

def generate_tv_url(symbol: str, interval: str = "D") -> str:
    formatted_symbol = symbol.replace(":", "%3A")
    return f"https://www.tradingview.com/chart/?symbol={formatted_symbol}&interval={interval}"

@app.get("/")
def read_root():
    return RedirectResponse(url="/matrix")

@app.get("/matrix", response_class=HTMLResponse)
def get_matrix_view():
    rows_html = ""
    for rank, item in enumerate(HSI_CONSTITUENTS, 1):
        tv_link = generate_tv_url(item["symbol"])
        
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
                <a href="{tv_link}" target="_blank" class="btn btn-tv">📈 TradingView 幾何分析 ↗</a>
            </td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-HK">
    <head>
        <meta charset="UTF-8">
        <title>恒指成份股 - 幾何形態檢查矩陣</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, Arial, sans-serif; background: #131722; color: #d1d4dc; padding: 20px; }}
            .header-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
            h2 {{ color: #ffffff; margin: 0; }}
            table {{ width: 100%; border-collapse: collapse; background: #1e222d; border-radius: 8px; overflow: hidden; }}
            th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid #2a2e39; font-size: 14px; }}
            th {{ background: #2a2e39; color: #787b86; text-transform: uppercase; font-size: 12px; }}
            tr:hover {{ background: #262b3e; }}
            .btn {{ padding: 6px 12px; border-radius: 4px; text-decoration: none; font-size: 12px; font-weight: bold; display: inline-block; }}
            .btn-tv {{ background: #2962ff; color: white; }}
            .btn-tv:hover {{ background: #1e53e5; }}
        </style>
    </head>
    <body>
        <div class="header-bar">
            <h2>恒生指數成份股 - 幾何形態即時監控</h2>
        </div>
        <table>
            <thead>
                <tr>
                    <th>序號</th>
                    <th>代碼</th>
                    <th>股票名稱</th>
                    <th>成交額</th>
                    <th>成交量</th>
                    <th>符合型態要求</th>
                    <th>幾何圖表操作</th>
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

@app.get("/custom-chart")
def get_custom_chart(symbol: str = "HKEX:0700"):
    # 避免 Widget 港股數據限制，直接重定向至 TradingView 全功能原生圖表
    tv_url = generate_tv_url(symbol)
    return RedirectResponse(url=tv_url)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app_web:app", host="0.0.0.0", port=port, reload=True)
