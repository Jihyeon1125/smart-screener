"""
FMP API 테스트
"""
import requests
import os

FMP_KEY = os.environ.get("FMP_API_KEY", "")
BASE = "https://financialmodelingprep.com/api/v3"

print("=" * 50)
print("FMP API 테스트")
print("=" * 50)

print(f"\nAPI KEY 존재: {bool(FMP_KEY)}")

# 1. S&P 500 목록
print("\n[1] S&P 500 목록")
try:
    url = f"{BASE}/sp500_constituent?apikey={FMP_KEY}"
    resp = requests.get(url)
    data = resp.json()
    if isinstance(data, list):
        print(f"  종목수: {len(data)}")
        if len(data) > 0:
            print(f"  샘플: {data[0]}")
        print("  OK")
    else:
        print(f"  응답: {data}")
except Exception as e:
    print(f"  실패: {e}")

# 2. 주가 데이터
print("\n[2] AAPL 주가")
try:
    url = f"{BASE}/historical-price-full/AAPL?timeseries=120&apikey={FMP_KEY}"
    resp = requests.get(url)
    data = resp.json()
    if "historical" in data:
        prices = data["historical"]
        print(f"  데이터: {len(prices)}일")
        print(f"  최근: {prices[0]}")
        print("  OK")
    else:
        print(f"  응답: {str(data)[:200]}")
except Exception as e:
    print(f"  실패: {e}")

# 3. 재무 데이터
print("\n[3] AAPL 재무")
try:
    url = f"{BASE}/ratios-ttm/AAPL?apikey={FMP_KEY}"
    resp = requests.get(url)
    data = resp.json()
    if isinstance(data, list) and len(data) > 0:
        r = data[0]
        print(f"  ROE: {r.get('returnOnEquityTTM', 'N/A')}")
        print(f"  PE: {r.get('peRatioTTM', 'N/A')}")
        print("  OK")
    else:
        print(f"  응답: {str(data)[:200]}")
except Exception as e:
    print(f"  실패: {e}")

# 4. 한국 종목 테스트
print("\n[4] 한국 종목 (삼성전자)")
try:
    url = f"{BASE}/historical-price-full/005930.KS?timeseries=120&apikey={FMP_KEY}"
    resp = requests.get(url)
    data = resp.json()
    if "historical" in data:
        prices = data["historical"]
        print(f"  데이터: {len(prices)}일")
        print(f"  최근: {prices[0]}")
        print("  OK")
    else:
        print(f"  응답: {str(data)[:200]}")
        # 다른 포맷 시도
        url2 = f"{BASE}/historical-price-full/005930.KQ?timeseries=120&apikey={FMP_KEY}"
        resp2 = requests.get(url2)
        data2 = resp2.json()
        print(f"  KQ 응답: {str(data2)[:200]}")
except Exception as e:
    print(f"  실패: {e}")

# 5. 스크리너 API 테스트
print("\n[5] 스크리너 (시총 상위)")
try:
    url = f"{BASE}/stock-screener?marketCapMoreThan=10000000000&country=US&limit=10&apikey={FMP_KEY}"
    resp = requests.get(url)
    data = resp.json()
    if isinstance(data, list):
        print(f"  결과: {len(data)}개")
        if len(data) > 0:
            s = data[0]
            print(f"  샘플: {s.get('symbol')} {s.get('companyName')} cap={s.get('marketCap')}")
        print("  OK")
    else:
        print(f"  응답: {str(data)[:200]}")
except Exception as e:
    print(f"  실패: {e}")

# 6. 한국 스크리너
print("\n[6] 한국 스크리너")
try:
    url = f"{BASE}/stock-screener?country=KR&limit=10&apikey={FMP_KEY}"
    resp = requests.get(url)
    data = resp.json()
    if isinstance(data, list):
        print(f"  결과: {len(data)}개")
        if len(data) > 0:
            s = data[0]
            print(f"  샘플: {s.get('symbol')} {s.get('companyName')} cap={s.get('marketCap')}")
        print("  OK")
    else:
        print(f"  응답: {str(data)[:200]}")
except Exception as e:
    print(f"  실패: {e}")

# 7. 텔레그램
print("\n[7] 텔레그램")
try:
    from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    msg = "FMP API 테스트 완료!"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    resp = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    if resp.status_code == 200:
        print("  OK")
    else:
        print(f"  실패: {resp.text}")
except Exception as e:
    print(f"  실패: {e}")

print("\n" + "=" * 50)
print("테스트 완료")
print("=" * 50)
