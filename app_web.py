import json
import os
import subprocess
from flask import Flask, jsonify, render_template_string
import requests

app = Flask(__name__)

# 關閉 ASCII 轉義，確保 JSON 能正確顯示中文
app.json.ensure_ascii = False

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID")


def run_cpp_and_get_data():
    try:
        subprocess.run(["./pattern_engine"], check=True)
    except Exception as e:
        print(f"C++ Engine 執行失敗: {e}")
        return None

    if os.path.exists("result_top3.json"):
        with open("result_top3.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return None


@app.route("/")
def index():
    data = run_cpp_and_get_data()
    if not data:
        return jsonify({"status": "error", "message": "無法執行 C++ 引擎"}), 500

    scenarios = data.get("scenarios", [])

    # 發送 Telegram 通知
    if scenarios and TELEGRAM_BOT_TOKEN != "YOUR_TELEGRAM_BOT_TOKEN":
        top = scenarios[0]
        signals_str = ", ".join(
            [f"{s['type']}(Index {s['index']})" for s in top.get("signals", [])]
        )
        if not signals_str:
            signals_str = "無"

        msg = (
            f"🚨 **【波浪形態與 K 線全套算牌完成】**\n\n"
            f"🏆 **最佳方案**：{top['name']}\n"
            f"📈 **預估勝率**：{top['win_rate']}%\n"
            f"⚖️ **盈虧比**：{top['rr_ratio']}\n"
            f"🎯 **目標價 (W5)**：${top['target_w5']:.2f}\n"
            f"🛡️ **止損價**：${top['stop_loss']:.2f}\n"
            f"🔍 **觸發形態**：{signals_str}\n"
            f"📊 **Wave 3 爆量驗證**：{'通過 ✅' if top['w3_vol_pass'] else '未通過 ❌'}"
        )

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        try:
            requests.post(
                url,
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": msg,
                    "parse_mode": "Markdown",
                },
            )
        except Exception as e:
            print(f"Telegram 發送失敗: {e}")

    # 以美化過的 HTML 網頁呈現結果
    html_template = """
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>波浪形態算牌引擎</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #f4f6f9; padding: 20px; color: #333; }
            .container { max-width: 900px; margin: 0 auto; background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
            h1 { color: #1a365d; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
            .card { background: #f8fafc; border-left: 5px solid #3182ce; padding: 15px; margin-bottom: 20px; border-radius: 4px; }
            .card.rank-1 { border-left-color: #38a169; }
            .card h3 { margin-top: 0; color: #2d3748; }
            .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85em; }
            .badge-success { background: #c6f6d5; color: #22543d; }
            .badge-fail { background: #fed7d7; color: #742a2a; }
            pre { background: #1a202c; color: #63b3ed; padding: 15px; border-radius: 8px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 波浪形態與 K 線分析結果</h1>
            {% for s in scenarios %}
            <div class="card rank-{{ s.rank }}">
                <h3>Rank {{ s.rank }}: {{ s.name }}</h3>
                <p>
                    <strong>預估勝率：</strong> {{ s.win_rate }}% | 
                    <strong>盈虧比：</strong> {{ s.rr_ratio }} | 
                    <strong>目標價 (W5)：</strong> <span style="color: #2b6cb0;">${{ s.target_w5 }}</span> | 
                    <strong>止損價：</strong> <span style="color: #e53e3e;">${{ s.stop_loss }}</span>
                </p>
                <p>
                    <strong>Wave 3 爆量驗證：</strong> 
                    {% if s.w3_vol_pass %}
                        <span class="badge badge-success">通過 ✅</span>
                    {% else %}
                        <span class="badge badge-fail">未通過 ❌</span>
                    {% endif %}
                </p>
                <p><strong>觸發形態列表：</strong></p>
                <ul>
                    {% for sig in s.signals %}
                        <li>Index {{ sig.index }}: {{ sig.type }}</li>
                    {% else %}
                        <li>無特殊形態</li>
                    {% endfor %}
                </ul>
            </div>
            {% endfor %}

            <h2>📄 原始 JSON 數據</h2>
            <pre>{{ raw_json }}</pre>
        </div>
    </body>
    </html>
    """

    return render_template_string(
        html_template,
        scenarios=scenarios,
        raw_json=json.dumps(data, indent=2, ensure_ascii=False),
    )


@app.route("/api/data")
def get_raw_json():
    data = run_cpp_and_get_data()
    return jsonify(data)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
