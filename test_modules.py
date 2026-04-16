"""
각 모듈 개별 테스트
"""
import time
print("=" * 50)
print("모듈 테스트 시작")
print("=" * 50)

# 1. config 테스트
print("\n[1] config.py 테스트")
try:
    from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, TOP_N
    print(f"  TOP_N: {TOP_N}")
    print(f"  TOKEN 존재: {bool(TELEGRAM_TOKEN)}")
    print(f"  CHAT_ID 존재: {bool(TELEGRAM_CHAT_ID)}")
    print("  OK")
except Exception as e:
    print(f"  실패: {e}")

# 2. Wikipedia 테스트
print("\n[2] Wikipedia 테스트")
try:
    import requests
    import pandas as pd
    from io import StringIO
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(
        "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        headers=headers
    )
    sp500 = pd.read_html(StringIO(resp.text))[0]
    print(f"  S&P 500: {len(sp500)}개")
    print("  OK")
except Exception as e:
    print(f"  실패: {e}")

# 3. KRX JSON API 테스트
print("\n[3] KRX JSON API 테스트")
try:
    from datetime import datetime, timedelta
    url = "http://data.krx.co.kr/comm/bldAttend498/getJsonData.cmd"
    headers_krx = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101",
    }
    found = False
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
        resp = requests.post(url, data=params, headers=headers_krx)
        print(f"  {check_date}: status={resp.status_code}, len={len(resp.text)}")
        try:
            data = resp.json()
            keys = list(data.keys())
            print(f"  JSON keys: {keys}")
            if "OutBlock_1" in data:
                rows = data["OutBlock_1"]
                print(f"  종목수: {len(rows)}")
                if len(rows) > 0:
                    print(f"  샘플: {rows[0]}")
                    found = True
                    break
        except:
            print(f"  JSON 파싱 실패. 응답 앞부분: {resp.text[:200]}")
    if not found:
        print("  KRX 실패")
except Exception as e:
    print(f"  실패: {e}")

# 4. KRX 대안 - marcap 테스트
print("\n[4] KRX 대안 - KOSPI/KOSDAQ 종목 목록")
try:
    kospi_url = "https://raw.githubusercontent.com/FinanceData/marcap/master/data/marcap-2024.csv.gz"
    resp = requests.get(kospi_url, timeout=10)
    print(f"  marcap status: {resp.status_code}")
    if resp.status_code == 200:
        print("  marcap 접근 가능")
    else:
        print("  marcap 접근 불가")
except Exception as e:
    print(f"  실패: {e}")

# 5. yfinance 단건 테스트
print("\n[5] yfinance 단건 테스트")
try:
    import yfinance as yf
    aapl = yf.Ticker("AAPL").history(period="5d")
    print(f"  AAPL: {len(aapl)}행")
    if len(aapl) > 0:
        print(f"  종가: ${aapl['Close'].iloc[-1]:.2f}")
    print("  OK")
except Exception as e:
    print(f"  실패: {e}")

# 6. yfinance 배치 테스트 (5개)
print("\n[6] yfinance 배치 다운로드 테스트")
try:
    import yfinance as yf
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
    data = yf.download(tickers, period="6mo", interval="1d", group_by="ticker", threads=True)
    print(f"  배치 결과: {data.shape}")
    for t in tickers:
        try:
            close = data[t]["Close"]
            last = close.dropna().iloc[-1]
            print(f"  {t}: ${last:.2f}")
        except:
            print(f"  {t}: 데이터 없음")
    print("  OK")
except Exception as e:
    print(f"  실패: {e}")

# 7. yfinance 한국 테스트
print("\n[7] yfinance 한국 테스트")
try:
    import yfinance as yf
    samsung = yf.Ticker("005930.KS").history(period="5d")
    print(f"  삼성전자: {len(samsung)}행")
    if len(samsung) > 0:
        print(f"  종가: {samsung['Close'].iloc[-1]:,.0f}원")
    print("  OK")
except Exception as e:
    print(f"  실패: {e}")

# 8. 텔레그램 테스트
print("\n[8] 텔레그램 테스트")
try:
    from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    msg = "Smart Screener 모듈 테스트 완료!"
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
