import json
import os
import subprocess
import urllib.request
from flask import Flask, render_template_string, request

app = Flask(__name__)
app.json.ensure_ascii = False

# 50 隻重點港股數據池
HK_POOL = [
    f"{str(i).zfill(4)}.HK"
    for i in [
        700,
        9988,
        3690,
        1810,
        941,
        1211,
        2318,
        5,
        9999,
        1024,
        2015,
        2269,
        388,
        857,
        1299,
        883,
        2382,
        1113,
        16,
        2,
        669,
        2319,
        1088,
        1929,
        2888,
        9618,
        9888,
        9961,
        6862,
        2020,
        1398,
        3988,
        939,
        2628,
        3968,
        1177,
        1093,
        2600,
        2899,
        1800,
        386,
        836,
        1109,
        2007,
        1919,
        6030,
        3908,
        6060,
        9633,
        9995,
    ]
]


def fetch_stock_quote(ticker):
    """使用原生 HTTP 請求獲取行情，免額外套件"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d"
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            result = data["chart"]["result"][0]
            meta = result["meta"]
            close = meta.get("regularMarketPrice", 0.0)
            volume = meta.get("regularMarketVolume", 0)
            turnover = close * volume
            return {
                "ticker": ticker,
                "name": ticker,
                "tv_symbol": f"HKEX:{ticker.split('.')[0]}",
                "latest_close": close,
                "latest_volume": volume,
                "latest_turnover": turnover,
            }
    except Exception as e:
        print(f"獲取 {ticker} 數據失敗: {e}")
        return {
            "ticker": ticker,
            "name": ticker,
            "tv_symbol": f"HKEX:{ticker.split('.')[0]}",
            "latest_close": 0.0,
            "latest_volume": 0,
            "latest_turnover": 0,
        }


def get_top_50_merged():
    """抓取並整合成交額 Top 50 及成交量 Top 50 (去重)"""
    stock_list = []
    for ticker in HK_POOL:
        quote = fetch_stock_quote(ticker)
        stock_list.append(quote)

    top_turnover = sorted(
        stock_list, key=lambda x: x["latest_turnover"], reverse=True
    )[:50]
    top_volume = sorted(
        stock_list, key=lambda x: x["latest_volume"], reverse=True
    )[:50]

    merged = {s["ticker"]: s for s in top_turnover + top_volume}
    return list(merged.values())


def analyze_pattern(stock_info):
    """呼叫 C++ 引擎檢查型態與指標"""
    ticker = stock_info["ticker"]
    try:
        subprocess.run(["./pattern_engine", ticker], check=True)
        if os.path.exists("result_top3.json"):
            with open("result_top3.json", "r", encoding="utf-8") as f:
                res = json.load(f)
                stock_info.update(res)

                top_scenario = (
                    res["scenarios"][0] if res.get("scenarios") else {}
                )
                signals = top_scenario.get("signals", [])

                stock_info["has_pattern"] = len(signals) > 0
                stock_info["signals_text"] = (
                    ", ".join([s["type"] for s in signals])
                    if signals
                    else "無符合型態"
                )
                stock_info["w3_pass"] = top_scenario.get("w3_vol_pass", False)
                stock_info["win_rate"] = top_scenario.get("win_rate", 0.0)
                stock_info["is_matched"] = (
                    stock_info["has_pattern"] or stock_info["w3_pass"]
                )
                return stock_info
    except Exception as e:
        print(f"分析 {ticker} 失敗: {e}")

    stock_info["is_matched"] = False
    stock_info["signals_text"] = "未觸發"
    return stock_info


@app.route("/", methods=["GET", "POST"])
def index():
    custom_result = None

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
            stock_info = fetch_stock_quote(custom_ticker)
            custom_result = analyze_pattern(stock_info)

    # 1. 自動篩選最高成交額/量 Top 50 並去重
    unique_pool = get_top_50_merged()

    # 2. 進行型態檢查
    analyzed_stocks = [analyze_pattern(s) for s in unique_pool]

    # 3. 符合排序：符合指定型態/指標者排最上方，未符合者放下端
    analyzed_stocks.sort(
        key=lambda x: (
            1 if x.get("is_matched") else 0,
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
        <title>指定型態與指標檢查系統</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #f4f6f9; padding: 20px; color: #333; }
            .container { max-width: 1250px; margin: 0 auto; background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
            h1 { color: #1a365d; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
            
            .legend-box { background: #f8fafc; padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #cbd5e0; }
            .legend-item { display: inline-block; margin-right: 25px; font-weight: bold; font-size: 0.9em; }
            
            .search-box { background: #edf2f7; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
            .search-box input { padding: 8px 12px; width: 220px; border: 1px solid #cbd5e0; border-radius: 4px; }
            .search-box button { padding: 8px 16px; background: #2b6cb0; color: white; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; }
            
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }
            th { background-color: #edf2f7; color: #2d3748; }
            
            tr.matched { background-color: #f0fff4; font-weight: 500; }
            tr.matched:hover { background-color: #dcffe4; }
            tr.unmatched { background-color: #ffffff; color: #718096; }
            tr.unmatched:hover { background-color: #f7fafc; }
            
            .badge { padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold; }
            .badge-match { background: #38a169; color: white; }
            .badge-none { background: #edf2f7; color: #a0aec0; }
            .badge-pass { background: #c6f6d5; color: #22543d; }
            .tv-btn { display: inline-block; padding: 6px 12px; background: #2962ff; color: white; border-radius: 4px; text-decoration: none; font-size: 0.85em; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 指定型態與指標檢查清單</h1>

            <!-- 圖例區 -->
            <div class="legend-box">
                <strong>📌 圖例說明：</strong><br><br>
                <div class="legend-item"><span class="badge badge-match">🎯 符合型態</span> 觸發指標/型態條件（已排列於列表最上端）</div>
                <div class="legend-item"><span class="badge badge-none">⚪ 未符合</span> 未觸發指標條件（排列於列表下端）</div>
                <div class="legend-item"><span class="badge badge-pass">✅ 放量確認</span> 浪三成交量高於浪一成交量</div>
            </div>

            <!-- 自訂輸入 -->
            <div class="search-box">
                <form method="POST">
                    <label for="ticker"><strong>手動指定檢查股票：</strong></label>
                    <input type="text" id="ticker" name="ticker" placeholder="例如: 0700.HK" required>
                    <button type="submit">執行檢查</button>
                </form>
            </div>

            {% if custom %}
            <div style="background: #fffaf0; border: 1px solid #feebc8; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <h3>🎯 手動查詢結果: {{ custom.ticker }}</h3>
                <p>
                    <strong>觸發型態：</strong> {{ custom.signals_text }} | 
                    <strong>成交金額：</strong> ${{ "{:,.0f}".format(custom.latest_turnover or 0) }} |
                    <a href="https://www.tradingview.com/chart/?symbol={{ custom.tv_symbol }}" target="_blank" class="tv-btn">開啟 TradingView 圖表 📈</a>
                </p>
            </div>
            {% endif %}

            <h2>📋 檢查結果列表 (成交量/額 Top 50 聯集去重)</h2>
            <table>
                <thead>
                    <tr>
                        <th>圖例標籤</th>
                        <th>股票代號</th>
                        <th>最新價</th>
                        <th>成交量</th>
                        <th>成交金額</th>
                        <th>觸發型態指標</th>
                        <th>量能驗證</th>
                        <th>勝率</th>
                        <th>TradingView</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in stocks %}
                    <tr class="{% if item.is_matched %}matched{% else %}unmatched{% endif %}">
                        <td>
                            {% if item.is_matched %}
                                <span class="badge badge-match">🎯 符合型態</span>
                            {% else %}
                                <span class="badge badge-none">⚪ 未符合</span>
                            {% endif %}
                        </td>
                        <td><strong>{{ item.ticker }}</strong></td>
                        <td>${{ "%.2f"|format(item.latest_close or 0) }}</td>
                        <td>{{ "{:,.0f}".format(item.latest_volume or 0) }}</td>
                        <td>${{ "{:,.0f}".format(item.latest_turnover or 0) }}</td>
                        <td><strong>{{ item.signals_text }}</strong></td>
                        <td>
                            {% if item.w3_pass %}
                                <span class="badge badge-pass">通過 ✅</span>
                            {% else %}
                                <span>-</span>
                            {% endif %}
                        </td>
                        <td><strong>{{ item.win_rate or 0 }}%</strong></td>
                        <td>
                            <a href="https://www.tradingview.com/chart/?symbol={{ item.tv_symbol }}" target="_blank" class="tv-btn">圖表 📈</a>
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
        html_template, stocks=analyzed_stocks, custom=custom_result
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
