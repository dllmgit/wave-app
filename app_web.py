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

# 頂行要顯示的所有形態與指標
PATTERN_COLUMNS = [
    {"key": "triangle", "name": "三角形形態"},
    {"key": "head_shoulders", "name": "頭肩頂/底"},
    {"key": "double_top_bottom", "name": "雙頂/雙底"},
    {"key": "candlestick", "name": "K線轉向形態"},
    {"key": "trendline_break", "name": "趨勢線突破"},
    {"key": "w3_vol_pass", "name": "浪三爆量驗證"},
]


def fetch_stock_quote(ticker):
    """擷取行情以計算成交量/額進行去重排序"""
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
            return {
                "ticker": ticker,
                "name": ticker,
                "tv_symbol": f"HKEX:{ticker.split('.')[0]}",
                "latest_close": close,
                "latest_turnover": close * volume,
                "latest_volume": volume,
            }
    except Exception:
        return {
            "ticker": ticker,
            "name": ticker,
            "tv_symbol": f"HKEX:{ticker.split('.')[0]}",
            "latest_close": 0.0,
            "latest_turnover": 0,
            "latest_volume": 0,
        }


def get_top_50_merged():
    stock_list = [fetch_stock_quote(t) for t in HK_POOL]
    top_turnover = sorted(
        stock_list, key=lambda x: x["latest_turnover"], reverse=True
    )[:50]
    top_volume = sorted(
        stock_list, key=lambda x: x["latest_volume"], reverse=True
    )[:50]
    merged = {s["ticker"]: s for s in top_turnover + top_volume}
    return list(merged.values())


def analyze_pattern(stock_info):
    """執行 C++ 引擎並將觸發的形態對應到各個指標方格中"""
    ticker = stock_info["ticker"]
    matches = {p["key"]: False for p in PATTERN_COLUMNS}

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
                sig_text = " ".join([s.get("type", "") for s in signals])

                # 判定各個型態欄位是否符合 (符合記為 True)
                if (
                    "Triangle" in sig_text
                    or "narrowing" in sig_text
                    or "broadening" in sig_text
                ):
                    matches["triangle"] = True
                if "Head" in sig_text or "Shoulders" in sig_text:
                    matches["head_shoulders"] = True
                if "Double" in sig_text:
                    matches["double_top_bottom"] = True
                if (
                    "Hammer" in sig_text
                    or "Star" in sig_text
                    or "Engulfing" in sig_text
                ):
                    matches["candlestick"] = True
                if "Trendline" in sig_text or "Break" in sig_text:
                    matches["trendline_break"] = True

                matches["w3_vol_pass"] = top_scenario.get(
                    "w3_vol_pass", False
                )
                stock_info["win_rate"] = top_scenario.get("win_rate", 0.0)
    except Exception as e:
        print(f"分析 {ticker} 失敗: {e}")

    stock_info["matches"] = matches
    stock_info["has_any_match"] = any(matches.values())
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

    # 1. 取最高成交量與成交額 Top 50 聯集去重
    unique_pool = get_top_50_merged()

    # 2. 進行型態分析
    analyzed_stocks = [analyze_pattern(s) for s in unique_pool]

    # 3. 有符合任意指標的排列表格上端，無則放下端
    analyzed_stocks.sort(
        key=lambda x: (
            1 if x.get("has_any_match") else 0,
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
        <title>形態與指標檢查矩陣</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #f4f6f9; padding: 20px; color: #333; }
            .container { max-width: 1300px; margin: 0 auto; background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
            h1 { color: #1a365d; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
            
            .legend-box { background: #f8fafc; padding: 12px 18px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #cbd5e0; font-size: 0.95em; }
            
            .search-box { background: #edf2f7; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
            .search-box input { padding: 8px 12px; width: 220px; border: 1px solid #cbd5e0; border-radius: 4px; }
            .search-box button { padding: 8px 16px; background: #2b6cb0; color: white; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; }
            
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th, td { padding: 12px; text-align: center; border: 1px solid #e2e8f0; }
            th { background-color: #2b6cb0; color: white; font-weight: 600; }
            td.left-align { text-align: left; }
            
            tr.matched { background-color: #f0fff4; }
            tr.matched:hover { background-color: #dcffe4; }
            tr.unmatched { background-color: #ffffff; }
            tr.unmatched:hover { background-color: #f7fafc; }
            
            .check-icon { color: #2e7d32; font-size: 1.2em; font-weight: bold; }
            .tv-btn { display: inline-block; padding: 5px 10px; background: #2962ff; color: white; border-radius: 4px; text-decoration: none; font-size: 0.85em; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 技術形態與指標檢查矩陣</h1>

            <!-- 圖例說明 -->
            <div class="legend-box">
                <strong>📌 圖例說明：</strong> 方格顯示 <strong>✅</strong> 代表符合該項指標條件；未符合則保持留空。符合條件之股票已優先排列於上端。
            </div>

            <!-- 手動查詢股票 -->
            <div class="search-box">
                <form method="POST">
                    <label for="ticker"><strong>手動指定股票號碼：</strong></label>
                    <input type="text" id="ticker" name="ticker" placeholder="例如: 0700.HK" required>
                    <button type="submit">執行檢查</button>
                </form>
            </div>

            {% if custom %}
            <div style="background: #fffaf0; border: 1px solid #feebc8; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <h3>🎯 手動查詢結果: {{ custom.ticker }}</h3>
                <p>
                    <strong>現價：</strong> ${{ "%.2f"|format(custom.latest_close or 0) }} | 
                    <strong>歷史勝率：</strong> {{ custom.win_rate or 0 }}% |
                    <a href="https://www.tradingview.com/chart/?symbol={{ custom.tv_symbol }}" target="_blank" class="tv-btn">開啟 TradingView 圖表 📈</a>
                </p>
            </div>
            {% endif %}

            <!-- 主表格：型態指標全列於最頂行 -->
            <table>
                <thead>
                    <tr>
                        <th style="width: 140px;">股票代號</th>
                        <th style="width: 90px;">最新價</th>
                        {% for col in columns %}
                            <th>{{ col.name }}</th>
                        {% endfor %}
                        <th style="width: 80px;">勝率</th>
                        <th style="width: 100px;">TradingView</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in stocks %}
                    <tr class="{% if item.has_any_match %}matched{% else %}unmatched{% endif %}">
                        <td class="left-align"><strong>{{ item.ticker }}</strong></td>
                        <td>${{ "%.2f"|format(item.latest_close or 0) }}</td>
                        
                        <!-- 檢查每一個型態，符合顯示 ✅，無則留空 -->
                        {% for col in columns %}
                            <td>
                                {% if item.matches[col.key] %}
                                    <span class="check-icon">✅</span>
                                {% endif %}
                            </td>
                        {% endfor %}

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
        html_template,
        stocks=analyzed_stocks,
        columns=PATTERN_COLUMNS,
        custom=custom_result,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
