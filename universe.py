"""
Smart Stock Screener v3.0
"""
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from io import StringIO
import requests
import json


def get_us_master():
    print("미국 마스터 유니버스 수집 중...")
    tickers = set()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        resp = requests.get(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
            headers=headers
        )
        resp.raise_for_status()
        sp500 = pd.read_html(StringIO(resp.text))[0]
        sp500_tickers = sp500["Symbol"].str.replace(".", "-", regex=False).tolist()
        tickers.update(sp500_tickers)
        print(f"  S&P 500: {len(sp500_tickers)}개")
    except Exception as e:
        print(f"  S&P 500 수집 실패: {e}")
    try:
        resp = requests.get(
            "https://en.wikipedia.org/wiki/Nasdaq-100",
            headers=headers
        )
        resp.raise_for_status()
        tables = pd.read_html(StringIO(resp.text))
        for table in tables:
            if "Ticker" in table.columns:
                nasdaq_tickers = table["Ticker"].tolist()
                tickers.update(nasdaq_tickers)
                print(f"  NASDAQ 100: {len(nasdaq_tickers)}개")
                break
    except Exception as e:
        print(f"  NASDAQ 100 수집 실패: {e}")
    result = sorted(list(tickers))
    print(f"  미국 마스터: 총 {len(result)}개")
    return result


def get_kr_master():
    print("한국 마스터 유니버스 수집 중...")
    try:
        otp_url = "http://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd"
        otp_params = {
            "locale": "ko_KR",
            "mktId": "ALL",
            "trdDd": datetime.now().strftime("%Y%m%d"),
            "money": "1",
            "csvxls_is498": "false",
            "name": "fileDown",
            "url": "dbms/MDC/STAT/standard/MDCSTAT01501"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101"
        }
        otp_resp = requests.post(otp_url, data=otp_params, headers=headers)
        otp = otp_resp.text
        down_url = "http://data.krx.co.kr/comm/fileDn/download_csv/download.cmd"
        down_resp = requests.post(
            down_url,
            data={"code": otp},
            headers=headers
        )
        df = pd.read_csv(StringIO(down_resp.text), encoding="euc-kr")
        print(f"  KRX 원본 컬럼: {list(df.columns)}")
        print(f"  KRX 원본 행수: {len(df)}")
        # 컬럼명 유연하게 찾기
        code_col = None
        name_col = None
        cap_col = None
        vol_col = None
        for col in df.columns:
            col_str = str(col)
            if "종목코드" in col_str or "코드" in col_str:
                code_col = col
            elif "종목명" in col_str or "종목" in col_str and name_col is None:
                name_col = col
            elif "시가총액" in col_str:
                cap_col = col
            elif "거래량" in col_str and vol_col is None:
                vol_col = col
        print(f"  매핑: code={code_col}, name={name_col}, cap={cap_col}, vol={vol_col}")
        if code_col is None or name_col is None or cap_col is None:
            print("  필요한 컬럼을 찾을 수 없습니다.")
            print(f"  전체 컬럼: {list(df.columns)}")
            return pd.DataFrame()
        # 시가총액 3000억 이상, 거래량 10만 이상 필터
        df[cap_col] = pd.to_numeric(df[cap_col].astype(str).str.replace(",", ""), errors="coerce").fillna(0)
        if vol_col:
            df[vol_col] = pd.to_numeric(df[vol_col].astype(str).str.replace(",", ""), errors="coerce").fillna(0)
            filtered = df[(df[cap_col] >= 300_000_000_000) & (df[vol_col] >= 100_000)]
        else:
            filtered = df[df[cap_col] >= 300_000_000_000]
        result = []
        for _, row in filtered.iterrows():
            code = str(row[code_col]).zfill(6)
            result.append({
                "code": code,
                "name": row[name_col],
                "market_cap": row[cap_col],
            })
        result_df = pd.DataFrame(result)
        print(f"  한국 마스터: 총 {len(result_df)}개")
        return result_df
    except Exception as e:
        print(f"  한국 마스터 수집 실패: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def filter_momentum_us(tickers, min_stocks=50):
    print(f"미국 모멘텀 필터링 중... ({len(tickers)}개 대상)")
    passed = []
    errors = 0
    for i, ticker in enumerate(tickers):
        try:
            data = yf.Ticker(ticker).history(period="6mo", interval="1d")
            if len(data) < 50:
                continue
            close = data["Close"]
            ma20 = close.rolling(20).mean().iloc[-1]
            ma50 = close.rolling(50).mean().iloc[-1]
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean().iloc[-1]
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean().iloc[-1]
            rs = gain / loss if loss != 0 else 0
            rsi = 100 - (100 / (1 + rs))
            if ma20 > ma50 and rsi > 50:
                passed.append(ticker)
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"  오류 샘플: {ticker} -> {e}")
        if (i + 1) % 50 == 0:
            print(f"  진행: {i+1}/{len(tickers)} (통과: {len(passed)}개, 오류: {errors}개)")
    print(f"  미국 모멘텀 통과: {len(passed)}개 (오류: {errors}개)")
    return passed


def filter_momentum_kr(kr_df, min_stocks=30):
    print(f"한국 모멘텀 필터링 중... ({len(kr_df)}개 대상)")
    passed = []
    errors = 0
    for i, row in kr_df.iterrows():
        try:
            code = row["code"]
            yf_ticker = yf.Ticker(f"{code}.KS")
            data = yf_ticker.history(period="6mo", interval="1d")
            if len(data) < 50:
                yf_ticker = yf.Ticker(f"{code}.KQ")
                data = yf_ticker.history(period="6mo", interval="1d")
            if len(data) < 50:
                continue
            close = data["Close"]
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
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"  오류 샘플: {code} -> {e}")
        if (i + 1) % 30 == 0:
            print(f"  진행: {i+1}/{len(kr_df)} (통과: {len(passed)}개)")
    print(f"  한국 모멘텀 통과: {len(passed)}개 (오류: {errors}개)")
    return passed


def build_universe():
    print("=" * 50)
    print("유니버스 빌드 시작")
    print("=" * 50)
    us_master = get_us_master()
    kr_master = get_kr_master()
    us_filtered = filter_momentum_us(us_master)
    kr_filtered = filter_momentum_kr(kr_master)
    print("=" * 50)
    print(f"최종 유니버스: 미국 {len(us_filtered)}개 + 한국 {len(kr_filtered)}개")
    print("=" * 50)
    return us_filtered, kr_filtered
