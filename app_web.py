import json
import os
import subprocess
from flask import Flask, jsonify
import requests

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID")


def run_cpp_and_get_data():
    # 執行 C++ 引擎輸出 JSON
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

    return jsonify({"status": "success", "data": data})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
