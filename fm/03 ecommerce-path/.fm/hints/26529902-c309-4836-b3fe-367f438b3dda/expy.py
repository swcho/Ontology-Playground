# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
# 표준 라이브러리 decimal / fractions 만으로도 대부분의 셀은 실행 가능하다.

# %% [markdown]
# # 왜 `Order.total` / `Product.price` 는 `decimal (USD)` 인가
#
# 이 노트북은 두 가지를 실험으로 확인한다.
#
# 1. **왜 `decimal`인가** — IEEE 754 이진 부동소수점은 `0.1`, `19.99` 같은 십진 소수를
#    정확히 표현하지 못하고, 그 오차가 합산·정산 과정에서 누적된다.
# 2. **왜 `(USD)`인가** — 단위 없는 수치는 비교·집계가 성립하지 않는다.
#    통화를 타입 메타데이터로 못 박아야 서로 다른 통화가 한 컬럼에 섞이지 않는다.

# %%
from decimal import Decimal, getcontext, ROUND_HALF_EVEN, ROUND_HALF_UP
from fractions import Fraction
import random


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


print("준비 완료")
# 출력: 준비 완료

# %% [markdown]
# ## 1. 이진 부동소수점은 십진 소수를 담지 못한다
#
# IEEE 754 `binary64`(파이썬 `float`)는 값을 다음 꼴로만 표현한다.
#
# $$x = (-1)^{s}\;\times\;\left(1 + \sum_{i=1}^{52} b_i 2^{-i}\right)\;\times\;2^{e}$$
#
# 즉 **분모가 $2$의 거듭제곱인 유리수**만 정확히 표현된다.
# $0.1 = \dfrac{1}{10} = \dfrac{1}{2 \cdot 5}$ 는 분모에 소인수 $5$가 있으므로
# 유한한 이진 소수로 쓸 수 없다. 반면 `Decimal`은 분모가 $10$의 거듭제곱인
# $x = m \times 10^{-k}$ 를 정확히 표현하므로, 화폐 금액(센트 단위 = $10^{-2}$)이
# 손실 없이 들어간다.

# %%
print("0.1 + 0.2       =", 0.1 + 0.2)
print("== 0.3 ?        ", 0.1 + 0.2 == 0.3)
print("float 0.1 의 실제 값:", Decimal(0.1))
print("float 19.99 의 실제 값:", Decimal(19.99))
# 출력: 0.1 + 0.2       = 0.30000000000000004
# 출력: == 0.3 ?         False
# 출력: float 0.1 의 실제 값: 0.1000000000000000055511151231257827021181583404541015625
# 출력: float 19.99 의 실제 값: 19.989999999999998436805981327779591083526611328125

# %%
# Decimal 은 "사람이 쓴 십진 문자열"을 그대로 보존한다.
print("Decimal('0.1') + Decimal('0.2') =", Decimal("0.1") + Decimal("0.2"))
print("== Decimal('0.3') ?             ", Decimal("0.1") + Decimal("0.2") == Decimal("0.3"))
# 주의: Decimal(0.1) 처럼 float 을 넘기면 이미 오염된 값이 들어온다.
print("Decimal(0.1) == Decimal('0.1') ?", Decimal(0.1) == Decimal("0.1"))
# 출력: Decimal('0.1') + Decimal('0.2') = 0.3
# 출력: == Decimal('0.3') ?              True
# 출력: Decimal(0.1) == Decimal('0.1') ? False

# %% [markdown]
# ## 2. 오차는 "보이지 않다가" 합산에서 드러난다
#
# `Order.total`은 장바구니 항목들의 합이다. 항목 하나의 오차는 $10^{-16}$ 수준이지만,
# $n$개를 더하면 오차는 대략
#
# $$|E_n| \lesssim (n-1)\,\varepsilon \sum_{i=1}^{n} |x_i|, \qquad \varepsilon = 2^{-53} \approx 1.11 \times 10^{-16}$$
#
# 까지 커질 수 있다(실제로는 부호가 상쇄되어 $\sqrt{n}$ 정도로 자라는 경우가 많다).
# 문제는 크기가 아니라 **경계**다. 오차가 반 센트($0.005$)를 넘는 순간 반올림 결과가
# 뒤집혀, 정산 금액이 1센트 어긋난다.

# %%
# Product.price = 0.10 USD 인 상품을 100개 담은 Shopping-Cart
prices_float = [0.10] * 100
prices_dec = [Decimal("0.10")] * 100

subtotal_float = sum(prices_float)
subtotal_dec = sum(prices_dec)

print("float   subtotal:", repr(subtotal_float))
print("Decimal subtotal:", subtotal_dec)
print("float == 10.0 ? ", subtotal_float == 10.0)
print("절대 오차       :", Decimal(subtotal_float) - Decimal("10"))
# 출력: float   subtotal: 9.99999999999998
# 출력: Decimal subtotal: 10.00
# 출력: float == 10.0 ?  False
# 출력: 절대 오차       : -1.9539925233402755E-14

# %%
# 더 현실적인 케이스: 소수 둘째 자리 가격 100개 (seed 고정)
random.seed(7)
prices = [Decimal(random.randrange(1, 20000)) / 100 for _ in range(100)]

total_dec = sum(prices)                       # 정확한 합
total_float = sum(float(p) for p in prices)   # float 누적 합

print("Decimal total:", total_dec)
print("float   total:", repr(total_float))
print("차이         :", Decimal(total_float) - total_dec)
print("2자리 반올림 비교:",
      total_dec.quantize(Decimal("0.01")),
      "vs", round(total_float, 2))
# 출력: Decimal total: 10689.45
# 출력: float   total: 10689.449999999995
# 출력: 차이         : -4.729372449219226837158203125E-12
# 출력: 2자리 반올림 비교: 10689.45 vs 10689.45
#
# 이 규모에서는 반올림 결과가 아직 같다. 바로 이 점이 함정이다 —
# float 금액은 "대개 맞다가" 항목 수·금액 규모가 커지면 조용히 틀린다.

# %% [markdown]
# ## 3. 반 센트를 넘기면 실제로 금액이 바뀐다
#
# 오차 자체보다 위험한 것은 **반올림 경계 근처의 값**이다.
# `x.xx5` 형태의 중간값은 float 으로 저장되는 순간 이미 위/아래로 치우쳐 있어서,
# "정확히 절반이면 올림" 같은 회계 규칙이 무력화된다.

# %%
cases = ["2.675", "1.005", "8.835", "0.125"]
for s in cases:
    f = float(s)
    print(f"{s:>6}  float실제값={Decimal(f):.20f}  round(f,2)={round(f, 2):<6}"
          f"  Decimal HALF_UP={Decimal(s).quantize(Decimal('0.01'), ROUND_HALF_UP)}")
# 출력:  2.675  float실제값=2.67499999999999982236  round(f,2)=2.67    Decimal HALF_UP=2.68
# 출력:  1.005  float실제값=1.00499999999999989342  round(f,2)=1.0     Decimal HALF_UP=1.01
# 출력:  8.835  float실제값=8.83500000000000085265  round(f,2)=8.84    Decimal HALF_UP=8.84
# 출력:  0.125  float실제값=0.12500000000000000000  round(f,2)=0.12    Decimal HALF_UP=0.13
#
# 2.675, 1.005 는 float 으로 저장되는 순간 이미 "절반보다 아래"라서 내림된다.
# 0.125 는 이진수로 정확히 표현되는(1/8) 진짜 중간값이라 파이썬 round() 의
# 은행가 반올림이 적용되어 0.12 가 된다 — 규칙 자체가 달라진다.

# %% [markdown]
# ## 4. 반올림 모드: `ROUND_HALF_EVEN` vs `ROUND_HALF_UP`
#
# `Decimal`은 오차가 없는 대신, **반올림 규칙을 명시적으로 선택**하게 만든다.
#
# - `ROUND_HALF_UP` — 정확히 절반이면 항상 올림. 소비자 청구서·세금계산서 관행.
# - `ROUND_HALF_EVEN` (banker's rounding, 파이썬 `Decimal` 기본값) — 절반이면 짝수 쪽으로.
#   대량 집계 시 올림/내림이 균형을 이뤄 **편향(bias)이 0에 수렴**한다.
#
# 기대 편향은 대략
#
# $$\mathbb{E}[\text{HALF\_UP bias}] = +\tfrac{1}{2}\times 10^{-2} \times P(\text{tie}), \qquad
#   \mathbb{E}[\text{HALF\_EVEN bias}] \approx 0$$

# %%
ties = [Decimal(f"{n}.{d}5") for n in range(1, 6) for d in range(0, 10)]
up = sum(t.quantize(Decimal("0.1"), ROUND_HALF_UP) for t in ties)
even = sum(t.quantize(Decimal("0.1"), ROUND_HALF_EVEN) for t in ties)
exact = sum(ties)

print("정확한 합       :", exact)
print("HALF_UP   합    :", up, " 편향:", up - exact)
print("HALF_EVEN 합    :", even, " 편향:", even - exact)
# 출력: 정확한 합       : 175.00
# 출력: HALF_UP   합    : 177.5  편향: 2.50
# 출력: HALF_EVEN 합    : 175.0  편향: 0.00
#
# 50건의 중간값만으로도 HALF_UP 은 +2.50 을 만들어낸다. 건수가 늘수록 선형으로 커진다.

# %% [markdown]
# ## 5. 대안: 정수 minor unit(cents) 저장
#
# `decimal` 대신 **금액을 최소 통화 단위 정수로 저장**하는 방식도 널리 쓰인다
# (Stripe 등 결제 API의 `amount` 필드가 이 방식이다).
#
# $$\text{price}_{\text{USD}} = \frac{\text{price\_cents}}{100}$$
#
# | 방식 | 정확도 | 나눗셈/세금 계산 | 스키마 가독성 | 통화 표현 |
# |---|---|---|---|---|
# | `float` | ✗ 손실 | 오차 누적 | 좋음 | 없음 |
# | `decimal(USD)` | ✓ 십진 정확 | 스케일·반올림 모드 명시 필요 | 좋음 | 타입에 포함 |
# | `integer cents` | ✓ 완전 정확 | 나눗셈 시 몫/나머지 직접 처리 | 단위 오해 위험 | 별도 컬럼 필요 |
#
# 온톨로지 스키마에서 `decimal (USD)`를 쓰는 이유는, **정확도와 "읽는 사람이 단위를
# 오해하지 않는 것"을 동시에** 만족시키기 때문이다. `19.99`가 달러인지 센트인지
# 헷갈릴 여지가 없다.

# %%
def split_evenly(total_cents: int, n: int) -> list[int]:
    """총액을 n명에게 1센트도 잃지 않고 분배한다."""
    q, r = divmod(total_cents, n)
    return [q + (1 if i < r else 0) for i in range(n)]


order_total = Decimal("100.00")
cents = int(order_total * 100)
parts = split_evenly(cents, 3)

print("주문 총액(cents):", cents)
print("3분할          :", parts, "합계:", sum(parts))
print("USD 환산       :", [Decimal(p) / 100 for p in parts])

# 순진하게 나눈 뒤 각자 반올림하면 1센트가 증발한다 (penny leak)
naive = [round(100.00 / 3, 2)] * 3
print("float 나눗셈 후 반올림:", naive, "합계:", sum(naive), "-> 손실:", 100.00 - sum(naive))
# 출력: 주문 총액(cents): 10000
# 출력: 3분할          : [3334, 3333, 3333] 합계: 10000
# 출력: USD 환산       : [Decimal('33.34'), Decimal('33.33'), Decimal('33.33')]
# 출력: float 나눗셈 후 반올림: [33.33, 33.33, 33.33] 합계: 99.99 -> 손실: 0.010000000000005116
#
# 손실값조차 0.01 이 아니라 0.010000000000005116 로 나온다.
# 정수 cents 방식은 divmod 의 나머지를 명시적으로 분배해 총액 보존을 보장한다.

# %% [markdown]
# ## 6. `(USD)`가 없으면 집계 자체가 의미를 잃는다
#
# 온톨로지에서 타입은 "저장 형식"이 아니라 **값이 무엇을 의미하는지에 대한 계약**이다.
# 숫자 $42$ 는 그 자체로 아무 뜻이 없다. 물리량은 언제나
#
# $$\text{quantity} = \text{numeric value} \times \text{unit}$$
#
# 이고, **같은 단위끼리만 덧셈·비교가 정의된다**(dimensional homogeneity).
# `Product.price : decimal` 만 있고 `(USD)`가 없으면
# `SUM(price)` 는 달러와 원과 엔을 아무 저항 없이 더해버린다.

# %%
class Money:
    """금액 = (십진 수치, 통화). 단위가 다르면 연산을 거부한다."""

    def __init__(self, amount, currency):
        self.amount = Decimal(amount)
        self.currency = currency

    def __add__(self, other):
        if self.currency != other.currency:
            raise TypeError(f"통화 불일치: {self.currency} + {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __repr__(self):
        return f"{self.amount} {self.currency}"


raw = [("19.99", "USD"), ("25000", "KRW"), ("5.00", "USD")]

# (a) 단위를 버린 경우 — 조용히 틀린 합계가 나온다
naive_total = sum(Decimal(a) for a, _ in raw)
print("단위 없는 SUM(price):", naive_total, "  <- 19.99달러 + 25000원 + 5달러 ???")

# (b) 단위를 타입에 넣은 경우 — 즉시 실패한다
try:
    total = Money("0", "USD")
    for a, c in raw:
        total = total + Money(a, c)
except TypeError as e:
    print("Money 합산 실패:", e)

usd_only = [Money(a, c) for a, c in raw if c == "USD"]
print("USD 만 집계:", sum(usd_only[1:], usd_only[0]))
# 출력: 단위 없는 SUM(price): 25024.99   <- 19.99달러 + 25000원 + 5달러 ???
# 출력: Money 합산 실패: 통화 불일치: USD + KRW
# 출력: USD 만 집계: 24.99 USD

# %% [markdown]
# > `25024.99` 는 **어떤 통화로도 존재하지 않는 값**이다. 그런데 float/decimal 타입만
# > 보고는 이 결과가 틀렸다는 사실을 알아낼 방법이 없다. 오류가 "예외"가 아니라
# > "그럴듯한 숫자"로 나타나는 것이 단위 누락의 가장 위험한 점이다.

# %% [markdown]
# ## 7. 항목 수 대비 float 누적 오차의 성장
#
# 아래 그래프는 합산 항목 수 $n$ 을 늘려가며 부동소수점 누적합과 정확한 합의
# 절대 오차를 그린 것이다. 붉은 점선은 **반 센트($0.005$ USD)** — 이 선을 넘으면
# 반올림 결과가 실제로 1센트 이상 어긋난다.
#
# `binary32`(SQL 의 `REAL` / `FLOAT4`) 곡선을 함께 그린 이유는, 많은 스키마가
# "그냥 실수형"으로 32비트를 고르기 때문이다. $\varepsilon_{32} = 2^{-24} \approx 6\times10^{-8}$
# 이므로 수천 건만 모여도 반 센트 경계를 넘어버린다.

# %%
import struct
import plotly.graph_objects as go

getcontext().prec = 60


def f32(x):
    """binary32 로 반올림한 값을 돌려준다 (SQL REAL 컬럼 흉내)."""
    return struct.unpack("f", struct.pack("f", x))[0]


def error_curves(price_gen, ns, seed=11):
    rng = random.Random(seed)
    prices = [price_gen(rng) for _ in range(max(ns))]
    ns_set = set(ns)
    acc64, acc32, exact = 0.0, f32(0.0), Fraction(0)
    e64, e32 = [], []
    for i, p in enumerate(prices, start=1):
        acc64 += float(p)
        acc32 = f32(acc32 + f32(float(p)))
        exact += Fraction(p)
        if i in ns_set:
            e64.append(abs(float(Fraction(acc64) - exact)))
            e32.append(abs(float(Fraction(acc32) - exact)))
    return e64, e32


ns = sorted({n for n in (int(10 ** (k / 8)) for k in range(8, 49)) if n >= 10})

e64_rand, e32_rand = error_curves(lambda r: Decimal(r.randrange(1, 20000)) / 100, ns)
e64_dime, _ = error_curves(lambda r: Decimal("0.10"), ns)

FLOOR = 1e-17
fig = go.Figure()
fig.add_trace(go.Scatter(x=ns, y=[max(v, FLOOR) for v in e32_rand],
                         mode="lines+markers", name="binary32 (SQL REAL) 누적합 오차",
                         line=dict(color="#dc2626", width=2), marker=dict(size=4)))
fig.add_trace(go.Scatter(x=ns, y=[max(v, FLOOR) for v in e64_rand],
                         mode="lines+markers", name="binary64 (float) 누적합 오차 — 무작위 가격",
                         line=dict(color="#2563eb", width=2), marker=dict(size=4)))
fig.add_trace(go.Scatter(x=ns, y=[max(v, FLOOR) for v in e64_dime],
                         mode="lines+markers", name="binary64 (float) 누적합 오차 — $0.10 반복",
                         line=dict(color="#f59e0b", width=2, dash="dot"), marker=dict(size=4)))
fig.add_trace(go.Scatter(x=ns, y=[FLOOR] * len(ns),
                         mode="lines", name="Decimal / 정수 cents — 오차 정확히 0",
                         line=dict(color="#059669", width=3)))
fig.add_hline(y=0.005, line_dash="dash", line_color="#111827",
              annotation_text="반 센트 (0.005 USD) — 이 위로는 반올림 결과가 뒤집힌다",
              annotation_position="top left")

fig.update_layout(
    # 주의: plotly 제목/라벨에서 짝을 이룬 '$'는 LaTeX 수식으로 해석되므로 쓰지 않는다.
    title=dict(text="합산 항목 수 대비 부동소수점 누적합 오차 (항목 가격 0.01~199.99 USD)",
               x=0.02, y=0.96),
    xaxis=dict(title="합산한 항목 수 n (log)", type="log",
               tickvals=[10, 100, 1_000, 10_000, 100_000, 1_000_000],
               ticktext=["10", "100", "1천", "1만", "10만", "100만"]),
    yaxis=dict(title="|부동소수점 합 − 정확한 합|  USD (log)", type="log",
               range=[-17.6, 1.5],
               tickvals=[1e-17, 1e-14, 1e-11, 1e-8, 1e-5, 1e-2, 1e1],
               exponentformat="power"),
    legend=dict(orientation="h", y=-0.26, x=0),
    template="plotly_white",
    margin=dict(t=90, b=120),
    width=980, height=580,
)

_show(fig)

import os
_out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(_out, scale=2)
print("saved:", _out)
# 출력: saved: .../expy.png

# %% [markdown]
# ## 정리
#
# | 관찰 | 스키마 결정 |
# |---|---|
# | `0.1`, `19.99` 는 binary64 로 표현 불가 | 금액은 `float` 금지 |
# | 오차가 항목 수에 따라 자라 반 센트를 넘김 | 십진 정확 타입(`decimal`) 또는 정수 cents |
# | `x.xx5` 중간값이 float 에서 이미 치우침 | 반올림 모드(`HALF_UP` / `HALF_EVEN`)를 명시 |
# | 단위 없는 `SUM` 이 그럴듯한 오답을 냄 | 통화를 타입 메타데이터 `(USD)` 로 고정 |
#
# 그래서 `Order.total`, `Product.price`, `Shopping-Cart.subtotal`, `Buyer.totalSpent` 는
# 모두 **`decimal (USD)`** 로 선언된다. 네 속성이 같은 타입·같은 단위를 공유해야
# "카트 평균값 vs 주문 평균값", "생애 총 구매액" 같은 비교·집계가 성립한다.
