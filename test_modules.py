"""
FMP v4 API + 다른 대안 테스트
"""
import requests
import os

FMP_KEY = os.environ.get("FMP_API_KEY", "")

print("=" * 50)
print("데이터 소스 테스트")
print("=" * 50)

# 1. FMP v4 테스트
print("\n[1] FMP v4 - S&P 500")
try:
    url = f"https://financialmodelingprep.com/stable/sp500-constituent?apikey={FMP_KEY}"
    resp = requests.get(url)
    data = resp.json()
    if isinstance(data, list) and len(data) > 0:
        print(f"  종목수: {len(data)}")
        print(f"  샘플: {data[0]}")
        print("  OK")
    else:
        print(f"  응답: {str(data)[:300]}")
except Exception as e:
    print(f"  실패: {e}")

# 2. FMP v4 주가
print("\n[2] FMP v4 - AAPL 주가")
try:
    url = f"https://financialmodelingprep.com/stable/historical-price-full/AAPL?apikey={FMP_KEY}"
    resp = requests.get(url)
    data = resp.json()
    if isinstance(data, list):
        print(f"  데이터: {len(data)}일")
        if len(data) > 0:
            print(f"  최근: {data[0]}")
        print("  OK")
    elif isinstance(data, dict) and "historical" in data:
        prices = data["historical"]
        print(f"  데이터: {len(prices)}일")
        print(f"  최근: {prices[0]}")
        print("  OK")
    else:
        print(f"  응답: {str(data)[:300]}")
except Exception as e:
    print(f"  실패: {e}")

# 3. FMP v4 재무
print("\n[3] FMP v4 - AAPL 재무")
try:
    url = f"https://financialmodelingprep.com/stable/ratios-ttm?symbol=AAPL&apikey={FMP_KEY}"
    resp = requests.get(url)
    data = resp.json()
    if isinstance(data, list) and len(data) > 0:
        r = data[0]
        print(f"  키 샘플: {list(r.keys())[:8]}")
        print("  OK")
    else:
        print(f"  응답: {str(data)[:300]}")
except Exception as e:
    print(f"  실패: {e}")

# 4. FMP v4 스크리너
print("\n[4] FMP v4 - 스크리너")
try:
    url = f"https://financialmodelingprep.com/stable/company-screener?marketCapMoreThan=10000000000&country=US&limit=5&apikey={FMP_KEY}"
    resp = requests.get(url)
    data = resp.json()
    if isinstance(data, list) and len(data) > 0:
        print(f"  결과: {len(data)}개")
        s = data[0]
        print(f"  샘플: {s.get('symbol')} {s.get('companyName')} cap={s.get('marketCap')}")
        print("  OK")
    else:
        print(f"  응답: {str(data)[:300]}")
except Exception as e:
    print(f"  실패: {e}")

# 5. FMP v4 한국 스크리너
print("\n[5] FMP v4 - 한국 스크리너")
try:
    url = f"https://financialmodelingprep.com/stable/company-screener?country=KR&limit=5&apikey={FMP_KEY}"
    resp = requests.get(url)
    data = resp.json()
    if isinstance(data, list) and len(data) > 0:
        print(f"  결과: {len(data)}개")
        s = data[0]
        print(f"  샘플: {s.get('symbol')} {s.get('companyName')} cap={s.get('marketCap')}")
        print("  OK")
    else:
        print(f"  응답: {str(data)[:300]}")
except Exception as e:
    print(f"  실패: {e}")

# 6. Alpha Vantage 무료 테스트
print("\n[6] Alpha Vantage (키 없이 데모)")
try:
    url = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=AAPL&outputsize=compact&apikey=demo"
    resp = requests.get(url)
    data = resp.json()
    if "Time Series (Daily)" in data:
        ts = data["Time Series (Daily)"]
        print(f"  데이터: {len(ts)}일")
        print("  OK")
    else:
        print(f"  응답 키: {list(data.keys())}")
except Exception as e:
    print(f"  실패: {e}")

# 7. Twelve Data 무료 테스트
print("\n[7] Twelve Data (키 없이)")
try:
    url = "https://api.twelvedata.com/time_series?symbol=AAPL&interval=1day&outputsize=5&apikey=demo"
    resp = requests.get(url)
    data = resp.json()
    if "values" in data:
        print(f"  데이터: {len(data['values'])}개")
        print(f"  최근: {data['values'][0]}")
        print("  OK")
    else:
        print(f"  응답: {str(data)[:300]}")
except Exception as e:
    print(f"  실패: {e}")

# 8. 텔레그램
print("\n[8] 텔레그램")
try:
    from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    msg = "데이터 소스 테스트 완료!"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    resp = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    print("  OK" if resp.status_code == 200 else f"  실패: {resp.text}")
except Exception as e:
    print(f"  실패: {e}")

print("\n" + "=" * 50)
print("테스트 완료")
print("=" * 50)
