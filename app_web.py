import os
import ctypes
import pandas as pd
import yfinance as yf
import requests

# ---------------------------------------------------------
# 1. 配置 Telegram Bot 資訊
# ---------------------------------------------------------
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "＠Peter5041"

# ---------------------------------------------------------
# 2. 載入 C++ 動態連結庫 (DLL / .so)
# ---------------------------------------------------------
class PatternResult(ctypes.Structure):
    _fields_ = [
        ("is_valid", ctypes.c_bool),
        ("pattern_type", ctypes.c_char_p),
        ("neckline_price", ctypes.c_double)
    ]

# 載入 compiled C++ 庫
pattern_lib = ctypes.CDLL('./libpattern.so')
pattern_lib.analyze_hs_pattern.argtypes = [
    ctypes.POINTER(ctypes.c_double),
    ctypes.POINTER(ctypes.c_double),
    ctypes.POINTER(ctypes.c_double),
    ctypes.c_int
]
pattern_lib.analyze_hs_pattern.restype = PatternResult

# ---------------------------------------------------------
# 3. 定義監控標的清單 (Top 50 美股/港股、商品、BTC、外匯)
# ---------------------------------------------------------
WATCHLIST = {
    "🇭🇰 港股 Top 50": ["0700.HK", "9988.HK", "3690.HK", "1810.HK", "0939.HK", "1299.HK", "2318.HK"],
    "🇺🇸 美股 Top 50": ["NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "AMD"],
    "🪙 大宗商品 & Crypto": ["BTC-USD", "ETH-USD", "GC=F", "CL=F", "SI=F", "HG=F"],
    "💱 外匯交叉盤 Top 10": ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "EURGBP=X", "EURJPY=X", "GBPJPY=X"]
}

# ---------------------------------------------------------
# 4. Telegram 發送函式
# ---------------------------------------------------------
def send_telegram_msg(category, symbol, pattern_type, neckline):
    message = (
        f"🚨 **【X浪 / 頭肩形態觸發通知】**\n\n"
        f"📌 **類別**：{category}\n"
        f"📈 **標的代碼**：`{symbol}`\n"
        f"⚠️ **形態辨識**：{pattern_type}\n"
        f"🎯 **關鍵頸線位**：${neckline:.2f}\n\n"
        f"📲 *請打開 TradingView 輸入 `{symbol}` 載入 Pine Script 確認 K 線圖。*"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram 推播失敗: {e}")

# ---------------------------------------------------------
# 5. 主執行邏輯 (批次掃描，用完即關)
# ---------------------------------------------------------
def run_scan():
    print("🚀 開始掃描全球市場標的...")
    
    for category, symbols in WATCHLIST.items():
        for symbol in symbols:
            try:
                # 抓取最近 60 根 1小時 K線
                df = yf.Ticker(symbol).history(period="10d", interval="1h")
                if df.empty or len(df) < 20:
                    continue
                
                highs = (ctypes.c_double * len(df))(*df['High'].tolist())
                lows = (ctypes.c_double * len(df))(*df['Low'].tolist())
                closes = (ctypes.c_double * len(df))(*df['Close'].tolist())
                
                # 呼叫 C++ 底層運算 (極速)
                res = pattern_lib.analyze_hs_pattern(highs, lows, closes, len(df))
                
                if res.is_valid:
                    pattern_name = res.pattern_type.decode('utf-8')
                    print(f"✅ 發現形態！[{symbol}] -> {pattern_name}")
                    send_telegram_msg(category, symbol, pattern_name, res.neckline_price)
            except Exception as e:
                print(f"跳過 {symbol}: {e}")

    print("🏁 掃描完成，釋放記憶體。")

if __name__ == "__main__":
    run_scan()
