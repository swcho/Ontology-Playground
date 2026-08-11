# %% [markdown]
# # `timestamp`은 왜 date가 아니라 datetime인가
#
# Transaction 프로퍼티 표에서 `timestamp`의 타입은 `datetime`이다.
# 이유는 한 줄로 요약된다: **시간 타입의 해상도가 곧 답할 수 있는 질문의 해상도다.**
#
# 이 노트북은 같은 거래 로그를 두 가지 해상도로 보면서, `date`로 절단(truncate)할 때
# 어떤 질문이 **답할 수 없게 되는지**를 직접 출력해 확인한다.
#
# | 셀 | 확인하는 것 |
# |---|---|
# | 1 | velocity 규칙(10분 내 3건 이상)이 date 절단 시 어떻게 망가지는가 |
# | 2 | 같은 날 거래 **순서**에 따라 잔액이 음수가 되는지가 갈린다 |
# | 3 | impossible travel: $v = d / \Delta t$ 로 필요 이동속도 계산 |
# | 4 | 타임존 변환으로 **날짜 경계**가 바뀌는 문제 |
# | 5 | plotly 시각화: datetime 타임라인 vs date 절단 시 한 점으로 뭉치는 모습 |

# %%
# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
# 표준 라이브러리만으로 계산하고, 마지막 시각화에서만 plotly를 사용한다.

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import math


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


def ts(s: str) -> datetime:
    """'2026-03-15 09:12:03' 형태를 UTC datetime으로."""
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


# 작은 거래 로그. (account, transactionId, timestamp, amount, merchant)
TX = [
    # A-1001: 09:12~09:14 에 소액 4건이 몰린 카드 테스팅(card testing) 패턴
    ("A-1001", "T-001", ts("2026-03-15 09:12:03"), 1.00, "OnlineShop-A"),
    ("A-1001", "T-002", ts("2026-03-15 09:12:41"), 1.00, "OnlineShop-B"),
    ("A-1001", "T-003", ts("2026-03-15 09:13:20"), 2.50, "OnlineShop-C"),
    ("A-1001", "T-004", ts("2026-03-15 09:14:02"), 1.00, "OnlineShop-D"),
    # A-1001: 같은 날이지만 하루에 넓게 퍼진 정상 결제 3건
    ("A-1001", "T-005", ts("2026-03-15 12:30:00"), 12800.0, "Cafe-Seoul"),
    ("A-1001", "T-006", ts("2026-03-15 15:45:00"), 43000.0, "Bookstore"),
    ("A-1001", "T-007", ts("2026-03-15 19:10:00"), 21500.0, "Grocery"),
    # A-2002: 하루에 3건이지만 전부 몇 시간씩 떨어진 완전한 정상 사용
    ("A-2002", "T-101", ts("2026-03-15 08:00:00"), 4500.0, "Subway"),
    ("A-2002", "T-102", ts("2026-03-15 13:00:00"), 9800.0, "Lunch"),
    ("A-2002", "T-103", ts("2026-03-15 20:00:00"), 33000.0, "Pharmacy"),
    # A-2002: 자정을 걸쳐 3분 안에 터진 버스트 (날짜 경계를 넘는다)
    ("A-2002", "T-104", ts("2026-03-16 23:58:10"), 1.00, "Gateway-X"),
    ("A-2002", "T-105", ts("2026-03-16 23:59:30"), 1.00, "Gateway-X"),
    ("A-2002", "T-106", ts("2026-03-17 00:01:05"), 1.00, "Gateway-X"),
]

print(f"거래 {len(TX)}건, 계좌 {len({t[0] for t in TX})}개")
print("첫 거래:", TX[0][2].isoformat())
# 출력: 거래 13건, 계좌 2개
# 출력: 첫 거래: 2026-03-15T09:12:03+00:00

# %% [markdown]
# ## 1. velocity 규칙 — date로 절단하면 규칙 자체를 표현할 수 없다
#
# **velocity check**는 사기 탐지의 기본 규칙이다: 같은 카드/계좌/기기/IP가
# **짧은 시간 창** 안에 몇 번 행동했는지를 센다. 여기서는
#
# $$\text{flag} \iff \exists\, t_i \;:\; \bigl|\{\, t_j \;:\; 0 \le t_j - t_i \le 10\text{min} \,\}\bigr| \ge 3$$
#
# 즉 **10분 창 안에 3건 이상**이면 flag. 이 규칙에는 $\Delta t$가 들어간다.
#
# `timestamp`가 `date`뿐이라면 $\Delta t$의 최소 단위가 **1일**이 되어 10분 창을
# 아예 쓸 수 없다. 할 수 있는 최선의 근사는 "**같은 날** 3건 이상"이다.
# 그 근사가 얼마나 다른 답을 주는지 보자.

# %%
def velocity_datetime(rows, window=timedelta(minutes=10), threshold=3):
    """datetime 해상도: 슬라이딩 시간 창 안의 건수를 센다."""
    flags = {}
    by_acct = {}
    for acct, tid, t, amt, m in rows:
        by_acct.setdefault(acct, []).append((t, tid))
    for acct, items in by_acct.items():
        items.sort()
        for i, (t0, _) in enumerate(items):
            burst = [tid for (t, tid) in items if timedelta(0) <= t - t0 <= window]
            if len(burst) >= threshold:
                flags.setdefault(acct, []).append((t0, burst))
    return flags


def velocity_date_only(rows, threshold=3):
    """date 해상도: 시각이 사라졌으므로 '같은 날 N건 이상'밖에 못 센다."""
    buckets = {}
    for acct, tid, t, amt, m in rows:
        buckets.setdefault((acct, t.date()), []).append(tid)
    return {k: v for k, v in buckets.items() if len(v) >= threshold}


dt_flags = velocity_datetime(TX)
print("[datetime] 10분 내 3건 이상 버스트:")
for acct, hits in sorted(dt_flags.items()):
    t0, burst = hits[0]  # 계좌별 첫 버스트만 요약
    print(f"  {acct}: {t0:%Y-%m-%d %H:%M:%S} 부터 {len(burst)}건 -> {burst}")

print("\n[date 절단] 같은 날 3건 이상:")
for (acct, d), tids in sorted(velocity_date_only(TX).items()):
    print(f"  {acct} {d}: {len(tids)}건 -> {tids}")
# 출력: [datetime] 10분 내 3건 이상 버스트:
# 출력:   A-1001: 2026-03-15 09:12:03 부터 4건 -> ['T-001', 'T-002', 'T-003', 'T-004']
# 출력:   A-2002: 2026-03-16 23:58:10 부터 3건 -> ['T-104', 'T-105', 'T-106']
# 출력:
# 출력: [date 절단] 같은 날 3건 이상:
# 출력:   A-1001 2026-03-15: 7건 -> ['T-001', 'T-002', 'T-003', 'T-004', 'T-005', 'T-006', 'T-007']
# 출력:   A-2002 2026-03-15: 3건 -> ['T-101', 'T-102', 'T-103']

# %%
# 두 결과의 차이를 명시적으로 대조한다.
dt_acct_dates = {(a, hits[0][0].date()) for a, hits in dt_flags.items()}
date_acct_dates = set(velocity_date_only(TX).keys())

print("date 절단이 놓친 진짜 버스트 (false negative):")
for k in sorted(dt_acct_dates - date_acct_dates):
    print(f"  {k[0]} {k[1]}  <- 23:58~00:01, 자정을 걸쳐 두 날짜로 쪼개짐")

print("\ndate 절단이 잘못 잡은 정상 사용 (false positive):")
for k in sorted(date_acct_dates - dt_acct_dates):
    print(f"  {k[0]} {k[1]}  <- 하루에 흩어진 3건, 실제로는 몇 시간씩 떨어져 있음")

print("\nA-1001 2026-03-15는 양쪽 모두 flag이지만 의미가 다르다:")
print("  datetime: 09:12:03~09:14:02 의 소액 4건 = 카드 테스팅 구간을 특정")
print("  date    : 그날 7건 전부 = 정상 결제 3건까지 같이 물들여 조사 범위가 뭉개짐")
# 출력: date 절단이 놓친 진짜 버스트 (false negative):
# 출력:   A-2002 2026-03-16  <- 23:58~00:01, 자정을 걸쳐 두 날짜로 쪼개짐
# 출력:
# 출력: date 절단이 잘못 잡은 정상 사용 (false positive):
# 출력:   A-2002 2026-03-15  <- 하루에 흩어진 3건, 실제로는 몇 시간씩 떨어져 있음
# 출력:
# 출력: A-1001 2026-03-15는 양쪽 모두 flag이지만 의미가 다르다:
# 출력:   datetime: 09:12:03~09:14:02 의 소액 4건 = 카드 테스팅 구간을 특정
# 출력:   date    : 그날 7건 전부 = 정상 결제 3건까지 같이 물들여 조사 범위가 뭉개짐

# %% [markdown]
# ## 2. 거래 순서 — 같은 날 잔액이 음수가 되는지는 순서에 달렸다
#
# `date`만 있으면 같은 날 거래들 사이에 **전순서(total order)가 없다**.
# 그런데 잔액은 누적합이므로 순서에 의존한다:
#
# $$B_k = B_0 + \sum_{i=1}^{k} a_i, \qquad \text{overdraft} \iff \min_k B_k < 0$$
#
# 합계 $\sum a_i$는 순서와 무관하지만, **최솟값** $\min_k B_k$는 순서에 따라 바뀐다.
# 그래서 "이 계좌가 잔액 부족이었나?", "수수료를 부과해야 하나?"는
# `date` 해상도로는 답이 정해지지 않는다.

# %%
OPENING = 100_000.0  # 3/15 시작 잔액 (원)

same_day = [
    ("T-201", ts("2026-03-15 09:05:00"), -400_000.0, "Rent"),      # 출금
    ("T-202", ts("2026-03-15 14:00:00"), +500_000.0, "Payroll"),   # 입금
]


def run_balance(seq, opening=OPENING):
    bal, trail = opening, []
    for tid, t, amt, m in seq:
        bal += amt
        trail.append((tid, m, amt, bal))
    return trail


for label, seq in [
    ("실제 시각 순서 (09:05 출금 -> 14:00 입금)", sorted(same_day, key=lambda r: r[1])),
    ("date만 보고 임의 순서 (입금 -> 출금)", sorted(same_day, key=lambda r: r[2], reverse=True)),
]:
    trail = run_balance(seq)
    lo = min(b for *_, b in trail)
    print(f"{label}")
    for tid, m, amt, bal in trail:
        print(f"   {tid} {m:<8} {amt:>+12,.0f} -> 잔액 {bal:>+12,.0f}")
    print(f"   최저 잔액 {lo:>+12,.0f} / 최종 잔액 {trail[-1][3]:>+12,.0f}"
          f" / 잔액부족? {'YES (수수료 발생)' if lo < 0 else 'NO'}\n")

print("최종 잔액은 두 순서 모두 같지만(합은 순서 무관), 잔액부족 판정은 정반대다.")
# 출력: 실제 시각 순서 (09:05 출금 -> 14:00 입금)
# 출력:    T-201 Rent          -400,000 -> 잔액     -300,000
# 출력:    T-202 Payroll       +500,000 -> 잔액     +200,000
# 출력:    최저 잔액     -300,000 / 최종 잔액     +200,000 / 잔액부족? YES (수수료 발생)
# 출력:
# 출력: date만 보고 임의 순서 (입금 -> 출금)
# 출력:    T-202 Payroll       +500,000 -> 잔액     +600,000
# 출력:    T-201 Rent          -400,000 -> 잔액     +200,000
# 출력:    최저 잔액     +200,000 / 최종 잔액     +200,000 / 잔액부족? NO
# 출력:
# 출력: 최종 잔액은 두 순서 모두 같지만(합은 순서 무관), 잔액부족 판정은 정반대다.

# %% [markdown]
# ## 3. impossible travel — $v = d / \Delta t$
#
# 같은 카드가 서로 다른 도시에서 결제됐을 때, 두 결제 사이에 필요한 이동 속도는
#
# $$v = \frac{d}{\Delta t}$$
#
# 이고 $d$는 대권거리(haversine):
#
# $$d = 2R \arcsin\sqrt{\sin^2\frac{\Delta\varphi}{2} + \cos\varphi_1\cos\varphi_2\sin^2\frac{\Delta\lambda}{2}}$$
#
# $v$가 여객기 속도(약 900 km/h)를 넘으면 **물리적으로 불가능** → 카드 복제 의심.
# 핵심은 분모가 $\Delta t$라는 것. `date`만 있으면 $\Delta t = 0$이거나 1일 단위여서
# $v$를 계산할 수 없다($\Delta t = 0$이면 정의되지 않고, 1일로 뭉개면 항상 "가능"해진다).

# %%
CITY = {  # (lat, lon)
    "Seoul":  (37.5665, 126.9780),
    "Busan":  (35.1796, 129.0756),
    "Incheon": (37.4563, 126.7052),
}
PLANE_KMH = 900.0


def haversine_km(a, b, R=6371.0):
    (la1, lo1), (la2, lo2) = a, b
    p1, p2 = math.radians(la1), math.radians(la2)
    dp, dl = p2 - p1, math.radians(lo2 - lo1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


PAIRS = [
    ("Seoul", ts("2026-03-15 14:30:00"), "Busan", ts("2026-03-15 14:35:00")),
    ("Seoul", ts("2026-03-15 14:30:00"), "Incheon", ts("2026-03-15 15:30:00")),
]

for c1, t1, c2, t2 in PAIRS:
    d = haversine_km(CITY[c1], CITY[c2])
    dt_h = (t2 - t1).total_seconds() / 3600
    v = d / dt_h
    verdict = "IMPOSSIBLE TRAVEL" if v > PLANE_KMH else "가능"
    print(f"{c1} {t1:%H:%M} -> {c2} {t2:%H:%M}: d={d:6.1f} km, "
          f"dt={dt_h*60:5.1f} min, v={v:8.1f} km/h  => {verdict}")

# date 해상도에서는 같은 날 두 결제의 dt가 0이 되어 판정이 불가능하다.
d = haversine_km(CITY["Seoul"], CITY["Busan"])
print(f"\n[date 절단] Seoul/Busan 둘 다 2026-03-15 -> dt = 0 -> v = {d}/0 : 계산 불가")
print(f"[date 절단] 1일로 뭉개면 v = {d/24:.1f} km/h -> '가능'으로 오판")
# 출력: Seoul 14:30 -> Busan 14:35: d= 325.1 km, dt=  5.0 min, v=  3901.3 km/h  => IMPOSSIBLE TRAVEL
# 출력: Seoul 14:30 -> Incheon 15:30: d=  27.0 km, dt= 60.0 min, v=    27.0 km/h  => 가능
# 출력:
# 출력: [date 절단] Seoul/Busan 둘 다 2026-03-15 -> dt = 0 -> v = 325.11125884976224/0 : 계산 불가
# 출력: [date 절단] 1일로 뭉개면 v = 13.5 km/h -> '가능'으로 오판

# %% [markdown]
# ## 4. 타임존 — "며칠 거래인가"조차 해석에 달려 있다
#
# `datetime`은 반드시 **UTC로 저장하고 표시할 때 로컬로 변환**하는 것이 원칙이다.
# `date`로 저장하면 이 변환 정보가 이미 파괴되어 있어, 어느 타임존 기준의
# 날짜인지 되돌릴 수 없다. 아래처럼 **같은 순간이 타임존마다 다른 날짜**가 된다.

# %%
moment = datetime(2026, 3, 15, 23, 30, 0, tzinfo=timezone.utc)
print(f"UTC 저장값: {moment.isoformat()}\n")
for zone in ["UTC", "Asia/Seoul", "America/New_York", "Pacific/Kiritimati"]:
    local = moment.astimezone(ZoneInfo(zone))
    print(f"  {zone:<20} {local:%Y-%m-%d %H:%M %Z}  -> date = {local.date()}")

seoul_date = moment.astimezone(ZoneInfo("Asia/Seoul")).date()
ny_date = moment.astimezone(ZoneInfo("America/New_York")).date()
print(f"\n같은 한 순간인데 서울 기준 {seoul_date}, 뉴욕 기준 {ny_date} — 하루가 다르다.")
print("월말/분기말이면 이 하루 차이가 회계 기간을 바꾼다. date만 남기면 복구 불가.")
# 출력: UTC 저장값: 2026-03-15T23:30:00+00:00
# 출력:
# 출력:   UTC                  2026-03-15 23:30 UTC  -> date = 2026-03-15
# 출력:   Asia/Seoul           2026-03-16 08:30 KST  -> date = 2026-03-16
# 출력:   America/New_York     2026-03-15 19:30 EDT  -> date = 2026-03-15
# 출력:   Pacific/Kiritimati   2026-03-16 13:30 +14  -> date = 2026-03-16
# 출력:
# 출력: 같은 한 순간인데 서울 기준 2026-03-16, 뉴욕 기준 2026-03-15 — 하루가 다르다.
# 출력: 월말/분기말이면 이 하루 차이가 회계 기간을 바꾼다. date만 남기면 복구 불가.

# %% [markdown]
# ## 5. 승인 시각 ≠ 정산 시각 — 그래서 시각 프로퍼티는 여러 개일 수 있다
#
# 카드 결제는 **승인(authorization)** 시점과 **정산(settlement/posting)** 시점이 다르다.
# 사기 탐지는 승인 시각을, 회계와 잔액 확정은 정산 시각을 쓴다.
# 즉 `timestamp` 하나로 끝나지 않고 `authorizedAt`, `settledAt` 처럼 분리될 수 있다.

# %%
CARD = [
    ("T-301", ts("2026-03-15 23:47:00"), ts("2026-03-17 04:00:00"), 89_000.0),
    ("T-302", ts("2026-03-16 10:02:00"), ts("2026-03-17 04:00:00"), 15_400.0),
]
for tid, auth, settled, amt in CARD:
    lag = settled - auth
    print(f"{tid} 승인 {auth:%m-%d %H:%M} / 정산 {settled:%m-%d %H:%M} "
          f"(lag {lag.total_seconds()/3600:.1f}h) {amt:,.0f}원")

print("\n승인 기준 3/15 매출:", sum(a for _, au, _, a in CARD if au.date().day == 15))
print("정산 기준 3/15 매출:", sum(a for _, _, s, a in CARD if s.date().day == 15))
print("-> 어느 시각을 쓰느냐로 일별 매출이 달라진다. 시각 프로퍼티를 하나로 합치면 안 되는 이유.")
# 출력: T-301 승인 03-15 23:47 / 정산 03-17 04:00 (lag 28.2h) 89,000원
# 출력: T-302 승인 03-16 10:02 / 정산 03-17 04:00 (lag 18.0h) 15,400원
# 출력:
# 출력: 승인 기준 3/15 매출: 89000.0
# 출력: 정산 기준 3/15 매출: 0
# 출력: -> 어느 시각을 쓰느냐로 일별 매출이 달라진다. 시각 프로퍼티를 하나로 합치면 안 되는 이유.

# %% [markdown]
# ## 6. 시각화 — datetime 타임라인 vs date 절단
#
# 세 단으로 같은 데이터를 서로 다른 해상도로 본다.
#
# 1. **하루 전체 타임라인** — velocity 창(10분)을 붉게 강조. A-1001의 오전 점 하나가 실은 뭉친 것이다.
# 2. **09:10~09:20 확대** — 그 점이 소액 4건(카드 테스팅)이었음이 드러난다. 해상도를 올리자 사건이 나타났다.
# 3. **date 절단** — 하루 전체가 자정 한 점으로 뭉친다(원 크기 = 뭉친 건수). 1도 2도 복구할 수 없다.

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

DAY = TX[:10]  # 2026-03-15 하루치
ACCTS = ["A-1001", "A-2002"]
COLORS = {"A-1001": "#2563eb", "A-2002": "#ea580c"}
HOVER = ("%{customdata[0]}<br>%{x|%H:%M:%S}<br>"
         "%{customdata[1]:,.0f}원 @ %{customdata[2]}<extra></extra>")

fig = make_subplots(
    rows=3, cols=1, vertical_spacing=0.16,
    subplot_titles=(
        "① datetime — 하루 전체. 붉은 구간이 10분 velocity 창",
        "② 같은 구간 확대 — 소액 4건 = 카드 테스팅 버스트가 드러난다",
        "③ date 절단 — 하루가 자정 한 점으로 뭉치고 ①②가 모두 사라진다",
    ),
)

w0 = ts("2026-03-15 09:12:03")

# (①,②) 실제 시각 타임라인 — 같은 데이터를 축 범위만 바꿔 두 번 그린다
for row in (1, 2):
    for acct in ACCTS:
        rows = [r for r in DAY if r[0] == acct]
        fig.add_trace(go.Scatter(
            x=[r[2] for r in rows], y=[acct] * len(rows),
            mode="markers", name=acct, legendgroup=acct, showlegend=(row == 1),
            marker=dict(size=13, color=COLORS[acct], line=dict(width=1, color="white")),
            customdata=[(r[1], r[3], r[4]) for r in rows],
            hovertemplate=HOVER,
        ), row=row, col=1)
    fig.add_vrect(x0=w0, x1=w0 + timedelta(minutes=10),
                  fillcolor="#ef4444", opacity=0.18, line_width=0, row=row, col=1)

fig.add_annotation(x=w0 + timedelta(minutes=5), y="A-1001", yshift=34,
                   text="10분 창 안 4건 → flag", showarrow=False,
                   font=dict(color="#b91c1c", size=12), row=2, col=1)

# (③) date로 절단 — 모두 자정으로 collapse
day0 = datetime(2026, 3, 15, tzinfo=timezone.utc)
for acct in ACCTS:
    n = len([r for r in DAY if r[0] == acct])
    fig.add_trace(go.Scatter(
        x=[day0], y=[acct], mode="markers+text",
        marker=dict(size=16 + 6 * n, color=COLORS[acct], opacity=0.55,
                    line=dict(width=1, color="white")),
        text=[f"{n}건이 한 점"], textposition="middle right",
        showlegend=False, legendgroup=acct,
        hovertemplate=f"{acct}<br>2026-03-15<br>{n}건이 구분 불가<extra></extra>",
    ), row=3, col=1)

fig.update_xaxes(title_text="시각 (UTC, 2026-03-15)", tickformat="%H:%M",
                 dtick=2 * 3600_000, row=1, col=1)
fig.update_xaxes(title_text="시각 (UTC) — 09:10~09:20 확대", tickformat="%H:%M:%S",
                 dtick=120_000,
                 range=[ts("2026-03-15 09:10:00"), ts("2026-03-15 09:20:00")],
                 row=2, col=1)
fig.update_xaxes(title_text="date (시각 정보 소실)", tickformat="%Y-%m-%d",
                 dtick=86_400_000,
                 range=[datetime(2026, 3, 14, 4, tzinfo=timezone.utc),
                        datetime(2026, 3, 16, 20, tzinfo=timezone.utc)], row=3, col=1)
for row in (1, 2, 3):
    fig.update_yaxes(title_text="계좌", row=row, col=1)
fig.update_layout(
    title="시간 타입의 해상도 = 답할 수 있는 질문의 해상도",
    template="plotly_white", height=900, width=1000,
    legend=dict(orientation="h", y=-0.08),
)

_show(fig)
fig.write_image("expy.png", scale=2)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리 — 필요한 해상도만 쓴다
#
# | 프로퍼티 | 타입 | 왜 |
# |---|---|---|
# | `Transaction.timestamp` | **datetime** | velocity·impossible travel·거래 순서·감사 추적이 모두 $\Delta t$를 요구 |
# | `Account.openDate` | **date** | 계좌 개설은 "며칠에 열렸나"로 충분. 09:12에 열렸다는 사실로 답할 질문이 없다 |
#
# `datetime`이 항상 옳은 게 아니라, **그 프로퍼티로 답할 질문이 요구하는 해상도**를
# 고르는 것이다. 필요 이상의 해상도는 저장·인덱스·타임존 처리 비용과
# 개인정보(행동 시각) 노출을 늘린다.
