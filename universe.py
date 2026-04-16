"""
Smart Stock Screener v3.0 — 유니버스 자동 생성
Level 1: 마스터 (월 1회)
Level 2: 섹터 필터 (주 1회)
Level 3: 모멘텀 스캔 (매일)
"""
import pandas as pd
import yfinance as yf
from pykrx import stock as pykrx_stock
from datetime import datetime, timedelta
import FinanceDataReader as fdr
 
 
def get_us_master():
    """미국 마스터 유니버스: S&P 500 + NASDAQ 100"""
    print("📡 미국 마스터 유니버스 수집 중...")
    
    tickers = set()
    
    # S&P 500
    try:
        sp500 = pd.read_html(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        )[0]
        sp500_tickers = sp500["Symbol"].str.replace(".", "-", regex=False).tolist()
        tickers.update(sp500_tickers)
        print(f"  S&P 500: {len(sp500_tickers)}개")
    except Exception as e:
        print(f"  S&P 500 수집 실패: {e}")
    
    # NASDAQ 100
    try:
        nasdaq = pd.read_html(
            "https://en.wikipedia.org/wiki/Nasdaq-100"
        )[4]
        nasdaq_tickers = nasdaq["Ticker"].tolist()
        tickers.update(nasdaq_tickers)
        print(f"  NASDAQ 100: {len(nasdaq_tickers)}개")
    except Exception as e:
        print(f"  NASDAQ 100 수집 실패: {e}")
    
    result = sorted(list(tickers))
    print(f"  ✅ 미국 마스터: 총 {len(result)}개")
    return result
 
 
def get_kr_master():
    """한국 마스터 유니버스: 시총 3000억+ & 거래량 10만주+"""
    print("📡 한국 마스터 유니버스 수집 중...")
    
    today = datetime.now().strftime("%Y%m%d")
    
    # 최근 거래일 찾기
    for i in range(7):
        check_date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            test = pykrx_stock.get_market_cap(check_date, market="ALL")
            if len(test) > 0:
                today = check_date
                break
        except:
            continue
    
    try:
        # 시가총액 데이터
        market_cap = pykrx_stock.get_market_cap(today, market="ALL")
        
        # 거래량 데이터
        ohlcv = pykrx_stock.get_market_ohlcv(today, market="ALL")
        
        # 병합
        merged = market_cap.join(ohlcv[["거래량"]], how="inner")
        
        # 필터링: 시총 3000억+ & 거래량 10만주+
        filtered = merged[
            (merged["시가총액"] >= 300_000_000_000) &
            (merged["거래량"] >= 100_000)
        ]
        
        # 종목명 추가
        result = []
        for code in filtered.index:
            try:
                name = pykrx_stock.get_market_ticker_name(code)
                result.append({
                    "code": code,
                    "name": name,
                    "market_cap": filtered.loc[code, "시가총액"],
                    "volume": filtered.loc[code, "거래량"],
                })
            except:
                continue
        
        df = pd.DataFrame(result)
        print(f"  ✅ 한국 마스터: 총 {len(df)}개")
        return df
        
    except Exception as e:
        print(f"  한국 마스터 수집 실패: {e}")
        return pd.DataFrame()
 
 
def filter_momentum_us(tickers, min_stocks=50):
    """미국 모멘텀 필터: 20MA > 50MA & RSI > 50"""
    print(f"📊 미국 모멘텀 필터링 중... ({len(tickers)}개 대상)")
    
    passed = []
    
    for i, ticker in enumerate(tickers):
        try:
            data = yf.Ticker(ticker).history(period="6mo", interval="1d")
            if len(data) < 50:
                continue
            
            close = data["Close"]
            ma20 = close.rolling(20).mean().iloc[-1]
            ma50 = close.rolling(50).mean().iloc[-1]
            
            # 간단한 RSI 계산
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean().iloc[-1]
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean().iloc[-1]
            rs = gain / loss if loss != 0 else 0
            rsi = 100 - (100 / (1 + rs))
            
            if ma20 > ma50 and rsi > 50:
                passed.append(ticker)
            
            if (i + 1) % 50 == 0:
                print(f"  진행: {i+1}/{len(tickers)} ({len(passed)}개 통과)")
                
        except Exception:
            continue
    
    print(f"  ✅ 미국 모멘텀 통과: {len(passed)}개")
    return passed
 
 
def filter_momentum_kr(kr_df, min_stocks=30):
    """한국 모멘텀 필터: 20MA > 50MA & RSI > 50"""
    print(f"📊 한국 모멘텀 필터링 중... ({len(kr_df)}개 대상)")
    
    passed = []
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=180)).strftime("%Y%m%d")
    
    for i, row in kr_df.iterrows():
        try:
            code = row["code"]
            data = pykrx_stock.get_market_ohlcv(start_date, end_date, code)
            
            if len(data) < 50:
                continue
            
            close = data["종가"]
            ma20 = close.rolling(20).mean().iloc[-1]
            ma50 = close.rolling(50).mean().iloc[-1]
            
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean().iloc[-1]
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean().iloc[-1]
            rs = gain / loss if loss != 0 else 0
            rsi = 100 - (100 / (1 + rs))
            
            if ma20 > ma50 and rsi > 50:
                passed.append({
                    "code": code,
                    "name": row["name"],
                    "market_cap": row["market_cap"],
                })
            
            if (i + 1) % 30 == 0:
                print(f"  진행: {i+1}/{len(kr_df)} ({len(passed)}개 통과)")
                
        except Exception:
            continue
    
    print(f"  ✅ 한국 모멘텀 통과: {len(passed)}개")
    return passed
 
 
def build_universe():
    """전체 유니버스 빌드"""
    print("=" * 50)
    print("🌍 유니버스 빌드 시작")
    print("=" * 50)
    
    # Level 1: 마스터
    us_master = get_us_master()
    kr_master = get_kr_master()
    
    # Level 2+3: 모멘텀 필터
    us_filtered = filter_momentum_us(us_master)
    kr_filtered = filter_momentum_kr(kr_master)
    
    print("=" * 50)
    print(f"🎯 최종 유니버스: 미국 {len(us_filtered)}개 + 한국 {len(kr_filtered)}개")
    print("=" * 50)
    
    return us_filtered, kr_filtered
