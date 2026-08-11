# 필요 패키지: plotly, kaleido (pip install plotly kaleido)
# 표준 라이브러리(random, statistics, dataclasses)만으로도 대부분의 셀은 동작한다.

# %% [markdown]
# # Sensor: `lastReading` + `threshold`
#
# **질문** — Sensor에 `lastReading`과 `threshold`를 함께 두는 이유는?
#
# **답** — 현재 판독값을 알려진 안전 경계와 비교해 이상을 자동 감지하기 위해서다.
# 이 패턴은 설비 고장 전에 운영자에게 경고하는 **예지 보전(predictive maintenance)** 의 기본이다.
#
# 이 노트북에서 단계적으로 확인할 것:
#
# 1. Sensor 엔티티를 정의하고 `lastReading`/`threshold`를 1급 속성으로 둔다
# 2. 서서히 고장으로 드리프트하는 진동 센서 시계열을 시뮬레이션한다
# 3. `lastReading > threshold` 비교만으로 이상 시점을 잡아낸다
# 4. 임계값이 센서 밖에 있으면 무슨 일이 벌어지는지 대조한다
# 5. 고정 임계값 vs 이동 통계 임계값 $\mu + k\sigma$ 를 비교한다
# 6. 전체 온톨로지 경로(Sensor → Machine → Part ← QualityCheck) 질의로 확장한다

# %%
import math
import random
from dataclasses import dataclass, field
from statistics import mean, pstdev


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


random.seed(7)
print("setup done")
# 출력: setup done

# %% [markdown]
# ## 1. Sensor 엔티티
#
# manufacturing-path 1단계(Factory Floor)의 정의를 그대로 코드로 옮긴다.
#
# | Property | Type | Identifier? |
# |---|---|---|
# | `sensorId` | string | ✓ |
# | `type` | string | |
# | `unit` | string | |
# | `lastReading` | float | |
# | `threshold` | float | |
#
# 핵심은 **관측치(`lastReading`)와 정책값(`threshold`)이 같은 노드에 산다**는 것이다.

# %%
@dataclass
class Machine:
    machineId: str
    name: str
    type: str
    status: str = "running"


@dataclass
class Sensor:
    sensorId: str
    type: str
    unit: str
    lastReading: float
    threshold: float
    monitors: str = ""  # → Machine.machineId (many-to-one)

    @property
    def is_anomalous(self) -> bool:
        # 이상 감지 전체 로직이 '속성 비교 한 줄'로 끝난다
        return self.lastReading > self.threshold


machines = {
    "M-01": Machine("M-01", "CNC-01", "cnc"),
    "M-02": Machine("M-02", "PRESS-02", "press"),
}

sensors = [
    Sensor("SEN-001", "temperature", "°C", 71.4, 85.0, "M-01"),
    Sensor("SEN-002", "vibration", "mm/s", 5.2, 4.5, "M-01"),
    Sensor("SEN-003", "pressure", "bar", 9.8, 12.0, "M-02"),
]

for s in sensors:
    flag = "ALERT" if s.is_anomalous else "ok"
    print(f"{s.sensorId} {s.type:<12} {s.lastReading:>6.1f}{s.unit:<5} / thr {s.threshold:>5.1f}  -> {flag}")
# 출력: SEN-001 temperature    71.4°C    / thr  85.0  -> ok
# 출력: SEN-002 vibration       5.2mm/s  / thr   4.5  -> ALERT
# 출력: SEN-003 pressure        9.8bar   / thr  12.0  -> ok

# %% [markdown]
# 여기서 이미 요점이 드러난다.
#
# - `71.4`, `5.2`, `9.8` 이라는 숫자만 봐서는 정상/이상을 **판단할 수 없다**.
#   단위도 다르고, 물리량도 다르고, 안전 범위도 다르다.
# - `threshold`가 센서마다 다르기 때문에 전역 상수로 뺄 수 없다.
#   → 임계값은 **센서 인스턴스의 속성**이어야 한다.

# %% [markdown]
# ## 2. 고장으로 드리프트하는 진동 센서 시뮬레이션
#
# 실제 설비 고장은 갑자기 오지 않는다. 베어링 마모처럼 **서서히 값이 올라간다**.
#
# 시간 $t$(시간 단위)에서의 진동값을 이렇게 모델링한다.
#
# $$ r(t) = b + d \cdot \max(0,\, t - t_0)^{1.35} + \varepsilon_t, \qquad \varepsilon_t \sim \mathcal{N}(0, \sigma^2) $$
#
# - $b$ : 기준선(baseline) 진동
# - $t_0$ : 열화가 시작되는 시점
# - $d$ : 드리프트 계수
# - $\varepsilon_t$ : 센서 노이즈

# %%
BASELINE = 2.10  # mm/s
DRIFT_START = 40  # hour
DRIFT_COEF = 0.020
NOISE_SD = 0.16
N_HOURS = 96
THRESHOLD = 4.50  # mm/s — SEN-002의 threshold


def simulate(n=N_HOURS):
    out = []
    for t in range(n):
        deg = DRIFT_COEF * max(0, t - DRIFT_START) ** 1.35
        out.append(round(BASELINE + deg + random.gauss(0, NOISE_SD), 3))
    return out


readings = simulate()
print("t=0..5   ", readings[:6])
print("t=45..50 ", readings[45:51])
print("t=90..95 ", readings[90:96])
print("min/max  ", min(readings), max(readings))
# 출력: t=0..5    [2.059, 2.182, 2.064, 2.05, 1.951, 2.066]
# 출력: t=45..50  [2.485, 2.002, 2.325, 2.414, 2.358, 2.627]
# 출력: t=90..95  [5.716, 6.037, 6.381, 6.064, 6.433, 6.735]
# 출력: min/max   1.821 6.735

# %% [markdown]
# ## 3. `lastReading > threshold` — 이상 감지
#
# 스트리밍 파이프라인이 매 시각 `Sensor.lastReading`을 갱신한다고 하자.
# 감지 로직은 **오직 이 한 줄**이다.
#
# ```python
# sensor.lastReading > sensor.threshold
# ```

# %%
sen002 = sensors[1]  # vibration sensor on CNC-01

breaches = []
for t, r in enumerate(readings):
    sen002.lastReading = r  # 텔레메트리 인입 → 노드 속성 갱신
    if sen002.is_anomalous:  # ← 이상 감지의 전부
        breaches.append(t)

print("threshold        :", sen002.threshold)
print("총 초과 시각 수  :", len(breaches))
print("최초 초과 시각 t :", breaches[0])
print("최초 10개        :", breaches[:10])
# 출력: threshold        : 4.5
# 출력: 총 초과 시각 수  : 19
# 출력: 최초 초과 시각 t : 77
# 출력: 최초 10개        : [77, 78, 79, 80, 81, 82, 83, 84, 85, 86]

# %% [markdown]
# 최초 초과 시각이 $t=77$, 시뮬레이션 종료가 $t=95$.
# 즉 **완전 고장까지 약 19시간의 정비 창(maintenance window)** 을 확보했다.
# 이것이 예지 보전이 만들어내는 실질 가치다.

# %%
lead_time = (N_HOURS - 1) - breaches[0]
print(f"경보 → 시뮬레이션 종료까지 리드타임: {lead_time} 시간")
print(f"경보 시점 판독값: {readings[breaches[0]]} mm/s (threshold {THRESHOLD})")
# 출력: 경보 → 시뮬레이션 종료까지 리드타임: 18 시간
# 출력: 경보 시점 판독값: 4.875 mm/s (threshold 4.5)

# %% [markdown]
# ## 4. 대조군 — `threshold`가 Sensor 밖에 있다면?
#
# 임계값을 외부 설정에 두면, 이상 감지는 더 이상 그래프 안에서 끝나지 않는다.
# 조회할 때마다 **외부 조회 → 매핑 → 비교** 3단계를 거쳐야 한다.

# %%
# (A) 나쁜 설계: 임계값이 별도 룰 스토어에 있음
EXTERNAL_RULES = {
    ("cnc", "vibration"): 4.5,
    ("press", "pressure"): 12.0,
    # ("cnc", "temperature") 누락 → 조회 실패 = 감지 구멍
}


def detect_external(sensor: Sensor) -> str:
    machine = machines[sensor.monitors]  # 1) 기계 조인
    thr = EXTERNAL_RULES.get((machine.type, sensor.type))  # 2) 외부 룰 조회
    if thr is None:
        return "UNKNOWN (룰 없음)"  # 3) 실패 경로가 생김
    return "ALERT" if sensor.lastReading > thr else "ok"


# (B) 좋은 설계: 임계값이 센서 속성
def detect_inline(sensor: Sensor) -> str:
    return "ALERT" if sensor.lastReading > sensor.threshold else "ok"


probe = [
    Sensor("SEN-001", "temperature", "°C", 91.0, 85.0, "M-01"),
    Sensor("SEN-002", "vibration", "mm/s", 5.2, 4.5, "M-01"),
    Sensor("SEN-003", "pressure", "bar", 9.8, 12.0, "M-02"),
]
for s in probe:
    print(f"{s.sensorId} 외부룰={detect_external(s):<15} 속성비교={detect_inline(s)}")
# 출력: SEN-001 외부룰=UNKNOWN (룰 없음)  속성비교=ALERT
# 출력: SEN-002 외부룰=ALERT           속성비교=ALERT
# 출력: SEN-003 외부룰=ok              속성비교=ok

# %% [markdown]
# SEN-001은 실제로 임계값을 넘었는데(91.0 > 85.0) 외부 룰 방식에서는 **감지되지 않는다**.
# 룰 스토어와 센서 목록이 서로 다른 시스템이라 동기화가 깨졌기 때문이다.
#
# > 온톨로지 원칙: **판단에 필요한 값은 판단이 일어나는 노드에 둔다.**
# > 그래야 새 센서를 추가하는 순간부터 감지가 자동으로 따라온다.

# %% [markdown]
# ## 5. 고정 임계값 vs 이동 통계 임계값
#
# 고정 임계값은 단순하지만 개체차·환경 변화를 반영하지 못한다.
# 대안은 과거 $w$ 구간의 이동 통계로 임계값을 만드는 것이다.
#
# $$ \text{threshold}_t = \mu_{[t-g-w,\; t-g)} + k\,\sigma_{[t-g-w,\; t-g)} $$
#
# 여기서 $g$ 는 **지연(gap)** 이다. $g=0$ 이면 창 안에 드리프트가 그대로 들어와
# 임계값이 판독값을 따라 올라가버린다(자기추종, self-chasing). 아래에서 직접 확인한다.
#
# 중요한 점: **쿼리 형태는 바뀌지 않는다.** 계산 결과를 다시 `Sensor.threshold`에 써 넣으면
# 소비자 쪽 로직은 여전히 `lastReading > threshold` 한 줄이다.

# %%
WINDOW = 24
K = 3.0
GAP = 12


def rolling_threshold(vals, w=WINDOW, k=K, gap=0):
    out = []
    for t in range(len(vals)):
        start, end = t - gap - w, t - gap
        if start < 0:
            out.append(None)  # 워밍업 구간
            continue
        win = vals[start:end]
        out.append(mean(win) + k * pstdev(win))
    return out


chasing = rolling_threshold(readings, gap=0)  # 나쁜 설정: 창이 드리프트를 흡수
roll_thr = rolling_threshold(readings, gap=GAP)  # 좋은 설정: 12시간 지연 창

fixed_hits = [t for t, r in enumerate(readings) if r > THRESHOLD]
chase_hits = [t for t, r in enumerate(readings) if chasing[t] is not None and r > chasing[t]]
roll_hits = [t for t, r in enumerate(readings) if roll_thr[t] is not None and r > roll_thr[t]]

print("고정 임계값  최초 경보 t :", fixed_hits[0], f"(총 {len(fixed_hits)}회)")
print("자기추종(g=0) 최초 경보 t :", chase_hits[0], f"(총 {len(chase_hits)}회)")
print("지연창(g=12) 최초 경보 t :", roll_hits[0], f"(총 {len(roll_hits)}회)")
print(f"t=60  고정 {THRESHOLD} / g=0 {chasing[60]:.3f} / g=12 {roll_thr[60]:.3f}")
print(f"t=90  고정 {THRESHOLD} / g=0 {chasing[90]:.3f} / g=12 {roll_thr[90]:.3f}")
# 출력: 고정 임계값  최초 경보 t : 77 (총 19회)
# 출력: 자기추종(g=0) 최초 경보 t : 45 (총 2회)
# 출력: 지연창(g=12) 최초 경보 t : 50 (총 45회)
# 출력: t=60  고정 4.5 / g=0 3.677 / g=12 2.570
# 출력: t=90  고정 4.5 / g=0 7.037 / g=12 5.349

# %% [markdown]
# 세 가지가 확연히 갈린다.
#
# | 방식 | 최초 경보 | 경보 지속 | 문제점 |
# |---|---|---|---|
# | 고정 `threshold = 4.5` | $t=77$ | 19회 | 늦다. 하지만 안전 한계로서 명확 |
# | 이동 통계, $g=0$ | $t=45$ | **2회** | 임계값이 드리프트를 따라 올라가 경보가 꺼진다 |
# | 이동 통계, $g=12$ | $t=50$ | 45회 | 27시간 조기 경보 + 지속 유지 |
#
# $g=0$ 이 $t=90$에 7.037까지 치솟는 것이 자기추종의 증거다 —
# 기계가 확실히 고장으로 가고 있는데 "최근 24시간 기준으로는 정상"이 되어버린다.
#
# → 실무에서는 **고정 상한(안전 한계) + 지연 이동 통계(조기 경보)** 를 함께 쓴다.
# 온톨로지 관점에서는 둘 다 결국 Sensor 노드의 속성 비교로 표현된다.

# %% [markdown]
# ### 오탐 억제: 연속 N회 초과(디바운스)

# %%
def debounce(vals, thr, n=3):
    streak = 0
    for t, r in enumerate(vals):
        streak = streak + 1 if r > thr else 0
        if streak >= n:
            return t
    return None


for n in (1, 2, 3, 5):
    print(f"연속 {n}회 초과 요구 -> 최초 확정 경보 t = {debounce(readings, THRESHOLD, n)}")
# 출력: 연속 1회 초과 요구 -> 최초 확정 경보 t = 77
# 출력: 연속 2회 초과 요구 -> 최초 확정 경보 t = 78
# 출력: 연속 3회 초과 요구 -> 최초 확정 경보 t = 79
# 출력: 연속 5회 초과 요구 -> 최초 확정 경보 t = 81

# %% [markdown]
# ## 6. 온톨로지 전체 경로로 확장
#
# `lastReading > threshold`가 **인라인 술어**이기 때문에,
# 다른 도메인 조건과 한 번의 그래프 순회에서 합칠 수 있다.
#
# ```gql
# MATCH (s:Sensor)-[:monitors]->(m:Machine)-[:has_part]->(p:Part)<-[:inspects]-(qc:QualityCheck)
# WHERE s.lastReading > s.threshold AND qc.passed = false
# RETURN m.name, s.type, s.lastReading, p.name, qc.defectCode
# ```

# %%
@dataclass
class Part:
    partId: str
    name: str
    produced_by: str  # → Machine.machineId


@dataclass
class QualityCheck:
    checkId: str
    inspects: str  # → Part.partId
    passed: bool
    defectCode: str = ""


parts = [
    Part("P-100", "Bracket-A", "M-01"),
    Part("P-101", "Bracket-B", "M-01"),
    Part("P-200", "Housing-C", "M-02"),
]
checks = [
    QualityCheck("QC-1", "P-100", False, "DIM-OUT"),
    QualityCheck("QC-2", "P-101", True),
    QualityCheck("QC-3", "P-200", False, "SURF-01"),
]

live = [
    Sensor("SEN-001", "temperature", "°C", 71.4, 85.0, "M-01"),
    Sensor("SEN-002", "vibration", "mm/s", readings[-1], 4.5, "M-01"),
    Sensor("SEN-003", "pressure", "bar", 9.8, 12.0, "M-02"),
]

rows = []
for s in live:
    if not s.is_anomalous:  # ← WHERE s.lastReading > s.threshold
        continue
    for p in parts:
        if p.produced_by != s.monitors:
            continue
        for qc in checks:
            if qc.inspects == p.partId and not qc.passed:  # ← AND qc.passed = false
                rows.append((machines[s.monitors].name, s.type, s.lastReading, p.name, qc.defectCode))

for r in rows:
    print(r)
# 출력: ('CNC-01', 'vibration', 6.735, 'Bracket-A', 'DIM-OUT')

# %% [markdown]
# "센서 이상이 있던 기계가 만든 부품 중 품질 검사에 실패한 것"이 정확히 한 건 나온다.
# 만약 `threshold`가 Sensor 밖에 있었다면 이 순회 중간에 외부 시스템 호출이 끼어들어야 했다.

# %% [markdown]
# ## 7. 시각화

# %%
try:
    import plotly.graph_objects as go

    hours = list(range(N_HOURS))
    breach_x = [t for t in hours if readings[t] > THRESHOLD]
    breach_y = [readings[t] for t in breach_x]
    roll_x = [t for t in hours if roll_thr[t] is not None]
    roll_y = [roll_thr[t] for t in roll_x]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=hours, y=readings, mode="lines", name="lastReading (vibration)",
            line=dict(color="#4C78A8", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=hours, y=[THRESHOLD] * N_HOURS, mode="lines", name=f"threshold = {THRESHOLD} mm/s",
            line=dict(color="#E45756", width=2, dash="dash"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=roll_x, y=roll_y, mode="lines", name="rolling μ + 3σ (w=24, gap=12)",
            line=dict(color="#F58518", width=2, dash="dot"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=breach_x, y=breach_y, mode="markers", name="lastReading > threshold",
            marker=dict(color="#E45756", size=8, symbol="circle-open", line=dict(width=2)),
        )
    )
    fig.add_vline(x=DRIFT_START, line=dict(color="#888", width=1, dash="dot"))
    fig.add_annotation(x=DRIFT_START, y=max(readings), text="열화 시작", showarrow=False, yshift=12, font=dict(size=11))
    fig.add_annotation(
        x=breach_x[0], y=breach_y[0], text=f"최초 경보 t={breach_x[0]}", showarrow=True,
        arrowhead=2, ax=-60, ay=-40, font=dict(size=11),
    )
    fig.update_layout(
        title="Sensor.lastReading vs Sensor.threshold — 드리프트 고장의 조기 감지",
        xaxis_title="시간 (hour)",
        yaxis_title="진동 (mm/s)",
        template="plotly_white",
        width=980,
        height=520,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    _show(fig)

    import os

    out_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
    fig.write_image(out_png, scale=2)
    print("saved:", out_png)
except ImportError as e:
    print("plotly/kaleido 미설치 — 시각화 건너뜀:", e)
# 출력: saved: .../expy.png

# %% [markdown]
# ## 정리
#
# | 관점 | `lastReading`만 있을 때 | `lastReading` + `threshold` |
# |---|---|---|
# | 이상 판단 | 불가 (기준 없음) | `lastReading > threshold` 한 줄 |
# | 센서별 차이 | 외부 룰 필요 | 노드 속성으로 자연 표현 |
# | 신규 센서 | 룰 등록 누락 시 감지 구멍 | 등록 즉시 감지 대상 |
# | 복합 질의 | 순회 중 외부 호출 | 인라인 술어로 결합 |
# | 정비 전략 | 사후 보전 | **예지 보전** |
#
# 두 속성을 한 노드에 두는 순간, 이상 감지는 별도 시스템이 아니라
# **그래프 속성 비교**가 되고 — 그것이 예지 보전의 출발점이다.
