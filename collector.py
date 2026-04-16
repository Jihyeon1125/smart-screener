"""
Smart Stock Screener v3.0 — 데이터 수집 + 기술적 지표 계산
"""
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from pykrx import stock as pykrx_stock
from datetime import datetime, timedelta
 
 
def collect_us_stock(ticker):
    """미국 종목 데이터 수집"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 주가 데이터
        daily = stock.history(period="1y", interval="1d")
        weekly = stock.history(period="2y", interval="1wk")
        
        if len(daily) < 60 or len(weekly) < 30:
            return None
        
        # 기본 정보
        result = {
            "ticker": ticker,
            "name": info.get("shortName", ticker),
            "market": "US",
            "price": daily["Close"].iloc[-1],
            "market_cap": info.get("marketCap", 0),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            
            # 재무 데이터
            "revenue_growth": info.get("revenueGrowth", 0) or 0,
            "earnings_growth": info.get("earningsGrowth", 0) or 0,
            "roe": info.get("returnOnEquity", 0) or 0,
            "profit_margin": info.get("profitMargins", 0) or 0,
            "operating_margin": info.get("operatingMargins", 0) or 0,
            "debt_to_equity": (info.get("debtToEquity", 0) or 0) / 100,
            "free_cashflow": info.get("freeCashflow", 0) or 0,
            "pe_ratio": info.get("trailingPE", 0) or 0,
            "peg_ratio": info.get("pegRatio", 0) or 0,
        }
        
        # 기술적 지표 계산
        technicals = calculate_technicals(daily, weekly)
        result.update(technicals)
        
        return result
        
    except Exception as e:
        print(f"  ❌ {ticker} 수집 실패: {e}")
        return None
 
 
def collect_kr_stock(code, name=""):
    """한국 종목 데이터 수집"""
    try:
        end_date = datetime.now().strftime("%Y%m%d")
        daily_start = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        weekly_start = (datetime.now() - timedelta(days=730)).strftime("%Y%m%d")
        
        # 일봉 데이터
        daily = pykrx_stock.get_market_ohlcv(daily_start, end_date, code)
        if len(daily) < 60:
            return None
        
        # 주봉 데이터 생성 (일봉에서 리샘플링)
        daily.index = pd.to_datetime(daily.index)
        weekly = daily.resample("W").agg({
            "시가": "first",
            "고가": "max",
            "저가": "min",
            "종가": "last",
            "거래량": "sum",
        }).dropna()
        
        if len(weekly) < 30:
            return None
        
        # 재무 데이터 (FinanceDataReader 또는 yfinance)
        try:
            yf_ticker = yf.Ticker(f"{code}.KS")
            info = yf_ticker.info
            revenue_growth = info.get("revenueGrowth", 0) or 0
            earnings_growth = info.get("earningsGrowth", 0) or 0
            roe = info.get("returnOnEquity", 0) or 0
            operating_margin = info.get("operatingMargins", 0) or 0
            debt_to_equity = (info.get("debtToEquity", 0) or 0) / 100
            free_cashflow = info.get("freeCashflow", 0) or 0
            pe_ratio = info.get("trailingPE", 0) or 0
            peg_ratio = info.get("pegRatio", 0) or 0
            market_cap = info.get("marketCap", 0) or 0
            sector = info.get("sector", "Unknown")
            industry = info.get("industry", "Unknown")
        except:
            # yfinance 실패 시 기본값
            revenue_growth = 0
            earnings_growth = 0
            roe = 0
            operating_margin = 0
            debt_to_equity = 0
            free_cashflow = 0
            pe_ratio = 0
            peg_ratio = 0
            market_cap = 0
            sector = "Unknown"
            industry = "Unknown"
        
        # 일봉 컬럼명 통일 (pandas-ta 호환)
        daily_renamed = daily.rename(columns={
            "시가": "Open", "고가": "High",
            "저가": "Low", "종가": "Close",
            "거래량": "Volume"
        })
        weekly_renamed = weekly.rename(columns={
            "시가": "Open", "고가": "High",
            "저가": "Low", "종가": "Close",
            "거래량": "Volume"
        })
        
        result = {
            "ticker": code,
            "name": name or pykrx_stock.get_market_ticker_name(code),
            "market": "KR",
            "price": daily["종가"].iloc[-1],
            "market_cap": market_cap,
            "sector": sector,
            "industry": industry,
            "revenue_growth": revenue_growth,
            "earnings_growth": earnings_growth,
            "roe": roe,
            "profit_margin": 0,
            "operating_margin": operating_margin,
            "debt_to_equity": debt_to_equity,
            "free_cashflow": free_cashflow,
            "pe_ratio": pe_ratio,
            "peg_ratio": peg_ratio,
        }
        
        # 기술적 지표 계산
        technicals = calculate_technicals(daily_renamed, weekly_renamed)
        result.update(technicals)
        
        return result
        
    except Exception as e:
        print(f"  ❌ {code} 수집 실패: {e}")
        return None
 
 
def calculate_technicals(daily, weekly):
    """기술적 지표 계산 (일봉 + 주봉 이중 타임프레임)"""
    
    result = {}
    
    # ═══════════════════════════════════
    # 일봉(Daily) 지표
    # ═══════════════════════════════════
    
    close_d = daily["Close"]
    high_d = daily["High"]
    low_d = daily["Low"]
    current_price = close_d.iloc[-1]
    
    # --- RSI (14) ---
    try:
        rsi_series = ta.rsi(close_d, length=14)
        result["rsi_daily"] = round(rsi_series.iloc[-1], 2)
    except:
        result["rsi_daily"] = 50.0
    
    # --- MACD (12, 26, 9) ---
    try:
        macd_df = ta.macd(close_d, fast=12, slow=26, signal=9)
        macd_line = macd_df.iloc[-1, 0]
        signal_line = macd_df.iloc[-1, 2]
        result["macd_value"] = round(macd_line, 4)
        result["macd_signal"] = round(signal_line, 4)
        result["macd_golden"] = macd_line > signal_line
        result["macd_above_zero"] = macd_line > 0
    except:
        result["macd_value"] = 0
        result["macd_signal"] = 0
        result["macd_golden"] = False
        result["macd_above_zero"] = False
    
    # --- 볼린저밴드 (20, 2) ---
    try:
        bb = ta.bbands(close_d, length=20, std=2)
        bb_upper = bb.iloc[-1, 0]
        bb_mid = bb.iloc[-1, 1]
        bb_lower = bb.iloc[-1, 2]
        result["bb_upper"] = round(bb_upper, 2)
        result["bb_mid"] = round(bb_mid, 2)
        result["bb_lower"] = round(bb_lower, 2)
        
        if current_price > bb_upper:
            result["bb_position"] = "above_upper"
        elif current_price > bb_mid:
            result["bb_position"] = "above_mid"
        elif current_price > bb_lower:
            result["bb_position"] = "below_mid"
        else:
            result["bb_position"] = "below_lower"
    except:
        result["bb_position"] = "unknown"
    
    # --- 이동평균선 (20, 50, 200) ---
    try:
        ma20 = ta.sma(close_d, length=20).iloc[-1]
        ma50 = ta.sma(close_d, length=50).iloc[-1]
        
        ma200_series = ta.sma(close_d, length=200)
        if len(ma200_series.dropna()) > 0:
            ma200 = ma200_series.iloc[-1]
        else:
            ma200 = 0
        
        result["ma20"] = round(ma20, 2)
        result["ma50"] = round(ma50, 2)
        result["ma200"] = round(ma200, 2) if ma200 else 0
        
        if ma200 and ma20 > ma50 > ma200:
            # 기울기 확인
            ma20_prev = ta.sma(close_d, length=20).iloc[-5]
            ma50_prev = ta.sma(close_d, length=50).iloc[-5]
            if ma20 > ma20_prev and ma50 > ma50_prev:
                result["ma_alignment"] = "perfect"
            else:
                result["ma_alignment"] = "partial"
        elif ma20 > ma50:
            result["ma_alignment"] = "partial"
        else:
            result["ma_alignment"] = "none"
    except:
        result["ma_alignment"] = "none"
    
    # ═══════════════════════════════════
    # 주봉(Weekly) 지표 — 일목균형표
    # ═══════════════════════════════════
    
    try:
        close_w = weekly["Close"]
        high_w = weekly["High"]
        low_w = weekly["Low"]
        weekly_price = close_w.iloc[-1]
        
        # 일목균형표 수동 계산
        # 전환선 (9주)
        tenkan = (high_w.rolling(9).max() + low_w.rolling(9).min()) / 2
        # 기준선 (26주)
        kijun = (high_w.rolling(26).max() + low_w.rolling(26).min()) / 2
        # 선행스팬A
        senkou_a = ((tenkan + kijun) / 2).shift(26)
        # 선행스팬B (52주)
        senkou_b = ((high_w.rolling(52).max() + low_w.rolling(52).min()) / 2).shift(26)
        
        # 현재 구름대 값
        current_senkou_a = senkou_a.iloc[-1] if not pd.isna(senkou_a.iloc[-1]) else 0
        current_senkou_b = senkou_b.iloc[-1] if not pd.isna(senkou_b.iloc[-1]) else 0
        current_tenkan = tenkan.iloc[-1] if not pd.isna(tenkan.iloc[-1]) else 0
        current_kijun = kijun.iloc[-1] if not pd.isna(kijun.iloc[-1]) else 0
        
        cloud_top = max(current_senkou_a, current_senkou_b)
        cloud_bottom = min(current_senkou_a, current_senkou_b)
        
        result["ichimoku_tenkan"] = round(current_tenkan, 2)
        result["ichimoku_kijun"] = round(current_kijun, 2)
        result["ichimoku_cloud_top"] = round(cloud_top, 2)
        result["ichimoku_cloud_bottom"] = round(cloud_bottom, 2)
        result["tenkan_above_kijun"] = current_tenkan > current_kijun
        
        if weekly_price > cloud_top:
            result["ichimoku_position"] = "above"
        elif weekly_price > cloud_bottom:
            result["ichimoku_position"] = "inside"
        else:
            result["ichimoku_position"] = "below"
    except:
        result["ichimoku_position"] = "unknown"
        result["tenkan_above_kijun"] = False
    
    return result
