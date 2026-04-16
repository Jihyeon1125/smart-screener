"""
Smart Stock Screener v3.0 — 메인 실행
"""
from datetime import datetime
from universe import build_universe
from collector import collect_us_stock, collect_kr_stock
from scorer import score_fundamental, score_technical, score_total
from notifier import send_telegram, format_results, format_detail_card
from config import TOP_N


def run_screening():
    """메인 스크리닝 실행"""

    scan_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n{'='*50}")
    print(f"Smart Stock Screener v3.0 시작")
    print(f"{scan_date}")
    print(f"{'='*50}\n")

    # Step 1: 유니버스 빌드
    us_universe, kr_universe = build_universe()

    # Step 2: 미국 종목 분석
    print(f"\n미국 종목 상세 분석 중... ({len(us_universe)}개)")
    us_results = []

    for i, ticker in enumerate(us_universe):
        stock = collect_us_stock(ticker)
        if stock is None:
            continue

        fund_score, fund_signal, fund_details = score_fundamental(stock)
        tech_score, tech_signal, tech_details, veto = score_technical(stock)

        if fund_signal == "🔴" or veto:
            continue

        total, total_signal, action = score_total(fund_score, tech_score)

        stock.update({
            "fund_score": fund_score,
            "signal_fund": fund_signal,
            "fund_details": fund_details,
            "tech_score": tech_score,
            "signal_tech": tech_signal,
            "tech_details": tech_details,
            "total_score": total,
            "signal_total": total_signal,
            "action": action,
        })

        us_results.append(stock)

        if (i + 1) % 20 == 0:
            print(f"  진행: {i+1}/{len(us_universe)}")

    us_results.sort(key=lambda x: x["total_score"], reverse=True)
    us_top5 = us_results[:TOP_N]
    print(f"  미국 분석 완료: {len(us_results)}개 적격, Top {TOP_N} 선별")

    # Step 3: 한국 종목 분석
    print(f"\n한국 종목 상세 분석 중... ({len(kr_universe)}개)")
    kr_results = []

    for i, item in enumerate(kr_universe):
        code = item["code"] if isinstance(item, dict) else item
        name = item.get("name", "") if isinstance(item, dict) else ""

        stock = collect_kr_stock(code, name)
        if stock is None:
            continue

        fund_score, fund_signal, fund_details = score_fundamental(stock)
        tech_score, tech_signal, tech_details, veto = score_technical(stock)

        if fund_signal == "🔴" or veto:
            continue

        total, total_signal, action = score_total(fund_score, tech_score)

        stock.update({
            "fund_score": fund_score,
            "signal_fund": fund_signal,
            "fund_details": fund_details,
            "tech_score": tech_score,
            "signal_tech": tech_signal,
            "tech_details": tech_details,
            "total_score": total,
            "signal_total": total_signal,
            "action": action,
        })

        kr_results.append(stock)

        if (i + 1) % 20 == 0:
            print(f"  진행: {i+1}/{len(kr_universe)}")

    kr_results.sort(key=lambda x: x["total_score"], reverse=True)
    kr_top5 = kr_results[:TOP_N]
    print(f"  한국 분석 완료: {len(kr_results)}개 적격, Top {TOP_N} 선별")

    # Step 4: 결과 전송
    print(f"\n텔레그램 전송 중...")

    summary = format_results(us_top5, kr_top5, scan_date)
    send_telegram(summary)

    for stock in us_top5[:3]:
        card = format_detail_card(stock)
        send_telegram(card)

    for stock in kr_top5[:3]:
        card = format_detail_card(stock)
        send_telegram(card)

    print(f"\n{'='*50}")
    print(f"스크리닝 완료! 텔레그램을 확인하세요.")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    run_screening()
