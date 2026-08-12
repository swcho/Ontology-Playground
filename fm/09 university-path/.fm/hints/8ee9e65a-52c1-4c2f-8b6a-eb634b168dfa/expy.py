# 필요 패키지: numpy, plotly, kaleido  (pip install numpy plotly kaleido)

# %% [markdown]
# # `Student.gpa` 는 왜 `float` 인가
#
# University 온톨로지의 `Student` 엔티티:
#
# | Property | Type | Identifier? |
# |---|---|---|
# | `studentId` | string | ✓ |
# | `name` | string | |
# | `gpa` | **float** | |
# | `enrollmentYear` | integer | |
# | `major` | string | |
#
# > The `gpa` property is a float — Grade Point Average ranges from 0.0 to 4.0.
# > This aggregate metric enables academic standing queries and honor roll calculations.
#
# 핵심은 두 가지다.
#
# 1. **값의 성질** — GPA 는 개수를 세는 값이 아니라 *학점 가중 평균*이다. 정의상 $0.0 \le \text{GPA} \le 4.0$ 구간의 연속적인 소수값이다.
# 2. **질의의 성질** — `float` 이어야 임계값 비교(`gpa < 2.0` 학사경고, `gpa >= 3.5` 우등생)와
#    집계(`AVG(gpa)` per Department)가 의미를 갖는다.
#
# 이 노트북은 (1) GPA 를 실제로 계산해 보고, (2) 정수/반올림으로 저장했을 때 무엇이 깨지는지 세어 본다.

# %%
from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


HERE = os.path.dirname(os.path.abspath(__file__))
print("ready")
# 출력: ready

# %% [markdown]
# ## 1. 원천 데이터는 `Enrollment.grade` (string)
#
# 온톨로지에서 성적 자체는 Enrollment 라는 **junction entity** 위에 `grade: string` 으로 얹혀 있다.
# `Student.gpa` 는 그 문자열 등급들을 숫자로 환산해 **학점(credits)으로 가중평균한 파생 지표**다.
#
# $$\text{GPA} = \frac{\sum_i c_i \cdot p_i}{\sum_i c_i}$$
#
# - $c_i$ : i 번째 과목의 학점 수 (`Course.credits`, integer)
# - $p_i$ : i 번째 과목의 등급 점수 (letter grade → grade point)
#
# 등급 → 점수 매핑부터가 이미 소수다. `A- = 3.7`, `B+ = 3.3` 처럼 정수로 표현 불가능한 값이 나온다.

# %%
GRADE_POINTS: dict[str, float] = {
    "A+": 4.0, "A": 4.0, "A-": 3.7,
    "B+": 3.3, "B": 3.0, "B-": 2.7,
    "C+": 2.3, "C": 2.0, "C-": 1.7,
    "D+": 1.3, "D": 1.0, "F": 0.0,
}


@dataclass(frozen=True)
class Enrollment:
    """Enrollment junction entity (일부 속성만)."""

    course_id: str
    credits: int  # Course.credits (integer)
    grade: str  # Enrollment.grade (string)


def compute_gpa(enrollments: list[Enrollment]) -> float:
    """학점 가중 평균 GPA."""
    total_credits = sum(e.credits for e in enrollments)
    if total_credits == 0:
        return 0.0
    weighted = sum(e.credits * GRADE_POINTS[e.grade] for e in enrollments)
    return weighted / total_credits


alice = [
    Enrollment("CS101", 4, "A"),
    Enrollment("MATH201", 3, "B+"),
    Enrollment("PHYS110", 4, "A-"),
    Enrollment("ENG100", 2, "B"),
]

for e in alice:
    print(f"{e.course_id:9s} credits={e.credits}  grade={e.grade:2s} -> point={GRADE_POINTS[e.grade]}")
print("sum(credits) =", sum(e.credits for e in alice))
print("GPA =", compute_gpa(alice))
# 출력: CS101     credits=4  grade=A  -> point=4.0
# 출력: MATH201   credits=3  grade=B+ -> point=3.3
# 출력: PHYS110   credits=4  grade=A- -> point=3.7
# 출력: ENG100    credits=2  grade=B  -> point=3.0
# 출력: sum(credits) = 13
# 출력: GPA = 3.5923076923076924

# %% [markdown]
# GPA 는 `3.5923...` — 나눗셈의 결과라 **애초에 정수로 떨어지지 않는다**.
# 학점 가중이라는 점도 중요하다. 단순 산술평균과 값이 달라진다.

# %%
def report(name: str, enrollments: list[Enrollment]) -> None:
    simple = sum(GRADE_POINTS[e.grade] for e in enrollments) / len(enrollments)
    w = compute_gpa(enrollments)
    print(f"{name:6s} 단순평균={simple:.4f}  학점가중={w:.4f}  차이={w - simple:+.4f}  우등생(>=3.5)={w >= 3.5}")


# bob: 1학점 세미나에서 A, 4학점 전공에서 B -> 가중하면 크게 내려간다
bob = [Enrollment("SEM101", 1, "A"), Enrollment("CHEM210", 4, "B")]

report("alice", alice)
report("bob", bob)
# 출력: alice  단순평균=3.5000  학점가중=3.5923  차이=+0.0923  우등생(>=3.5)=True
# 출력: bob    단순평균=3.5000  학점가중=3.2000  차이=-0.3000  우등생(>=3.5)=False

# %% [markdown]
# 단순평균은 둘 다 정확히 3.50 이지만, 학점 가중 후에는 alice 3.5923 / bob 3.2000 으로 갈린다.
# **소수점 아래 값이 그대로 우등생 판정을 가른다.** 값을 뭉개면 이 구분이 사라진다.

# %% [markdown]
# ## 2. 정수/반올림으로 저장하면 무엇을 잃는가
#
# `gpa` 를 integer 로 선언했다고 가정하고 세 가지 저장 전략을 비교한다.
#
# | 전략 | 표현 | 해상도 |
# |---|---|---|
# | `int_trunc` | `int(gpa)` (버림) | 5단계 (0,1,2,3,4) |
# | `int_round` | `round(gpa)` (반올림) | 5단계 |
# | `one_dec` | `round(gpa, 1)` | 41단계 |
# | `float` | 원값 | 연속 |

# %%
def encode(gpa: float) -> dict[str, float]:
    return {
        "float": gpa,
        "one_dec": round(gpa, 1),
        "int_round": float(round(gpa)),
        "int_trunc": float(int(gpa)),
    }


for g in (3.5923, 1.96, 3.49, 3.51, 2.00):
    enc = encode(g)
    print(f"gpa={g:<7} float={enc['float']:<7} one_dec={enc['one_dec']:<5} "
          f"int_round={enc['int_round']:<4} int_trunc={enc['int_trunc']}")
# 출력: gpa=3.5923  float=3.5923  one_dec=3.6   int_round=4.0  int_trunc=3.0
# 출력: gpa=1.96    float=1.96    one_dec=2.0   int_round=2.0  int_trunc=1.0
# 출력: gpa=3.49    float=3.49    one_dec=3.5   int_round=3.0  int_trunc=3.0
# 출력: gpa=3.51    float=3.51    one_dec=3.5   int_round=4.0  int_trunc=3.0
# 출력: gpa=2.0     float=2.0     one_dec=2.0   int_round=2.0  int_trunc=2.0

# %% [markdown]
# 벌써 문제가 보인다.
#
# - `1.96` → `int_round = 2` : 학사경고(< 2.0) 대상인데 **경고를 빠져나간다**.
# - `3.51` → `int_trunc = 3` : 우등생(≥ 3.5)인데 **탈락한다**.
# - `3.49` 와 `3.51` 은 `one_dec` 에서 둘 다 `3.5` 가 되어 **경계에서 뒤집힌다**.
#
# 즉 어떤 정수 인코딩도 두 임계값을 동시에 보존하지 못한다.

# %% [markdown]
# ## 3. 학사경고 / 우등생 판정
#
# `float` 이기 때문에 성립하는 대표 질의:
#
# ```gql
# MATCH (s:Student) WHERE s.gpa < 2.0  RETURN s.studentId   // academic probation
# MATCH (s:Student) WHERE s.gpa >= 3.5 RETURN s.studentId   // honor roll
# ```

# %%
PROBATION = 2.0  # 학사경고
HONOR_ROLL = 3.5  # 우등생
DEANS_LIST = 3.9  # 학장 표창


def standing(gpa: float) -> str:
    if gpa < PROBATION:
        return "probation"
    if gpa >= DEANS_LIST:
        return "deans_list"
    if gpa >= HONOR_ROLL:
        return "honor_roll"
    return "good"


for g in (1.72, 1.99, 2.00, 3.49, 3.50, 3.92):
    print(f"gpa={g:<5} -> {standing(g)}")
# 출력: gpa=1.72  -> probation
# 출력: gpa=1.99  -> probation
# 출력: gpa=2.0   -> good
# 출력: gpa=3.49  -> good
# 출력: gpa=3.5   -> honor_roll
# 출력: gpa=3.92  -> deans_list

# %% [markdown]
# 임계값이 `2.0`, `3.5`, `3.9` 처럼 **소수 경계**라는 점에 주목.
# 속성 타입이 integer 였다면 이 경계 자체를 표현할 수 없다.
#
# > 참고: float 은 이진 부동소수라 `0.1 + 0.2 != 0.3` 같은 오차가 있다.
# > GPA 처럼 임계값 비교를 하는 값은 **경계에서 `>=` / `<` 방향을 명확히 정의**해 두는 것이 안전하다.

# %%
print("0.1 + 0.2 == 0.3 ?", 0.1 + 0.2 == 0.3)
print("repr(0.1+0.2) =", repr(0.1 + 0.2))
# 등급 점수 합산도 오차가 난다 -> 경계 비교는 항상 부등호 방향을 고정
print("3.3 + 0.2 >= 3.5 ?", 3.3 + 0.2 >= 3.5, " (repr:", repr(3.3 + 0.2), ")")
# 출력: 0.1 + 0.2 == 0.3 ? False
# 출력: repr(0.1+0.2) = 0.30000000000000004
# 출력: 3.3 + 0.2 >= 3.5 ? True  (repr: 3.5 )

# %% [markdown]
# ## 4. 코호트 시뮬레이션 — 오분류를 세어 본다
#
# 학생 2,000 명의 GPA 를 생성하고, 각 저장 전략이 **학사경고 / 우등생 판정을 몇 명이나 틀리는지** 센다.

# %%
rng = np.random.default_rng(20260812)

DEPARTMENTS = ["Computer Science", "Mathematics", "Physics", "Biology"]
DEPT_MEAN = {"Computer Science": 3.18, "Mathematics": 3.05, "Physics": 3.12, "Biology": 3.21}
N_PER_DEPT = 500

dept_of: list[str] = []
gpas: list[float] = []
for d in DEPARTMENTS:
    raw = rng.normal(DEPT_MEAN[d], 0.55, N_PER_DEPT)
    raw = np.clip(raw, 0.0, 4.0)
    gpas.extend(np.round(raw, 2).tolist())  # 학적부 관행: 소수점 2자리
    dept_of.extend([d] * N_PER_DEPT)

gpa_arr = np.array(gpas)
dept_arr = np.array(dept_of)

print("N =", gpa_arr.size)
print(f"mean={gpa_arr.mean():.4f}  min={gpa_arr.min():.2f}  max={gpa_arr.max():.2f}")
print("distinct values:", np.unique(gpa_arr).size)
# 출력: N = 2000
# 출력: mean=3.1345  min=1.20  max=4.00
# 출력: distinct values: 227

# %%
enc_float = gpa_arr
enc_one_dec = np.round(gpa_arr, 1)
enc_int_round = np.round(gpa_arr).astype(float)  # numpy: half-to-even
enc_int_trunc = np.trunc(gpa_arr)

ENCODINGS = {
    "float (원본)": enc_float,
    "one_dec": enc_one_dec,
    "int_round": enc_int_round,
    "int_trunc": enc_int_trunc,
}

print("고유값 개수 (해상도):")
for name, arr in ENCODINGS.items():
    print(f"  {name:14s} {np.unique(arr).size:>4d}")
# 출력: 고유값 개수 (해상도):
# 출력:   float (원본)      227
# 출력:   one_dec          28
# 출력:   int_round         4
# 출력:   int_trunc         4

# %%
truth_prob = enc_float < PROBATION
truth_honor = enc_float >= HONOR_ROLL

rows = []
for name, arr in ENCODINGS.items():
    p = arr < PROBATION
    h = arr >= HONOR_ROLL
    rows.append(
        {
            "encoding": name,
            "prob_wrong": int((p != truth_prob).sum()),
            "honor_wrong": int((h != truth_honor).sum()),
            "mean": float(arr.mean()),
        }
    )

print(f"{'encoding':14s} {'학사경고 오분류':>14s} {'우등생 오분류':>13s} {'AVG(gpa)':>10s}")
for r in rows:
    print(f"{r['encoding']:14s} {r['prob_wrong']:>14d} {r['honor_wrong']:>13d} {r['mean']:>10.4f}")
print(f"\n실제 학사경고 대상 {int(truth_prob.sum())}명 / 우등생 {int(truth_honor.sum())}명")
# 출력: encoding            학사경고 오분류   우등생 오분류   AVG(gpa)
# 출력: float (원본)                   0             0     3.1345
# 출력: one_dec                       11            52     3.1343
# 출력: int_round                     36             0     3.1330
# 출력: int_trunc                      0           393     2.6530
# 출력:
# 출력: 실제 학사경고 대상 43명 / 우등생 509명

# %% [markdown]
# 결과 해석:
#
# - `int_trunc` : 학사경고는 우연히 맞지만(정수 경계가 2.0 과 일치) **우등생 509명 중 393명을 놓친다**.
#   3.5–3.99 가 전부 `3` 이 되어 `>= 3.5` 를 통과할 수 없기 때문(4.00 인 학생만 살아남는다).
#   게다가 `AVG(gpa)` 가 3.1345 → 2.6530 으로 **0.48 이나 낮게** 왜곡된다.
# - `int_round` : 우등생은 우연히 맞지만(3.5 이상이 4로 올라감) 1.5–1.99 구간이 `2` 로 올라가
#   **학사경고 대상 43명 중 36명을 놓친다**.
# - `one_dec` : 오차가 훨씬 작지만 경계값(3.45–3.49 → 3.5)에서 52명이 여전히 뒤집힌다.
#
# → **어떤 정수 인코딩도 두 임계값을 동시에 만족시키지 못한다.** 이것이 `gpa: float` 의 실질적 이유다.

# %% [markdown]
# ## 5. 집계 질의 — Department 단위 평균 GPA
#
# > Which departments have the highest average student GPA?
# > `Department → Course ← Enrollment ← Student (avg GPA)`
#
# 학과 평균은 학과 간 격차가 0.1 수준이라, 저장 해상도가 낮으면 **순위 자체가 뒤집힌다**.

# %%
def dept_means(values: np.ndarray) -> dict[str, float]:
    return {d: float(values[dept_arr == d].mean()) for d in DEPARTMENTS}


mean_float = dept_means(enc_float)
mean_trunc = dept_means(enc_int_trunc)
mean_round = dept_means(enc_int_round)

rank_float = sorted(DEPARTMENTS, key=lambda d: -mean_float[d])
rank_trunc = sorted(DEPARTMENTS, key=lambda d: -mean_trunc[d])

print(f"{'department':20s} {'float':>8s} {'int_round':>10s} {'int_trunc':>10s}")
for d in DEPARTMENTS:
    print(f"{d:20s} {mean_float[d]:>8.4f} {mean_round[d]:>10.4f} {mean_trunc[d]:>10.4f}")
print("\n순위(float)      :", " > ".join(rank_float))
print("순위(int_trunc)  :", " > ".join(rank_trunc))
print("순위 동일?       :", rank_float == rank_trunc)
# 출력: department              float  int_round  int_trunc
# 출력: Computer Science       3.1848     3.1860     2.6940
# 출력: Mathematics            3.0498     3.0280     2.5840
# 출력: Physics                3.1188     3.1200     2.6320
# 출력: Biology                3.1844     3.1980     2.7020
# 출력:
# 출력: 순위(float)      : Computer Science > Biology > Physics > Mathematics
# 출력: 순위(int_trunc)  : Biology > Computer Science > Physics > Mathematics
# 출력: 순위 동일?       : False

# %% [markdown]
# 1위가 뒤집혔다. float 기준 CS(3.1848) > Biology(3.1844) 인데, 정수 저장에서는 Biology 가 1위로 올라온다.
# 학과 간 격차가 0.0004 수준이라 **저장 해상도가 곧 순위의 신뢰도**다.
#
# 더 심각한 건 절대값이다. 학과 평균이 **0.48 씩 통째로 내려앉아**,
# "평균 GPA 3.0 이상 학과" 같은 임계값 질의를 걸면 `int_trunc` 저장에서는 **4개 학과 전부 탈락**한다.

# %%
THRESH = 3.0
print(f"AVG(gpa) >= {THRESH} 인 학과")
print("  float     :", [d for d in DEPARTMENTS if mean_float[d] >= THRESH])
print("  int_trunc :", [d for d in DEPARTMENTS if mean_trunc[d] >= THRESH])
# 출력: AVG(gpa) >= 3.0 인 학과
# 출력:   float     : ['Computer Science', 'Mathematics', 'Physics', 'Biology']
# 출력:   int_trunc : []

# %% [markdown]
# ## 6. 시각화
#
# 1. GPA 분포와 임계선 (2.0 / 3.5)
# 2. 저장 전략별 오분류 인원
# 3. 저장 전략의 계단형 왜곡 (true GPA → stored value)
# 4. 학과별 평균 GPA (float vs int_trunc)

# %%
fig = make_subplots(
    rows=2,
    cols=2,
    subplot_titles=(
        "① GPA 분포 (float) — 임계선 2.0 / 3.5",
        "② 저장 전략별 판정 오분류 인원",
        "③ true GPA → stored value (계단형 손실)",
        "④ 학과별 AVG(gpa)",
    ),
    vertical_spacing=0.14,
    horizontal_spacing=0.10,
)

# ① 분포
fig.add_trace(
    go.Histogram(x=enc_float, xbins=dict(start=0, end=4.01, size=0.1),
                 marker_color="#4C78A8", name="students", showlegend=False),
    row=1, col=1,
)
for x, color, label, pos in (
    (PROBATION, "#E45756", "probation<br>2.0", "top left"),
    (HONOR_ROLL, "#54A24B", "honor roll<br>3.5", "top right"),
):
    fig.add_vline(x=x, line=dict(color=color, width=2, dash="dash"),
                  annotation_text=label, annotation_position=pos,
                  annotation_font=dict(size=10, color=color),
                  annotation_yshift=-6, row=1, col=1)

# ② 오분류
names = [r["encoding"] for r in rows]
fig.add_trace(go.Bar(x=names, y=[r["prob_wrong"] for r in rows], name="학사경고 오분류",
                     marker_color="#E45756"), row=1, col=2)
fig.add_trace(go.Bar(x=names, y=[r["honor_wrong"] for r in rows], name="우등생 오분류",
                     marker_color="#F58518"), row=1, col=2)

# ③ 계단형 손실
grid = np.linspace(0, 4, 401)
fig.add_trace(go.Scatter(x=grid, y=grid, mode="lines", name="float",
                         line=dict(color="#4C78A8", width=2)), row=2, col=1)
fig.add_trace(go.Scatter(x=grid, y=np.round(grid, 1), mode="lines", name="one_dec",
                         line=dict(color="#54A24B", width=1.5)), row=2, col=1)
fig.add_trace(go.Scatter(x=grid, y=np.round(grid), mode="lines", name="int_round",
                         line=dict(color="#F58518", width=1.5, shape="hv")), row=2, col=1)
fig.add_trace(go.Scatter(x=grid, y=np.trunc(grid), mode="lines", name="int_trunc",
                         line=dict(color="#E45756", width=1.5, shape="hv")), row=2, col=1)
fig.add_hline(y=HONOR_ROLL, line=dict(color="#888", width=1, dash="dot"), row=2, col=1)

# ④ 학과 평균
fig.add_trace(go.Bar(x=DEPARTMENTS, y=[mean_float[d] for d in DEPARTMENTS],
                     name="AVG float", marker_color="#4C78A8",
                     text=[f"{mean_float[d]:.3f}" for d in DEPARTMENTS], textposition="outside"),
              row=2, col=2)
fig.add_trace(go.Bar(x=DEPARTMENTS, y=[mean_trunc[d] for d in DEPARTMENTS],
                     name="AVG int_trunc", marker_color="#E45756",
                     text=[f"{mean_trunc[d]:.3f}" for d in DEPARTMENTS], textposition="outside"),
              row=2, col=2)

fig.update_xaxes(title_text="GPA", row=1, col=1)
fig.update_yaxes(title_text="학생 수", row=1, col=1)
fig.update_yaxes(title_text="오분류 인원", row=1, col=2)
fig.update_xaxes(title_text="true GPA", row=2, col=1)
fig.update_yaxes(title_text="stored GPA", row=2, col=1)
fig.update_yaxes(title_text="AVG(gpa)", range=[0, 3.8], row=2, col=2)

fig.update_layout(
    title_text="Student.gpa 를 float 으로 두어야 하는 이유 (N=2,000)",
    barmode="group",
    height=820,
    width=1180,
    template="plotly_white",
    legend=dict(orientation="h", y=-0.08),
)

_show(fig)

png_path = os.path.join(HERE, "expy.png")
fig.write_image(png_path, scale=2)
print("saved:", png_path)
# 출력: saved: .../expy.png

# %% [markdown]
# ## 정리
#
# | 근거 | 내용 |
# |---|---|
# | 값의 정의 | GPA = 학점 가중 평균 → $0.0 \sim 4.0$ 의 연속 소수값. 등급 점수(`A- = 3.7`)부터 이미 소수 |
# | 임계값 질의 | 학사경고 `gpa < 2.0`, 우등생 `gpa >= 3.5`, 학장표창 `gpa >= 3.9` — 소수 경계를 표현하려면 float 필요 |
# | 집계 질의 | `AVG(gpa)` per Department. 정수 저장 시 평균이 0.48 왜곡되고 학과 1위 순위까지 뒤집힘 |
# | 정보 손실 | int_trunc 는 우등생 509명 중 393명 누락, int_round 는 학사경고 43명 중 36명 누락 |
#
# 온톨로지에서 **속성 타입은 그 속성으로 던질 수 있는 질의의 종류를 결정한다.**
# `credits`/`maxEnrollment` 가 integer 인 것(셀 수 있는 값), `tenured` 가 boolean 인 것(범주 필터),
# `gpa` 가 float 인 것(임계값 + 집계) 모두 같은 원리다.
