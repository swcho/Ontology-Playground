# 필요 패키지: plotly, pandas, kaleido  (pip install plotly pandas kaleido)
# 실행: python3 expy.py  또는 VSCode/Jupyter에서 셀 단위 실행

# %% [markdown]
# # `startDate` / `endDate`가 열어주는 historical questions
#
# Assignment는 `Employee` - `Department` - `Position`을 잇는 **junction entity**다.
# 거기에 `startDate` / `endDate`가 붙는 순간, 각 배치는 시간축 위의 **구간(validity interval)** 이 된다.
#
# $$ a = [\,a.\text{start},\; a.\text{end}\,] $$
#
# 이 한 가지 구조에서 세 종류의 질의가 도출된다.
#
# 1. **시점 질의 (as-of)** — 특정 날짜 $t$에 유효한 배치
# 2. **기간 겹침 질의 (period overlap)** — 기간 $[p_s, p_e]$와 겹치는 배치 → *"Who was in Finance during Q2?"*
# 3. **변화 감지 질의 (change detection)** — 같은 직원의 연속 배치에서 부서가 달라지는 지점 → *"Which employees changed departments this year?"*
#
# 아래에서 표준 라이브러리 `dataclass` / `date`만으로 작은 데이터셋을 만들고 세 질의를 직접 구현한다.

# %%
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# 재현성을 위해 "오늘"을 하드코딩한다.
# endDate=None(진행 중 배치)을 그림에 그릴 때의 오른쪽 끝으로도 쓴다.
TODAY = date(2025, 12, 31)

print("기준일(TODAY) =", TODAY)

# 출력: 기준일(TODAY) = 2025-12-31


# %% [markdown]
# ## 1. Assignment 데이터셋
#
# 4개 부서, 직원 5명. 일부러 다음 경우를 섞어 넣는다.
#
# - 부서 이동 (Alice, Carol, Eve)
# - 겸직 = 한 시점에 두 배치가 동시 유효, `isPrimary=False` (Dave)
# - 진행 중 배치 `endDate=None` (Bob, Carol, Dave, Eve)
# - Q2 **직전에 끝난** Finance 배치와 Q2 **한참 뒤에 시작한** Finance 배치 (겹침 조건식의 양쪽 경계 테스트)

# %%
@dataclass(frozen=True)
class Assignment:
    assignmentId: str
    employeeId: str
    employeeName: str
    departmentId: str
    positionId: str
    startDate: date
    endDate: date | None  # None = 아직 종료되지 않음 = 현재 진행 중
    isPrimary: bool


ASSIGNMENTS = [
    # Alice: Finance에서 일하다 Q2 중간(5/31)에 끝내고 Engineering으로 이동
    Assignment("A01", "E01", "Alice", "FIN", "P-ANALYST", date(2023, 2, 1), date(2025, 5, 31), True),
    Assignment("A02", "E01", "Alice", "ENG", "P-PM", date(2025, 6, 1), None, True),
    # Bob: 2020년부터 계속 Finance (진행 중)
    Assignment("A03", "E02", "Bob", "FIN", "P-MANAGER", date(2020, 3, 15), None, True),
    # Carol: Sales -> Finance, 이동 시점이 정확히 Q2 시작일
    Assignment("A04", "E03", "Carol", "SAL", "P-REP", date(2024, 1, 1), date(2025, 3, 31), True),
    Assignment("A05", "E03", "Carol", "FIN", "P-ANALYST", date(2025, 4, 1), None, True),
    # Dave: Engineering 주배치 + 하반기 Finance 겸직(isPrimary=False) -> 부서 "이동"이 아니다
    Assignment("A06", "E04", "Dave", "ENG", "P-STAFF", date(2022, 7, 1), None, True),
    Assignment("A07", "E04", "Dave", "FIN", "P-ADVISOR", date(2025, 9, 1), date(2025, 11, 30), False),
    # Eve: Marketing -> Finance -> Sales. Finance 구간은 Q2 시작 직전(3/31)에 끝난다
    Assignment("A08", "E05", "Eve", "MKT", "P-SPEC", date(2024, 5, 1), date(2025, 1, 31), True),
    Assignment("A09", "E05", "Eve", "FIN", "P-ANALYST", date(2025, 2, 1), date(2025, 3, 31), True),
    Assignment("A10", "E05", "Eve", "SAL", "P-REP", date(2025, 4, 1), None, True),
]

DEPT_NAME = {"FIN": "Finance", "ENG": "Engineering", "SAL": "Sales", "MKT": "Marketing"}

for a in ASSIGNMENTS:
    end = a.endDate.isoformat() if a.endDate else "(진행 중)"
    flag = "" if a.isPrimary else "  [겸직]"
    print(f"{a.assignmentId} {a.employeeName:<6} {DEPT_NAME[a.departmentId]:<12} {a.startDate} ~ {end}{flag}")

# 출력: A01 Alice  Finance      2023-02-01 ~ 2025-05-31
# 출력: A02 Alice  Engineering  2025-06-01 ~ (진행 중)
# 출력: A03 Bob    Finance      2020-03-15 ~ (진행 중)
# 출력: A04 Carol  Sales        2024-01-01 ~ 2025-03-31
# 출력: A05 Carol  Finance      2025-04-01 ~ (진행 중)
# 출력: A06 Dave   Engineering  2022-07-01 ~ (진행 중)
# 출력: A07 Dave   Finance      2025-09-01 ~ 2025-11-30  [겸직]
# 출력: A08 Eve    Marketing    2024-05-01 ~ 2025-01-31
# 출력: A09 Eve    Finance      2025-02-01 ~ 2025-03-31
# 출력: A10 Eve    Sales        2025-04-01 ~ (진행 중)


# %% [markdown]
# ## 2. 시점 질의 (as-of)
#
# 날짜 $t$를 포함하는 배치만 고른다. `endDate = NULL`은 "아직 안 끝났다"이므로 항상 통과시킨다.
#
# $$ a.\text{start} \le t \;\land\; (\,a.\text{end} = \text{NULL} \;\lor\; a.\text{end} \ge t\,) $$
#
# $t$를 과거로 놓으면 **그 시점의 조직 스냅샷**이 그대로 복원된다. 스냅샷을 따로 저장할 필요가 없다.

# %%
def is_active_on(a: Assignment, t: date) -> bool:
    """t 시점에 이 배치가 유효한가? (닫힌 구간 [start, end])"""
    return a.startDate <= t and (a.endDate is None or a.endDate >= t)


def as_of(t: date, primary_only: bool = True) -> list[Assignment]:
    return [a for a in ASSIGNMENTS if is_active_on(a, t) and (a.isPrimary or not primary_only)]


for t in (date(2025, 5, 15), date(2025, 10, 1), TODAY):
    rows = as_of(t, primary_only=False)
    desc = ", ".join(f"{a.employeeName}@{DEPT_NAME[a.departmentId]}" for a in rows)
    print(f"[as-of {t}] {desc}")

# 출력: [as-of 2025-05-15] Alice@Finance, Bob@Finance, Carol@Finance, Dave@Engineering, Eve@Sales
# 출력: [as-of 2025-10-01] Alice@Engineering, Bob@Finance, Carol@Finance, Dave@Engineering, Dave@Finance, Eve@Sales
# 출력: [as-of 2025-12-31] Alice@Engineering, Bob@Finance, Carol@Finance, Dave@Engineering, Eve@Sales


# %%
# 같은 함수로 "과거 시점의 부서별 인원수" = 조직 스냅샷을 만든다.
from collections import Counter

for t in (date(2025, 1, 15), date(2025, 5, 15), date(2025, 10, 1)):
    head = Counter(DEPT_NAME[a.departmentId] for a in as_of(t))
    print(f"[스냅샷 {t}] {dict(sorted(head.items()))}")

# 출력: [스냅샷 2025-01-15] {'Engineering': 1, 'Finance': 2, 'Marketing': 1, 'Sales': 1}
# 출력: [스냅샷 2025-05-15] {'Engineering': 1, 'Finance': 3, 'Sales': 1}
# 출력: [스냅샷 2025-10-01] {'Engineering': 2, 'Finance': 2, 'Sales': 1}


# %% [markdown]
# ## 3. 기간 겹침 질의 — "Who was in Finance during Q2?"
#
# Q2는 시점이 아니라 **기간** $[p_s, p_e]$ = `2025-04-01 ~ 2025-06-30`이다.
# 두 구간이 겹치지 **않는** 경우는 둘뿐이므로, 그 여집합에서 조건이 유도된다.
#
# $$
# \lnot(\,a.\text{end} < p_s \;\lor\; a.\text{start} > p_e\,)
# \;\equiv\;
# a.\text{start} \le p_e \;\land\; a.\text{end} \ge p_s
# $$
#
# `endDate = NULL` 처리를 더한 최종 형태:
#
# $$ a.\text{start} \le p_e \;\land\; (\,a.\text{end} = \text{NULL} \;\lor\; a.\text{end} \ge p_s\,) $$
#
# 외울 짝: **시작은 기간 끝과, 끝은 기간 시작과** 비교한다(교차 비교).

# %%
Q2_START, Q2_END = date(2025, 4, 1), date(2025, 6, 30)


def overlaps(a: Assignment, p_start: date, p_end: date) -> bool:
    """배치 구간이 기간 [p_start, p_end]와 하루라도 겹치는가?"""
    return a.startDate <= p_end and (a.endDate is None or a.endDate >= p_start)


print(f"기간 = {Q2_START} ~ {Q2_END} (Q2 2025)\n")
print("Finance 배치별 겹침 판정:")
for a in ASSIGNMENTS:
    if a.departmentId != "FIN":
        continue
    hit = overlaps(a, Q2_START, Q2_END)
    end = a.endDate.isoformat() if a.endDate else "NULL"
    reason = "겹침" if hit else ("Q2 이후 시작" if a.startDate > Q2_END else "Q2 이전 종료")
    print(f"  {a.assignmentId} {a.employeeName:<6} start={a.startDate} end={end:<12} -> {hit!s:<5} ({reason})")

answer = sorted({a.employeeName for a in ASSIGNMENTS if a.departmentId == "FIN" and overlaps(a, Q2_START, Q2_END)})
print(f"\nQ. Who was in Finance during Q2?\nA. {answer}")

# 출력: 기간 = 2025-04-01 ~ 2025-06-30 (Q2 2025)
# 출력:
# 출력: Finance 배치별 겹침 판정:
# 출력:   A01 Alice  start=2023-02-01 end=2025-05-31   -> True  (겹침)
# 출력:   A03 Bob    start=2020-03-15 end=NULL         -> True  (겹침)
# 출력:   A05 Carol  start=2025-04-01 end=NULL         -> True  (겹침)
# 출력:   A07 Dave   start=2025-09-01 end=2025-11-30   -> False (Q2 이후 시작)
# 출력:   A09 Eve    start=2025-02-01 end=2025-03-31   -> False (Q2 이전 종료)
# 출력:
# 출력: Q. Who was in Finance during Q2?
# 출력: A. ['Alice', 'Bob', 'Carol']


# %% [markdown]
# ### 흔한 실수 — 같은 쪽끼리 비교하기
#
# `start >= p_s AND end <= p_e`로 쓰면 그것은 겹침이 아니라 **포함(containment)** 질의이고,
# 게다가 `endDate = NULL`을 통과시키지 못한다. 결과가 조용히 비어버린다.

# %%
def wrong_overlap(a: Assignment, p_start: date, p_end: date) -> bool:
    # 잘못된 조건: 같은 쪽끼리 비교 + NULL 미처리
    return a.startDate >= p_start and a.endDate is not None and a.endDate <= p_end


def contains_period(a: Assignment, p_start: date, p_end: date) -> bool:
    """기간 전체를 이 배치가 덮는가? (엄격한 'during' 해석)"""
    return a.startDate <= p_start and (a.endDate is None or a.endDate >= p_end)


fin = [a for a in ASSIGNMENTS if a.departmentId == "FIN"]
print("겹침(overlap)   :", sorted({a.employeeName for a in fin if overlaps(a, Q2_START, Q2_END)}))
print("포함(containment):", sorted({a.employeeName for a in fin if contains_period(a, Q2_START, Q2_END)}))
print("잘못된 조건식    :", sorted({a.employeeName for a in fin if wrong_overlap(a, Q2_START, Q2_END)}))

# 출력: 겹침(overlap)   : ['Alice', 'Bob', 'Carol']
# 출력: 포함(containment): ['Bob', 'Carol']
# 출력: 잘못된 조건식    : []


# %% [markdown]
# ### 반열린 구간 $[\text{start}, \text{end})$
#
# 닫힌 구간을 쓰면 `prev.end == next.start`인 데이터에서 그 하루가 **양쪽에 이중 계상**된다.
# 반열린 구간을 쓰면 경계 중복이 구조적으로 사라진다.
#
# $$ [\,\text{start},\, \text{end}\,) = \{\, t \mid \text{start} \le t < \text{end} \,\} $$

# %%
# 경계에서 맞물리는 두 배치 (같은 날 종료/시작)
b1 = Assignment("X1", "E09", "Frank", "FIN", "P-A", date(2025, 1, 1), date(2025, 4, 1), True)
b2 = Assignment("X2", "E09", "Frank", "ENG", "P-B", date(2025, 4, 1), None, True)
boundary = date(2025, 4, 1)


def is_active_on_half_open(a: Assignment, t: date) -> bool:
    return a.startDate <= t and (a.endDate is None or a.endDate > t)  # > 로 바뀐다


closed = [a.assignmentId for a in (b1, b2) if is_active_on(a, boundary)]
half = [a.assignmentId for a in (b1, b2) if is_active_on_half_open(a, boundary)]
print(f"{boundary} 시점 유효 배치 — 닫힌 구간 [s,e] : {closed}  <- 하루 이중 계상")
print(f"{boundary} 시점 유효 배치 — 반열린   [s,e) : {half}  <- 정확히 하나")

# 출력: 2025-04-01 시점 유효 배치 — 닫힌 구간 [s,e] : ['X1', 'X2']  <- 하루 이중 계상
# 출력: 2025-04-01 시점 유효 배치 — 반열린   [s,e) : ['X2']  <- 정확히 하나


# %% [markdown]
# ## 4. 변화 감지 질의 — "Which employees changed departments this year?"
#
# 이건 한 레코드만 봐서는 답할 수 없다. **같은 직원의 배치를 `startDate` 순으로 줄 세워 이웃끼리 비교**한다.
#
# $$ \exists\, i:\; a_i.\text{dept} \ne a_{i+1}.\text{dept} \;\land\; a_{i+1}.\text{start} \in \text{올해} $$
#
# SQL이라면 `LAG(department_id) OVER (PARTITION BY employee_id ORDER BY start_date)`.
# `isPrimary=True`로 걸러야 **겸직 추가**가 **부서 이동**으로 오인되지 않는다.

# %%
def department_changes(year: int, primary_only: bool = True) -> list[tuple[str, date, str, str]]:
    """(직원명, 전환일, 이전부서, 새부서) 목록"""
    rows = [a for a in ASSIGNMENTS if a.isPrimary or not primary_only]
    by_emp: dict[str, list[Assignment]] = {}
    for a in rows:
        by_emp.setdefault(a.employeeId, []).append(a)

    out = []
    for emp in sorted(by_emp):
        seq = sorted(by_emp[emp], key=lambda a: a.startDate)  # 시간순 정렬이 전부다
        for prev, cur in zip(seq, seq[1:]):  # 연속한 이웃 쌍 비교
            if prev.departmentId != cur.departmentId and cur.startDate.year == year:
                out.append((cur.employeeName, cur.startDate, DEPT_NAME[prev.departmentId], DEPT_NAME[cur.departmentId]))
    return sorted(out, key=lambda r: r[1])


print("Q. Which employees changed departments this year? (2025, 주배치만)")
for name, when, frm, to in department_changes(2025):
    print(f"  {when}  {name:<6} {frm} -> {to}")
print("  =>", sorted({r[0] for r in department_changes(2025)}))

# 출력: Q. Which employees changed departments this year? (2025, 주배치만)
# 출력:   2025-02-01  Eve    Marketing -> Finance
# 출력:   2025-04-01  Carol  Sales -> Finance
# 출력:   2025-04-01  Eve    Finance -> Sales
# 출력:   2025-06-01  Alice  Finance -> Engineering
# 출력:   => ['Alice', 'Carol', 'Eve']


# %%
# isPrimary를 무시하면 Dave의 "겸직"이 가짜 부서 이동으로 잡힌다.
print("주배치만        :", sorted({r[0] for r in department_changes(2025, primary_only=True)}))
print("겸직 포함(오답) :", sorted({r[0] for r in department_changes(2025, primary_only=False)}))
print()
for name, when, frm, to in department_changes(2025, primary_only=False):
    if name == "Dave":
        print(f"  가짜 이동: {when} Dave {frm} -> {to}  (실제로는 ENG 유지 + FIN 겸직)")

# 출력: 주배치만        : ['Alice', 'Carol', 'Eve']
# 출력: 겸직 포함(오답) : ['Alice', 'Carol', 'Dave', 'Eve']
# 출력:
# 출력:   가짜 이동: 2025-09-01 Dave Engineering -> Finance  (실제로는 ENG 유지 + FIN 겸직)


# %% [markdown]
# ## 5. 파생 지표 — 재직 기간
#
# 진행 중 배치는 `endDate`를 기준일로 치환해 계산한다: $\text{COALESCE}(\text{end},\, \text{today}) - \text{start}$

# %%
def duration_days(a: Assignment, today: date = TODAY) -> int:
    return ((a.endDate or today) - a.startDate).days


tenure: dict[str, int] = {}
for a in ASSIGNMENTS:
    if a.isPrimary:
        tenure[a.employeeName] = tenure.get(a.employeeName, 0) + duration_days(a)

for name, days in sorted(tenure.items(), key=lambda kv: -kv[1]):
    print(f"  {name:<6} 누적 주배치 기간 {days:>5}일 ({days / 365.25:.1f}년)")

# 출력:   Bob    누적 주배치 기간  2117일 (5.8년)
# 출력:   Dave   누적 주배치 기간  1279일 (3.5년)
# 출력:   Alice  누적 주배치 기간  1063일 (2.9년)
# 출력:   Carol  누적 주배치 기간   729일 (2.0년)
# 출력:   Eve    누적 주배치 기간   607일 (1.7년)


# %% [markdown]
# ## 6. 시각화 — 배치 타임라인과 Q2 구간
#
# 각 Assignment를 시간축의 막대(구간)로 그린다. `endDate=None`인 배치는 기준일(2025-12-31)까지 늘려 그린다.
# 노란 띠가 Q2, 빨간 점선이 as-of 기준일이다. **Q2 띠를 지나가는 파란(Finance) 막대**가 곧 첫 질문의 답이다.
#
# 겸직(`isPrimary=False`)은 주배치와 같은 기간에 동시 유효하므로 같은 줄에 그리면 가려진다.
# 별도 레인(`Dave (겸직)`)으로 분리하고 사선 패턴을 준다.

# %%
import pandas as pd
import plotly.express as px

DEPT_COLOR = {"Finance": "#2563eb", "Engineering": "#16a34a", "Sales": "#f59e0b", "Marketing": "#a855f7"}
# 아래 -> 위 순서. 겸직은 주배치 바로 아래 별도 레인.
LANE_ORDER = ["Eve", "Dave (겸직)", "Dave", "Carol", "Bob", "Alice"]

records = []
for a in ASSIGNMENTS:
    ongoing = a.endDate is None
    records.append(
        {
            "레인": a.employeeName if a.isPrimary else f"{a.employeeName} (겸직)",
            "직원": a.employeeName,
            "부서": DEPT_NAME[a.departmentId],
            "시작": pd.Timestamp(a.startDate),
            "종료": pd.Timestamp(a.endDate or TODAY),
            "구분": "주배치" if a.isPrimary else "겸직",
            "표시종료": "진행 중 (endDate=NULL)" if ongoing else a.endDate.isoformat(),
            "ID": a.assignmentId,
        }
    )
df = pd.DataFrame(records)

fig = px.timeline(
    df,
    x_start="시작",
    x_end="종료",
    y="레인",
    color="부서",
    pattern_shape="구분",
    pattern_shape_map={"주배치": "", "겸직": "/"},
    color_discrete_map=DEPT_COLOR,
    category_orders={"레인": LANE_ORDER, "부서": list(DEPT_COLOR)},
    hover_data={"ID": True, "표시종료": True},
    title="Assignment 유효 구간과 Q2 겹침 — 'Who was in Finance during Q2?'",
)

# Q2 구간 하이라이트
fig.add_vrect(
    x0=Q2_START.isoformat(),
    x1=Q2_END.isoformat(),
    fillcolor="#fbbf24",
    opacity=0.22,
    line_width=0,
    layer="below",
    annotation_text="Q2 2025",
    annotation_position="top left",
)
# as-of 기준선
fig.add_vline(
    x=date(2025, 5, 15).isoformat(),
    line_dash="dot",
    line_color="#dc2626",
    annotation_text="as-of 5/15",
    annotation_position="top right",
)

fig.update_traces(marker_line_color="#1f2937", marker_line_width=1)
fig.update_yaxes(title=None)
fig.update_xaxes(
    title="시간 (진행 중 배치는 기준일 2025-12-31까지 표시)",
    range=["2020-01-01", "2026-06-01"],
    dtick="M12",
    tickformat="%Y",
)
fig.update_layout(
    height=520,
    width=1150,
    template="plotly_white",
    bargap=0.3,
    legend_title_text="",
    legend_orientation="h",
    legend_y=-0.16,
    margin=dict(l=110, r=40, t=70, b=95),
)

# Q2와 겹치는 Finance 배치에 "✔" 배지 — 이게 곧 질문의 답
for a in ASSIGNMENTS:
    if a.departmentId == "FIN" and overlaps(a, Q2_START, Q2_END):
        fig.add_annotation(
            x=Q2_END.isoformat(),
            y=a.employeeName,
            text=f"✔ {a.employeeName}",
            showarrow=False,
            xanchor="left",
            xshift=8,
            font=dict(color="white", size=11),
            bgcolor="rgba(37,99,235,0.9)",
            borderpad=3,
        )
# 겹치지 않는 Finance 배치에는 이유 표시
for a in ASSIGNMENTS:
    if a.departmentId == "FIN" and not overlaps(a, Q2_START, Q2_END):
        fig.add_annotation(
            x=(a.endDate or TODAY).isoformat() if a.startDate < Q2_START else a.startDate.isoformat(),
            y=a.employeeName if a.isPrimary else f"{a.employeeName} (겸직)",
            text="✗ Q2 이전 종료" if a.startDate < Q2_START else "✗ Q2 이후 시작",
            showarrow=True,
            arrowhead=2,
            arrowsize=0.8,
            ax=0,
            ay=-28,
            font=dict(color="#b91c1c", size=10),
            bgcolor="rgba(255,255,255,0.85)",
            borderpad=2,
        )

fig.write_image("expy.png", scale=2)
_show(fig)
print("saved expy.png")

# 출력: saved expy.png
