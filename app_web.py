import json
import os
import subprocess
from flask import Flask, render_template_string, request

app = Flask(__name__)
app.json.ensure_ascii = False

# 你欲掃瞄與檢查的股票市場清單（僅作為數據庫，非熱門推薦）
TARGET_MARKET_POOL = [
    {"ticker": "0700.HK", "name": "騰訊控股", "tv_symbol": "HKEX:700"},
    {"ticker": "9988.HK", "name": "阿里巴巴", "tv_symbol": "HKEX:9988"},
    {"ticker": "3690.HK", "name": "美團", "tv_symbol": "HKEX:3690"},
    {"ticker": "1810.HK", "name": "小米集團", "tv_symbol": "HKEX:1810"},
    {"ticker": "0941.HK", "name": "中國移動", "tv_symbol": "HKEX:941"},
    {"ticker": "1211.HK", "name": "比亞迪股份", "tv_symbol": "HKEX:1211"},
    {"ticker": "2318.HK", "name": "中國平安", "tv_symbol": "HKEX:2318"},
    {"ticker": "0005.HK", "name": "匯豐控股", "tv_symbol": "HKEX:5"},
    {"ticker": "NVDA", "name": "英偉達", "tv_symbol": "NASDAQ:NVDA"},
    {"ticker": "AAPL", "name": "蘋果公司", "tv_symbol": "NASDAQ:AAPL"},
    {"ticker": "TSLA", "name": "特斯拉", "tv_symbol": "NASDAQ:TSLA"},
    {"ticker": "MSFT", "name": "微軟", "tv_symbol": "NASDAQ:MSFT"},
    {"ticker": "AMZN", "name": "亞馬遜", "tv_symbol": "NASDAQ:AMZN"},
    {"ticker": "META", "name": "Meta", "tv_symbol": "NASDAQ:META"},
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

                top_scenario = (
                    res["scenarios"][0] if res.get("scenarios") else {}
                )
                signals = top_scenario.get("signals", [])

                # 精確指標判斷
                res["has_pattern"] = len(signals) > 0
                res["signals_text"] = (
                    ", ".join([s["type"] for s in signals])
                    if signals
                    else "無"
                )
                res["w3_pass"] = top_scenario.get("w3_vol_pass", False)
                res["win_rate"] = top_scenario.get("win_rate", 0.0)

                # 綜合判定：是否符合你要求的指標形態
                res["is_matched"] = res["has_pattern"] or res["w3_pass"]
                return res
    except Exception as e:
        print(f"分析 {ticker} 失敗: {e}")
    return None


@app.route("/", methods=["GET", "POST"])
def index():
    custom_result = None

    # 單隻股票手動輸入查詢
    if request.method == "POST":
        custom_ticker = request.form.get("ticker", "").strip().upper()
        if custom_ticker:
            tv_symbol = (
                custom_ticker
                if ":" in custom_ticker
                else f"HKEX:{custom_ticker.split('.')[0]}"
                if ".HK" in custom_ticker
                else custom_ticker
            )
            stock_info = {
                "ticker": custom_ticker,
                "name": custom_ticker,
                "tv_symbol": tv_symbol,
            }
            custom_result = analyze_stock(stock_info)

    # 1. 執行市場數據掃瞄
    raw_results = []
    for stock in TARGET_MARKET_POOL:
        data = analyze_stock(stock)
        if data:
            raw_results.append(data)

    # 2. 自動去重 (依 Ticker)
    unique_stocks = list({s["ticker"]: s for s in raw_results}.values())

    # 3. 排序邏輯：符合指標者 (is_matched=True) 強制排最上端；下端按成交額/量排序
    unique_stocks.sort(
        key=lambda x: (
            1 if x["is_matched"] else 0,
            x.get("latest_turnover", 0),
        ),
        reverse=True,
    )

    html_template = """
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>形態與指標檢查結果</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #f4f6f9; padding: 20px; color: #333; }
            .container { max-width: 1250px; margin: 0 auto; background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
            h1 { color: #1a365d; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
            
            .legend-box { background: #f8fafc; padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #cbd5e0; }
            .legend-item { display: inline-block; margin-right: 20px; font-weight: bold; font-size: 0.9em; }
            
            .search-box { background: #edf2f7; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
            .search-box input { padding: 8px 12px; width: 220px; border: 1px solid #cbd5e0; border-radius: 4px; }
            .search-box button { padding: 8px 16px; background: #2b6cb0; color: white; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; }
            
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }
            th { background-color: #edf2f7; color: #2d3748; }
            
            /* 符合指標高亮標示 */
            tr.matched { background-color: #f0fff4; font-weight: 500; }
            tr.matched:hover { background-color: #dcffe4; }
            tr.unmatched { background-color: #ffffff; color: #a0aec0; }
            
            .badge { padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold; }
            .badge-match { background: #38a169; color: white; }
            .badge-none { background: #edf2f7; color: #a0aec0; }
            .badge-pass { background: #c6f6d5; color: #22543d; }
            .tv-btn { display: inline-block; padding: 6px 12px; background: #2962ff; color: white; border-radius: 4px; text-decoration: none; font-size: 0.85em; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 指定形態與指標檢查結果</h1>

            <!-- 圖例表示 -->
            <div class="legend-box">
                <strong>📌 圖例說明：</strong><br><br>
                <div class="legend-item"><span class="badge badge-match">🎯 符合指標</span> 觸發所選形態 / 浪三爆量（已自動排列於最上端）</div>
                <div class="legend-item"><span class="badge badge-none">⚪ 未符合</span> 未觸發指定形態（排列於下端）</div>
                <div class="legend-item"><span class="badge badge-pass">✅ Wave 3 爆量</span> 浪三成交量高於浪一</div>
            </div>

            <!-- 自訂輸入代號 -->
            <div class="search-box">
                <form method="POST">
                    <label for="ticker"><strong>手動指定檢查股票：</strong></label>
                    <input type="text" id="ticker" name="ticker" placeholder="例如: 0700.HK" required>
                    <button type="submit">執行檢查</button>
                </form>
            </div>

            {% if custom %}
            <div style="background: #fffaf0; border: 1px solid #feebc8; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <h3>🎯 指定股票檢查結果: {{ custom.ticker }}</h3>
                <p>
                    <strong>形態觸發：</strong> {{ custom.signals_text }} | 
                    <strong>成交金額：</strong> ${{ "{:,.0f}".format(custom.latest_turnover) }} |
                    <a href="https://www.tradingview.com/chart/?symbol={{ custom.tv_symbol }}" target="_blank" class="tv-btn">圖表分析 📈</a>
                </p>
            </div>
            {% endif %}

            <h2>📋 檢查結果清單 (符合條件者排於最上方)</h2>
            <table>
                <thead>
                    <tr>
                        <th>指標狀態</th>
                        <th>股票代號 / 名稱</th>
                        <th>最新價</th>
                        <th>成交量</th>
                        <th>成交金額</th>
                        <th>觸發形態指標</th>
                        <th>浪三爆量驗證</th>
                        <th>勝率</th>
                        <th>TradingView 連結</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in stocks %}
                    <tr class="{% if item.is_matched %}matched{% else %}unmatched{% endif %}">
                        <td>
                            {% if item.is_matched %}
                                <span class="badge badge-match">🎯 符合指標</span>
                            {% else %}
                                <span class="badge badge-none">⚪ 未符合</span>
                            {% endif %}
                        </td>
                        <td>
                            <strong style="color: #2d3748;">{{ item.ticker }}</strong><br>
                            <small>{{ item.name }}</small>
                        </td>
                        <td>${{ "%.2f"|format(item.latest_close) }}</td>
                        <td>{{ "{:,.0f}".format(item.latest_volume) }}</td>
                        <td>${{ "{:,.0f}".format(item.latest_turnover) }}</td>
                        <td><strong>{{ item.signals_text }}</strong></td>
                        <td>
                            {% if item.w3_pass %}
                                <span class="badge badge-pass">通過 ✅</span>
                            {% else %}
                                <span>-</span>
                            {% endif %}
                        </td>
                        <td><strong>{{ item.win_rate }}%</strong></td>
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
        html_template, stocks=unique_stocks, custom=custom_result
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
