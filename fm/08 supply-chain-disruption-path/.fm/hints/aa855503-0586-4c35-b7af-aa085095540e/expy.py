# %% [markdown]
# # Phase 3 긴급도(urgency) 계산식과 임계값
#
# 공급망 붕괴 대응 파이프라인 Phase 3(minute 15)의 계산 엔진은 노출된 제품 라인마다
# 두 값을 만든다.
#
# $$\text{revenueAtRisk} = \frac{\text{annualRevenue}}{365} \times \text{daysOfSupplyOnHand}$$
#
# $$\text{urgency} = 100 - (\text{daysOfSupplyOnHand} \times 10)$$
#
# 그리고 $\text{urgency} > 70$ 인 제품 라인을 **critical** 로 분류한다.
#
# 임계값을 재고 일수로 되돌리면:
#
# $$100 - 10d > 70 \;\Longleftrightarrow\; 10d < 30 \;\Longleftrightarrow\; d < 3$$
#
# 즉 임계값 70은 "재고 3일 미만"의 다른 표기법이다.

# %%
# 필요 패키지: plotly, kaleido, numpy
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


URGENCY_THRESHOLD = 70

# %% [markdown]
# ## 1단계: 계산식 그대로 구현하고 핵심 지점 검증
#
# 기울기가 $-10$ 이므로 **재고 1일이 긴급도 10점에 정확히 대응한다.**


# %%
def urgency(days_of_supply_on_hand):
    """원문 Phase 3 계산 엔진의 식을 그대로 구현 (클램프 없음)."""
    return 100 - (days_of_supply_on_hand * 10)


def is_critical(days_of_supply_on_hand):
    return urgency(days_of_supply_on_hand) > URGENCY_THRESHOLD


for d in (0, 3, 10):
    u = urgency(d)
    print(f"daysOfSupplyOnHand={d:>2} -> urgency={u:>4}  critical={is_critical(d)}")
# 출력: daysOfSupplyOnHand= 0 -> urgency= 100  critical=True
# 출력: daysOfSupplyOnHand= 3 -> urgency=  70  critical=False
# 출력: daysOfSupplyOnHand=10 -> urgency=   0  critical=False

# %% [markdown]
# `d = 3` 은 urgency가 **정확히 70** 이고 조건은 `> 70` 이므로 critical에 포함되지 않는다.
# `daysOfSupplyOnHand` 가 정수형이므로 실제 critical 집합은 $d \in \{0, 1, 2\}$ 다.

# %%
print("경계 확인 (정수 재고):")
for d in range(0, 6):
    print(f"  d={d} urgency={urgency(d):>3} critical={is_critical(d)}")
print("critical 집합 =", [d for d in range(0, 21) if is_critical(d)])
# 출력: 경계 확인 (정수 재고):
# 출력:   d=0 urgency=100 critical=True
# 출력:   d=1 urgency= 90 critical=True
# 출력:   d=2 urgency= 80 critical=True
# 출력:   d=3 urgency= 70 critical=False
# 출력:   d=4 urgency= 60 critical=False
# 출력:   d=5 urgency= 50 critical=False
# 출력: critical 집합 = [0, 1, 2]

# %%
# 선형 모델의 한계 1: 재고 10일 초과 시 값이 0 이하로 발산하고 스케일 계약(0~100)이 깨진다
print("발산 확인:")
for d in (12, 30, 100):
    print(f"  d={d:>3} urgency={urgency(d):>5}")
# 출력: 발산 확인:
# 출력:   d= 12 urgency=  -20
# 출력:   d= 30 urgency= -200
# 출력:   d=100 urgency= -900

# %% [markdown]
# ## 2단계: 제품 라인 샘플 데이터
#
# 원문 Taiwan Power Outage 시나리오(`Component "GPU Module"`, `daysOfSupplyOnHand=3`)를
# 포함한 노출 제품 라인 샘플이다. `revenueAtRisk` 도 함께 계산한다.

# %%
# (productLineId, name, annualRevenue(USD), 병목 부품 daysOfSupplyOnHand, criticalityLevel)
PRODUCT_LINES = [
    ("PL-LAP-2024", "Gaming Laptop 2024", 50_000_000, 3, "Critical"),
    ("PL-WST-2024", "Workstation Pro", 30_000_000, 2, "Critical"),
    ("PL-TAB-2024", "Tablet Plus", 18_000_000, 1, "High"),
    ("PL-PHN-2024", "Phone Slim", 24_000_000, 0, "Critical"),
    ("PL-SRV-2024", "Server Rack X", 40_000_000, 5, "High"),
    ("PL-ACC-2024", "Accessory Kit", 6_000_000, 2, "Low"),
    ("PL-PRT-2024", "Printer Line", 12_000_000, 8, "Medium"),
    ("PL-CAM-2024", "Camera Module", 9_000_000, 12, "Medium"),
]

rows = []
for pid, name, revenue, dos, crit in PRODUCT_LINES:
    rows.append(
        {
            "id": pid,
            "name": name,
            "revenue": revenue,
            "dos": dos,
            "criticality": crit,
            "urgency": urgency(dos),
            "revenue_at_risk": revenue / 365 * dos,
        }
    )

rows_sorted = sorted(rows, key=lambda r: r["urgency"], reverse=True)

print(f"{'ProductLine':<20}{'dos':>4}{'urgency':>9}{'revenueAtRisk':>16}  critical")
for r in rows_sorted:
    flag = "YES" if r["urgency"] > URGENCY_THRESHOLD else "-"
    print(f"{r['name']:<20}{r['dos']:>4}{r['urgency']:>9}{r['revenue_at_risk']:>16,.0f}  {flag}")
crit_rows = [r for r in rows_sorted if r["urgency"] > URGENCY_THRESHOLD]
print(f"\ncritical_product_lines = {len(crit_rows)}개: {[r['name'] for r in crit_rows]}")
print(f"total_revenue_at_risk  = ${sum(r['revenue_at_risk'] for r in rows):,.0f}")
# 출력: ProductLine           dos  urgency   revenueAtRisk  critical
# 출력: Phone Slim              0      100               0  YES
# 출력: Tablet Plus             1       90          49,315  YES
# 출력: Workstation Pro         2       80         164,384  YES
# 출력: Accessory Kit           2       80          32,877  YES
# 출력: Gaming Laptop 2024      3       70         410,959  -
# 출력: Server Rack X           5       50         547,945  -
# 출력: Printer Line            8       20         263,014  -
# 출력: Camera Module          12      -20         295,890  -
# 출력:
# 출력: critical_product_lines = 4개: ['Phone Slim', 'Tablet Plus', 'Workstation Pro', 'Accessory Kit']
# 출력: total_revenue_at_risk  = $1,764,384

# %% [markdown]
# 주목할 두 가지 왜곡:
#
# - `Phone Slim` 은 `dos=0` 이라 urgency 100이지만 `revenueAtRisk` 는 0원이다.
#   두 식이 `daysOfSupplyOnHand` 를 **반대 방향**으로 쓰기 때문이다.
# - `Accessory Kit`(Low criticality, $6M)이 `Gaming Laptop 2024`(Critical, $50M)보다
#   급한 것으로 정렬된다 → 부품 criticality 미반영 (한계 3).

# %% [markdown]
# ## 3단계: 대안 모델
#
# **클램프** (한계 1 해소):
#
# $$u_{\text{clamp}}(d) = \min\big(100,\ \max(0,\ 100 - 10d)\big)$$
#
# **지수 감쇠** (항상 $(0, 100]$, 임박 구간 민감도 확보):
#
# $$u_{\exp}(d) = 100\, e^{-d/\tau}, \qquad \tau = \frac{-3}{\ln 0.7} \approx 8.41$$
#
# $\tau$ 를 이렇게 잡으면 $u_{\exp}(3) = 70$ 이 되어 선형 모델과 임계 지점이 정렬된다.
#
# **criticality 가중** (한계 3 해소):
#
# $$u_w(d) = u_{\text{clamp}}(d) \times w(\text{criticalityLevel})$$

# %%
TAU = -3 / np.log(0.7)
CRIT_WEIGHT = {"Critical": 1.0, "High": 0.85, "Medium": 0.6, "Low": 0.4}


def urgency_clamped(d):
    return np.minimum(100, np.maximum(0, 100 - 10 * np.asarray(d, dtype=float)))


def urgency_exp(d, tau=TAU):
    return 100 * np.exp(-np.asarray(d, dtype=float) / tau)


def urgency_weighted(d, criticality):
    return float(urgency_clamped(d)) * CRIT_WEIGHT[criticality]


print(f"tau = {TAU:.4f}")
for d in (0, 3, 10):
    print(f"  d={d:>2}  linear={urgency(d):>5}  clamped={urgency_clamped(d):>6.1f}  exp={urgency_exp(d):>6.2f}")
# 출력: tau = 8.4110
# 출력:   d= 0  linear=  100  clamped= 100.0  exp=100.00
# 출력:   d= 3  linear=   70  clamped=  70.0  exp= 70.00
# 출력:   d=10  linear=    0  clamped=   0.0  exp= 30.46

# %%
# criticality 가중을 적용하면 왜곡된 정렬이 바로잡힌다
print("가중 적용 후 재정렬:")
w_rows = sorted(rows, key=lambda r: urgency_weighted(r["dos"], r["criticality"]), reverse=True)
for r in w_rows:
    print(f"  {r['name']:<20} u={r['urgency']:>4} -> u_w={urgency_weighted(r['dos'], r['criticality']):>5.1f}")
# 출력: 가중 적용 후 재정렬:
# 출력:   Phone Slim           u= 100 -> u_w=100.0
# 출력:   Workstation Pro      u=  80 -> u_w= 80.0
# 출력:   Tablet Plus          u=  90 -> u_w= 76.5
# 출력:   Gaming Laptop 2024   u=  70 -> u_w= 70.0
# 출력:   Server Rack X        u=  50 -> u_w= 42.5
# 출력:   Accessory Kit        u=  80 -> u_w= 32.0
# 출력:   Printer Line         u=  20 -> u_w= 12.0
# 출력:   Camera Module        u= -20 -> u_w=  0.0

# %% [markdown]
# `Accessory Kit` 이 80 → 32 로 내려가 `Gaming Laptop 2024`(70) 아래로 정렬된다.

# %% [markdown]
# ## 4단계: 시각화
#
# 1. urgency 선형 함수 + 임계선 70 + critical 영역($d < 3$) 음영
# 2. 제품 라인 샘플의 urgency 정렬 막대그래프
# 3. 선형 vs 클램프 vs 지수 감쇠 비교 곡선

# %%
COL_LINE = "#2563eb"
COL_CRIT = "#dc2626"
COL_SAFE = "#64748b"
COL_EXP = "#059669"
COL_CLAMP = "#d97706"

fig = make_subplots(
    rows=2,
    cols=2,
    specs=[[{"colspan": 2}, None], [{}, {}]],
    row_heights=[0.46, 0.54],
    vertical_spacing=0.16,
    horizontal_spacing=0.11,
    subplot_titles=(
        "① urgency = 100 − (daysOfSupplyOnHand × 10) : 임계선 70 과 critical 영역",
        "② 제품 라인 urgency 정렬 (critical = urgency > 70)",
        "③ 선형 모델 vs 대안 (클램프 / 지수 감쇠)",
    ),
)

# --- ① 선형 함수 + 임계선 + critical 영역 음영 ---
d_grid = np.linspace(0, 14, 400)
u_grid = 100 - 10 * d_grid

fig.add_shape(
    type="rect",
    x0=0,
    x1=3,
    y0=-45,
    y1=110,
    fillcolor=COL_CRIT,
    opacity=0.10,
    line_width=0,
    row=1,
    col=1,
)
fig.add_annotation(
    x=1.5,
    y=32,
    text="<b>critical 영역</b><br>d &lt; 3  ⟺  urgency &gt; 70",
    showarrow=False,
    font=dict(size=12, color=COL_CRIT),
    row=1,
    col=1,
)
fig.add_hline(y=70, line=dict(color=COL_CRIT, width=2, dash="dash"), row=1, col=1)
fig.add_annotation(
    x=13.6, y=76, text="임계값 70", showarrow=False, font=dict(size=11, color=COL_CRIT), xanchor="right", row=1, col=1
)
fig.add_hline(y=0, line=dict(color="#94a3b8", width=1), row=1, col=1)
fig.add_vline(x=3, line=dict(color=COL_CRIT, width=1.5, dash="dot"), row=1, col=1)

fig.add_trace(
    go.Scatter(
        x=d_grid,
        y=u_grid,
        mode="lines",
        name="urgency (선형, 기울기 −10)",
        line=dict(color=COL_LINE, width=3),
        hovertemplate="d=%{x:.1f}일 → urgency=%{y:.0f}<extra></extra>",
    ),
    row=1,
    col=1,
)

marks_d = [0, 3, 10]
fig.add_trace(
    go.Scatter(
        x=marks_d,
        y=[urgency(d) for d in marks_d],
        mode="markers+text",
        name="검증 지점 (0 / 3 / 10일)",
        marker=dict(size=12, color=[COL_CRIT, COL_CRIT, COL_SAFE], line=dict(color="white", width=2)),
        text=[f"d={d}<br>u={urgency(d)}" for d in marks_d],
        textposition=["middle right", "top right", "top right"],
        textfont=dict(size=10),
        hovertemplate="d=%{x}일 → urgency=%{y}<extra></extra>",
    ),
    row=1,
    col=1,
)
fig.add_annotation(
    x=12.2,
    y=-32,
    text="한계: d &gt; 10 이면 urgency &lt; 0 (스케일 이탈)",
    showarrow=False,
    font=dict(size=10, color="#7c2d12"),
    xanchor="right",
    row=1,
    col=1,
)

# --- ② 제품 라인 정렬 막대 ---
bar_names = [r["name"] for r in rows_sorted]
bar_vals = [r["urgency"] for r in rows_sorted]
bar_cols = [COL_CRIT if v > URGENCY_THRESHOLD else COL_SAFE for v in bar_vals]
bar_text = [f"{v}" for v in bar_vals]

fig.add_trace(
    go.Bar(
        x=bar_names,
        y=bar_vals,
        marker=dict(color=bar_cols),
        text=bar_text,
        textposition="outside",
        textfont=dict(size=10),
        showlegend=False,
        customdata=[[r["dos"], r["criticality"], r["revenue_at_risk"]] for r in rows_sorted],
        hovertemplate=(
            "<b>%{x}</b><br>urgency=%{y}<br>daysOfSupply=%{customdata[0]}일"
            "<br>criticality=%{customdata[1]}<br>revenueAtRisk=$%{customdata[2]:,.0f}<extra></extra>"
        ),
    ),
    row=2,
    col=1,
)
fig.add_hline(y=70, line=dict(color=COL_CRIT, width=2, dash="dash"), row=2, col=1)
fig.add_annotation(
    x=bar_names[-1],
    y=76,
    text="임계값 70",
    showarrow=False,
    font=dict(size=11, color=COL_CRIT),
    xanchor="right",
    row=2,
    col=1,
)

# --- ③ 모델 비교 곡선 ---
fig.add_trace(
    go.Scatter(
        x=d_grid,
        y=u_grid,
        mode="lines",
        name="선형 100−10d",
        line=dict(color=COL_LINE, width=2.5),
        showlegend=False,
        hovertemplate="선형 d=%{x:.1f} → %{y:.0f}<extra></extra>",
    ),
    row=2,
    col=2,
)
fig.add_trace(
    go.Scatter(
        x=d_grid,
        y=urgency_clamped(d_grid),
        mode="lines",
        name="클램프 [0,100]",
        line=dict(color=COL_CLAMP, width=2.5, dash="dash"),
        showlegend=False,
        hovertemplate="클램프 d=%{x:.1f} → %{y:.0f}<extra></extra>",
    ),
    row=2,
    col=2,
)
fig.add_trace(
    go.Scatter(
        x=d_grid,
        y=urgency_exp(d_grid),
        mode="lines",
        name="지수 100·e^(−d/τ)",
        line=dict(color=COL_EXP, width=2.5),
        showlegend=False,
        hovertemplate="지수 d=%{x:.1f} → %{y:.1f}<extra></extra>",
    ),
    row=2,
    col=2,
)
fig.add_hline(y=70, line=dict(color=COL_CRIT, width=1.5, dash="dash"), row=2, col=2)
fig.add_trace(
    go.Scatter(
        x=[3],
        y=[70],
        mode="markers",
        marker=dict(size=11, color=COL_CRIT, symbol="circle", line=dict(color="white", width=2)),
        showlegend=False,
        hovertemplate="τ≈8.41 → 선형·지수 모두 (3, 70)<extra></extra>",
    ),
    row=2,
    col=2,
)
for label, color, ypos in (
    ("선형", COL_LINE, -30),
    ("클램프", COL_CLAMP, 6),
    ("지수 (τ≈8.41)", COL_EXP, 34),
):
    fig.add_annotation(
        x=13.6, y=ypos, text=label, showarrow=False, font=dict(size=10, color=color), xanchor="right", row=2, col=2
    )

fig.update_xaxes(title_text="daysOfSupplyOnHand (일)", range=[0, 14], row=1, col=1)
fig.update_yaxes(title_text="urgency", range=[-45, 112], row=1, col=1)
fig.update_xaxes(tickangle=-35, row=2, col=1)
fig.update_yaxes(title_text="urgency", range=[-40, 122], row=2, col=1)
fig.update_xaxes(title_text="daysOfSupplyOnHand (일)", range=[0, 14], row=2, col=2)
fig.update_yaxes(title_text="urgency", range=[-45, 112], row=2, col=2)

fig.update_layout(
    title=dict(
        text="Phase 3 긴급도: <b>urgency = 100 − (daysOfSupplyOnHand × 10)</b>, critical ⟺ urgency &gt; 70 ⟺ 재고 3일 미만",
        x=0.5,
        xanchor="center",
        font=dict(size=15),
    ),
    template="plotly_white",
    height=820,
    width=1150,
    legend=dict(orientation="h", yanchor="bottom", y=1.045, xanchor="center", x=0.5, font=dict(size=11)),
    margin=dict(t=160, b=90, l=70, r=40),
)

_show(fig)

# %%
import os

_out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(_out, scale=2)
print("saved:", _out)
# 출력: saved: .../expy.png

# %% [markdown]
# ## 정리
#
# - $\text{urgency} = 100 - 10 \times \text{daysOfSupplyOnHand}$ — 기울기 $-10$, 즉 **재고 1일 = 긴급도 10점**
# - $\text{urgency} > 70 \iff \text{daysOfSupplyOnHand} < 3$ — 임계값 70은 "재고 3일 미만"의 재표기
# - `d = 3` 은 정확히 70이므로 `>` 조건에서 **제외** (정수 재고 기준 critical 집합 = $\{0,1,2\}$)
# - 한계: $d > 10$ 이면 음수 발산, 상한 100 포화로 이미 결품 상태 구분 불가,
#   `criticalityLevel` 및 조달 리드타임 미반영
# - 보정: 클램프 → slack(리드타임) 기반 → 지수 감쇠 → criticality 가중
# - Phase 5 트리거(`revenueAtRisk > $50M AND timeToImpactDays < 5`)는 별개 계층 —
#   urgency는 **분류/랭킹**, Phase 5는 **자동 실행 게이트**(AND 2조건, 되돌리기 비용 큼)
