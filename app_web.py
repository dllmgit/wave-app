import json
import os
import subprocess
from flask import Flask, render_template_string, request
import yfinance as yf

app = Flask(__name__)
app.json.ensure_ascii = False


def fetch_top_50_stocks():
    """動態抓取港股成交額 Top 50 與成交量 Top 50 並進行去重聯集"""
    # 港股主要大型股代號池（可自行擴充或動態獲取）
    hk_tickers = [
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

    try:
        data = yf.download(
            hk_tickers, period="1d", group_by="ticker", progress=False
        )
        stock_stats = []

        for ticker in hk_tickers:
            try:
                df = data[ticker]
                if not df.empty:
                    close = float(df["Close"].iloc[-1])
                    volume = float(df["Volume"].iloc[-1])
                    turnover = close * volume
                    stock_stats.append(
                        {
                            "ticker": ticker,
                            "name": ticker,
                            "tv_symbol": f"HKEX:{ticker.split('.')[0]}",
                            "latest_close": close,
                            "latest_volume": volume,
                            "latest_turnover": turnover,
                        }
                    )
            except Exception:
                continue

        # 按成交額排序取 Top 50
        top_turnover = sorted(
            stock_stats, key=lambda x: x["latest_turnover"], reverse=True
        )[:50]
        # 按成交量排序取 Top 50
        top_volume = sorted(
            stock_stats, key=lambda x: x["latest_volume"], reverse=True
        )[:50]

        # 聯集去重 (相同的只保留一隻)
        merged_dict = {s["ticker"]: s for s in top_turnover + top_volume}
        return list(merged_dict.values())
    except Exception as e:
        print(f"獲取市場數據失敗: {e}")
        return []


def analyze_pattern(stock_info):
    """執行指定的型態與指標檢查（包含三角形收斂/擴散、趨勢線與波浪）"""
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

                # 指標/型態判定邏輯：檢查是否有觸發特定指標型態
                stock_info["has_pattern"] = len(signals) > 0
                stock_info["signals_text"] = (
                    ", ".join([s["type"] for s in signals])
                    if signals
                    else "無符合型態"
                )
                stock_info["w3_pass"] = top_scenario.get("w3_vol_pass", False)
                stock_info["win_rate"] = top_scenario.get("win_rate", 0.0)

                # 綜合判定：是否有符合指定的型態或指標條件
                stock_info["is_matched"] = (
                    stock_info["has_pattern"] or stock_info["w3_pass"]
                )
                return stock_info
    except Exception as e:
        print(f"分析 {ticker} 失敗: {e}")

    stock_info["is_matched"] = False
    stock_info["signals_text"] = "分析失敗"
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
            stock_info = {
                "ticker": custom_ticker,
                "name": custom_ticker,
                "tv_symbol": tv_symbol,
            }
            custom_result = analyze_pattern(stock_info)

    # 1. 自動抓取 最高成交額 Top 50 + 最高成交量 Top 50 (去重聯集)
    stock_pool = fetch_top_50_stocks()

    # 2. 對去重後的每隻股票進行型態與指標檢查
    analyzed_stocks = []
    for stock in stock_pool:
        res = analyze_pattern(stock)
        if res:
            analyzed_stocks.append(res)

    # 3. 排序原則：符合指定型態/指標的放最上端，沒有符合的放下端
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
        <title>成交量/額 Top 50 指定型態檢查</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #f4f6f9; padding: 20px; color: #333; }
            .container { max-width: 1250px; margin: 0 auto; background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
            h1 { color: #1a365d; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
            
            /* 圖例說明區 */
            .legend-box { background: #f8fafc; padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #cbd5e0; }
            .legend-item { display: inline-block; margin-right: 25px; font-weight: bold; font-size: 0.9em; }
            
            .search-box { background: #edf2f7; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
            .search-box input { padding: 8px 12px; width: 220px; border: 1px solid #cbd5e0; border-radius: 4px; }
            .search-box button { padding: 8px 16px; background: #2b6cb0; color: white; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; }
            
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }
            th { background-color: #edf2f7; color: #2d3748; }
            
            /* 置頂與未符合樣式區隔 */
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
            <h1>🔍 最高成交量/成交額 Top 50 型態檢查</h1>

            <!-- 圖例說明 -->
            <div class="legend-box">
                <strong>📌 圖例說明：</strong><br><br>
                <div class="legend-item"><span class="badge badge-match">🎯 符合型態/指標</span> 觸發三角形收斂/趨勢線/波浪指標（已自動置頂於表格上端）</div>
                <div class="legend-item"><span class="badge badge-none">⚪ 未符合</span> 未觸發指定型態（排列於表格下端）</div>
                <div class="legend-item"><span class="badge badge-pass">✅ 放量確認</span> 浪三成交量高於浪一成交量</div>
            </div>

            <!-- 手動指定查詢 -->
            <div class="search-box">
                <form method="POST">
                    <label for="ticker"><strong>手動檢查指定股票：</strong></label>
                    <input type="text" id="ticker" name="ticker" placeholder="例如: 0700.HK" required>
                    <button type="submit">執行檢查</button>
                </form>
            </div>

            {% if custom %}
            <div style="background: #fffaf0; border: 1px solid #feebc8; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <h3>🎯 手動檢查結果: {{ custom.ticker }}</h3>
                <p>
                    <strong>觸發型態：</strong> {{ custom.signals_text }} | 
                    <strong>成交金額：</strong> ${{ "{:,.0f}".format(custom.latest_turnover or 0) }} |
                    <a href="https://www.tradingview.com/chart/?symbol={{ custom.tv_symbol }}" target="_blank" class="tv-btn">開啟 TradingView 圖表 📈</a>
                </p>
            </div>
            {% endif %}

            <h2>📋 檢查結果清單 ( Top 50 成交量/額 聯集去重結果 )</h2>
            <table>
                <thead>
                    <tr>
                        <th>圖例標籤</th>
                        <th>股票代號</th>
                        <th>最新價</th>
                        <th>成交量</th>
                        <th>成交金額</th>
                        <th>指定型態與指標</th>
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
