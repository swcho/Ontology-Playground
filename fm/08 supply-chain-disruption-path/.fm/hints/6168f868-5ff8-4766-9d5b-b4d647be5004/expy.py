# %% [markdown]
# # RiskAssessment 결과 값 검산: `revenueAtRisk`=80M, `timeToImpactDays`=3
#
# 자료의 캐스케이드 예시는 다음과 같다.
#
# ```
# DisruptionEvent "Taiwan Power Outage" (Critical)
#   affects → Supplier "ChipX Corp" (singleSourced=true)
#     supplies → Component "GPU Module" (daysOfSupplyOnHand=3)
#       usedIn → ProductLine "Gaming Laptop 2024" ($50M annualRevenue)
#              → ProductLine "Workstation Pro"    ($30M annualRevenue)
#       triggers → RiskAssessment(revenueAtRisk=$80M, timeToImpactDays=3)
# ```
#
# 이 노트북에서 확인할 것:
#
# 1. **단순 합산 정의**: $\text{revenueAtRisk} = \sum_i \text{annualRevenue}_i$ → 50M + 30M = **80M** (자료의 값과 일치)
# 2. **Phase 3 일할 환산 공식**: $\text{revenue\_at\_risk} = \frac{\text{annualRevenue}}{365} \times \text{daysOfSupplyOnHand}$ → 약 0.66M (자료의 80M과 불일치)
# 3. **긴급도**: $\text{urgency} = 100 - \text{daysOfSupplyOnHand} \times 10$ 과 $\text{timeToImpactDays} = \text{daysOfSupplyOnHand} = 3$ 의 관계
# 4. **Phase 5 자동화 트리거**: `revenueAtRisk > $50M AND timeToImpactDays < 5`

# %%
# 필요 패키지: plotly, kaleido (정적 이미지 저장용). 없으면 계산 셀만 실행됨.
import math
from dataclasses import dataclass, field


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1단계: 캐스케이드 예시를 파이썬 자료구조로

# %%
@dataclass
class ProductLine:
    product_line_id: str
    name: str
    annual_revenue: float  # USD
    market_segment: str


@dataclass
class Component:
    component_id: str
    name: str
    days_of_supply_on_hand: int
    criticality_level: str
    used_in: list[ProductLine] = field(default_factory=list)


@dataclass
class Supplier:
    supplier_id: str
    name: str
    country: str
    single_sourced: bool
    supplies: list[Component] = field(default_factory=list)


gaming = ProductLine("PL-LAP-2024", "Gaming Laptop 2024", 50_000_000, "Consumer")
workstation = ProductLine("PL-WKS-2024", "Workstation Pro", 30_000_000, "Professional")

gpu_module = Component(
    component_id="COMP-SEM-0821",
    name="GPU Module",
    days_of_supply_on_hand=3,
    criticality_level="Critical",
    used_in=[gaming, workstation],
)

chipx = Supplier("SUPP-00456", "ChipX Corp", "Taiwan", True, supplies=[gpu_module])

for c in chipx.supplies:
    print(f"{chipx.name} → {c.name} (daysOfSupplyOnHand={c.days_of_supply_on_hand})")
    for pl in c.used_in:
        print(f"    usedIn → {pl.name}: ${pl.annual_revenue / 1e6:.0f}M/year")
# 출력:
# ChipX Corp → GPU Module (daysOfSupplyOnHand=3)
#     usedIn → Gaming Laptop 2024: $50M/year
#     usedIn → Workstation Pro: $30M/year

# %% [markdown]
# ## 2단계: 정의 ① — 연매출 단순 합산
#
# $$\text{revenueAtRisk}_{\text{sum}} = \sum_{i \in \text{exposed}} \text{annualRevenue}_i$$
#
# "이 제품 라인들의 매출 전체가 위험 노출 상태"라는 **노출 규모(exposure)** 관점이다.


# %%
def revenue_at_risk_sum(component: Component) -> float:
    return sum(pl.annual_revenue for pl in component.used_in)


sum_based = revenue_at_risk_sum(gpu_module)
print(f"① 단순 합산: ${sum_based / 1e6:.0f}M")
print(f"   자료의 revenueAtRisk=$80M 과 일치? {abs(sum_based - 80_000_000) < 1e-6}")
# 출력:
# ① 단순 합산: $80M
#    자료의 revenueAtRisk=$80M 과 일치? True

# %% [markdown]
# ## 3단계: 정의 ② — Phase 3 일할 환산 공식
#
# $$\text{revenue\_at\_risk} = \frac{\text{annualRevenue}}{365} \times \text{daysOfSupplyOnHand}$$
#
# "안전재고가 버티는 일수 동안의 매출분"만 계산하는 **기간 환산(pro-rated)** 관점이다.


# %%
def revenue_at_risk_phase3(component: Component) -> float:
    d = component.days_of_supply_on_hand
    return sum(pl.annual_revenue / 365 * d for pl in component.used_in)


phase3_based = revenue_at_risk_phase3(gpu_module)

for pl in gpu_module.used_in:
    per = pl.annual_revenue / 365 * gpu_module.days_of_supply_on_hand
    print(f"  {pl.name:20s}: {pl.annual_revenue / 1e6:>4.0f}M/365*3 = ${per:>12,.0f}")
print(f"② Phase 3 공식 합계: ${phase3_based:,.0f}  (= ${phase3_based / 1e6:.2f}M)")
print(f"① / ② 배율: {sum_based / phase3_based:.1f}배  (= 365/3 = {365 / 3:.1f})")
# 출력:
#   Gaming Laptop 2024  :   50M/365*3 = $     410,959
#   Workstation Pro     :   30M/365*3 = $     246,575
# ② Phase 3 공식 합계: $657,534  (= $0.66M)
# ① / ② 배율: 121.7배  (= 365/3 = 121.7)

# %% [markdown]
# ### 결론: 자료의 80M은 정의 ①(연매출 단순 합산)
#
# | 정의 | 값 | 자료의 $80M과 일치 |
# |---|---|---|
# | ① $\sum \text{annualRevenue}$ | \$80,000,000 | ✅ |
# | ② $\sum \frac{\text{annualRevenue}}{365}\times d$ | \$657,534 | ❌ (약 1/121.7) |
#
# 즉 캐스케이드 예시의 `revenueAtRisk`=80M은 Phase 3 의사코드를 적용한 값이 아니라
# **노출된 제품 라인의 연매출을 그대로 더한 값**이다. 두 정의는 정확히 $\frac{365}{d}$ 배 차이가 난다.

# %%
comparison = {
    "sum_of_annual_revenue": sum_based,
    "phase3_pro_rated": phase3_based,
    "ratio": sum_based / phase3_based,
    "matches_article_80M": abs(sum_based - 80_000_000) < 1e-6,
}
for k, v in comparison.items():
    print(f"{k:24s} = {v}")
# 출력:
# sum_of_annual_revenue    = 80000000
# phase3_pro_rated         = 657534.2465753425
# ratio                    = 121.66666666666666
# matches_article_80M      = True

# %% [markdown]
# ## 4단계: `timeToImpactDays`와 urgency
#
# $$\text{timeToImpactDays} = \text{daysOfSupplyOnHand} = 3$$
#
# $$\text{urgency} = 100 - \text{daysOfSupplyOnHand} \times 10 = 100 - 30 = 70$$
#
# 안전재고가 3일치뿐이므로 3일 뒤 생산이 멈춘다 → 조치 가능한 시간(window)이 3일이라는 뜻.


# %%
def urgency(days: int) -> int:
    return 100 - days * 10


d = gpu_module.days_of_supply_on_hand
time_to_impact = d  # 재고 소진 시점 = 영향 발생 시점
print(f"daysOfSupplyOnHand = {d}")
print(f"timeToImpactDays   = {time_to_impact}  (자료 값 3과 일치? {time_to_impact == 3})")
print(f"urgency            = {urgency(d)}")
print(f"Phase 3 critical 판정 (urgency > 70): {urgency(d) > 70}  ← 경계값이라 '>' 로는 탈락")
print(f"urgency >= 70 로 보면: {urgency(d) >= 70}")
# 출력:
# daysOfSupplyOnHand = 3
# timeToImpactDays   = 3  (자료 값 3과 일치? True)
# urgency            = 70
# Phase 3 critical 판정 (urgency > 70): False  ← 경계값이라 '>' 로는 탈락
# urgency >= 70 로 보면: True

# %% [markdown]
# ## 5단계: Phase 5 자동화 트리거 판정
#
# ```
# IF RiskAssessment.revenueAtRisk > $50M AND RiskAssessment.timeToImpactDays < 5:
#     THEN PO 발주 / 생산일정 갱신 / 메일 발송 / Activator 경보 / 상태 모니터링
# ```


# %%
def phase5_triggered(revenue_at_risk: float, time_to_impact_days: int) -> bool:
    return revenue_at_risk > 50_000_000 and time_to_impact_days < 5


print(f"revenueAtRisk > $50M      : {sum_based > 50_000_000}  (${sum_based / 1e6:.0f}M)")
print(f"timeToImpactDays < 5      : {time_to_impact < 5}  ({time_to_impact}일)")
print(f"→ Phase 5 자동 워크플로 발동: {phase5_triggered(sum_based, time_to_impact)}")
print()
print("비용 대비: 완화 조치 $2M(ChipX Europe) + $0.5M(안전재고) vs 노출 $80M")
print(f"→ 조치 비용은 노출액의 {2.5 / 80 * 100:.1f}%")
# 출력:
# revenueAtRisk > $50M      : True  ($80M)
# timeToImpactDays < 5      : True  (3일)
# → Phase 5 자동 워크플로 발동: True
#
# 비용 대비: 완화 조치 $2M(ChipX Europe) + $0.5M(안전재고) vs 노출 $80M
# → 조치 비용은 노출액의 3.1%

# %% [markdown]
# ### 임계값 민감도: 며칠까지 자동 발동되는가

# %%
for days in range(1, 8):
    tti = days
    fired = phase5_triggered(sum_based, tti)
    print(f"daysOfSupply={days} → timeToImpactDays={tti}, urgency={urgency(days):3d}, Phase5={'발동' if fired else '미발동'}")
# 출력:
# daysOfSupply=1 → timeToImpactDays=1, urgency= 90, Phase5=발동
# daysOfSupply=2 → timeToImpactDays=2, urgency= 80, Phase5=발동
# daysOfSupply=3 → timeToImpactDays=3, urgency= 70, Phase5=발동
# daysOfSupply=4 → timeToImpactDays=4, urgency= 60, Phase5=발동
# daysOfSupply=5 → timeToImpactDays=5, urgency= 50, Phase5=미발동
# daysOfSupply=6 → timeToImpactDays=6, urgency= 40, Phase5=미발동
# daysOfSupply=7 → timeToImpactDays=7, urgency= 30, Phase5=미발동

# %% [markdown]
# ## 6단계: 시각화 — `daysOfSupplyOnHand` 변화에 따른 두 정의와 urgency
#
# - 위 패널: 노출 금액 (로그 스케일). ① 단순 합산은 일수와 무관한 상수 \$80M, ② Phase 3 공식은 일수에 비례해 증가.
# - 아래 패널: urgency는 일수에 대해 선형 감소. `daysOfSupplyOnHand=3`에서 urgency=70, Phase 5 트리거 경계는 5일.

# %%
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    days_range = list(range(1, 15))
    total_annual = sum(pl.annual_revenue for pl in gpu_module.used_in)
    sum_curve = [total_annual / 1e6 for _ in days_range]
    phase3_curve = [total_annual / 365 * dd / 1e6 for dd in days_range]
    urgency_curve = [urgency(dd) for dd in days_range]

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.10,
        row_heights=[0.62, 0.38],
        subplot_titles=(
            "revenueAtRisk 정의 비교 (로그 스케일)",
            "urgency = 100 − daysOfSupplyOnHand × 10",
        ),
    )
    fig.add_trace(
        go.Scatter(
            x=days_range, y=sum_curve, name="① 연매출 단순 합산 ($80M, 상수) ← 자료의 값",
            mode="lines+markers", line=dict(color="#1f77b4", width=3),
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=days_range, y=phase3_curve, name="② Phase 3 일할 환산 (annualRevenue/365×d)",
            mode="lines+markers", line=dict(color="#d62728", width=3),
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=days_range, y=urgency_curve, name="urgency",
            mode="lines+markers", line=dict(color="#2ca02c", width=2, dash="dot"),
            showlegend=False,
        ),
        row=2, col=1,
    )
    # d=3 (예시), d=5 (Phase 5 경계) 보조선
    for row in (1, 2):
        fig.add_vline(x=3, line_dash="dash", line_color="#888888", row=row, col=1)
        fig.add_vline(x=5, line_dash="dot", line_color="#ff7f0e", row=row, col=1)
    # 주의: 로그 축에서 shape/annotation의 y 값은 log10 단위로 줘야 한다.
    fig.add_hline(y=math.log10(50), line_dash="dot", line_color="#ff7f0e",
                  annotation_text="Phase 5 임계: revenueAtRisk > $50M",
                  annotation_position="bottom right", row=1, col=1)
    fig.add_annotation(x=3, y=math.log10(400), xref="x", yref="y", text="예시 d=3",
                       showarrow=False, xanchor="left", xshift=6, font=dict(color="#555555"))
    fig.add_annotation(x=5, y=math.log10(120), xref="x", yref="y",
                       text="Phase 5 경계 (timeToImpactDays < 5)", showarrow=False,
                       xanchor="left", xshift=6, font=dict(color="#ff7f0e"))
    fig.add_hline(y=70, line_dash="dot", line_color="#2ca02c",
                  annotation_text="d=3 → urgency 70", annotation_position="bottom right",
                  row=2, col=1)
    money_ticks = [0.2, 0.5, 1, 2, 5, 10, 20, 50, 80, 200, 500]
    fig.update_yaxes(
        title_text="노출 금액", type="log",
        range=[math.log10(0.15), math.log10(900)],
        tickvals=money_ticks,
        ticktext=[f"${t:g}M" for t in money_ticks],
        row=1, col=1,
    )
    fig.update_yaxes(title_text="urgency", range=[0, 100], row=2, col=1)
    fig.update_xaxes(title_text="daysOfSupplyOnHand (일)", dtick=1, row=2, col=1)
    fig.update_layout(
        title="daysOfSupplyOnHand에 따른 revenueAtRisk 두 정의 비교와 urgency",
        template="plotly_white",
        width=1000,
        height=680,
        legend=dict(orientation="h", yanchor="bottom", y=-0.16, x=0),
    )
    _show(fig)

    import pathlib

    out = pathlib.Path(__file__).parent / "expy.png" if "__file__" in dir() else pathlib.Path("expy.png")
    fig.write_image(str(out), scale=2)
    print(f"saved: {out}")
except ImportError as e:
    print(f"plotly/kaleido 미설치로 시각화 생략: {e}")
# 출력:
# saved: .../expy.png

# %% [markdown]
# ## 정리
#
# | 항목 | 값 | 근거 |
# |---|---|---|
# | `revenueAtRisk` | \$80M | Gaming Laptop \$50M + Workstation Pro \$30M (연매출 합산) |
# | `timeToImpactDays` | 3 | GPU Module의 `daysOfSupplyOnHand`=3 |
# | urgency | 70 | $100 - 3 \times 10$ |
# | Phase 5 트리거 | 발동 | \$80M > \$50M **AND** 3일 < 5일 |
#
# 한 줄 해석: **"3일 안에 조치하지 않으면 80M 달러 규모 매출이 위험해진다."**
#
# 주의점: 자료 안에 `revenueAtRisk` 정의가 두 가지로 섞여 있다. 캐스케이드 예시의 \$80M은
# 연매출 단순 합산이고, Phase 3 의사코드의 공식은 일할 환산이다. 실제 온톨로지를 구현할 때는
# 어느 정의를 쓸지 문서화해야 하며, 두 값은 $\frac{365}{d}$ 배 차이가 나므로
# Phase 5의 `> $50M` 같은 임계값도 정의에 맞춰 조정해야 한다.
