import json
import os
import subprocess
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)
app.json.ensure_ascii = False

# 示範股票清單 (可加入港股、美股等代號)
WATCHLIST = [
    {"ticker": "0700.HK", "name": "騰訊控股", "tv_symbol": "HKEX:700"},
    {"ticker": "9988.HK", "name": "阿里巴巴", "tv_symbol": "HKEX:9988"},
    {"ticker": "3690.HK", "name": "美團", "tv_symbol": "HKEX:3690"},
    {"ticker": "1810.HK", "name": "小米集團", "tv_symbol": "HKEX:1810"},
    {"ticker": "0941.HK", "name": "中國移動", "tv_symbol": "HKEX:941"},
    {"ticker": "NVDA", "name": "英偉達", "tv_symbol": "NASDAQ:NVDA"},
    {"ticker": "AAPL", "name": "蘋果公司", "tv_symbol": "NASDAQ:AAPL"},
    {"ticker": "TSLA", "name": "特斯拉", "tv_symbol": "NASDAQ:TSLA"},
]


def analyze_stock(stock_info):
    ticker = stock_info["ticker"]
    try:
        # 呼叫 C++ 引擎並傳入股票代號
        subprocess.run(["./pattern_engine", ticker], check=True)
        if os.path.exists("result_top3.json"):
            with open("result_top3.json", "r", encoding="utf-8") as f:
                res = json.load(f)
                res["name"] = stock_info["name"]
                res["tv_symbol"] = stock_info["tv_symbol"]
                return res
    except Exception as e:
        print(f"分析 {ticker} 失敗: {e}")
    return None


@app.route("/")
def index():
    results = []
    # 逐一執行分析
    for stock in WATCHLIST:
        data = analyze_stock(stock)
        if data:
            results.append(data)

    # 預設依據【成交金額 (latest_turnover)】從大到小排序，取 前50 名
    results.sort(key=lambda x: x.get("latest_turnover", 0), reverse=True)
    top_50 = results[:50]

    html_template = """
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>波浪形態算牌 - 成交量/金額前50名</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #f4f6f9; padding: 20px; color: #333; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
            h1 { color: #1a365d; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }
            th { background-color: #edf2f7; color: #2d3748; }
            tr:hover { background-color: #f7fafc; }
            .badge { padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold; }
            .badge-pass { background: #c6f6d5; color: #22543d; }
            .badge-fail { background: #fed7d7; color: #742a2a; }
            .tv-btn { display: inline-block; padding: 6px 12px; background: #2962ff; color: white; border-radius: 4px; text-decoration: none; font-size: 0.85em; font-weight: bold; }
            .tv-btn:hover { background: #1e4bd8; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 波浪形態分析 (成交金額 TOP 50)</h1>
            <table>
                <thead>
                    <tr>
                        <th>股票名稱/代號</th>
                        <th>最新價</th>
                        <th>成交量</th>
                        <th>成交金額</th>
                        <th>最佳形態 (Rank 1)</th>
                        <th>勝率</th>
                        <th>浪三爆量</th>
                        <th>TradingView</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in stocks %}
                    {% set top = item.scenarios[0] %}
                    <tr>
                        <td>
                            <strong>{{ item.name }}</strong><br>
                            <small style="color: #718096;">{{ item.ticker }}</small>
                        </td>
                        <td>${{ "%.2f"|format(item.latest_close) }}</td>
                        <td>{{ "{:,.0f}".format(item.latest_volume) }}</td>
                        <td>${{ "{:,.0f}".format(item.latest_turnover) }}</td>
                        <td>{{ top.name }}</td>
                        <td><strong>{{ top.win_rate }}%</strong></td>
                        <td>
                            {% if top.w3_vol_pass %}
                                <span class="badge badge-pass">通過 ✅</span>
                            {% else %}
                                <span class="badge badge-fail">未通過 ❌</span>
                            {% endif %}
                        </td>
                        <td>
                            <a href="https://www.tradingview.com/chart/?symbol={{ item.tv_symbol }}" target="_blank" class="tv-btn">開啟圖表 📈</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """

    return render_template_string(html_template, stocks=top_50)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
