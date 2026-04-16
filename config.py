"""
Smart Stock Screener v3.0 — 설정 파일
"""
import os
 
# ═══════════════════════════════════════
# API 키 (GitHub Secrets에서 자동으로 가져옴)
# ═══════════════════════════════════════
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
 
# ═══════════════════════════════════════
# 스코어카드 기준
# ═══════════════════════════════════════
 
# 기본적 분석 (30점 만점)
FUNDAMENTAL_CRITERIA = {
    "min_revenue_growth": 0.10,      # 최소 매출 성장률 10%
    "min_roe": 0.15,                 # 최소 ROE 15%
    "max_debt_ratio": 2.0,           # 최대 부채비율 200%
    "min_market_cap_us": 2_000_000_000,    # 미국 최소 시총 $2B
    "min_market_cap_kr": 300_000_000_000,  # 한국 최소 시총 3000억원
}
 
# 기술적 분석 (9점 만점)
TECHNICAL_CRITERIA = {
    "rsi_buy_threshold": 50,          # RSI 매수 기준
    "rsi_overbought": 80,             # RSI 과매수 경고
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "bb_length": 20,
    "bb_std": 2,
    "ma_short": 20,
    "ma_mid": 50,
    "ma_long": 200,
    "ichimoku_tenkan": 9,
    "ichimoku_kijun": 26,
    "ichimoku_senkou": 52,
}
 
# 종합점수 가중치 (적극형)
WEIGHT_FUNDAMENTAL = 55  # 기본적 55%
WEIGHT_TECHNICAL = 45    # 기술적 45%
 
# 리스크 관리
RISK_MANAGEMENT = {
    "max_single_stock": 0.20,         # 1종목 최대 20%
    "max_single_sector": 0.40,        # 1섹터 최대 40%
    "max_stocks": 10,                 # 최대 보유 종목 수
    "min_cash": 0.10,                 # 최소 현금 비중 10%
    "stop_loss": -0.10,              # 손절 -10%
}
 
# 출력 설정
TOP_N = 5  # 각 시장별 Top N 종목
