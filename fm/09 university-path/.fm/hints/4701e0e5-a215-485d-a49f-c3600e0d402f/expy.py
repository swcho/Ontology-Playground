# %% [markdown]
# # 학과별 평균 GPA: `Department → Course ← Enrollment ← Student`
#
# 이 노트북은 University 온톨로지의 3홉 경로를 작은 in-memory 데이터셋으로 재현하고,
# **중복 계수(double counting)** 가 학과 순위를 어떻게 뒤집는지 보인다.
#
# 경로:
#
# ```
# Department --offers--> Course <--for_course-- Enrollment <--enrolls_in-- Student
# ```
#
# - `offers`   : Department → Course (1:N) — 정방향 순회
# - `for_course`: Enrollment → Course (N:1) — **역방향** 순회
# - `enrolls_in`: Student → Enrollment (1:N) — **역방향** 순회
#
# 1:N 확장이 두 번 들어 있으므로, 경로를 그대로 펼친 결과 행의 단위는
# **학생이 아니라 수강기록(Enrollment)** 이다. 여기에 학생 속성인 `gpa`를 그대로
# 평균내면 수강 과목 수가 가중치로 붙는다.
#
# $$
# \overline{\text{GPA}}^{\text{naive}}_{d}
# = \frac{\sum_{s \in S_d} k_{s,d}\,\text{gpa}(s)}{\sum_{s \in S_d} k_{s,d}}
# \qquad\text{vs}\qquad
# \overline{\text{GPA}}^{\text{distinct}}_{d}
# = \frac{1}{|S_d|}\sum_{s \in S_d} \text{gpa}(s)
# $$
#
# 두 값은 $k_{s,d}$가 모든 학생에 대해 같을 때만 일치한다.

# %%
# 필요 패키지: pandas, plotly, kaleido
import random

import pandas as pd
import plotly.graph_objects as go


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


RNG = random.Random(20260812)
pd.set_option("display.width", 120)
print("ready")
# 출력: ready

# %% [markdown]
# ## 1. 엔티티 만들기 — Department, Course, Student
#
# 학과 3개, 학과당 강좌 4개, 학생 45명.
# 각 학과에는 **GPA와 수강 과목 수의 상관(rho)** 을 다르게 심어 둔다.
# 이 상관이 중복 계수 편향의 방향과 크기를 결정한다.

# %%
DEPARTMENTS = [
    # departmentId, name, rho: GPA-수강수 상관 (+면 고학점 학생이 많이 수강)
    ("D-CS", "Computer Science", -0.9),
    ("D-MA", "Mathematics", +0.9),
    ("D-BI", "Biology", 0.0),
]

departments = pd.DataFrame(
    [{"departmentId": d, "name": n} for d, n, _ in DEPARTMENTS]
)
RHO = {d: r for d, _, r in DEPARTMENTS}
RHO_BY_NAME = {n: r for _, n, r in DEPARTMENTS}

# Department --offers--> Course  (1:N)
courses = pd.DataFrame(
    [
        {"courseId": f"{d.split('-')[1]}{lvl}", "title": f"{n} {lvl}", "departmentId": d}
        for d, n, _ in DEPARTMENTS
        for lvl in (101, 201, 301, 401)
    ]
)

students = pd.DataFrame(
    [
        {"studentId": f"S{i:03d}", "name": f"Student {i:03d}", "gpa": round(RNG.uniform(2.0, 4.0), 2)}
        for i in range(1, 46)
    ]
)

print(departments)
print(courses.head(6))
print(students.head(5))
print(f"\ncourses={len(courses)}, students={len(students)}")
# 출력:
#   departmentId              name
# 0         D-CS  Computer Science
# 1         D-MA       Mathematics
# 2         D-BI           Biology
#   courseId                 title departmentId
# 0    CS101  Computer Science 101         D-CS
# 1    CS201  Computer Science 201         D-CS
# 2    CS301  Computer Science 301         D-CS
# 3    CS401  Computer Science 401         D-CS
# 4    MA101       Mathematics 101         D-MA
# 5    MA201       Mathematics 201         D-MA
#   studentId         name   gpa
# 0      S001  Student 001  2.11
# 1      S002  Student 002  2.61
# 2      S003  Student 003  3.51
# 3      S004  Student 004  3.71
# 4      S005  Student 005  3.22
#
# courses=12, students=45

# %% [markdown]
# ## 2. Enrollment 만들기 — 정션 엔티티
#
# `Enrollment`는 Student와 Course를 잇는 **정션 엔티티**다.
# 학생 $s$가 학과 $d$에서 듣는 과목 수 $k_{s,d}$를 다음과 같이 정한다.
#
# $$
# k_{s,d} = \operatorname{clamp}\big(\,\mathrm{round}(2.5 + \rho_d \cdot (\text{gpa}(s)-3.0)\cdot 1.5 + \varepsilon)\,,\;1,\;4\big)
# $$
#
# - $\rho_{\text{CS}} = -0.9$ → 고학점 학생일수록 **적게** 수강
# - $\rho_{\text{MA}} = +0.9$ → 고학점 학생일수록 **많이** 수강
# - $\rho_{\text{BI}} = 0$ → 무상관

# %%
def k_courses(gpa: float, rho: float) -> int:
    raw = 2.5 + rho * (gpa - 3.0) * 2.0 + RNG.uniform(-0.3, 0.3)
    return max(1, min(4, round(raw)))


# 학생마다 참여 학과 2개를 라운드로빈으로 배정 → 학과별 학생 수를 30명으로 균형
DEPT_PAIRS = [("D-CS", "D-MA"), ("D-MA", "D-BI"), ("D-BI", "D-CS")]

rows = []
eid = 0
for i, (_, s) in enumerate(students.iterrows()):
    # 한 학생이 여러 학과의 강좌를 들을 수 있다 (학과 소속이 배타적이지 않음)
    for dept_id in DEPT_PAIRS[i % 3]:
        pool = courses.loc[courses.departmentId == dept_id, "courseId"].tolist()
        for cid in RNG.sample(pool, k=k_courses(s.gpa, RHO[dept_id])):
            eid += 1
            rows.append(
                {
                    "enrollmentId": f"E{eid:04d}",
                    "studentId": s.studentId,   # <-- enrolls_in (Student → Enrollment)
                    "courseId": cid,            # <-- for_course (Enrollment → Course)
                    "semester": "2026-SP",
                    "grade": RNG.choice(["A", "B", "C", "D"]),
                }
            )

enrollments = pd.DataFrame(rows)
print(enrollments.head(5))
print(f"\nenrollments={len(enrollments)}")
# 출력:
#   enrollmentId studentId courseId semester grade
# 0        E0001      S001    CS101  2026-SP     D
# 1        E0002      S001    CS201  2026-SP     C
# 2        E0003      S001    CS401  2026-SP     B
# 3        E0004      S001    CS301  2026-SP     C
# 4        E0005      S001    MA301  2026-SP     C
#
# enrollments=224
# --> 학생 45명 x 학과 2곳 x 평균 2.5과목 ≈ 224 건

# %% [markdown]
# ## 3. 경로를 그대로 펼치기 (naive)
#
# ```gql
# MATCH (d:Department)-[:offers]->(c:Course)
#       <-[:for_course]-(e:Enrollment)
#       <-[:enrolls_in]-(s:Student)
# RETURN d.name, AVG(s.gpa)      -- 중복 계수!
# ```
#
# 조인 결과의 **행 하나 = 수강기록 하나**. 학생 GPA가 수강 횟수만큼 복제된다.

# %%
path = (
    enrollments
    .merge(courses[["courseId", "departmentId"]], on="courseId")           # Course <-for_course- Enrollment
    .merge(departments, on="departmentId")                                  # Department -offers-> Course
    .merge(students[["studentId", "gpa"]], on="studentId")                  # Enrollment <-enrolls_in- Student
)

print(f"경로 조인 결과 행 수 = {len(path)}  (= 수강기록 수 {len(enrollments)})")
print(path.loc[path.studentId == "S002", ["name", "studentId", "courseId", "gpa"]].to_string(index=False))
# 출력:
# 경로 조인 결과 행 수 = 224  (= 수강기록 수 224)
#        name studentId courseId  gpa
# Mathematics      S002    MA201 2.61
# Mathematics      S002    MA401 2.61
#     Biology      S002    BI101 2.61
#     Biology      S002    BI301 2.61
#     Biology      S002    BI201 2.61
# --> S002(gpa 2.61)는 Mathematics 에서 2번, Biology 에서 3번 집계된다 (중복 계수)

# %%
naive = (
    path.groupby("name")
    .agg(avg_gpa_naive=("gpa", "mean"), rows=("gpa", "size"))
    .sort_values("avg_gpa_naive", ascending=False)
)
print(naive)
# 출력:
#                   avg_gpa_naive  rows
# name
# Mathematics            3.127534    73
# Biology                3.044487    78
# Computer Science       2.794658    73

# %% [markdown]
# ## 4. `WITH DISTINCT d, s` — 집계 전에 입도를 낮추기
#
# ```gql
# MATCH (d:Department)-[:offers]->(c:Course)
#       <-[:for_course]-(e:Enrollment)
#       <-[:enrolls_in]-(s:Student)
# WITH DISTINCT d, s                      -- (학과, 학생) 쌍으로 접기
# RETURN d.name, AVG(s.gpa), COUNT(s)
# ORDER BY 2 DESC
# ```
#
# pandas에서는 `drop_duplicates(["name", "studentId"])`가 `WITH DISTINCT d, s`에 해당한다.

# %%
distinct_pairs = path.drop_duplicates(subset=["name", "studentId"])
print(f"(학과, 학생) 쌍 수 = {len(distinct_pairs)}  ({len(path)}행 -> 축소)")

distinct = (
    distinct_pairs.groupby("name")
    .agg(avg_gpa_distinct=("gpa", "mean"), students=("gpa", "size"))
    .sort_values("avg_gpa_distinct", ascending=False)
)
print(distinct)
# 출력:
# (학과, 학생) 쌍 수 = 90  (224행 -> 축소)
#                   avg_gpa_distinct  students
# name
# Biology                   3.036667        30
# Computer Science          2.982000        30
# Mathematics               2.912000        30
# --> 학과마다 학생 30명으로 균형 (라운드로빈 배정). 224행 -> 90행으로 접힘

# %% [markdown]
# ## 5. 나란히 비교 — 순위가 뒤집힌다
#
# 세 학과 모두 학생 수가 30명으로 **동일**한데도 결과가 갈린다.
# naive 1위였던 Mathematics 는 DISTINCT 에서 **꼴찌**로 떨어지고,
# naive 꼴찌였던 Computer Science 는 2위로 올라온다.
# 편향의 부호는 심어 둔 상관 $\rho$ 그대로다.
#
# - Mathematics($\rho>0$): 고학점 학생이 과목을 많이 들어 GPA가 여러 번 집계 → **과대평가** (+0.216)
# - Computer Science($\rho<0$): 고학점 학생이 적게 들어 GPA가 덜 집계 → **과소평가** (−0.187)
# - Biology($\rho=0$): 두 값이 거의 같음 → 편향 없음 (+0.008)
#
# 즉 편향은 데이터의 크기나 학생 수 문제가 아니라 **GPA와 수강 과목 수의 상관** 문제다.

# %%
compare = naive.join(distinct)
compare["편향"] = compare.avg_gpa_naive - compare.avg_gpa_distinct
compare["평균 수강수 k"] = compare.rows / compare.students
compare["naive 순위"] = compare.avg_gpa_naive.rank(ascending=False).astype(int)
compare["distinct 순위"] = compare.avg_gpa_distinct.rank(ascending=False).astype(int)
print(compare.round(3).to_string())
# 출력:
#                   avg_gpa_naive  rows  avg_gpa_distinct  students     편향  평균 수강수 k  naive 순위  distinct 순위
# name
# Mathematics               3.128    73             2.912        30  0.216      2.433          1              3
# Biology                   3.044    78             3.037        30  0.008      2.600          2              1
# Computer Science          2.795    73             2.982        30 -0.187      2.433          3              2
# --> 편향 부호가 심어 둔 rho 부호와 정확히 일치한다 (MA +0.9 / BI 0.0 / CS -0.9)

# %%
best_naive = compare.avg_gpa_naive.idxmax()
best_distinct = compare.avg_gpa_distinct.idxmax()
print(f"naive    1위: {best_naive}")
print(f"distinct 1위: {best_distinct}   <-- 정답")
print(f"순위 뒤집힘 발생: {best_naive != best_distinct}")
# 출력:
# naive    1위: Mathematics
# distinct 1위: Biology   <-- 정답
# 순위 뒤집힘 발생: True
# --> naive 1위였던 Mathematics 는 DISTINCT 에서 꼴찌(3위)로 떨어진다

# %% [markdown]
# ## 6. `AVG(DISTINCT s.gpa)`의 함정
#
# `AVG(DISTINCT s.gpa)`는 노드가 아니라 **값**을 중복 제거한다.
# 서로 다른 두 학생의 GPA가 우연히 같으면 한 명으로 접혀 또 다른 편향이 생긴다.
# 그래서 `WITH DISTINCT d, s`가 정석이다.

# %%
value_distinct = (
    path.groupby("name")
    .agg(avg_gpa_value_distinct=("gpa", lambda g: g.drop_duplicates().mean()),
         unique_gpa_values=("gpa", lambda g: g.nunique()))
)
check = distinct.join(value_distinct)
check["학생수 - 고유GPA수"] = check.students - check.unique_gpa_values
print(check.round(3).to_string())
# 출력:
#                   avg_gpa_distinct  students  avg_gpa_value_distinct  unique_gpa_values  학생수 - 고유GPA수
# name
# Biology                      3.037        30                   3.065                 28                 2
# Computer Science             2.982        30                   2.982                 30                 0
# Mathematics                  2.912        30                   2.905                 28                 2
# --> Biology / Mathematics 는 GPA 값이 겹치는 학생이 2명씩 있어 AVG(DISTINCT s.gpa) 가 어긋난다.
#     학생 30명인데 고유 GPA 값은 28개 -> 2명이 통째로 사라진 셈.

# %%
# GPA를 소수 1자리로 반올림해 충돌을 강제하면 두 값이 갈라진다.
coarse = path.assign(gpa=path.gpa.round(1))
gap = (
    coarse.groupby("name").agg(
        correct=("gpa", lambda g: g.groupby(coarse.loc[g.index, "studentId"]).first().mean()),
        value_distinct=("gpa", lambda g: g.drop_duplicates().mean()),
    )
)
gap["차이"] = gap.correct - gap.value_distinct
print(gap.round(3).to_string())
# 출력:
#                   correct  value_distinct     차이
# name
# Biology             3.037           3.082 -0.046
# Computer Science    2.983           3.041 -0.058
# Mathematics         2.920           2.943 -0.023
# --> GPA를 소수 1자리로 뭉개면 값 충돌이 늘고, AVG(DISTINCT s.gpa) 오차도 함께 커진다.

# %% [markdown]
# ## 7. 시각화 — 두 방식의 학과별 평균 GPA
#
# 왼쪽: 두 집계 방식의 평균 GPA를 학과별로 나란히 놓은 막대 (0 기준선 유지).
# 오른쪽: 편향 $\overline{\text{GPA}}^{\text{naive}} - \overline{\text{GPA}}^{\text{distinct}}$.
# 막대는 0에서 시작해야 길이 비교가 정직하므로, 미세한 차이는 편향 패널이 대신 보여준다.

# %%
from plotly.subplots import make_subplots  # noqa: E402

LIGHT_SURFACE = "#fcfcfb"
INK = "#0b0b0b"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
C_NAIVE = "#eb6834"     # categorical slot 2 (orange) — 중복 계수
C_DISTINCT = "#2a78d6"  # categorical slot 1 (blue)   — DISTINCT 학생
# 팔레트 검증: validate_palette.js "#2a78d6,#eb6834" --mode light -> ALL CHECKS PASS
#   CVD 분리 ΔE 24.7 (protan) / 정상시 ΔE 33.6 / 대비 3:1 이상

order = compare.sort_values("avg_gpa_distinct", ascending=False)
labels = [f"{n}<br><span style='font-size:11px;color:{MUTED}'>ρ={RHO_BY_NAME[n]:+.1f}</span>" for n in order.index]

fig = make_subplots(
    rows=1,
    cols=2,
    column_widths=[0.62, 0.38],
    horizontal_spacing=0.13,
    subplot_titles=("평균 GPA (0 기준선)", "편향 = naive − DISTINCT"),
)

fig.add_bar(
    name="중복 계수 (naive AVG)",
    x=labels,
    y=order.avg_gpa_naive.round(3),
    marker=dict(color=C_NAIVE, line=dict(color=LIGHT_SURFACE, width=2)),
    text=[f"{v:.3f}" for v in order.avg_gpa_naive],
    textposition="outside",
    textfont=dict(color=INK, size=12),
    customdata=order.rows,
    hovertemplate="%{x}<br>naive AVG: %{y:.3f}<br>행 수(수강기록): %{customdata}<extra></extra>",
    row=1,
    col=1,
)
fig.add_bar(
    name="DISTINCT 학생 (WITH DISTINCT d, s)",
    x=labels,
    y=order.avg_gpa_distinct.round(3),
    marker=dict(color=C_DISTINCT, line=dict(color=LIGHT_SURFACE, width=2)),
    text=[f"{v:.3f}" for v in order.avg_gpa_distinct],
    textposition="outside",
    textfont=dict(color=INK, size=12),
    customdata=order.students,
    hovertemplate="%{x}<br>DISTINCT AVG: %{y:.3f}<br>학생 수: %{customdata}<extra></extra>",
    row=1,
    col=1,
)

bias = order["편향"]
fig.add_bar(
    name="편향",
    x=labels,
    y=bias.round(3),
    marker=dict(
        color=[C_NAIVE if v > 0 else C_DISTINCT for v in bias],
        line=dict(color=LIGHT_SURFACE, width=2),
    ),
    text=[f"{v:+.3f}" for v in bias],
    textposition="outside",
    textfont=dict(color=INK, size=12),
    hovertemplate="%{x}<br>편향: %{y:+.3f}<extra></extra>",
    showlegend=False,
    row=1,
    col=2,
)

fig.update_layout(
    title=dict(
        text="학과별 평균 학생 GPA — 중복 계수 vs DISTINCT 학생<br>"
        "<sub>Department →offers→ Course ←for_course← Enrollment ←enrolls_in← Student"
        " · 학과마다 학생 30명으로 동일<br>"
        f"naive 1위 {best_naive}(ρ&gt;0)는 DISTINCT 에서 3위로 추락 · 정답 1위는 {best_distinct}</sub>",
        font=dict(color=INK, size=17),
        x=0,
        xanchor="left",
        y=0.965,
        yanchor="top",
    ),
    barmode="group",
    bargap=0.35,
    bargroupgap=0.06,
    paper_bgcolor=LIGHT_SURFACE,
    plot_bgcolor=LIGHT_SURFACE,
    legend=dict(orientation="h", y=1.075, x=0, yanchor="bottom", font=dict(color=INK, size=12)),
    margin=dict(l=64, r=32, t=150, b=64),
    width=1000,
    height=560,
)
for c in (1, 2):
    fig.update_xaxes(tickfont=dict(color=INK, size=12), showgrid=False, linecolor=BASELINE, row=1, col=c)
fig.update_yaxes(
    title=dict(text="평균 GPA", font=dict(color=MUTED, size=12)),
    range=[0, 3.85],
    gridcolor=GRID,
    zeroline=True,
    zerolinecolor=BASELINE,
    tickfont=dict(color=MUTED, size=11),
    row=1,
    col=1,
)
fig.update_yaxes(
    title=dict(text="GPA 편향", font=dict(color=MUTED, size=12)),
    range=[-0.30, 0.30],
    gridcolor=GRID,
    zeroline=True,
    zerolinecolor=INK,
    zerolinewidth=1,
    tickfont=dict(color=MUTED, size=11),
    row=1,
    col=2,
)
for ann in fig.layout.annotations[:2]:
    ann.font = dict(color=MUTED, size=12)

_show(fig)
fig.write_image("expy.png", scale=2)
print("saved expy.png")
# 출력: saved expy.png

# %% [markdown]
# ## 8. 정리
#
# | 항목 | 내용 |
# |---|---|
# | 경로 | `Department -offers-> Course <-for_course- Enrollment <-enrolls_in- Student` |
# | 결과 행 단위 | Enrollment (학생 아님) |
# | 문제 | 학생 속성 `gpa`가 수강 과목 수만큼 복제 → 가중평균 |
# | 편향 방향 | 수강 과목이 많은 학생 쪽으로 평균이 끌려감 |
# | 해법 | 집계 **전에** `WITH DISTINCT d, s`로 (학과, 학생) 쌍으로 접기 |
# | 비권장 | `AVG(DISTINCT s.gpa)` — 노드가 아니라 값을 중복 제거 |
# | 항상 함께 출력 | `COUNT(DISTINCT s)` — 분모를 봐야 이상값이 보임 |
#
# 참고: `COUNT(e)` 같은 **Enrollment 단위 지표**(수강생 수, 낙제 건수)는 중복 계수가
# 오히려 정답이다. 문제가 되는 것은 **경로 끝 노드의 속성을 집계할 때**뿐이다.
