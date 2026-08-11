# %% [markdown]
# # Phase 3: 제품 라인별 위험 매출(revenue_at_risk) 계산
#
# 공급망 중단 온톨로지의 **Phase 3 Quantify impact** 단계를 그대로 구현해 본다.
#
# $$\text{revenue\_at\_risk} = \frac{\text{annualRevenue}}{365} \times \text{daysOfSupplyOnHand}$$
#
# $$\text{urgency} = 100 - 10 \times \text{daysOfSupplyOnHand}$$
#
# 집계 규칙:
#
# $$\text{total\_revenue\_at\_risk} = \sum_i \frac{R_i}{365} D_i,
# \qquad \text{critical} = \{i : \text{urgency}_i > 70\}$$
#
# 필요 패키지: pandas, plotly, kaleido

# %%
# 필요 패키지: pandas, plotly, kaleido
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


DAYS_PER_YEAR = 365
URGENCY_SLOPE = 10  # urgency = 100 - slope * D
URGENCY_THRESHOLD = 70  # critical 판정 임계값

HERE = Path(__file__).parent if "__file__" in globals() else Path.cwd()
print(f"DAYS_PER_YEAR={DAYS_PER_YEAR}, threshold={URGENCY_THRESHOLD}")
# 출력: DAYS_PER_YEAR=365, threshold=70


# %% [markdown]
# ## 1단계: 노출된 12개 제품 라인 데이터
#
# Phase 2에서 `Supplier → supplies → Component → usedIn → ProductLine` 경로를 타고
# **12개 제품 라인**이 노출된 상황이다.
#
# - `annualRevenue` 는 `ProductLine` 엔티티의 속성 (USD)
# - `daysOfSupplyOnHand` 는 `Component` 엔티티의 속성 (일)
# - 한 라인이 여러 부품에 의존하면 **병목 부품**(가장 먼저 소진되는 것, `min`)의 값을 쓴다

# %%
product_lines = pd.DataFrame(
    [
        # (productLineId, name, annualRevenue(USD), bottleneck component, daysOfSupplyOnHand)
        ("PL-LAP-2024", "Gaming Laptop 2024", 50_000_000, "GPU Module", 3),
        ("PL-WKS-2024", "Workstation Pro", 30_000_000, "GPU Module", 3),
        ("PL-TAB-2024", "Tablet Plus", 18_000_000, "Memory Board", 5),
        ("PL-SRV-2023", "Server Rack X", 120_000_000, "Power Supply", 2),
        ("PL-PHN-2025", "Phone Ultra", 220_000_000, "Camera Sensor", 1),
        ("PL-PHN-2024", "Phone Lite", 75_000_000, "Camera Sensor", 4),
        ("PL-WCH-2025", "Smartwatch S", 22_000_000, "OLED Panel", 7),
        ("PL-TVS-2024", "Smart TV 65", 64_000_000, "OLED Panel", 9),
        ("PL-AUD-2024", "Wireless Buds", 41_000_000, "BT Chipset", 6),
        ("PL-NET-2023", "Router Max", 15_000_000, "Ethernet PHY", 12),
        ("PL-IOT-2025", "Sensor Hub", 9_000_000, "MCU Board", 2),
        ("PL-EVC-2025", "EV Charger", 55_000_000, "Power Module", 8),
    ],
    columns=["productLineId", "name", "annualRevenue", "bottleneckComponent", "daysOfSupplyOnHand"],
)
print(product_lines.to_string(index=False))
# 출력:
# productLineId               name  annualRevenue bottleneckComponent  daysOfSupplyOnHand
#   PL-LAP-2024 Gaming Laptop 2024       50000000          GPU Module                   3
#   PL-WKS-2024    Workstation Pro       30000000          GPU Module                   3
#   PL-TAB-2024        Tablet Plus       18000000        Memory Board                   5
#   PL-SRV-2023      Server Rack X      120000000        Power Supply                   2
#   PL-PHN-2025        Phone Ultra      220000000       Camera Sensor                   1
#   PL-PHN-2024         Phone Lite       75000000       Camera Sensor                   4
#   PL-WCH-2025       Smartwatch S       22000000          OLED Panel                   7
#   PL-TVS-2024        Smart TV 65       64000000          OLED Panel                   9
#   PL-AUD-2024      Wireless Buds       41000000          BT Chipset                   6
#   PL-NET-2023         Router Max       15000000        Ethernet PHY                  12
#   PL-IOT-2025         Sensor Hub        9000000           MCU Board                   2
#   PL-EVC-2025         EV Charger       55000000        Power Module                   8


# %% [markdown]
# ## 2단계: 두 식을 함수로 구현
#
# 1. **일 매출 환산** — $r = R/365$. 원점을 지나는 일차함수의 기울기.
# 2. **누적 노출** — $V = r \times D$. 높이 $r$, 너비 $D$ 인 직사각형의 면적.
# 3. **시급도** — $U = 100 - 10D$, 기울기 $-10$ 의 일차함수. 음수는 0으로 클램프.

# %%
def daily_revenue(annual_revenue: float) -> float:
    """연 매출 -> 일 매출. 비례식 365:R = 1:x 의 해. 단위: USD/day"""
    return annual_revenue / DAYS_PER_YEAR


def revenue_at_risk(annual_revenue: float, days_of_supply: float) -> float:
    """버퍼 기간 동안 누적되는 노출 매출. (USD/day) x day = USD"""
    return daily_revenue(annual_revenue) * days_of_supply


def urgency(days_of_supply: float) -> float:
    """시급도 스코어. 0~100 으로 클램프."""
    return max(0.0, 100.0 - URGENCY_SLOPE * days_of_supply)


# Gaming Laptop 2024 손계산 검증
r = daily_revenue(50_000_000)
v = revenue_at_risk(50_000_000, 3)
print(f"daily_revenue = {r:,.0f} USD/day")
print(f"revenue_at_risk(D=3) = {v:,.0f} USD  (= {v/1e6:.3f}M)")
print(f"urgency(D=3) = {urgency(3):.0f}  -> critical? {urgency(3) > URGENCY_THRESHOLD}")
# 출력: daily_revenue = 136,986 USD/day
# 출력: revenue_at_risk(D=3) = 410,959 USD  (= 0.411M)
# 출력: urgency(D=3) = 70  -> critical? False


# %% [markdown]
# ## 3단계: `urgency > 70` 부등식을 풀면 `D < 3`
#
# $$100 - 10D > 70 \iff -10D > -30 \iff D < 3$$
#
# (음수로 나누므로 부등호가 역전된다.) 코드로 동치성을 확인한다.
# $D=3$ 은 $U=70$ 이 되어 **초과가 아니므로 제외**된다 — 경계값 주의.

# %%
for D in range(0, 7):
    u = urgency(D)
    print(f"D={D:2d}  urgency={u:5.0f}  (urgency>70)={u > URGENCY_THRESHOLD!s:5}  (D<3)={D < 3!s:5}  일치={(u > URGENCY_THRESHOLD) == (D < 3)}")
# 출력: D= 0  urgency=  100  (urgency>70)=True   (D<3)=True   일치=True
# 출력: D= 1  urgency=   90  (urgency>70)=True   (D<3)=True   일치=True
# 출력: D= 2  urgency=   80  (urgency>70)=True   (D<3)=True   일치=True
# 출력: D= 3  urgency=   70  (urgency>70)=False  (D<3)=False  일치=True
# 출력: D= 4  urgency=   60  (urgency>70)=False  (D<3)=False  일치=True
# 출력: D= 5  urgency=   50  (urgency>70)=False  (D<3)=False  일치=True
# 출력: D= 6  urgency=   40  (urgency>70)=False  (D<3)=False  일치=True


# %% [markdown]
# ## 4단계: 12개 라인 전체 계산 (Calculation Engine)
#
# ```
# For each exposed ProductLine:
#   revenue_at_risk = annualRevenue / 365 * daysOfSupplyOnHand
#   urgency = 100 - (daysOfSupplyOnHand * 10)
# ```

# %%
df = product_lines.copy()
df["dailyRevenue"] = df["annualRevenue"].map(daily_revenue)
df["revenue_at_risk"] = df.apply(
    lambda row: revenue_at_risk(row["annualRevenue"], row["daysOfSupplyOnHand"]), axis=1
)
df["urgency"] = df["daysOfSupplyOnHand"].map(urgency)
df["critical"] = df["urgency"] > URGENCY_THRESHOLD

view = df[["name", "annualRevenue", "daysOfSupplyOnHand", "revenue_at_risk", "urgency", "critical"]].copy()
view["annualRevenue"] = (view["annualRevenue"] / 1e6).round(1).astype(str) + "M"
view["revenue_at_risk"] = view["revenue_at_risk"].map(lambda x: f"{x:,.0f}")
print(view.sort_values("urgency", ascending=False).to_string(index=False))
# 출력:
#               name annualRevenue  daysOfSupplyOnHand revenue_at_risk  urgency  critical
#        Phone Ultra        220.0M                   1         602,740     90.0      True
#      Server Rack X        120.0M                   2         657,534     80.0      True
#         Sensor Hub          9.0M                   2          49,315     80.0      True
# Gaming Laptop 2024         50.0M                   3         410,959     70.0     False
#    Workstation Pro         30.0M                   3         246,575     70.0     False
#         Phone Lite         75.0M                   4         821,918     60.0     False
#        Tablet Plus         18.0M                   5         246,575     50.0     False
#      Wireless Buds         41.0M                   6         673,973     40.0     False
#       Smartwatch S         22.0M                   7         421,918     30.0     False
#         EV Charger         55.0M                   8       1,205,479     20.0     False
#        Smart TV 65         64.0M                   9       1,578,082     10.0     False
#         Router Max         15.0M                  12         493,151      0.0     False


# %% [markdown]
# ## 5단계: 집계 — 총 노출액과 critical 필터
#
# ```
# total_revenue_at_risk = SUM(revenue_at_risk)
# critical_product_lines = WHERE urgency > 70
# ```
#
# 두 지표가 **반대 방향**임을 확인하자: `urgency` 상위 라인이 `revenue_at_risk` 상위는 아니다.

# %%
total = df["revenue_at_risk"].sum()
critical = df[df["critical"]]

print(f"노출 제품 라인 수         : {len(df)}")
print(f"total_revenue_at_risk    : {total:,.0f} USD  ({total/1e6:.2f}M)")
print(f"연 매출 단순 합            : {df['annualRevenue'].sum()/1e6:.0f}M  <- 정의가 다름(6단계 참조)")
print(f"critical (urgency>70)     : {len(critical)}개 -> {list(critical['name'])}")
print(f"critical 노출액 합         : {critical['revenue_at_risk'].sum():,.0f} USD  "
      f"({critical['revenue_at_risk'].sum()/total*100:.1f}% of total)")
print(f"최소 timeToImpactDays     : {df['daysOfSupplyOnHand'].min()}일")
print()
print("revenue_at_risk 상위 3   :", list(df.nlargest(3, "revenue_at_risk")["name"]))
print("urgency 상위 3           :", list(df.nlargest(3, "urgency")["name"]))
# 출력: 노출 제품 라인 수         : 12
# 출력: total_revenue_at_risk    : 7,408,219 USD  (7.41M)
# 출력: 연 매출 단순 합            : 719M  <- 정의가 다름(6단계 참조)
# 출력: critical (urgency>70)     : 3개 -> ['Server Rack X', 'Phone Ultra', 'Sensor Hub']
# 출력: critical 노출액 합         : 1,309,589 USD  (17.7% of total)
# 출력: 최소 timeToImpactDays     : 1일
# 출력:
# 출력: revenue_at_risk 상위 3   : ['Smart TV 65', 'EV Charger', 'Phone Lite']
# 출력: urgency 상위 3           : ['Phone Ultra', 'Server Rack X', 'Sensor Hub']
# 주목: 노출액 상위 3 과 urgency 상위 3 은 겹치는 라인이 하나도 없다 -> 두 지표는 반대 방향


# %% [markdown]
# ## 6단계: ⚠️ 자산 문서의 $80M과 정의가 다르다
#
# 자산 문서의 캐스케이드 예시는 이렇게 적혀 있다.
#
# ```
# Component "GPU Module" (daysOfSupplyOnHand=3)
#   ├─ ProductLine "Gaming Laptop 2024" ($50M annual revenue)
#   ├─ ProductLine "Workstation Pro"    ($30M annual revenue)
#   └─ RiskAssessment revenueAtRisk = $80M
# ```
#
# $80\text{M} = 50\text{M} + 30\text{M}$ — 이는 **연 매출의 단순 합**이다.
# 반면 Phase 3 공식은 **버퍼 기간 중 흐르는 매출**을 계산한다.
#
# $$\frac{50\text{M}}{365}\times 3 + \frac{30\text{M}}{365}\times 3
# = \frac{3}{365}\times 80\text{M} \approx \$0.66\text{M}$$
#
# 배수는 정확히 $\dfrac{365}{D} = \dfrac{365}{3} \approx 121.7$ 배다.
#
# | 지표 | 정의 | 답하는 질문 |
# |---|---|---|
# | $80M | $\sum R_i$ | 얼마나 **큰 사업**이 위태로운가 (스톡, 규모) |
# | $0.66M | $\sum \frac{R_i}{365}D_i$ | 버퍼 기간에 **실제로 흐르는** 매출 (플로우 × 시간) |
#
# 어느 쪽이 옳다기보다, **정의를 명시하지 않으면 두 자릿수 배수의 오차**가 생긴다는 것이 요점이다.
# 문서의 $127M도 규모 계열 수치에 가깝다.

# %%
gpu = df[df["bottleneckComponent"] == "GPU Module"]
scale_based = gpu["annualRevenue"].sum()          # 문서 캐스케이드 방식
flow_based = gpu["revenue_at_risk"].sum()         # Phase 3 공식
print(f"규모 기반 (문서 $80M)  : {scale_based:,.0f} USD  ({scale_based/1e6:.0f}M)")
print(f"유량 기반 (Phase 3 식) : {flow_based:,.0f} USD  ({flow_based/1e6:.3f}M)")
print(f"배수                    : {scale_based/flow_based:.1f}배  (= 365/D = {365/3:.1f})")
# 출력: 규모 기반 (문서 $80M)  : 80,000,000 USD  (80M)
# 출력: 유량 기반 (Phase 3 식) : 657,534 USD  (0.658M)
# 출력: 배수                    : 121.7배  (= 365/D = 121.7)


# %% [markdown]
# ## 7단계: 시각화 — daysOfSupplyOnHand 스윕
#
# $D$ 를 0부터 14까지 훑으며 두 함수를 그린다.
#
# - **왼쪽**: 12개 라인 실제 값 (막대 = revenue_at_risk, 점 = urgency, 점선 = 임계 70)
# - **오른쪽**: 스윕 곡선. $V(D) = \frac{R}{365}D$ 는 **기울기 $+\frac{R}{365}$ 의 상승 직선**,
#   $U(D) = 100 - 10D$ 는 **기울기 $-10$ 의 하강 직선**.
#   임계선 $U = 70$ 과의 교점이 $D = 3$ 이며, 그 왼쪽 음영이 critical 영역이다.

# %%
import numpy as np

D_sweep = np.linspace(0, 14, 141)
R_REF = 220_000_000  # Phone Ultra 기준
v_sweep = R_REF / DAYS_PER_YEAR * D_sweep
u_sweep = np.maximum(0.0, 100.0 - URGENCY_SLOPE * D_sweep)
D_crit = (100 - URGENCY_THRESHOLD) / URGENCY_SLOPE  # 3.0
print(f"임계 교점 D = {D_crit}일,  V(D_crit) = {R_REF/365*D_crit:,.0f} USD")
# 출력: 임계 교점 D = 3.0일,  V(D_crit) = 1,808,219 USD

INK = "#1f2933"
MUTED = "#7b8794"
ACCENT_V = "#2c7fb8"   # revenue_at_risk
ACCENT_U = "#d95f02"   # urgency
CRIT = "#c1272d"

fig = make_subplots(
    rows=1,
    cols=2,
    column_widths=[0.56, 0.44],
    horizontal_spacing=0.13,
    specs=[[{"secondary_y": True}, {"secondary_y": True}]],
    subplot_titles=(
        "12개 노출 제품 라인: 노출액 vs 시급도",
        f"D 스윕 (R=${R_REF/1e6:.0f}M 기준): 두 일차함수",
    ),
)

# --- 왼쪽: 라인별 실측 ---
left = df.sort_values("daysOfSupplyOnHand")
fig.add_trace(
    go.Bar(
        x=left["name"],
        y=left["revenue_at_risk"] / 1e6,
        name="revenue_at_risk (M USD)",
        marker_color=[CRIT if c else ACCENT_V for c in left["critical"]],
        marker_line_width=0,
        hovertemplate="<b>%{x}</b><br>노출액 %{y:.2f}M USD<br>D=%{customdata[0]}일"
        "<br>urgency %{customdata[1]:.0f}<extra></extra>",
        customdata=np.stack([left["daysOfSupplyOnHand"], left["urgency"]], axis=-1),
    ),
    row=1,
    col=1,
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(
        x=left["name"],
        y=left["urgency"],
        name="urgency",
        mode="markers+lines",
        line=dict(color=ACCENT_U, width=1.5, dash="dot"),
        marker=dict(color=ACCENT_U, size=9, symbol="diamond"),
        hovertemplate="urgency %{y:.0f}<extra></extra>",
    ),
    row=1,
    col=1,
    secondary_y=True,
)
fig.add_hline(
    y=URGENCY_THRESHOLD,
    line=dict(color=CRIT, width=1.2, dash="dash"),
    row=1,
    col=1,
    secondary_y=True,
)
# add_hline/add_vrect 의 annotation 은 secondary_y 서브플롯에서 위치가 어긋나므로
# add_annotation 으로 직접 배치한다.
fig.add_annotation(
    text="임계 urgency=70  ⟺  D<3",
    x="Phone Lite", y=73, xanchor="left", yanchor="bottom",
    showarrow=False, font=dict(size=12, color=CRIT),
    row=1, col=1, secondary_y=True,
)

# --- 오른쪽: 스윕 ---
fig.add_vrect(
    x0=0,
    x1=D_crit,
    fillcolor=CRIT,
    opacity=0.10,
    line_width=0,
    row=1,
    col=2,
)
fig.add_annotation(
    text="critical<br>D&lt;3",
    x=1.5, y=97, xanchor="center", yanchor="top",
    showarrow=False, font=dict(size=11, color=CRIT),
    row=1, col=2, secondary_y=True,
)
fig.add_trace(
    go.Scatter(
        x=D_sweep,
        y=v_sweep / 1e6,
        name="V(D)=R/365·D  (M USD)",
        mode="lines",
        line=dict(color=ACCENT_V, width=3),
        hovertemplate="D=%{x:.1f}일 → 노출 %{y:.2f}M USD<extra></extra>",
    ),
    row=1,
    col=2,
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(
        x=D_sweep,
        y=u_sweep,
        name="U(D)=100−10D",
        mode="lines",
        line=dict(color=ACCENT_U, width=3, dash="dash"),
        hovertemplate="D=%{x:.1f}일 → urgency %{y:.0f}<extra></extra>",
    ),
    row=1,
    col=2,
    secondary_y=True,
)
fig.add_trace(
    go.Scatter(
        x=[D_crit],
        y=[URGENCY_THRESHOLD],
        mode="markers+text",
        marker=dict(color=CRIT, size=12, symbol="x", line=dict(width=2, color=CRIT)),
        text=["D=3, U=70"],
        textposition="top right",
        textfont=dict(size=11, color=CRIT),
        showlegend=False,
        hovertemplate="임계 교점 D=3일<extra></extra>",
    ),
    row=1,
    col=2,
    secondary_y=True,
)
fig.add_hline(
    y=URGENCY_THRESHOLD,
    line=dict(color=CRIT, width=1.2, dash="dash"),
    row=1,
    col=2,
    secondary_y=True,
)
# 실제 12개 라인을 스윕 곡선 위에 겹쳐 표시 (각 라인의 R은 다르므로 참고용)
fig.add_trace(
    go.Scatter(
        x=df["daysOfSupplyOnHand"],
        y=df["urgency"],
        mode="markers",
        name="실제 라인 (D, urgency)",
        marker=dict(color=MUTED, size=8, symbol="circle-open", line=dict(width=1.6)),
        hovertemplate="%{text}<br>D=%{x}일, urgency=%{y:.0f}<extra></extra>",
        text=df["name"],
    ),
    row=1,
    col=2,
    secondary_y=True,
)

# secondary_y 축이 있으면 plotly 자동 range 가 어긋나므로 명시적으로 지정한다
bar_max = (df["revenue_at_risk"] / 1e6).max() * 1.18
fig.update_yaxes(title_text="revenue_at_risk (M USD)", row=1, col=1, secondary_y=False,
                 range=[0, bar_max], color=ACCENT_V, gridcolor="#e4e7eb", zeroline=False)
fig.update_yaxes(title_text="urgency", row=1, col=1, secondary_y=True, range=[0, 105],
                 color=ACCENT_U, showgrid=False)
fig.update_yaxes(title_text="revenue_at_risk (M USD)", row=1, col=2, secondary_y=False,
                 range=[0, v_sweep.max() / 1e6 * 1.06], color=ACCENT_V,
                 gridcolor="#e4e7eb", zeroline=False)
fig.update_yaxes(title_text="urgency", row=1, col=2, secondary_y=True, range=[0, 105],
                 color=ACCENT_U, showgrid=False)
fig.update_xaxes(title_text="", tickangle=-45, row=1, col=1, tickfont=dict(size=9))
fig.update_xaxes(title_text="daysOfSupplyOnHand (일)", row=1, col=2, dtick=2,
                 gridcolor="#e4e7eb")

fig.update_layout(
    title=dict(
        text="<b>revenue_at_risk = annualRevenue/365 × daysOfSupplyOnHand</b>"
        f"<br><span style='font-size:12px;color:{MUTED}'>총 노출 "
        f"${total/1e6:.2f}M · critical(urgency&gt;70) {len(critical)}개 · "
        "노출액↑ 과 urgency↓ 은 반대 방향</span>",
        x=0.5,
        xanchor="center",
        font=dict(size=17, color=INK),
    ),
    template="plotly_white",
    width=1240,
    height=580,
    font=dict(family="Helvetica, Arial, sans-serif", size=12, color=INK),
    legend=dict(orientation="h", yanchor="bottom", y=-0.30, xanchor="center", x=0.5,
                font=dict(size=10)),
    margin=dict(l=70, r=70, t=95, b=150),
    bargap=0.32,
)

png_path = HERE / "expy.png"
fig.write_image(str(png_path), scale=2)
print(f"saved: {png_path}")
# 출력: saved: .../a34da461-50a1-4b40-a26d-e3091ae7b847/expy.png

_show(fig)


# %% [markdown]
# ## 8단계: 대안 정의 — 중단 기간을 반영하면?
#
# Phase 3 식은 **버퍼 기간 중 노출**만 센다. 실제 손실은 재고가 소진된 뒤
# 복구까지의 **생산 정지 기간**에서 발생한다.
#
# $$V_{\text{stopped}} = \frac{R}{365}\times \max(0,\ \text{estimatedDurationDays} - D)$$
#
# 문서의 Taiwan 사례는 `estimatedDurationDays = 7` 이다. 두 정의를 비교해 보자.
# $D$ 가 7일 이상인 라인은 재고로 중단을 넘길 수 있어 정지 손실이 0이다.

# %%
EST_DURATION = 7

df["exposure_buffer"] = df["revenue_at_risk"]  # Phase 3 식
df["exposure_stopped"] = df.apply(
    lambda row: daily_revenue(row["annualRevenue"]) * max(0, EST_DURATION - row["daysOfSupplyOnHand"]),
    axis=1,
)

cmp = df[["name", "daysOfSupplyOnHand", "exposure_buffer", "exposure_stopped"]].copy()
cmp["exposure_buffer"] = cmp["exposure_buffer"].map(lambda x: f"{x:,.0f}")
cmp["exposure_stopped"] = cmp["exposure_stopped"].map(lambda x: f"{x:,.0f}")
print(cmp.to_string(index=False))
print()
print(f"버퍼 기간 노출 합   : {df['exposure_buffer'].sum():,.0f} USD")
print(f"정지 기간 노출 합   : {df['exposure_stopped'].sum():,.0f} USD  (duration={EST_DURATION}일 가정)")
# 출력:
#               name  daysOfSupplyOnHand exposure_buffer exposure_stopped
# Gaming Laptop 2024                   3         410,959          547,945
#    Workstation Pro                   3         246,575          328,767
#        Tablet Plus                   5         246,575           98,630
#      Server Rack X                   2         657,534        1,643,836
#        Phone Ultra                   1         602,740        3,616,438
#         Phone Lite                   4         821,918          616,438
#       Smartwatch S                   7         421,918                0
#        Smart TV 65                   9       1,578,082                0
#      Wireless Buds                   6         673,973          112,329
#         Router Max                  12         493,151                0
#         Sensor Hub                   2          49,315          123,288
#         EV Charger                   8       1,205,479                0
# 출력:
# 출력: 버퍼 기간 노출 합   : 7,408,219 USD
# 출력: 정지 기간 노출 합   : 7,087,671 USD  (duration=7일 가정)


# %% [markdown]
# ## 정리
#
# 1. $R/365$ 는 **일 매출**이며, 매출 누적 직선 $f(t)=rt$ 의 **기울기**다.
#    "매출이 1년간 균등"이라는 선형 근사를 담고 있다.
# 2. $\times D$ 는 높이 $r$, 너비 $D$ 인 **직사각형 면적** = $\int_0^D r\,dt$.
#    단위 검산 $\frac{\text{USD}}{\text{day}}\times\text{day}=\text{USD}$ 로 형태를 복원할 수 있다.
# 3. $U(D)=100-10D$ 는 기울기 $-10$ 의 일차함수이고, `urgency > 70` 은
#    부등식을 풀면 정확히 **$D < 3$** 이다 (3단계에서 코드로 확인).
# 4. $V$ 는 $D$ 에 **증가**, $U$ 는 $D$ 에 **감소** — 방향이 반대여서 Phase 5의
#    AND 트리거(`revenueAtRisk > $50M AND timeToImpactDays < 5`) 교집합이
#    저절로 좁아지고 알람 피로를 막는다.
# 5. 이 식은 **버퍼 기간 노출(유량)** 이므로 자산 문서 캐스케이드의
#    **$80M(연 매출 단순 합, 규모)** 과 정의가 다르다. 배수는 $365/D$.
