"""
Smart Stock Screener v3.0 — 스코어카드 자동 채점
"""
from config import WEIGHT_FUNDAMENTAL, WEIGHT_TECHNICAL


def score_fundamental(stock):
    scores = {}
    total = 0
    rev_g = abs(stock.get("revenue_growth", 0)) * 100
    if rev_g >= 30:
        s = 5
    elif rev_g >= 20:
        s = 4
    elif rev_g >= 15:
        s = 3
    elif rev_g >= 10:
        s = 2
    else:
        s = 1
    scores["산업매력도"] = s
    total += s
    rev_pct = stock.get("revenue_growth", 0) * 100
    if rev_pct >= 50:
        s = 5
    elif rev_pct >= 30:
        s = 4
    elif rev_pct >= 20:
        s = 3
    elif rev_pct >= 10:
        s = 2
    else:
        s = 1
    scores["매출성장"] = f"{rev_pct:.1f}% -> {s}점"
    total += s
    earn_pct = stock.get("earnings_growth", 0) * 100
    if earn_pct >= 50:
        s = 5
    elif earn_pct >= 30:
        s = 4
    elif earn_pct >= 20:
        s = 3
    elif earn_pct >= 15:
        s = 2
    else:
        s = 1
    scores["이익성장"] = f"{earn_pct:.1f}% -> {s}점"
    total += s
    roe_pct = stock.get("roe", 0) * 100
    if roe_pct >= 30:
        s = 5
    elif roe_pct >= 25:
        s = 4
    elif roe_pct >= 20:
        s = 3
    elif roe_pct >= 15:
        s = 2
    else:
        s = 1
    scores["수익성"] = f"ROE {roe_pct:.1f}% -> {s}점"
    total += s
    debt = stock.get("debt_to_equity", 0)
    fcf = stock.get("free_cashflow", 0)
    if debt <= 0.3 and fcf > 0:
        s = 5
    elif debt <= 0.5 and fcf > 0:
        s = 4
    elif debt <= 1.0:
        s = 3
    elif debt <= 1.5:
        s = 2
    else:
        s = 1
    scores["재무건전"] = f"부채 {debt:.1%} -> {s}점"
    total += s
    mcap = stock.get("market_cap", 0)
    margin = stock.get("operating_margin", 0) * 100
    if mcap > 100_000_000_000 and margin > 25:
        s = 5
    elif mcap > 50_000_000_000 and margin > 20:
        s = 4
    elif mcap > 10_000_000_000 and margin > 15:
        s = 3
    elif mcap > 2_000_000_000:
        s = 2
    else:
        s = 1
    scores["경쟁우위"] = f"시총기반 -> {s}점"
    total += s
    if total >= 24:
        signal = "green"
    elif total >= 18:
        signal = "yellow"
    elif total >= 15:
        signal = "orange"
    else:
        signal = "red"
    return total, signal, scores


def score_technical(stock):
    scores = {}
    total = 0
    ichimoku = stock.get("ichimoku_position", "unknown")
    tenkan_above = stock.get("tenkan_above_kijun", False)
    if ichimoku == "above":
        s = 2
        desc = "구름대 위"
    elif ichimoku == "inside":
        s = 1
        if tenkan_above:
            s = 1.5
            desc = "구름대 내부 (전환>기준)"
        else:
            desc = "구름대 내부"
    else:
        s = 0
        desc = "구름대 아래"
    scores["일목(주봉)"] = f"{desc} -> {s}점"
    total += s
    ichimoku_veto = (ichimoku == "below")
    bb_pos = stock.get("bb_position", "unknown")
    if bb_pos == "above_upper":
        s = 2
        desc = "상단밴드 워킹"
    elif bb_pos == "above_mid":
        s = 1
        desc = "중심선 위"
    elif bb_pos == "below_mid":
        s = 0
        desc = "중심선 아래"
    else:
        s = -1
        desc = "하단밴드 이탈"
    scores["볼린저(일봉)"] = f"{desc} -> {s}점"
    total += s
    macd_golden = stock.get("macd_golden", False)
    macd_above = stock.get("macd_above_zero", False)
    if macd_golden and macd_above:
        s = 2
        desc = "골든크로스 + 0선위"
    elif macd_golden or macd_above:
        s = 1
        desc = "부분 충족"
    else:
        s = 0
        desc = "데드크로스/0선아래"
    scores["MACD(일봉)"] = f"{desc} -> {s}점"
    total += s
    rsi = stock.get("rsi_daily", 50)
    if rsi > 50:
        s = 1
        desc = f"RSI {rsi:.1f}"
    else:
        s = 0
        desc = f"RSI {rsi:.1f}"
    scores["RSI(일봉)"] = f"{desc} -> {s}점"
    total += s
    ma_align = stock.get("ma_alignment", "none")
    if ma_align == "perfect":
        s = 2
        desc = "완벽 정배열"
    elif ma_align == "partial":
        s = 1
        desc = "부분 정배열"
    else:
        s = 0
        desc = "역배열/수렴"
    scores["이평선(일봉)"] = f"{desc} -> {s}점"
    total += s
    if total >= 7:
        signal = "green"
    elif total >= 4:
        signal = "yellow"
    else:
        signal = "red"
    if ichimoku_veto:
        signal = "red"
    return total, signal, scores, ichimoku_veto


def score_total(fund_score, tech_score):
    total = (fund_score / 30 * WEIGHT_FUNDAMENTAL) + (tech_score / 9 * WEIGHT_TECHNICAL)
    total = round(total, 1)
    if total >= 80:
        signal = "green"
        action = "적극 매수"
    elif total >= 65:
        signal = "yellow"
        action = "조건부 매수"
    elif total >= 50:
        signal = "orange"
        action = "관심 목록"
    else:
        signal = "red"
        action = "매수 불가"
    return total, signal, action
