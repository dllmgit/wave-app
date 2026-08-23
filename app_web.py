import json
import os
import subprocess
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)
app.json.ensure_ascii = False

# 預設清單
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
        subprocess.run(["./pattern_engine", ticker], check=True)
        if os.path.exists("result_top3.json"):
            with open("result_top3.json", "r", encoding="utf-8") as f:
                res = json.load(f)
                res["name"] = stock_info.get("name", ticker)
                res["tv_symbol"] = stock_info.get("tv_symbol", ticker)
                return res
    except Exception as e:
        print(f"分析 {ticker} 失敗: {e}")
    return None


@app.route("/", methods=["GET", "POST"])
def index():
    custom_result = None

    # 處理使用者自訂輸入查詢
    if request.method == "POST":
        custom_ticker = request.form.get("ticker", "").strip().upper()
        if custom_ticker:
            # 自動推導 TradingView 符號格式
            tv_symbol = (
                custom_ticker
                if ":" in custom_ticker
                else f"HKEX:{custom_ticker.split('.')[0]}"
                if ".HK" in custom_ticker
                else custom_ticker
            )
            stock_info = {
                "ticker": custom_ticker,
                "name": f"自訂股: {custom_ticker}",
                "tv_symbol": tv_symbol,
            }
            custom_result = analyze_stock(stock_info)

    # 預設清單批次分析與排序 (Top 50)
    results = []
    for stock in WATCHLIST:
        data = analyze_stock(stock)
        if data:
            results.append(data)

    results.sort(key=lambda x: x.get("latest_turnover", 0), reverse=True)
    top_50 = results[:50]

    html_template = """
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>波浪形態算牌引擎</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #f4f6f9; padding: 20px; color: #333; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
            h1 { color: #1a365d; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
            .search-box { background: #edf2f7; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
            .search-box input { padding: 8px 12px; width: 250px; border: 1px solid #cbd5e0; border-radius: 4px; font-size: 1em; }
            .search-box button { padding: 8px 16px; background: #3182ce; color: white; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; }
            .search-box button:hover { background: #2b6cb0; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }
            th { background-color: #edf2f7; color: #2d3748; }
            tr:hover { background-color: #f7fafc; }
            .badge { padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold; }
            .badge-pass { background: #c6f6d5; color: #22543d; }
            .badge-fail { background: #fed7d7; color: #742a2a; }
            .tv-btn { display: inline-block; padding: 6px 12px; background: #2962ff; color: white; border-radius: 4px; text-decoration: none; font-size: 0.85em; font-weight: bold; }
            .tv-btn:hover { background: #1e4bd8; }
            .custom-card { background: #fffaf0; border: 1px solid #feebc8; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 波浪形態分析與算牌系統</h1>
            
            <!-- 自訂輸入股票號碼區塊 -->
            <div class="search-box">
                <form method="POST">
                    <label for="ticker"><strong>🔍 自訂查詢股票：</strong></label>
                    <input type="text" id="ticker" name="ticker" placeholder="例如: 0700.HK 或 AAPL" required>
                    <button type="submit">立即分析</button>
                </form>
            </div>

            {% if custom %}
            <div class="custom-card">
                <h3>🎯 自訂查詢結果: {{ custom.name }} ({{ custom.ticker }})</h3>
                <p>
                    <strong>現價：</strong> ${{ "%.2f"|format(custom.latest_close) }} | 
                    <strong>成交金額：</strong> ${{ "{:,.0f}".format(custom.latest_turnover) }} |
                    <strong>TradingView：</strong> <a href="https://www.tradingview.com/chart/?symbol={{ custom.tv_symbol }}" target="_blank" class="tv-btn">開啟圖表 📈</a>
                </p>
                <ul>
                    {% for s in custom.scenarios %}
                    <li><strong>Rank {{ s.rank }} ({{ s.name }})</strong> - 勝率: {{ s.win_rate }}% | 目標價: ${{ s.target_w5 }} | 止損: ${{ s.stop_loss }}</li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}

            <h2>📈 成交金額/量 TOP 50 總覽</h2>
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

    return render_template_string(
        html_template, stocks=top_50, custom=custom_result
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
