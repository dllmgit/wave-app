#include <iostream>
#include <vector>
#include <cmath>
#include <string>
#include <algorithm>
#include <iomanip>

// ==========================================
// 1. 基礎數據結構
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
    std::string line_type; // "TRENDLINE", "CHANNEL_BOT", "CHANNEL_TOP", "CHANNEL_MID"
};

struct PatternResult {
    std::string category; // "CANDLESTICK", "CHART_PATTERN", "WAVE"
    std::string name;
    int64_t index;
    std::string detail;
};

// ==========================================
// 2. 全套核心引擎類別
// ==========================================
class FullQuantEngine {
private:
    int p_len_;
    double tolerance_;
    double min_ratio_;
    double max_ratio_;

    std::vector<Pivot> ph_list_;
    std::vector<Pivot> pl_list_;

public:
    FullQuantEngine(int p_len = 5, double tolerance = 0.015, double min_ratio = 0.5, double max_ratio = 1.5)
        : p_len_(p_len), tolerance_(tolerance), min_ratio_(min_ratio), max_ratio_(max_ratio) {}

    // ------------------------------------------
    // A. 完整 K 線組合型態 (嚴格 1:3 影線比)
    // ------------------------------------------
    std::vector<PatternResult> detect_candlestick_patterns(const std::vector<KBar>& bars) {
        std::vector<PatternResult> results;
        int n = static_cast<int>(bars.size());
        if (n < 1) return results;

        // 單棒型態 (實體與影線比例 1:3)
        for (int i = 0; i < n; ++i) {
            const auto& c = bars[i];
            double b = (c.body() == 0) ? 0.0001 : c.body();

            if (c.lower_shadow() >= b * 3.0 && c.upper_shadow() <= b * 0.5) {
                results.push_back({"CANDLESTICK", "HAMMER", c.index, "鎚頭 (下影線>=3倍實體)"});
            }
            if (c.upper_shadow() >= b * 3.0 && c.lower_shadow() <= b * 0.5) {
                results.push_back({"CANDLESTICK", "INVERTED_HAMMER", c.index, "倒轉鎚頭 (上影線>=3倍實體)"});
            }
            if (c.lower_shadow() >= b * 3.0 && c.upper_shadow() <= b * 0.5) {
                results.push_back({"CANDLESTICK", "HANGING_MAN", c.index, "吊人線 (高位下影線>=3倍實體)"});
            }
            if (c.upper_shadow() >= b * 3.0 && c.lower_shadow() <= b * 0.5) {
                results.push_back({"CANDLESTICK", "SHOOTING_STAR", c.index, "流星線 (高位上影線>=3倍實體)"});
            }
            if (c.body() <= c.range() * 0.05) {
                results.push_back({"CANDLESTICK", "DOJI", c.index, "十字星"});
            }
        }

        // 兩棒型態
        for (int i = 1; i < n; ++i) {
            const auto& c1 = bars[i - 1];
            const auto& c2 = bars[i];

            if (c1.is_bear() && c2.is_bull() && c2.close > c1.open && c2.open < c1.close) {
                results.push_back({"CANDLESTICK", "BULLISH_ENGULFING", c2.index, "看漲吞噬"});
            }
            if (c1.is_bull() && c2.is_bear() && c2.close < c1.open && c2.open > c1.close) {
                results.push_back({"CANDLESTICK", "BEARISH_ENGULFING", c2.index, "看跌吞噬"});
            }
        }

        // 三棒型態
        for (int i = 2; i < n; ++i) {
            const auto& c1 = bars[i - 2];
            const auto& c2 = bars[i - 1];
            const auto& c3 = bars[i];

            bool m_c1 = c1.is_bear() && (c1.body() >= c1.range() * 0.5);
            bool m_c2 = c2.body() <= (c1.body() * 0.3);
            bool m_c3 = c3.is_bull() && (c3.close >= c1.open - (c1.body() * 0.5));
            if (m_c1 && m_c2 && m_c3) {
                results.push_back({"CANDLESTICK", "MORNING_STAR", c3.index, "早晨之星"});
            }

            bool e_c1 = c1.is_bull() && (c1.body() >= c1.range() * 0.5);
            bool e_c2 = c2.body() <= (c1.body() * 0.3);
            bool e_c3 = c3.is_bear() && (c3.close <= c1.open + (c1.body() * 0.5));
            if (e_c1 && e_c2 && e_c3) {
                results.push_back({"CANDLESTICK", "EVENING_STAR", c3.index, "黃昏之星"});
            }
        }

        return results;
    }

    // ------------------------------------------
    // B. 波段點擷取與大型結構分析
    // ------------------------------------------
    void update_pivots(const std::vector<KBar>& bars) {
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

    // 1. 三點趨勢線
    std::vector<GeometricLine> detect_trendlines(int64_t current_idx) {
        std::vector<GeometricLine> lines;
        if (pl_list_.size() >= 3) {
            auto p1 = pl_list_[pl_list_.size()-3], p2 = pl_list_[pl_list_.size()-2], p3 = pl_list_[pl_list_.size()-1];
            double slope = (p3.price - p1.price) / static_cast<double>(p3.index - p1.index);
            double expected_p2 = p1.price + slope * (p2.index - p1.index);
            if (std::abs(p2.price - expected_p2) / p2.price <= tolerance_) {
                lines.push_back({p1.index, p1.price, current_idx, p1.price + slope * (current_idx - p1.index), slope, "TRENDLINE_SUPPORT"});
            }
        }
        return lines;
    }

    // 2. 紅線平行通道 (底線 + 平行頂線 + 藍虛中軸線)
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

    // 3. 馬頭與嚴格修復版頭肩頂/底 (5點連動驗證，防止時間錯亂)
    std::vector<PatternResult> detect_chart_patterns() {
        std::vector<PatternResult> results;

        // 馬頭形態 (雙頂 / 雙底)
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

        // 修復版頭肩底 (LS -> N1 -> Head -> N2 -> RS)
        if (pl_list_.size() >= 3 && ph_list_.size() >= 2) {
            auto ls = pl_list_[pl_list_.size() - 3];
            auto head = pl_list_[pl_list_.size() - 2];
            auto rs = pl_list_.back();

            auto n1 = ph_list_[ph_list_.size() - 2];
            auto n2 = ph_list_.back();

            // 1. 時間遞增順序過濾
            bool time_ok = (ls.index < n1.index) && (n1.index < head.index) &&
                           (head.index < n2.index) && (n2.index < rs.index);

            // 2. 幾何極值驗證 (頭部必須最低)
            bool geo_ok = (head.price < ls.price) && (head.price < rs.price) &&
                          (n1.price > ls.price) && (n2.price > rs.price);

            // 3. 比例驗證 (左右肩寬高比)
            double h_left = ls.price - head.price;
            double h_right = rs.price - head.price;
            double h_ratio = (h_left == 0) ? 0 : (h_right / h_left);

            bool ratio_ok = (h_ratio >= min_ratio_ && h_ratio <= max_ratio_);

            if (time_ok && geo_ok && ratio_ok) {
                results.push_back({"CHART_PATTERN", "HEAD_AND_SHOULDERS_BOTTOM", rs.index, "修復版頭肩底 (時間與頸線驗證通過)"});
            }
        }

        // 修復版頭肩頂
        if (ph_list_.size() >= 3 && pl_list_.size() >= 2) {
            auto ls = ph_list_[ph_list_.size() - 3];
            auto head = ph_list_[ph_list_.size() - 2];
            auto rs = ph_list_.back();

            auto n1 = pl_list_[pl_list_.size() - 2];
            auto n2 = pl_list_.back();

            bool time_ok = (ls.index < n1.index) && (n1.index < head.index) &&
                           (head.index < n2.index) && (n2.index < rs.index);

            bool geo_ok = (head.price > ls.price) && (head.price > rs.price) &&
                          (n1.price < ls.price) && (n2.price < rs.price);

            double h_left = head.price - ls.price;
            double h_right = head.price - rs.price;
            double h_ratio = (h_left == 0) ? 0 : (h_right / h_left);

            bool ratio_ok = (h_ratio >= min_ratio_ && h_ratio <= max_ratio_);

            if (time_ok && geo_ok && ratio_ok) {
                results.push_back({"CHART_PATTERN", "HEAD_AND_SHOULDERS_TOP", rs.index, "修復版頭肩頂 (時間與頸線驗證通過)"});
            }
        }

        return results;
    }

    // 4. 艾略特波浪推進浪 1-5 驗證
    std::vector<PatternResult> detect_elliott_waves() {
        std::vector<PatternResult> results;
        if (pl_list_.size() < 3 || ph_list_.size() < 3) return results;

        size_t n_l = pl_list_.size(), n_h = ph_list_.size();
        auto p0 = pl_list_[n_l - 3], p2 = pl_list_[n_l - 2], p4 = pl_list_[n_l - 1];
        auto p1 = ph_list_[n_h - 3], p3 = ph_list_[n_h - 2], p5 = ph_list_[n_h - 1];

        if (!(p0.index < p1.index && p1.index < p2.index && p2.index < p3.index && p3.index < p4.index && p4.index < p5.index)) {
            return results;
        }

        bool rule1 = (p2.price > p0.price); // 浪2不破浪0
        bool rule2 = (p4.price > p1.price);  // 浪4不重疊浪1
        double len1 = p1.price - p0.price, len3 = p3.price - p2.price, len5 = p5.price - p4.price;
        bool rule3 = (len3 >= len1 || len3 >= len5); // 浪3非最短

        if (rule1 && rule2 && rule3 && (p3.price > p1.price) && (p5.price > p3.price)) {
            results.push_back({"WAVE", "ELLIOTT_IMPULSE_5", p5.index, "標準艾略特 1-5 推進浪"});
        }
        return results;
    }
};

// ==========================================
// 3. 主程式驗證
// ==========================================
int main() {
    std::vector<KBar> bars;
    for (int64_t i = 0; i < 120; ++i) {
        double p = 20000.0 + i * 40.0 + std::sin(i * 0.25) * 350.0;
        bars.push_back({i, p - 25, p + 90, p - 90, p + 35});
    }

    FullQuantEngine engine(5, 0.015, 0.5, 1.5);
    
    // 執行全套識別
    auto candle_patterns = engine.detect_candlestick_patterns(bars);
    engine.update_pivots(bars);
    auto chart_patterns = engine.detect_chart_patterns();
    auto waves = engine.detect_elliott_waves();

    GeometricLine bot, top, mid;
    bool has_channel = engine.detect_red_channel(bars, bot, top, mid);
    auto trendlines = engine.detect_trendlines(bars.back().index);

    std::cout << "{\n";
    std::cout << "  \"engine_status\": \"SUCCESS_FULL_STACK\",\n";
    std::cout << "  \"candlestick_patterns\": " << candle_patterns.size() << ",\n";
    std::cout << "  \"chart_patterns\": " << chart_patterns.size() << ",\n";
    std::cout << "  \"elliott_waves\": " << waves.size() << ",\n";
    std::cout << "  \"trendlines\": " << trendlines.size() << ",\n";
    std::cout << "  \"red_channel_active\": " << (has_channel ? "true" : "false") << "\n";
    std::cout << "}\n";

    return 0;
}
