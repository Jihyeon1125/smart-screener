"""
Smart Stock Screener v3.0 — 데이터 수집 + 기술적 지표 계산
"""
import yfinance as yf
import pandas as pd
from pykrx import stock as pykrx_stock
from datetime import datetime, timedelta
import numpy as np


def calc_rsi(close, length=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(length).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(length).mean()
    rs = gain / loss
    rs = rs.replace([np.inf, -np.inf], 0).fillna(0)
    return 100 - (100 / (1 + rs))


def calc_macd(close, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast).mean()
    ema_slow = close.ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    return macd_line, signal_line


def calc_bbands(close, length=20, std=2):
    mid = close.rolling(length).mean()
    bb_std = close.rolling(length).std()
    upper = mid + std * bb_std
    lower = mid - std * bb_std
    return upper, mid, lower


def collect_us_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        daily = stock.history(period="1y", interval="1d")
        weekly = stock.history(period="2y", interval="1wk")
        if len(daily) < 60 or len(weekly) < 30:
            return None
        result = {
            "ticker": ticker,
            "name": info.get("shortName", ticker),
            "market": "US",
            "price": daily["Close"].iloc[-1],
            "market_cap": info.get("marketCap", 0),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
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
        technicals = calculate_technicals(daily, weekly)
        result.update(technicals)
        return result
    except Exception as e:
        print(f"  {ticker} 수집 실패: {e}")
        return None


def collect_kr_stock(code, name=""):
    try:
        end_date = datetime.now().strftime("%Y%m%d")
        daily_start = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        daily = pykrx_stock.get_market_ohlcv(daily_start, end_date, code)
        if len(daily) < 60:
            return None
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
        technicals = calculate_technicals(daily_renamed, weekly_renamed)
        result.update(technicals)
        return result
    except Exception as e:
        print(f"  {code} 수집 실패: {e}")
        return None


def calculate_technicals(daily, weekly):
    result = {}
    close_d = daily["Close"]
    high_d = daily["High"]
    low_d = daily["Low"]
    current_price = close_d.iloc[-1]

    # RSI
    try:
        rsi_series = calc_rsi(close_d, 14)
        result["rsi_daily"] = round(rsi_series.iloc[-1], 2)
    except:
        result["rsi_daily"] = 50.0

    # MACD
    try:
        macd_line, signal_line = calc_macd(close_d, 12, 26, 9)
        ml = macd_line.iloc[-1]
        sl = signal_line.iloc[-1]
        result["macd_value"] = round(ml, 4)
        result["macd_signal"] = round(sl, 4)
        result["macd_golden"] = ml > sl
        result["macd_above_zero"] = ml > 0
    except:
        result["macd_value"] = 0
        result["macd_signal"] = 0
        result["macd_golden"] = False
        result["macd_above_zero"] = False

    # Bollinger Bands
    try:
        bb_upper, bb_mid, bb_lower = calc_bbands(close_d, 20, 2)
        bu = bb_upper.iloc[-1]
        bm = bb_mid.iloc[-1]
        bl = bb_lower.iloc[-1]
        result["bb_upper"] = round(bu, 2)
        result["bb_mid"] = round(bm, 2)
        result["bb_lower"] = round(bl, 2)
        if current_price > bu:
            result["bb_position"] = "above_upper"
        elif current_price > bm:
            result["bb_position"] = "above_mid"
        elif current_price > bl:
            result["bb_position"] = "below_mid"
        else:
            result["bb_position"] = "below_lower"
    except:
        result["bb_position"] = "unknown"

    # Moving Averages
    try:
        ma20 = close_d.rolling(20).mean().iloc[-1]
        ma50 = close_d.rolling(50).mean().iloc[-1]
        ma200_series = close_d.rolling(200).mean()
        ma200 = ma200_series.iloc[-1] if not pd.isna(ma200_series.iloc[-1]) else 0
        result["ma20"] = round(ma20, 2)
        result["ma50"] = round(ma50, 2)
        result["ma200"] = round(ma200, 2) if ma200 else 0
        if ma200 and ma20 > ma50 > ma200:
            ma20_prev = close_d.rolling(20).mean().iloc[-5]
            ma50_prev = close_d.rolling(50).mean().iloc[-5]
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

    # Ichimoku (Weekly)
    try:
        close_w = weekly["Close"]
        high_w = weekly["High"]
        low_w = weekly["Low"]
        weekly_price = close_w.iloc[-1]
        tenkan = (high_w.rolling(9).max() + low_w.rolling(9).min()) / 2
        kijun = (high_w.rolling(26).max() + low_w.rolling(26).min()) / 2
        senkou_a = ((tenkan + kijun) / 2).shift(26)
        senkou_b = ((high_w.rolling(52).max() + low_w.rolling(52).min()) / 2).shift(26)
        cs_a = senkou_a.iloc[-1] if not pd.isna(senkou_a.iloc[-1]) else 0
        cs_b = senkou_b.iloc[-1] if not pd.isna(senkou_b.iloc[-1]) else 0
        ct = tenkan.iloc[-1] if not pd.isna(tenkan.iloc[-1]) else 0
        ck = kijun.iloc[-1] if not pd.isna(kijun.iloc[-1]) else 0
        cloud_top = max(cs_a, cs_b)
        cloud_bottom = min(cs_a, cs_b)
        result["ichimoku_tenkan"] = round(ct, 2)
        result["ichimoku_kijun"] = round(ck, 2)
        result["ichimoku_cloud_top"] = round(cloud_top, 2)
        result["ichimoku_cloud_bottom"] = round(cloud_bottom, 2)
        result["tenkan_above_kijun"] = ct > ck
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
