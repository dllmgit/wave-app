#include <iostream>
#include <vector>
#include <cmath>
#include <string>
#include <algorithm>
#include <iomanip>

// ==========================================
// 1. 基礎 K 棒結構與擴展數據
// ==========================================
struct KBar {
    int64_t index;
    double open, high, low, close;

    double body() const { return std::abs(close - open); }
    double upper_shadow() const { return high - std::max(open, close); }
    double lower_shadow() const { return std::min(open, close) - low; }
    double range() const { return high - low; }
    bool is_bull() const { return close > open; }
    bool is_bear() const { return close < open; }
};

struct Pivot {
    int64_t index;
    double price;
    bool is_high;
};

struct GeometricLine {
    int64_t x1; double y1;
    int64_t x2; double y2;
    double slope;
    std::string line_type;
};

struct PatternResult {
    std::string category; // "CANDLESTICK", "CHART_PATTERN"
    std::string name;
    int64_t index;
    std::string detail;
};

// ==========================================
// 2. 全功能 K 線與幾何形態核心引擎
// ==========================================
class UltimatePatternEngine {
private:
    int p_len_;
    double tolerance_;
    std::vector<Pivot> ph_list_;
    std::vector<Pivot> pl_list_;

public:
    UltimatePatternEngine(int p_len = 5, double tolerance = 0.015)
        : p_len_(p_len), tolerance_(tolerance) {}

    // A. 獨立 K 線組合形態偵測 (全套)
    std::vector<PatternResult> detect_candlestick_patterns(const std::vector<KBar>& bars) {
        std::vector<PatternResult> results;
        int n = static_cast<int>(bars.size());
        if (n < 1) return results;

        // --- 單棒形態 (嚴格 1:3 影線比) ---
        for (int i = 0; i < n; ++i) {
            const auto& c = bars[i];
            double b = (c.body() == 0) ? 0.0001 : c.body();

            // 1. 鎚頭 (Hammer): 底部下影線 >= 3*實體
            if (c.lower_shadow() >= b * 3.0 && c.upper_shadow() <= b * 0.5) {
                results.push_back({"CANDLESTICK", "HAMMER", c.index, "鎚頭 (下影線>=3倍實體)"});
            }
            // 2. 倒轉鎚頭 (Inverted Hammer): 底部上影線 >= 3*實體
            if (c.upper_shadow() >= b * 3.0 && c.lower_shadow() <= b * 0.5) {
                results.push_back({"CANDLESTICK", "INVERTED_HAMMER", c.index, "倒轉鎚頭 (上影線>=3倍實體)"});
            }
            // 3. 吊人線 (Hanging Man): 高位下影線 >= 3*實體
            if (c.lower_shadow() >= b * 3.0 && c.upper_shadow() <= b * 0.5) {
                results.push_back({"CANDLESTICK", "HANGING_MAN", c.index, "吊人線 (高位下影線>=3倍實體)"});
            }
            // 4. 流星線 (Shooting Star): 高位上影線 >= 3*實體
            if (c.upper_shadow() >= b * 3.0 && c.lower_shadow() <= b * 0.5) {
                results.push_back({"CANDLESTICK", "SHOOTING_STAR", c.index, "流星線 (高位上影線>=3倍實體)"});
            }
            // 5. 十字星 (Doji): 實體極小
            if (c.body() <= c.range() * 0.05) {
                results.push_back({"CANDLESTICK", "DOJI", c.index, "十字星"});
            }
        }

        // --- 兩棒形態 ---
        for (int i = 1; i < n; ++i) {
            const auto& c1 = bars[i - 1];
            const auto& c2 = bars[i];

            // 6. 看漲吞噬 (Bullish Engulfing)
            if (c1.is_bear() && c2.is_bull() && c2.close > c1.open && c2.open < c1.close) {
                results.push_back({"CANDLESTICK", "BULLISH_ENGULFING", c2.index, "看漲吞噬"});
            }
            // 7. 看跌吞噬 (Bearish Engulfing)
            if (c1.is_bull() && c2.is_bear() && c2.close < c1.open && c2.open > c1.close) {
                results.push_back({"CANDLESTICK", "BEARISH_ENGULFING", c2.index, "看跌吞噬"});
            }
        }

        // --- 三棒形態 ---
        for (int i = 2; i < n; ++i) {
            const auto& c1 = bars[i - 2];
            const auto& c2 = bars[i - 1];
            const auto& c3 = bars[i];

            // 8. 早晨之星 (Morning Star): 長陰 -> 小星線 -> 深入第一棒實體過半之長陽
            bool m_c1 = c1.is_bear() && (c1.body() >= c1.range() * 0.5);
            bool m_c2 = c2.body() <= (c1.body() * 0.3);
            bool m_c3 = c3.is_bull() && (c3.close >= c1.open - (c1.body() * 0.5));
            if (m_c1 && m_c2 && m_c3) {
                results.push_back({"CANDLESTICK", "MORNING_STAR", c3.index, "早晨之星"});
            }

            // 9. 黃昏之星 (Evening Star): 長陽 -> 小星線 -> 深入第一棒實體過半之長陰
            bool e_c1 = c1.is_bull() && (c1.body() >= c1.range() * 0.5);
            bool e_c2 = c2.body() <= (c1.body() * 0.3);
            bool e_c3 = c3.is_bear() && (c3.close <= c1.open + (c1.body() * 0.5));
            if (e_c1 && e_c2 && e_c3) {
                results.push_back({"CANDLESTICK", "EVENING_STAR", c3.index, "黃昏之星"});
            }
        }

        return results;
    }

    // B. 圖表大型幾何形態 (馬頭/雙頂底、頭肩頂底、紅線通道、趨勢線)
    void process_pivots(const std::vector<KBar>& bars) {
        ph_list_.clear(); pl_list_.clear();
        int n = static_cast<int>(bars.size());
        if (n < 2 * p_len_ + 1) return;

        for (int i = p_len_; i < n - p_len_; ++i) {
            bool is_ph = true, is_pl = true;
            for (int j = i - p_len_; j <= i + p_len_; ++j) {
                if (j != i && bars[j].high >= bars[i].high) is_ph = false;
                if (j != i && bars[j].low <= bars[i].low) is_pl = false;
            }
            if (is_ph) ph_list_.push_back({bars[i].index, bars[i].high, true});
            if (is_pl) pl_list_.push_back({bars[i].index, bars[i].low, false});
        }
    }

    std::vector<PatternResult> detect_chart_patterns() {
        std::vector<PatternResult> results;

        // 1. 馬頭頂 (雙頂) / 馬頭底 (雙底)
        if (ph_list_.size() >= 2) {
            auto h1 = ph_list_[ph_list_.size() - 2], h2 = ph_list_.back();
            if (std::abs(h1.price - h2.price) / h1.price <= tolerance_) {
                results.push_back({"CHART_PATTERN", "HORSE_HEAD_TOP", h2.index, "馬頭 (雙頂)"});
            }
        }
        if (pl_list_.size() >= 2) {
            auto l1 = pl_list_[pl_list_.size() - 2], l2 = pl_list_.back();
            if (std::abs(l1.price - l2.price) / l1.price <= tolerance_) {
                results.push_back({"CHART_PATTERN", "HORSE_HEAD_BOTTOM", l2.index, "馬頭 (雙底)"});
            }
        }

        // 2. 頭肩頂 / 頭肩底
        if (pl_list_.size() >= 3 && !ph_list_.empty()) {
            auto ls = pl_list_[pl_list_.size() - 3], head = pl_list_[pl_list_.size() - 2], rs = pl_list_.back();
            auto neck = ph_list_.back();
            if (head.price < ls.price && head.price < rs.price && neck.index > ls.index && neck.index < rs.index) {
                results.push_back({"CHART_PATTERN", "HEAD_AND_SHOULDERS_BOTTOM", rs.index, "頭肩底"});
            }
        }
        if (ph_list_.size() >= 3 && !pl_list_.empty()) {
            auto ls = ph_list_[ph_list_.size() - 3], head = ph_list_[ph_list_.size() - 2], rs = ph_list_.back();
            auto neck = pl_list_.back();
            if (head.price > ls.price && head.price > rs.price && neck.index > ls.index && neck.index < rs.index) {
                results.push_back({"CHART_PATTERN", "HEAD_AND_SHOULDERS_TOP", rs.index, "頭肩頂"});
            }
        }

        return results;
    }

    // C. 紅線通道辨識
    bool detect_red_channel(const std::vector<KBar>& bars, GeometricLine& bot, GeometricLine& top, GeometricLine& mid) {
        if (pl_list_.size() < 2) return false;
        Pivot l2 = pl_list_.back(), l1 = pl_list_[pl_list_.size() - 2];
        if (l2.price <= l1.price || l2.index <= l1.index) return false;

        double slope = (l2.price - l1.price) / static_cast<double>(l2.index - l1.index);
        double mid_max_y = -1.0; int64_t mid_max_x = -1;

        for (const auto& b : bars) {
            if (b.index >= l1.index && b.index <= l2.index && b.high > mid_max_y) {
                mid_max_y = b.high; mid_max_x = b.index;
            }
        }
        if (mid_max_x == -1) return false;
        int64_t cur_x = bars.back().index;

        bot = {l1.index, l1.price, cur_x, l1.price + slope * (cur_x - l1.index), slope, "CHANNEL_BOT"};
        top = {mid_max_x, mid_max_y, cur_x, mid_max_y + slope * (cur_x - mid_max_x), slope, "CHANNEL_TOP"};
        
        double mid_start = (l1.price + (mid_max_y - slope * (mid_max_x - l1.index))) / 2.0;
        mid = {l1.index, mid_start, cur_x, mid_start + slope * (cur_x - l1.index), slope, "CHANNEL_MID"};
        return true;
    }
};

// ==========================================
// 3. 執行測試
// ==========================================
int main() {
    std::vector<KBar> bars;
    for (int64_t i = 0; i < 100; ++i) {
        double p = 20000.0 + i * 50.0 + std::sin(i * 0.3) * 300.0;
        bars.push_back({i, p - 20, p + 80, p - 80, p + 30});
    }

    UltimatePatternEngine engine(5, 0.02);
    engine.process_pivots(bars);

    auto candle_patterns = engine.detect_candlestick_patterns(bars);
    auto chart_patterns = engine.detect_chart_patterns();

    GeometricLine bot, top, mid;
    bool has_channel = engine.detect_red_channel(bars, bot, top, mid);

    std::cout << "{\n  \"status\": \"ALL_PATTERNS_LOADED\",\n";
    std::cout << "  \"candlestick_patterns_count\": " << candle_patterns.size() << ",\n";
    std::cout << "  \"chart_patterns_count\": " << chart_patterns.size() << ",\n";
    std::cout << "  \"red_channel_active\": " << (has_channel ? "true" : "false") << "\n}";

    return 0;
}
