# %% [markdown]
# # 학과별 충원율(enrollment rate) 계산 실험
#
# 온톨로지 경로: `Department -[:offers]-> Course <-[:for_course]- Enrollment`
#
# - **분자**: 해당 학과 강좌에 걸린 `Enrollment` 건수 (단, 유효한 건만)
# - **분모**: 해당 강좌들의 `Course.maxEnrollment` (정원)
#
# 핵심 함정 3가지를 실험으로 확인한다.
#
# 1. **비율의 평균 ≠ 평균의 비율** — 강좌별 충원율을 단순 평균하느냐, 총합끼리 나누느냐(가중 평균)에 따라 학과 순위가 뒤집힌다.
# 2. **status 필터** — `drop`/`withdrawn` 건을 세면 충원율이 100%를 넘는 유령 수치가 나온다.
# 3. **semester 구분** — 학기를 안 끊으면 여러 학기 수강건수가 한 학기 정원에 누적된다.
#
# 필요 패키지: pandas, plotly, kaleido

# %%
# 필요 패키지: pandas, plotly, kaleido (png 저장용)
import pandas as pd
import plotly.graph_objects as go


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


pd.set_option("display.width", 160)
pd.set_option("display.max_columns", None)

# %% [markdown]
# ## 1. Course 데이터 (Department -[:offers]-> Course)
#
# 정원(`maxEnrollment`) 편차를 크게 잡는 것이 포인트다. 200명짜리 개론과 5명짜리 세미나가
# 같은 학과에 섞여 있을 때 두 계산 방식의 차이가 극적으로 드러난다.

# %%
courses = pd.DataFrame(
    [
        # courseId,   departmentId, title,               maxEnrollment
        ("CS101", "CS", "Intro to Programming", 200),
        ("CS490", "CS", "Compiler Seminar", 10),
        ("MATH201", "MATH", "Linear Algebra", 50),
        ("MATH310", "MATH", "Real Analysis", 20),
        ("MATH999", "MATH", "Topology Seminar", 5),
        ("ART100", "ART", "Drawing Basics", 40),
        ("ART250", "ART", "Sculpture", 30),
    ],
    columns=["courseId", "departmentId", "title", "maxEnrollment"],
)
print(courses)
# 출력:
#   courseId departmentId                 title  maxEnrollment
# 0    CS101           CS  Intro to Programming            200
# 1    CS490           CS      Compiler Seminar             10
# 2  MATH201         MATH        Linear Algebra             50
# 3  MATH310         MATH         Real Analysis             20
# 4  MATH999         MATH      Topology Seminar              5
# 5   ART100          ART        Drawing Basics             40
# 6   ART250          ART            Sculpture             30

# %% [markdown]
# ## 2. Enrollment 데이터 (Course <-[:for_course]- Enrollment)
#
# `Enrollment`는 junction entity라서 자기 속성 `semester`, `status`, `grade`를 갖는다.
# 여기서는 두 학기(`2024-Fall`, `2025-Spring`)와 네 가지 status를 만든다.
#
# - 유효 등록: `enrolled`, `completed`
# - 제외 대상: `dropped`, `withdrawn`

# %%
# (courseId, semester, status, count) 스펙에서 Enrollment 레코드를 펼친다.
enrollment_spec = [
    # --- 2025-Spring (분석 대상 학기) ---
    ("CS101", "2025-Spring", "enrolled", 120),
    ("CS101", "2025-Spring", "completed", 60),
    ("CS101", "2025-Spring", "dropped", 20),
    ("CS101", "2025-Spring", "withdrawn", 5),
    ("CS490", "2025-Spring", "enrolled", 3),
    ("MATH201", "2025-Spring", "enrolled", 20),
    ("MATH201", "2025-Spring", "completed", 15),
    ("MATH201", "2025-Spring", "dropped", 10),
    ("MATH310", "2025-Spring", "enrolled", 16),
    ("MATH310", "2025-Spring", "dropped", 2),
    ("MATH999", "2025-Spring", "enrolled", 5),
    ("ART100", "2025-Spring", "enrolled", 30),
    ("ART100", "2025-Spring", "withdrawn", 4),
    ("ART250", "2025-Spring", "enrolled", 24),
    ("ART250", "2025-Spring", "dropped", 3),
    # --- 2024-Fall (이전 학기 노이즈) ---
    ("CS101", "2024-Fall", "completed", 150),
    ("MATH201", "2024-Fall", "completed", 40),
    ("ART100", "2024-Fall", "completed", 38),
]

rows = []
seq = 0
for course_id, semester, status, n in enrollment_spec:
    for _ in range(n):
        seq += 1
        rows.append((f"E{seq:04d}", course_id, semester, status))
enrollments = pd.DataFrame(rows, columns=["enrollmentId", "courseId", "semester", "status"])

print(len(enrollments))
print(enrollments.groupby(["semester", "status"]).size())
# 출력:
# 565
# semester     status
# 2024-Fall    completed    228
# 2025-Spring  completed     75
#              dropped       35
#              enrolled     218
#              withdrawn      9
# dtype: int64

# %% [markdown]
# ## 3. 필터: 학기 + 유효 status
#
# 충원율은 "특정 학기의 정원 대비 실제로 자리를 차지한 인원"이다.
# 따라서 **학기를 고정**하고, **중도 포기 건을 제외**해야 한다.

# %%
TARGET_SEMESTER = "2025-Spring"
VALID_STATUS = {"enrolled", "completed"}

sem = enrollments[enrollments["semester"] == TARGET_SEMESTER]
valid = sem[sem["status"].isin(VALID_STATUS)]

counts_valid = valid.groupby("courseId").size().rename("validCount")
counts_all = sem.groupby("courseId").size().rename("allCount")

df = courses.set_index("courseId").join([counts_valid, counts_all]).fillna(0).reset_index()
df[["validCount", "allCount"]] = df[["validCount", "allCount"]].astype(int)
df["rate_valid"] = df["validCount"] / df["maxEnrollment"]
df["rate_all"] = df["allCount"] / df["maxEnrollment"]
print(df[["courseId", "departmentId", "maxEnrollment", "validCount", "allCount", "rate_valid", "rate_all"]])
# 출력:
#   courseId departmentId  maxEnrollment  validCount  allCount  rate_valid  rate_all
# 0    CS101           CS            200         180       205        0.90     1.025
# 1    CS490           CS             10           3         3        0.30     0.300
# 2  MATH201         MATH             50          35        45        0.70     0.900
# 3  MATH310         MATH             20          16        18        0.80     0.900
# 4  MATH999         MATH              5           5         5        1.00     1.000
# 5   ART100          ART             40          30        34        0.75     0.850
# 6   ART250          ART             30          24        27        0.80     0.900

# %% [markdown]
# ### 함정 2 확인: drop을 포함하면 충원율 > 100%
#
# `CS101`은 정원 200명에 유효 등록 180명이지만, 취소 25건을 같이 세면 $205/200 = 102.5\%$가 된다.
# 정원 초과처럼 보이지만 실제로는 빈 자리가 20개 있는 강의다.

# %%
over = df[df["rate_all"] > 1.0]
print(over[["courseId", "maxEnrollment", "validCount", "allCount", "rate_all"]])
# 출력:
#   courseId  maxEnrollment  validCount  allCount  rate_all
# 0    CS101            200         180       205     1.025

# %% [markdown]
# ## 4. 두 가지 학과 충원율 정의
#
# 학과 $d$가 강좌 $c \in C_d$를 offers 한다고 하자.
# $n_c$ = 유효 수강건수, $m_c$ = `Course.maxEnrollment`.
#
# **(A) 단순 평균 (비율의 평균, macro-average)**
#
# $$\mathrm{rate}^{\text{macro}}_d = \frac{1}{|C_d|}\sum_{c \in C_d} \frac{n_c}{m_c}$$
#
# 강좌 하나하나를 동등하게 취급한다. 5명짜리 세미나와 200명짜리 개론이 같은 1표를 갖는다.
#
# **(B) 가중 평균 (평균의 비율, micro-average)**
#
# $$\mathrm{rate}^{\text{micro}}_d = \frac{\sum_{c \in C_d} n_c}{\sum_{c \in C_d} m_c}
# = \sum_{c \in C_d} w_c \cdot \frac{n_c}{m_c}, \quad w_c = \frac{m_c}{\sum_{k \in C_d} m_k}$$
#
# "학과 전체 좌석 중 몇 %가 찼는가"를 뜻한다. 정원이 큰 강좌가 그만큼 크게 반영된다.
#
# 두 값은 모든 $m_c$가 같을 때만 일치한다. 정원 편차가 클수록 벌어진다.

# %%
def dept_rates(frame, count_col):
    g = frame.groupby("departmentId")
    out = pd.DataFrame(
        {
            "courses": g.size(),
            "sum_n": g[count_col].sum(),
            "sum_m": g["maxEnrollment"].sum(),
            "macro": g.apply(lambda x: (x[count_col] / x["maxEnrollment"]).mean(), include_groups=False),
        }
    )
    out["micro"] = out["sum_n"] / out["sum_m"]
    out["gap"] = out["micro"] - out["macro"]
    return out.sort_values("micro", ascending=False)


dept_valid = dept_rates(df, "validCount")
print(dept_valid.round(4))
# 출력:
#               courses  sum_n  sum_m   macro   micro     gap
# departmentId
# CS                  2    183    210  0.6000  0.8714  0.2714
# ART                 2     54     70  0.7750  0.7714 -0.0036
# MATH                3     56     75  0.8333  0.7467 -0.0867

# %% [markdown]
# ## 5. 함정 1 확인: 순위 역전
#
# 같은 데이터인데 정의만 바꾸면 "충원율 1위 학과"가 달라진다.

# %%
rank_macro = dept_valid.sort_values("macro", ascending=False).index.tolist()
rank_micro = dept_valid.sort_values("micro", ascending=False).index.tolist()
print("단순평균(macro) 순위:", rank_macro)
print("가중평균(micro) 순위:", rank_micro)
print("역전 발생:", rank_macro != rank_micro)
# 출력:
# 단순평균(macro) 순위: ['MATH', 'ART', 'CS']
# 가중평균(micro) 순위: ['CS', 'ART', 'MATH']
# 역전 발생: True

# %%
# 왜 CS가 뒤집히는가 — 가중치 w_c 를 직접 본다.
cs = df[df["departmentId"] == "CS"].copy()
cs["w"] = cs["maxEnrollment"] / cs["maxEnrollment"].sum()
cs["w*rate"] = cs["w"] * cs["rate_valid"]
print(cs[["courseId", "maxEnrollment", "validCount", "rate_valid", "w", "w*rate"]].round(4))
print("macro =", round(cs["rate_valid"].mean(), 4), "| micro =", round(cs["w*rate"].sum(), 4))
# 출력:
#   courseId  maxEnrollment  validCount  rate_valid       w  w*rate
# 0    CS101            200         180         0.9  0.9524  0.8571
# 1    CS490             10           3         0.3  0.0476  0.0143
# macro = 0.6 | micro = 0.8714
#
# CS490(정원 10)이 macro에서는 1/2 = 50%의 발언권을 갖지만,
# micro에서는 10/210 = 4.8%에 불과하다. 이 차이가 0.6 vs 0.87을 만든다.

# %% [markdown]
# ## 6. 함정 2 확인: drop 필터 전후 비교

# %%
dept_all = dept_rates(df, "allCount")
cmp = pd.DataFrame(
    {
        "micro_필터적용": dept_valid["micro"],
        "micro_필터없음": dept_all["micro"],
        "macro_필터적용": dept_valid["macro"],
        "macro_필터없음": dept_all["macro"],
    }
).round(4)
cmp["micro_과대계상"] = (cmp["micro_필터없음"] - cmp["micro_필터적용"]).round(4)
print(cmp)
# 출력:
#               micro_필터적용  micro_필터없음  macro_필터적용  macro_필터없음  micro_과대계상
# departmentId
# ART               0.7714      0.8714      0.7750      0.8750       0.1000
# CS                0.8714      0.9905      0.6000      0.6625       0.1191
# MATH              0.7467      0.9067      0.8333      0.9333       0.1600
#
# MATH는 필터를 빼면 90.7%로 "거의 만석"처럼 보이지만 실제로는 74.7%다.

# %% [markdown]
# ## 7. 함정 3 확인: 학기 미구분
#
# `semester` 조건을 빼면 2024-Fall 수강건수까지 2025-Spring 정원에 얹힌다.

# %%
no_sem = enrollments[enrollments["status"].isin(VALID_STATUS)].groupby("courseId").size().rename("nCount")
tmp = courses.set_index("courseId").join(no_sem).fillna(0).reset_index()
tmp["nCount"] = tmp["nCount"].astype(int)
g = tmp.groupby("departmentId")
micro_nosem = (g["nCount"].sum() / g["maxEnrollment"].sum()).round(4)
print(pd.DataFrame({"micro_학기고정": dept_valid["micro"].round(4), "micro_학기무시": micro_nosem}))
# 출력:
#               micro_학기고정  micro_학기무시
# departmentId
# ART                0.7714      1.3143
# CS                 0.8714      1.5857
# MATH               0.7467      1.2800
#
# 전 학과가 100%를 넘는다 — 분자는 누적, 분모는 한 학기치라서 생기는 전형적 오류.

# %% [markdown]
# ## 8. 대응하는 GQL
#
# ```gql
# // 가중 평균(micro) — 권장 기본값
# MATCH (d:Department)-[:offers]->(c:Course)
# OPTIONAL MATCH (c)<-[:for_course]-(e:Enrollment)
#   WHERE e.semester = '2025-Spring' AND e.status IN ['enrolled', 'completed']
# WITH d, c, COUNT(e) AS n, c.maxEnrollment AS m
# WITH d, SUM(n) AS totalEnrolled, SUM(m) AS totalSeats
# RETURN d.name, 1.0 * totalEnrolled / totalSeats AS enrollmentRate
# ORDER BY enrollmentRate DESC
# ```
#
# `OPTIONAL MATCH`가 중요하다. 수강생이 0인 강좌를 `MATCH`로 쓰면 그 강좌의 정원이
# 분모에서 통째로 빠져 충원율이 부풀려진다.
#
# ```gql
# // 단순 평균(macro) — 강좌 하나하나를 동등 취급
# MATCH (d:Department)-[:offers]->(c:Course)
# OPTIONAL MATCH (c)<-[:for_course]-(e:Enrollment)
#   WHERE e.semester = '2025-Spring' AND e.status IN ['enrolled', 'completed']
# WITH d, c, COUNT(e) AS n
# WITH d, AVG(1.0 * n / c.maxEnrollment) AS enrollmentRate
# RETURN d.name, enrollmentRate ORDER BY enrollmentRate DESC
# ```

# %% [markdown]
# ### 함정 4(보너스): 수강생 0인 강좌를 분모에서 누락시키기

# %%
# MATCH만 쓰면 validCount == 0 인 강좌가 사라진다고 가정하고 시뮬레이션.
zero_course = pd.DataFrame([("PHYS500", "MATH", "Quantum Field Theory", 25)], columns=courses.columns)
df2 = pd.concat([df, zero_course.assign(validCount=0, allCount=0, rate_valid=0.0, rate_all=0.0)], ignore_index=True)
inner = df2[df2["validCount"] > 0]  # MATCH 동작
math_outer = df2[df2["departmentId"] == "MATH"]
math_inner = inner[inner["departmentId"] == "MATH"]
print("OPTIONAL MATCH(정확):", round(math_outer["validCount"].sum() / math_outer["maxEnrollment"].sum(), 4))
print("MATCH(0명 강좌 누락):", round(math_inner["validCount"].sum() / math_inner["maxEnrollment"].sum(), 4))
# 출력:
# OPTIONAL MATCH(정확): 0.56
# MATCH(0명 강좌 누락): 0.7467

# %% [markdown]
# ## 9. 시각화 — 두 방식의 학과별 충원율 비교

# %%
order = ["CS", "MATH", "ART"]
d = dept_valid.reindex(order)
d_all = dept_rates(df, "allCount").reindex(order)

fig = go.Figure()
fig.add_bar(
    name="단순 평균 macro (비율의 평균)",
    x=order,
    y=(d["macro"] * 100).round(1),
    text=[f"{v:.1f}%" for v in d["macro"] * 100],
    textposition="outside",
    marker_color="#4C78A8",
)
fig.add_bar(
    name="가중 평균 micro (총계/총정원)",
    x=order,
    y=(d["micro"] * 100).round(1),
    text=[f"{v:.1f}%" for v in d["micro"] * 100],
    textposition="outside",
    marker_color="#F58518",
)
fig.add_bar(
    name="micro, drop 미필터 (오답)",
    x=order,
    y=(d_all["micro"] * 100).round(1),
    text=[f"{v:.1f}%" for v in d_all["micro"] * 100],
    textposition="outside",
    marker_color="#BAB0AC",
)
fig.add_hline(y=100, line_dash="dot", line_color="crimson", annotation_text="정원 100%")
fig.update_layout(
    title="학과별 충원율: 계산 방식에 따라 1위가 바뀐다 (2025-Spring)<br>"
    "<sub>macro 1위=MATH(83.3%) vs micro 1위=CS(87.1%) — 순위 역전</sub>",
    yaxis_title="충원율 (%)",
    xaxis_title="Department",
    yaxis_range=[0, 118],
    barmode="group",
    template="plotly_white",
    legend=dict(orientation="h", yanchor="bottom", y=-0.28, x=0),
    width=900,
    height=560,
)
_show(fig)

# %%
import os

out_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(out_png, scale=2)
print("saved:", out_png)
# 출력: saved: .../expy.png

# %% [markdown]
# ## 정리
#
# | 항목 | 잘못된 계산 | 올바른 계산 |
# |---|---|---|
# | 집계 방식 | 정의 없이 강좌별 비율 평균 | 목적에 맞게 macro/micro를 **명시**. 기본은 micro |
# | status | 전체 Enrollment 카운트 | `status IN ['enrolled','completed']` |
# | semester | 전 학기 누적 | 대상 학기 고정 |
# | 0명 강좌 | `MATCH`로 누락 | `OPTIONAL MATCH`로 정원 유지 |
#
# - **micro(가중 평균)** = "학과 좌석 활용률". 자원 배분·예산 판단에 적합.
# - **macro(단순 평균)** = "평균적인 강좌가 얼마나 차는가". 폐강 후보 탐지에 적합.
