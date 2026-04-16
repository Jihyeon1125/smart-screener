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
        url = "http://data.krx.co.kr/comm/bldAttend498/getJsonData.cmd"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        # 최근 7일 중 거래일 찾기
        for i in range(7):
            check_date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
            params = {
                "bld": "dbms/MDC/STAT/standard/MDCSTAT01501",
                "locale": "ko_KR",
                "mktId": "ALL",
                "trdDd": check_date,
                "share": "1",
                "money": "1",
                "csvxls_isNo": "false",
            }
            resp = requests.post(url, data=params, headers=headers)
            try:
                data = resp.json()
                if "OutBlock_1" in data and len(data["OutBlock_1"]) > 0:
                    print(f"  거래일: {check_date}")
                    break
            except:
                continue
        else:
            print("  KRX 데이터를 가져올 수 없습니다.")
            return pd.DataFrame()
        rows = data["OutBlock_1"]
        print(f"  KRX 원본: {len(rows)}개")
        if len(rows) > 0:
            print(f"  샘플 키: {list(rows[0].keys())}")
        result = []
        for row in rows:
            try:
                code = str(row.get("ISU_SRT_CD", "")).strip()
                name = str(row.get("ISU_ABBRV", "")).strip()
                cap_str = str(row.get("MKTCAP", "0")).replace(",", "")
                vol_str = str(row.get("ACC_TRDVOL", "0")).replace(",", "")
                cap = int(float(cap_str)) if cap_str else 0
                vol = int(float(vol_str)) if vol_str else 0
                if len(code) == 6 and code.isdigit():
                    if cap >= 300_000_000_000 and vol >= 100_000:
                        result.append({
                            "code": code,
                            "name": name,
                            "market_cap": cap,
                        })
            except:
                continue
        result_df = pd.DataFrame(result)
        print(f"  한국 마스터: 총 {len(result_df)}개 (시총 3000억+, 거래량 10만+)")
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
