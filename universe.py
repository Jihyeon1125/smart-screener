def filter_momentum_kr(kr_df, min_stocks=30):
    """한국 모멘텀 필터: 20MA > 50MA & RSI > 50"""
    print(f"한국 모멘텀 필터링 중... ({len(kr_df)}개 대상)")

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
                print(f"  진행: {i+1}/{len(kr_df)} ({len(passed)}개 통과)")

        except Exception:
            continue

    print(f"  한국 모멘텀 통과: {len(passed)}개")
    return passed


def build_universe():
    """전체 유니버스 빌드"""
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
