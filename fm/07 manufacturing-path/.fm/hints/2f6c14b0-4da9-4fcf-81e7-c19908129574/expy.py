# %% [markdown]
# # tolerance는 왜 생산 계획의 핵심 제약이 되는가
#
# Smart Manufacturing 온톨로지에서 `Part.tolerance`는 단순한 숫자 속성이 아니라
# **어떤 부품(Part)을 어떤 기계(Machine)에 배정할 수 있는가**를 결정하는 제약이다.
#
# - 부품은 목표 치수 $\mu_0$ (nominal)와 허용 편차 $T$ (tolerance)를 가진다.
#   규격 한계는 $LSL = \mu_0 - T$, $USL = \mu_0 + T$.
# - 기계는 고유한 공정 산포 $\sigma$ (정밀도)를 가진다. $\sigma$가 작을수록 고정밀 기계.
# - 실제 가공 치수는 $X \sim \mathcal{N}(\mu_0, \sigma^2)$ 로 근사한다.
#
# 공정 능력 지수(process capability index):
#
# $$C_p = \frac{USL - LSL}{6\sigma} = \frac{2T}{6\sigma} = \frac{T}{3\sigma}$$
#
# 즉 **$C_p$는 tolerance $T$와 기계 정밀도 $\sigma$의 비율**이다.
# $T$가 좁아지면(tighter) 같은 $C_p$를 유지하기 위해 $\sigma$도 작아져야 한다 → 더 정밀한 기계가 필요하다.

# %%
# 필요 패키지: numpy, plotly, kaleido
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import norm


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


RNG_SEED = 42
N_SAMPLES = 20000
NOMINAL = 10.000  # 목표 치수 (mm)

# 기계: sigma(mm)가 작을수록 고정밀 = 비싸고 대수가 적다
MACHINES = [
    {"machineId": "CNC-01", "name": "5-Axis Precision CNC", "sigma": 0.0020},
    {"machineId": "CNC-02", "name": "3-Axis Standard CNC", "sigma": 0.0100},
    {"machineId": "LATHE-07", "name": "Legacy Manual Lathe", "sigma": 0.0180},
]

# 부품: tolerance(±mm)가 좁을수록 tighter
PARTS = [
    {"partId": "P-100", "name": "Turbine Blade Seat", "tolerance": 0.010},
    {"partId": "P-200", "name": "Gearbox Housing", "tolerance": 0.045},
    {"partId": "P-300", "name": "Bracket", "tolerance": 0.080},
]

for m in MACHINES:
    print(f"{m['machineId']:9s} sigma={m['sigma']:.4f} mm  {m['name']}")
for p in PARTS:
    print(f"{p['partId']:9s} tol=±{p['tolerance']:.3f} mm  {p['name']}")

# 출력: CNC-01    sigma=0.0020 mm  5-Axis Precision CNC
# 출력: CNC-02    sigma=0.0100 mm  3-Axis Standard CNC
# 출력: LATHE-07  sigma=0.0180 mm  Legacy Manual Lathe
# 출력: P-100     tol=±0.010 mm  Turbine Blade Seat
# 출력: P-200     tol=±0.045 mm  Gearbox Housing
# 출력: P-300     tol=±0.080 mm  Bracket

# %% [markdown]
# ## 1. 시뮬레이션: 기계 × 부품 조합별 수율(yield)
#
# 각 (machine, part) 쌍에 대해 $N$개의 부품을 가공했다고 가정하고,
# 치수가 $[LSL, USL]$ 안에 들어간 비율을 **수율**로 계산한다.
#
# 이론값은 $\text{yield} = \Phi\!\left(\frac{T}{\sigma}\right) - \Phi\!\left(\frac{-T}{\sigma}\right) = 2\Phi(3C_p) - 1$.

# %%
rng = np.random.default_rng(RNG_SEED)
rows = []
for m in MACHINES:
    samples = rng.normal(NOMINAL, m["sigma"], N_SAMPLES)
    for p in PARTS:
        lsl, usl = NOMINAL - p["tolerance"], NOMINAL + p["tolerance"]
        inside = np.logical_and(samples >= lsl, samples <= usl)
        cp = p["tolerance"] / (3 * m["sigma"])
        rows.append(
            {
                "machineId": m["machineId"],
                "partId": p["partId"],
                "sigma": m["sigma"],
                "tolerance": p["tolerance"],
                "cp": cp,
                "yield_sim": inside.mean(),
                "yield_theory": 2 * norm.cdf(3 * cp) - 1,
                "ppm_defect": (1 - inside.mean()) * 1e6,
            }
        )

print(f"{'machine':9s} {'part':6s} {'sigma':>7s} {'tol':>7s} {'Cp':>6s} {'yield':>8s} {'theory':>8s} {'ppm':>9s}")
for r in rows:
    print(
        f"{r['machineId']:9s} {r['partId']:6s} {r['sigma']:7.4f} {r['tolerance']:7.3f} "
        f"{r['cp']:6.2f} {r['yield_sim']:8.4f} {r['yield_theory']:8.4f} {r['ppm_defect']:9.0f}"
    )

# 출력: machine   part     sigma     tol     Cp    yield   theory       ppm
# 출력: CNC-01    P-100   0.0020   0.010   1.67   1.0000   1.0000         0
# 출력: CNC-01    P-200   0.0020   0.045   7.50   1.0000   1.0000         0
# 출력: CNC-01    P-300   0.0020   0.080  13.33   1.0000   1.0000         0
# 출력: CNC-02    P-100   0.0100   0.010   0.33   0.6778   0.6827    322200
# 출력: CNC-02    P-200   0.0100   0.045   1.50   1.0000   1.0000         0
# 출력: CNC-02    P-300   0.0100   0.080   2.67   1.0000   1.0000         0
# 출력: LATHE-07  P-100   0.0180   0.010   0.19   0.4261   0.4215    573850
# 출력: LATHE-07  P-200   0.0180   0.045   0.83   0.9869   0.9876     13100
# 출력: LATHE-07  P-300   0.0180   0.080   1.48   1.0000   1.0000        50

# %% [markdown]
# ## 2. 배정 가능 여부 판정
#
# 업계 관례상 $C_p \ge 1.33$ (4-sigma, 약 63 ppm 불량)을 "공정 능력 있음"으로 본다.
# 이것이 온톨로지의 `assigned_to` 관계를 만들 때 적용되는 **하드 제약**이다.
#
# $$\text{assignable}(m, p) \iff C_p = \frac{T_p}{3\sigma_m} \ge 1.33$$

# %%
CP_MIN = 1.33
for r in rows:
    r["assignable"] = r["cp"] >= CP_MIN

for p in PARTS:
    ok = [r["machineId"] for r in rows if r["partId"] == p["partId"] and r["assignable"]]
    print(f"{p['partId']} (±{p['tolerance']:.3f}) -> 배정 가능 기계: {ok if ok else '없음 (설비 투자 필요)'}")

# 출력: P-100 (±0.010) -> 배정 가능 기계: ['CNC-01']
# 출력: P-200 (±0.045) -> 배정 가능 기계: ['CNC-01', 'CNC-02']
# 출력: P-300 (±0.080) -> 배정 가능 기계: ['CNC-01', 'CNC-02', 'LATHE-07']

# %%
# tolerance가 좁아질수록 요구되는 기계 정밀도(sigma_max)는 선형으로 작아진다.
# Cp >= 1.33  <=>  sigma <= T / (3 * 1.33)
for p in PARTS:
    print(f"{p['partId']}: tol=±{p['tolerance']:.3f} -> 요구 sigma <= {p['tolerance'] / (3 * CP_MIN):.4f} mm")

# 출력: P-100: tol=±0.010 -> 요구 sigma <= 0.0025 mm
# 출력: P-200: tol=±0.045 -> 요구 sigma <= 0.0113 mm
# 출력: P-300: tol=±0.080 -> 요구 sigma <= 0.0201 mm

# %% [markdown]
# ## 3. 시각화
#
# - 왼쪽 3개: 각 기계의 치수 분포와 부품별 tolerance 밴드(수직선)
# - 오른쪽: $C_p$ 매트릭스 — 배정 가능 조합(초록)과 불가능 조합(빨강)

# %%
fig = make_subplots(
    rows=3,
    cols=2,
    specs=[
        [{}, {"rowspan": 3}],
        [{}, None],
        [{}, None],
    ],
    subplot_titles=(
        f"CNC-01 (σ={MACHINES[0]['sigma']:.4f})",
        "Cp 매트릭스 (기계 × 부품)",
        f"CNC-02 (σ={MACHINES[1]['sigma']:.4f})",
        f"LATHE-07 (σ={MACHINES[2]['sigma']:.4f})",
    ),
    horizontal_spacing=0.12,
    vertical_spacing=0.10,
)

x = np.linspace(NOMINAL - 0.12, NOMINAL + 0.12, 800)
band_colors = ["#d62728", "#ff7f0e", "#2ca02c"]

for i, m in enumerate(MACHINES, start=1):
    pdf = norm.pdf(x, NOMINAL, m["sigma"])
    fig.add_trace(
        go.Scatter(
            x=x,
            y=pdf / pdf.max(),
            mode="lines",
            line={"color": "#1f77b4", "width": 2},
            name=m["machineId"],
            showlegend=False,
            hovertemplate="dim=%{x:.4f}<extra></extra>",
        ),
        row=i,
        col=1,
    )
    for j, p in enumerate(PARTS):
        for sign in (-1, 1):
            fig.add_vline(
                x=NOMINAL + sign * p["tolerance"],
                line={"color": band_colors[j], "width": 1.5, "dash": "dash"},
                row=i,
                col=1,
            )
    fig.update_yaxes(title_text="상대 밀도", range=[0, 1.15], row=i, col=1)
fig.update_xaxes(title_text="치수 (mm)", row=3, col=1)

cp_matrix = np.array([[r["cp"] for r in rows if r["machineId"] == m["machineId"]] for m in MACHINES])
text = [[f"Cp={c:.2f}<br>{'OK' if c >= CP_MIN else 'NG'}" for c in row] for row in cp_matrix]
fig.add_trace(
    go.Heatmap(
        z=np.clip(cp_matrix, 0, 3),
        x=[f"{p['partId']}<br>±{p['tolerance']:.3f}" for p in PARTS],
        y=[f"{m['machineId']}<br>σ={m['sigma']:.4f}" for m in MACHINES],
        text=text,
        texttemplate="%{text}",
        colorscale=[[0.0, "#c0392b"], [CP_MIN / 3, "#f1c40f"], [1.0, "#27ae60"]],
        zmin=0,
        zmax=3,
        colorbar={"title": "Cp", "len": 0.9},
        hovertemplate="%{y} / %{x}<br>%{text}<extra></extra>",
    ),
    row=1,
    col=2,
)
fig.update_yaxes(autorange="reversed", row=1, col=2)  # 고정밀 기계를 위쪽에

fig.update_layout(
    title_text="tolerance(부품) × σ(기계) → Cp → 배정 가능 여부",
    height=760,
    width=1180,
    template="plotly_white",
)
_show(fig)

import os

_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(_png, scale=2)
print("saved:", _png)

# 출력: saved: .../2f6c14b0-4da9-4fcf-81e7-c19908129574/expy.png

# %% [markdown]
# ## 4. 결론 — 온톨로지 관점
#
# | 조합 | $C_p$ | 판정 |
# |---|---|---|
# | P-100 (±0.010) × CNC-01 | 1.67 | OK — 가장 좁은 공차는 최고 정밀 기계 하나뿐 |
# | P-100 × CNC-02 / LATHE-07 | 0.33 / 0.19 | NG — 수율 68% / 43%, 불량 32만~57만 ppm |
# | P-200 (±0.045) × CNC-01 / CNC-02 | 7.50 / 1.50 | OK (LATHE-07은 0.83으로 NG) |
# | P-300 (±0.080) × 전 기계 | 13.33 / 2.67 / 1.48 | 전부 OK |
#
# 정리하면:
#
# 1. **tolerance가 좁을수록 요구 $\sigma$가 선형으로 작아진다** ($\sigma_{max} = T / 3C_{p,min}$).
#    즉 tighter tolerance = 더 높은 정밀도 기계가 **필수**.
# 2. 고정밀 기계는 수가 적고 비싸므로, 좁은 tolerance 부품은 배정 가능한 기계 집합이 좁아진다.
#    → `Work-Order --assigned_to--> Machine` 을 결정할 때 **선택지를 줄이는 제약**으로 작동.
# 3. 제약을 어기면 불량률이 급증하고(`Quality-Check.passed = false`),
#    `Quality-Check → Part → Work-Order → Machine` 피드백 루프로 문제 기계가 드러난다.
#
# 그래서 `Part.tolerance`는 단순 스펙 값이 아니라 **생산 계획(스케줄링)의 핵심 제약**이다.
