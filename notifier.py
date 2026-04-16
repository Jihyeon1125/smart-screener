"""
Smart Stock Screener v3.0 — 텔레그램 알림
"""
import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from datetime import datetime
 
 
def send_telegram(message):
    """텔레그램으로 메시지 전송"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ 텔레그램 설정이 없습니다.")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # 메시지가 4096자 초과 시 분할 전송
    max_length = 4000
    messages = []
    
    if len(message) <= max_length:
        messages = [message]
    else:
        # 줄 단위로 분할
        lines = message.split("\n")
        current = ""
        for line in lines:
            if len(current) + len(line) + 1 > max_length:
                messages.append(current)
                current = line + "\n"
            else:
                current += line + "\n"
        if current:
            messages.append(current)
    
    success = True
    for i, msg in enumerate(messages):
        try:
            response = requests.post(url, data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": msg,
                "parse_mode": "Markdown",
            })
            if response.status_code != 200:
                # Markdown 실패 시 일반 텍스트로 재시도
                response = requests.post(url, data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": msg,
                })
            if response.status_code != 200:
                print(f"  ❌ 텔레그램 전송 실패: {response.text}")
                success = False
        except Exception as e:
            print(f"  ❌ 텔레그램 오류: {e}")
            success = False
    
    return success
 
 
def format_results(us_top5, kr_top5, scan_date):
    """결과를 텔레그램 메시지 형식으로 포맷"""
    
    msg = f"""
📊 Smart Stock Screener v3.0
📅 {scan_date}
{'='*35}
 
🇺🇸 미국 Top 5
{'─'*35}
"""
    
    for i, stock in enumerate(us_top5, 1):
        msg += f"""
{i}. {stock['signal_total']} {stock['name']} ({stock['ticker']})
   현재가: ${stock['price']:.2f}
   기본적: {stock['fund_score']}/30 {stock['signal_fund']}
   기술적: {stock['tech_score']}/9 {stock['signal_tech']}
   종합: {stock['total_score']}점 → {stock['action']}
   섹터: {stock['sector']}
"""
    
    msg += f"""
{'='*35}
 
🇰🇷 한국 Top 5
{'─'*35}
"""
    
    for i, stock in enumerate(kr_top5, 1):
        msg += f"""
{i}. {stock['signal_total']} {stock['name']} ({stock['ticker']})
   현재가: {stock['price']:,.0f}원
   기본적: {stock['fund_score']}/30 {stock['signal_fund']}
   기술적: {stock['tech_score']}/9 {stock['signal_tech']}
   종합: {stock['total_score']}점 → {stock['action']}
   섹터: {stock['sector']}
"""
    
    msg += f"""
{'='*35}
⚠️ AI 자동 분석 결과이며 투자 권유가 아닙니다.
최종 판단은 투자자 본인의 책임입니다.
"""
    
    return msg
 
 
def format_detail_card(stock):
    """종목별 상세 카드"""
    
    market_label = "🇺🇸" if stock["market"] == "US" else "🇰🇷"
    price_fmt = f"${stock['price']:.2f}" if stock["market"] == "US" else f"{stock['price']:,.0f}원"
    
    msg = f"""
{'━'*35}
{market_label} {stock['name']} ({stock['ticker']})
종합: {stock['total_score']}점 {stock['signal_total']} {stock['action']}
{'━'*35}
 
현재가: {price_fmt}
섹터: {stock['sector']}
 
[기본적 분석] {stock['fund_score']}/30 {stock['signal_fund']}
"""
    
    for key, val in stock.get("fund_details", {}).items():
        msg += f"  {key}: {val}\n"
    
    msg += f"""
[기술적 분석] {stock['tech_score']}/9 {stock['signal_tech']}
★ 이중 타임프레임 ★
"""
    
    for key, val in stock.get("tech_details", {}).items():
        msg += f"  {key}: {val}\n"
    
    msg += f"{'━'*35}\n"
    
    return msg
