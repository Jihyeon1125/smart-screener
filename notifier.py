"""
Smart Stock Screener v3.0 — 텔레그램 알림
"""
import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from datetime import datetime


def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("텔레그램 설정이 없습니다.")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    max_length = 4000
    messages = []
    if len(message) <= max_length:
        messages = [message]
    else:
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
                response = requests.post(url, data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": msg,
                })
            if response.status_code != 200:
                print(f"  텔레그램 전송 실패: {response.text}")
                success = False
        except Exception as e:
            print(f"  텔레그램 오류: {e}")
            success = False
    return success


def format_results(us_top5, kr_top5, scan_date):
    msg = "📊 Smart Stock Screener v3.0\n"
    msg += f"📅 {scan_date}\n"
    msg += "=" * 35 + "\n\n"
    msg += "🇺🇸 미국 Top 5\n"
    msg += "-" * 35 + "\n"
    for i, stock in enumerate(us_top5, 1):
        msg += f"\n{i}. {stock['name']} ({stock['ticker']})\n"
        msg += f"   현재가: ${stock['price']:.2f}\n"
        msg += f"   기본적: {stock['fund_score']}/30\n"
        msg += f"   기술적: {stock['tech_score']}/9\n"
        msg += f"   종합: {stock['total_score']}점 -> {stock['action']}\n"
        msg += f"   섹터: {stock['sector']}\n"
    msg += "\n" + "=" * 35 + "\n\n"
    msg += "🇰🇷 한국 Top 5\n"
    msg += "-" * 35 + "\n"
    for i, stock in enumerate(kr_top5, 1):
        msg += f"\n{i}. {stock['name']} ({stock['ticker']})\n"
        msg += f"   현재가: {stock['price']:,.0f}원\n"
        msg += f"   기본적: {stock['fund_score']}/30\n"
        msg += f"   기술적: {stock['tech_score']}/9\n"
        msg += f"   종합: {stock['total_score']}점 -> {stock['action']}\n"
        msg += f"   섹터: {stock['sector']}\n"
    msg += "\n" + "=" * 35 + "\n"
    msg += "AI 자동 분석 결과이며 투자 권유가 아닙니다.\n"
    msg += "최종 판단은 투자자 본인의 책임입니다.\n"
    return msg


def format_detail_card(stock):
    market_label = "US" if stock["market"] == "US" else "KR"
    if stock["market"] == "US":
        price_fmt = f"${stock['price']:.2f}"
    else:
        price_fmt = f"{stock['price']:,.0f}원"
    msg = "-" * 35 + "\n"
    msg += f"[{market_label}] {stock['name']} ({stock['ticker']})\n"
    msg += f"종합: {stock['total_score']}점 {stock['action']}\n"
    msg += "-" * 35 + "\n"
    msg += f"현재가: {price_fmt}\n"
    msg += f"섹터: {stock['sector']}\n\n"
    msg += f"[기본적 분석] {stock['fund_score']}/30\n"
    for key, val in stock.get("fund_details", {}).items():
        msg += f"  {key}: {val}\n"
    msg += f"\n[기술적 분석] {stock['tech_score']}/9\n"
    for key, val in stock.get("tech_details", {}).items():
        msg += f"  {key}: {val}\n"
    msg += "-" * 35 + "\n"
    return msg
