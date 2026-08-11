# %% [markdown]
# # Department.budget 은 왜 `decimal` 인가
#
# 필요 패키지: plotly, kaleido (시각화 셀에서만 사용)
#
# HR 온톨로지의 `Department.budget` 은 금액이다. 금액은 "십진 소수"로 정의된
# 값인데, `float`(IEEE 754 binary64)은 십진 소수를 정확히 담을 수 없다.
# 이 노트북은 그 오차가 예산 집계에서 어떻게 자라는지 단계적으로 보여준다.

# %%
# 필요 패키지: plotly, kaleido
import math
import os
from decimal import Decimal, ROUND_HALF_UP, getcontext

import plotly.graph_objects as go

getcontext().prec = 34  # IEEE 754 decimal128 수준의 십진 유효숫자


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


print("setup ok")
# 출력: setup ok

# %% [markdown]
# ## 1. `0.1 + 0.2 != 0.3` — 이진 분수 전개
#
# binary64는 값을 $(-1)^{s}\cdot 1.f \cdot 2^{e}$ 형태, 즉 **2의 거듭제곱 분수의 합**으로만
# 표현한다. 어떤 십진 소수 $\frac{a}{10^{k}}$ 가 정확히 표현되려면 분모가 $2^{n}$ 꼴이어야 한다.
#
# $$0.1 = \frac{1}{10} = \frac{1}{2\cdot 5}$$
#
# 분모에 인수 5가 있으므로 $0.1$ 은 유한한 이진 소수로 끝나지 않고
# $0.0\overline{0011}_2$ 처럼 무한 순환한다. 53비트에서 잘리면서 저장된 값은
# 우리가 쓴 `0.1` 이 **아니다**.

# %%
print(0.1 + 0.2)                 # repr은 "가장 짧은 왕복 표현"이라 오차가 숨는다
print(0.1 + 0.2 == 0.3)
print(f"{0.1:.27f}")             # 실제 저장된 값을 소수 27자리까지 펼쳐 본다
print(f"{0.2:.27f}")
print(f"{0.3:.27f}")
print(Decimal(0.1))              # float에 담긴 값의 완전한 십진 전개
# 출력: 0.30000000000000004
# 출력: False
# 출력: 0.100000000000000005551115123
# 출력: 0.200000000000000011102230246
# 출력: 0.299999999999999988897769754
# 출력: 0.1000000000000000055511151231257827021181583404541015625

# %%
# 반면 Decimal은 십진수를 십진수로 저장한다 (단, 문자열로 만들어야 한다).
print(Decimal("0.1") + Decimal("0.2") == Decimal("0.3"))
print(Decimal("0.1") + Decimal("0.2"))
# 출력: True
# 출력: 0.3

# %% [markdown]
# ## 2. 예산 항목 10,000건 합산 — 누적 오차
#
# 각 덧셈은 최대 $\tfrac{1}{2}\varepsilon$ 의 상대 오차를 만들고($\varepsilon = 2^{-52}$),
# 순차 합산에서 오차는 대략 항목 수 $n$ 에 비례해 누적된다.
#
# $$\left|\hat{S}_n - S_n\right| \lesssim (n-1)\,\varepsilon \sum_i |x_i|$$
#
# `Department.budget` 이 cost center 롤업(하위 조직 예산의 합)으로 계산된다면
# 이 오차가 그대로 상위 부서의 예산 총액에 실린다.

# %%
ITEM = "99999.99"          # 부서 예산 항목 1건 (원)
N = 50_000                 # 전사 cost center 롤업 규모의 라인 아이템 수

float_sum = 0.0
for _ in range(N):
    float_sum += float(ITEM)

dec_sum = Decimal("0")
for _ in range(N):
    dec_sum += Decimal(ITEM)

exact = Decimal(ITEM) * N
print("float  합산:", repr(float_sum))
print("Decimal 합산:", dec_sum)
print("정확한 값   :", exact)
print("float 오차  :", Decimal(float_sum) - exact)
print("float == 정확?", Decimal(float_sum) == exact, "/ Decimal == 정확?", dec_sum == exact)
print("math.fsum   :", repr(math.fsum([float(ITEM)] * N)))
# 출력: float  합산: 4999999499.99366
# 출력: Decimal 합산: 4999999500.00
# 출력: 정확한 값   : 4999999500.00
# 출력: float 오차  : -0.00634002685546875
# 출력: float == 정확? False / Decimal == 정확? True
# 출력: math.fsum   : 4999999500.0

# %% [markdown]
# 오차는 $-0.0063$ 원, 사람 눈에는 0이다. 그런데 이 오차가 **표기 단위(0.01원)의 절반을
# 넘어서면** 반올림 결과가 바뀐다. `round(float_sum, 2)` 로 감사 보고서를 찍으면
# `4999999499.99` 가 되어 원장(ledger)의 `4999999500.00` 과 **1전 단위로 불일치**한다.
# 총액이 50억 원인데 마지막 자리가 안 맞는 보고서는 감사에서 그대로 지적 사항이 된다.
#
# `math.fsum`(보상 합산)은 이 케이스에서는 맞췄지만, 각 항목 자체가 부정확한 float이라
# 일반적으로 "정확함"을 보장하지 못한다. 즉 합산 알고리즘을 바꾸는 것은 근본 처방이 아니다.

# %%
print("float 합산 반올림 :", round(float_sum, 2))
print("Decimal 합산      :", dec_sum.quantize(Decimal("0.01")))
print("보고서 값 일치?    :", f"{round(float_sum, 2):.2f}" == f"{dec_sum:.2f}")
# 출력: float 합산 반올림 : 4999999499.99
# 출력: Decimal 합산      : 4999999500.00
# 출력: 보고서 값 일치?    : False

# %% [markdown]
# ## 3. 예산 배분 — 잔액이 0으로 안 맞는 현상
#
# resource planning에서는 부서 예산을 팀/비목에 비율로 쪼갠다.
# 비율 합이 $\sum w_i = 1$ 이어도 float 곱셈·반올림 뒤에는
# $\sum \mathrm{round}(B\,w_i) \ne B$ 가 되기 쉽다.

# %%
BUDGET = Decimal("1000000.00")
WEIGHTS = [Decimal("0.3333"), Decimal("0.3333"), Decimal("0.3334")]

# (a) float 배분
b_f = float(BUDGET)
alloc_f = [round(b_f * float(w), 2) for w in WEIGHTS]
print("float 배분 :", alloc_f, "합계:", repr(sum(alloc_f)), "잔액:", repr(b_f - sum(alloc_f)))

# (b) Decimal + quantize (반올림 규칙을 명시)
CENT = Decimal("0.01")
alloc_d = [(BUDGET * w).quantize(CENT, rounding=ROUND_HALF_UP) for w in WEIGHTS]
print("Decimal 배분:", alloc_d, "합계:", sum(alloc_d), "잔액:", BUDGET - sum(alloc_d))
# 출력: float 배분 : [333300.0, 333300.0, 333400.0] 합계: 1000000.0 잔액: 0.0
# 출력: Decimal 배분: [Decimal('333300.00'), Decimal('333300.00'), Decimal('333400.00')] 합계: 1000000.00 잔액: 0.00

# %% [markdown]
# 위 비율은 깔끔하게 나눠떨어져 우연히 맞았다.
# 나눠떨어지지 않는 실제 케이스(1/3씩 3개 팀, 인원수 비례 배분)에서는 잔액이 남는다.

# %%
BUDGET = Decimal("1000000.00")
HEADCOUNT = [7, 11, 13]      # 인원수 비례 배분
total_hc = sum(HEADCOUNT)

# (a) float
b_f = float(BUDGET)
alloc_f = [round(b_f * h / total_hc, 2) for h in HEADCOUNT]
print("float   배분:", alloc_f)
print("float   잔액:", repr(b_f - sum(alloc_f)))

# (b) Decimal quantize only — 잔액 발생을 '보이게' 만든다
alloc_d = [(BUDGET * h / total_hc).quantize(CENT, rounding=ROUND_HALF_UP) for h in HEADCOUNT]
residual = BUDGET - sum(alloc_d)
print("Decimal 배분:", [str(a) for a in alloc_d])
print("Decimal 잔액:", residual)

# (c) 잔액 보정(largest-remainder): 마지막(또는 최대 잔여) 항목에 잔액을 흘려보낸다
alloc_fix = list(alloc_d)
alloc_fix[-1] += residual
print("보정 후 배분:", [str(a) for a in alloc_fix])
print("보정 후 잔액:", BUDGET - sum(alloc_fix), "/ 합계 일치?", sum(alloc_fix) == BUDGET)
# 출력: float   배분: [225806.45, 354838.71, 419354.84]
# 출력: float   잔액: 0.0
# 출력: Decimal 배분: ['225806.45', '354838.71', '419354.84']
# 출력: Decimal 잔액: 0.00
# 출력: 보정 후 배분: ['225806.45', '354838.71', '419354.84']
# 출력: 보정 후 잔액: 0.00 / 합계 일치? True

# %% [markdown]
# 이번에도 맞았다 — 잔액 문제는 **반올림 방향이 한쪽으로 몰릴 때** 터진다.
# 세 항목이 모두 내림되는 조합을 만들어 보자.

# %%
BUDGET = Decimal("100.00")
HEADCOUNT = [1, 1, 1]        # 100 / 3 = 33.333...
total_hc = sum(HEADCOUNT)

alloc_d = [(BUDGET * h / total_hc).quantize(CENT, rounding="ROUND_DOWN") for h in HEADCOUNT]
residual = BUDGET - sum(alloc_d)
print("배분:", [str(a) for a in alloc_d], "합계:", sum(alloc_d), "잔액:", residual)

alloc_fix = list(alloc_d)
alloc_fix[-1] += residual    # 잔액을 명시적으로 귀속시켜야 원장이 맞는다
print("보정:", [str(a) for a in alloc_fix], "합계:", sum(alloc_fix), "일치?", sum(alloc_fix) == BUDGET)

# float으로 같은 일을 하면 잔액 자체를 신뢰할 수 없다
b_f = 100.0
alloc_f = [math.floor(b_f / 3 * 100) / 100] * 3
print("float 배분:", alloc_f, "잔액:", repr(b_f - sum(alloc_f)))
# 출력: 배분: ['33.33', '33.33', '33.33'] 합계: 99.99 잔액: 0.01
# 출력: 보정: ['33.33', '33.33', '33.34'] 합계: 100.00 일치? True
# 출력: float 배분: [33.33, 33.33, 33.33] 잔액: 0.010000000000005116

# %% [markdown]
# 마지막 줄이 핵심이다. Decimal의 잔액은 정확히 `0.01`(=1전)이라 **어느 팀에 줄지**만
# 정하면 끝난다. float의 잔액은 `0.010000000000005116` 이라
# "잔액이 정확히 1전인가?"라는 판정 자체가 부동소수점 비교 문제로 변한다.

# %% [markdown]
# ## 4. 대안: 최소단위 정수 저장 (cents / 원)
#
# 금액을 $\text{원} \times 100$ (전) 같은 **정수 최소단위**로 저장하면
# 덧셈·뺄셈은 완전히 정확하다. Python `int` 는 임의 정밀도라 오버플로도 없다.
# 다만 나눗셈·비율 계산에서는 여전히 반올림 정책과 잔액 보정을 직접 써야 한다.

# %%
minor = [1234567, 89, 100_000_000]     # 전(1/100원) 단위 정수
print("정수 합계(전):", sum(minor))
print("원 표기:", f"{sum(minor) // 100}.{sum(minor) % 100:02d}")

# Decimal <-> 최소단위 정수는 무손실 왕복
d = Decimal("12345.67")
as_minor = int(d.scaleb(2))
print("Decimal -> 전:", as_minor, "/ 전 -> Decimal:", Decimal(as_minor).scaleb(-2))
print("왕복 일치?", Decimal(as_minor).scaleb(-2) == d)
# 출력: 정수 합계(전): 101234656
# 출력: 원 표기: 1012346.56
# 출력: Decimal -> 전: 1234567 / 전 -> Decimal: 12345.67
# 출력: 왕복 일치? True

# %% [markdown]
# ## 5. 항목 수에 따른 float 절대 오차 성장
#
# 순차 float 합산의 절대 오차는 $n$ 에 대해 거의 선형으로 커진다.
# 아래는 항목 1건 = `99999.99` 원일 때, 항목 수 $n$ 을 늘려가며
# $|\hat{S}_n - S_n|$ 을 Decimal 기준값과 비교해 그린 것이다.
# 오차는 반올림 방향이 오르내리므로 톱니처럼 흔들리지만, 상한(envelope)은 $n$ 에 비례해 자란다.

# %%
ITEM_D = Decimal("99999.99")
ITEM_F = float(ITEM_D)
MAX_N = 200_000

ns, errs, cents = [], [], []
acc = 0.0
checkpoints = {int(MAX_N * i / 40) for i in range(1, 41)}
for i in range(1, MAX_N + 1):
    acc += ITEM_F
    if i in checkpoints:
        exact_i = ITEM_D * i
        err = abs(Decimal(acc) - exact_i)
        ns.append(i)
        errs.append(float(err))
        cents.append(float(err / Decimal("0.01")))   # 1전(0.01원) 대비 배수

print("n=%d 오차=%.6e 원 (%.2f 전)" % (ns[0], errs[0], cents[0]))
print("n=%d 오차=%.6e 원 (%.2f 전)" % (ns[len(ns) // 2], errs[len(ns) // 2], cents[len(ns) // 2]))
print("n=%d 오차=%.6e 원 (%.2f 전)" % (ns[-1], errs[-1], cents[-1]))
print("1전(0.01원)을 넘는 최초 n:", next((n for n, c in zip(ns, cents) if c >= 1.0), None))
# 출력: n=5000 오차=3.170967e-05 원 (0.00 전)
# 출력: n=105000 오차=1.892853e-02 원 (1.89 전)
# 출력: n=200000 오차=1.311874e-02 원 (1.31 전)
# 출력: 1전(0.01원)을 넘는 최초 n: 70000

# %%
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=ns, y=errs, mode="lines+markers", name="float 순차 합산 절대 오차",
    line=dict(color="#c0392b", width=2), marker=dict(size=5),
))
fig.add_trace(go.Scatter(
    x=ns, y=[0.0] * len(ns), mode="lines", name="Decimal 합산 오차 (항상 0)",
    line=dict(color="#27ae60", width=2, dash="dash"),
))
fig.add_hline(
    y=0.01, line=dict(color="#8e44ad", width=1, dash="dot"),
    annotation_text="1전 = 0.01원 (보고서 표기 단위)", annotation_position="top left",
)
fig.update_layout(
    title="Department.budget 합산: 항목 수에 따른 float 누적 오차 (항목당 99,999.99원)",
    xaxis_title="합산 항목 수 n",
    yaxis_title="|float 합계 - 정확한 합계|  (원)",
    template="plotly_white",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    width=900, height=520,
)
_show(fig)

png_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(png_path, scale=2)
print("saved:", os.path.basename(png_path), os.path.exists(png_path))
# 출력: saved: expy.png True

# %% [markdown]
# ## 정리
#
# | | float (binary64) | Decimal / SQL `decimal(p,s)` | 정수 최소단위 |
# |---|---|---|---|
# | `0.1` 표현 | 부정확 | 정확 | 정확(=10) |
# | 합산 정확도 | $O(n\varepsilon)$ 오차 누적 | 정확(스케일 내) | 정확 |
# | 잔액 판정 | `!= 0` 오판 발생 | 정확히 비교 가능 | 정확히 비교 가능 |
# | 반올림 제어 | 불가(암묵적) | `quantize` + 규칙 명시 | 직접 구현 |
#
# 그래서 HR 온톨로지에서 `Department.budget` 의 타입은 `decimal` 이다.
# cost center analysis와 resource planning이 이 값을 합하고 나누고 비교하며,
# 그 결과가 감사 대상 숫자가 되기 때문이다.
