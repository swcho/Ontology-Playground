# %% [markdown]
# # `Department <- Assignment <- Employee -> PerformanceReview` 를 직접 걸어보기
#
# 필요 패키지: plotly, kaleido (마지막 시각화 셀에서만 사용)
#
# 질문: **"Which teams have many outstanding reviews?"**
#
# 아티클이 제시한 경로:
#
# ```
# Department <- Assignment <- Employee -> PerformanceReview   (rating=outstanding)
# ```
#
# 이 노트북은
#
# 1. 표준 라이브러리만으로 작은 HR 그래프를 만들고 (이동·겸직·진행중 배치 포함),
# 2. 인접 딕셔너리로 위 경로를 **그대로** 순회하고,
# 3. 시점 정합을 무시한 집계와 리뷰 시점 배치 기준 집계를 나란히 비교하고,
# 4. 부서 규모로 정규화한 outstanding 비율까지 계산한다.
#
# 날짜는 전부 하드코딩이라 몇 번 돌려도 같은 결과가 나온다.

# %%
# 필요 패키지: plotly, kaleido
from __future__ import annotations   # Python 3.9 에서도 date | None 표기를 쓰기 위해

import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from enum import Enum

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# 오늘 날짜를 재현 가능하게 고정한다 (date.today() 를 쓰지 않는다)
AS_OF = date(2025, 9, 1)
print("as-of:", AS_OF)
# 출력: as-of: 2025-09-01

# %% [markdown]
# ## 1. 엔티티 정의 — 아티클의 5개 엔티티
#
# | 엔티티 | 식별자 | 이 노트북에서 쓰는 속성 |
# |---|---|---|
# | Employee | `employeeId` | `name`, `hireDate`, `jobLevel` |
# | Department | `departmentId` | `name` |
# | Position | `positionId` | `title`, `level` |
# | Assignment | `assignmentId` | `employeeId`, `departmentId`, `positionId`, `startDate`, `endDate`, `isPrimary` |
# | PerformanceReview | `reviewId` | `employeeId`, `reviewPeriod`, `rating`, `reviewDate` |
#
# Assignment 는 junction entity 라서 **외래 참조 3개 + 자기 속성**을 함께 들고 있다.
# PerformanceReview 는 Employee 만 참조한다 — **부서를 직접 모른다.** 이 사실이 경로 길이의 원인이다.

# %%
class Rating(str, Enum):
    OUTSTANDING = "outstanding"
    EXCEEDS = "exceeds"
    MEETS = "meets"
    NEEDS_IMPROVEMENT = "needs_improvement"


class JobLevel(str, Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"


@dataclass(frozen=True)
class Department:
    departmentId: str
    name: str


@dataclass(frozen=True)
class Position:
    positionId: str
    title: str
    level: JobLevel


@dataclass(frozen=True)
class Employee:
    employeeId: str
    name: str
    hireDate: date
    jobLevel: JobLevel


@dataclass(frozen=True)
class Assignment:
    assignmentId: str
    employeeId: str
    departmentId: str
    positionId: str
    startDate: date
    endDate: date | None          # None = 진행중
    isPrimary: bool


@dataclass(frozen=True)
class PerformanceReview:
    reviewId: str
    employeeId: str
    reviewPeriod: str
    rating: Rating
    reviewDate: date


print("entities defined")
# 출력: entities defined

# %% [markdown]
# ## 2. 데이터 — 함정을 일부러 심어 둔다
#
# * **E005 정민재**: 2024년 내내 Finance, 2025-01-01 에 Engineering 으로 **이동**
# * **E006 강수아**: 2024-07-01 에 Finance → Marketing 으로 **이동**
# * **E007 윤채원**: Data Platform 주배치 + Engineering **겸직**(`isPrimary=False`)
# * 진행중 배치는 `endDate=None`

# %%
DEPARTMENTS = [
    Department("D-ENG", "Engineering"),
    Department("D-FIN", "Finance"),
    Department("D-MKT", "Marketing"),
    Department("D-DATA", "Data Platform"),
]

POSITIONS = [
    Position("P-SWE2", "Software Engineer II", JobLevel.MID),
    Position("P-SWE3", "Senior Software Engineer", JobLevel.SENIOR),
    Position("P-FA", "Financial Analyst", JobLevel.MID),
    Position("P-FM", "Finance Manager", JobLevel.SENIOR),
    Position("P-MKTS", "Marketing Specialist", JobLevel.JUNIOR),
    Position("P-DE", "Data Engineer", JobLevel.SENIOR),
]

EMPLOYEES = [
    Employee("E001", "김서준", date(2019, 3, 4), JobLevel.SENIOR),
    Employee("E002", "이하은", date(2020, 7, 1), JobLevel.MID),
    Employee("E003", "박도윤", date(2018, 1, 15), JobLevel.SENIOR),
    Employee("E004", "최지우", date(2022, 9, 1), JobLevel.JUNIOR),
    Employee("E005", "정민재", date(2019, 11, 11), JobLevel.SENIOR),
    Employee("E006", "강수아", date(2021, 4, 19), JobLevel.MID),
    Employee("E007", "윤채원", date(2020, 2, 3), JobLevel.SENIOR),
    Employee("E008", "임지호", date(2023, 6, 1), JobLevel.MID),
    Employee("E009", "한소율", date(2024, 2, 19), JobLevel.JUNIOR),
    Employee("E010", "오지훈", date(2022, 1, 10), JobLevel.MID),
]

ASSIGNMENTS = [
    Assignment("A01", "E001", "D-ENG", "P-SWE3", date(2019, 3, 4), None, True),
    Assignment("A02", "E002", "D-ENG", "P-SWE2", date(2020, 7, 1), None, True),
    Assignment("A03", "E003", "D-FIN", "P-FM", date(2018, 1, 15), None, True),
    Assignment("A04", "E004", "D-MKT", "P-MKTS", date(2022, 9, 1), None, True),
    # E005: Finance -> Engineering 이동
    Assignment("A05", "E005", "D-FIN", "P-FA", date(2019, 11, 11), date(2024, 12, 31), True),
    Assignment("A06", "E005", "D-ENG", "P-SWE3", date(2025, 1, 1), None, True),
    # E006: Finance -> Marketing 이동
    Assignment("A07", "E006", "D-FIN", "P-FA", date(2021, 4, 19), date(2024, 6, 30), True),
    Assignment("A08", "E006", "D-MKT", "P-MKTS", date(2024, 7, 1), None, True),
    # E007: Data Platform 주배치 + Engineering 겸직
    Assignment("A09", "E007", "D-DATA", "P-DE", date(2020, 2, 3), None, True),
    Assignment("A10", "E007", "D-ENG", "P-SWE3", date(2024, 7, 1), None, False),
    Assignment("A11", "E008", "D-MKT", "P-MKTS", date(2023, 6, 1), None, True),
    Assignment("A12", "E009", "D-ENG", "P-SWE2", date(2024, 2, 19), None, True),
    Assignment("A13", "E010", "D-FIN", "P-FA", date(2022, 1, 10), None, True),
]

# reviewPeriod 문자열 -> 실제 평가 대상 구간 (경계 포함)
PERIOD_WINDOW = {
    "2024-H1": (date(2024, 1, 1), date(2024, 6, 30)),
    "2024-H2": (date(2024, 7, 1), date(2024, 12, 31)),
    "2025-H1": (date(2025, 1, 1), date(2025, 6, 30)),
}
# 리뷰 문서가 실제로 작성/확정된 날 — 평가 구간보다 늘 뒤에 있다
PERIOD_REVIEW_DATE = {
    "2024-H1": date(2024, 7, 15),
    "2024-H2": date(2025, 1, 20),
    "2025-H1": date(2025, 7, 14),
}

_raw_reviews = [
    ("E001", "2024-H1", Rating.EXCEEDS),
    ("E001", "2024-H2", Rating.OUTSTANDING),
    ("E001", "2025-H1", Rating.OUTSTANDING),
    ("E002", "2024-H1", Rating.MEETS),
    ("E002", "2024-H2", Rating.MEETS),
    ("E002", "2025-H1", Rating.EXCEEDS),
    ("E003", "2024-H1", Rating.OUTSTANDING),
    ("E003", "2024-H2", Rating.EXCEEDS),
    ("E003", "2025-H1", Rating.MEETS),
    ("E004", "2024-H1", Rating.MEETS),
    ("E004", "2024-H2", Rating.NEEDS_IMPROVEMENT),
    ("E004", "2025-H1", Rating.MEETS),
    ("E005", "2024-H1", Rating.OUTSTANDING),
    ("E005", "2024-H2", Rating.OUTSTANDING),
    ("E005", "2025-H1", Rating.EXCEEDS),
    ("E006", "2024-H1", Rating.OUTSTANDING),
    ("E006", "2024-H2", Rating.MEETS),
    ("E006", "2025-H1", Rating.OUTSTANDING),
    ("E007", "2024-H1", Rating.EXCEEDS),
    ("E007", "2024-H2", Rating.OUTSTANDING),
    ("E007", "2025-H1", Rating.OUTSTANDING),
    ("E008", "2024-H1", Rating.MEETS),
    ("E008", "2024-H2", Rating.EXCEEDS),
    ("E008", "2025-H1", Rating.MEETS),
    ("E009", "2024-H2", Rating.MEETS),          # 2024-02 입사 -> 2024-H1 리뷰 없음
    ("E009", "2025-H1", Rating.OUTSTANDING),
    ("E010", "2024-H1", Rating.MEETS),
    ("E010", "2024-H2", Rating.MEETS),
    ("E010", "2025-H1", Rating.EXCEEDS),
]
REVIEWS = [
    PerformanceReview(f"R{i:03d}", emp, period, rating, PERIOD_REVIEW_DATE[period])
    for i, (emp, period, rating) in enumerate(_raw_reviews, start=1)
]

print(f"부서 {len(DEPARTMENTS)} / 직위 {len(POSITIONS)} / 직원 {len(EMPLOYEES)}"
      f" / 배치 {len(ASSIGNMENTS)} / 리뷰 {len(REVIEWS)}")
print("outstanding 리뷰 수:", sum(r.rating is Rating.OUTSTANDING for r in REVIEWS))
# 출력: 부서 4 / 직위 6 / 직원 10 / 배치 13 / 리뷰 29
# 출력: outstanding 리뷰 수: 10

# %% [markdown]
# ## 3. 인접 딕셔너리 — 화살표 방향 vs 순회 방향
#
# 스키마상 관계 방향은 아티클대로 이렇다.
#
# $$\text{Employee} \rightarrow \text{Assignment},\quad
#   \text{Assignment} \rightarrow \text{Department},\quad
#   \text{Employee} \rightarrow \text{PerformanceReview}$$
#
# 즉 **외래키를 들고 있는 쪽이 화살표의 출발점**이다. Assignment 행에 `employeeId`,
# `departmentId` 가 들어 있고, PerformanceReview 행에 `employeeId` 가 들어 있다.
#
# 그런데 질문은 `rating=outstanding` 이라는 **PerformanceReview 쪽 필터**로 시작한다.
# 그래서 실제 순회는 화살표를 **거슬러** 올라간다. 아티클 표기 `Department <- Assignment <- Employee`
# 의 `<-` 는 "스키마 화살표가 반대"라는 표시이고, 질의는 이걸 역방향 인덱스로 탄다.
# 따라서 인접 딕셔너리를 **양방향 모두** 만들어 둔다.

# %%
DEPT = {d.departmentId: d for d in DEPARTMENTS}
POS = {p.positionId: p for p in POSITIONS}
EMP = {e.employeeId: e for e in EMPLOYEES}
ASG = {a.assignmentId: a for a in ASSIGNMENTS}
REV = {r.reviewId: r for r in REVIEWS}

# 정방향 (스키마 화살표 방향)
emp_to_assignments: dict[str, list[str]] = defaultdict(list)   # Employee -> Assignment
emp_to_reviews: dict[str, list[str]] = defaultdict(list)       # Employee -> PerformanceReview
assignment_to_dept: dict[str, str] = {}                        # Assignment -> Department
assignment_to_pos: dict[str, str] = {}                         # Assignment -> Position

# 역방향 (질의가 실제로 타는 방향)
review_to_emp: dict[str, str] = {}                             # PerformanceReview <- Employee
assignment_to_emp: dict[str, str] = {}                         # Assignment <- Employee
dept_to_assignments: dict[str, list[str]] = defaultdict(list)  # Department <- Assignment

for a in ASSIGNMENTS:
    emp_to_assignments[a.employeeId].append(a.assignmentId)
    assignment_to_dept[a.assignmentId] = a.departmentId
    assignment_to_pos[a.assignmentId] = a.positionId
    assignment_to_emp[a.assignmentId] = a.employeeId
    dept_to_assignments[a.departmentId].append(a.assignmentId)

for r in REVIEWS:
    emp_to_reviews[r.employeeId].append(r.reviewId)
    review_to_emp[r.reviewId] = r.employeeId

print("E005 의 배치:", emp_to_assignments["E005"])
print("E005 의 리뷰:", emp_to_reviews["E005"])
print("E007 의 배치:", emp_to_assignments["E007"], "<- 겸직으로 2건")
print("D-ENG 로 들어오는 배치:", dept_to_assignments["D-ENG"])
# 출력: E005 의 배치: ['A05', 'A06']
# 출력: E005 의 리뷰: ['R013', 'R014', 'R015']
# 출력: E007 의 배치: ['A09', 'A10'] <- 겸직으로 2건
# 출력: D-ENG 로 들어오는 배치: ['A01', 'A02', 'A06', 'A10', 'A12']

# %% [markdown]
# ## 4. 경로를 그대로 걷는 순회 함수 — V자 구조
#
# Employee 는 두 갈래가 **만나는 유일한 교차점**이다.
#
# ```
#                 Employee                   <- 교차점 (pivot)
#                 /      \
#      Assignment          PerformanceReview  <- 두 갈래
#          |                     |
#      Department          rating=outstanding
# ```
#
# 경로 문자열 `Department <- Assignment <- Employee -> PerformanceReview` 는
# 선형처럼 보이지만 실제 모양은 **V**(또는 뒤집힌 V)다. 화살표가 Employee 에서
# 양쪽으로 나가고, 그 둘 사이에는 직접 관계가 없다. 부서와 평가를 잇는 유일한 접착제가
# Employee 라서, 이 노드를 반드시 통과해야 한다.
#
# 아래 `walk_path` 는 필터된 리뷰에서 출발해 pivot 을 거쳐 부서까지 4스텝을 밟고,
# 밟은 노드를 전부 기록한다.

# %%
def walk_path(rating: Rating = Rating.OUTSTANDING, assignment_filter=None):
    """PerformanceReview(rating) -> Employee -> Assignment -> Department 로 4스텝 순회.

    assignment_filter(assignment, review) -> bool 로 어떤 배치를 인정할지 갈아끼운다.
    반환: (review, employee, assignment, department) 튜플 리스트 = 경로 흔적(trail).
    """
    trails = []
    # 스텝 1: PerformanceReview 에서 rating 필터 (경로의 오른쪽 끝)
    for r in REVIEWS:
        if r.rating is not rating:
            continue
        # 스텝 2: 리뷰 -> Employee 로 되짚기 (화살표 역방향)
        e = EMP[review_to_emp[r.reviewId]]
        # 스텝 3: Employee -> Assignment (화살표 정방향, 1:N 이라 팬아웃)
        for aid in emp_to_assignments[e.employeeId]:
            a = ASG[aid]
            if assignment_filter is not None and not assignment_filter(a, r):
                continue
            # 스텝 4: Assignment -> Department
            d = DEPT[assignment_to_dept[a.assignmentId]]
            trails.append((r, e, a, d))
    return trails


def fmt(trail):
    r, e, a, d = trail
    end = a.endDate.isoformat() if a.endDate else "진행중"
    tag = "primary" if a.isPrimary else "겸직"
    return (f"{d.name:<14} <- {a.assignmentId}({a.startDate}~{end},{tag}) <- "
            f"{e.name}({e.employeeId}) -> {r.reviewId}[{r.reviewPeriod},{r.rating.value}]")


raw = walk_path()                              # 아무 필터 없이 경로만 따라간다
print("경로 흔적 개수:", len(raw), "(outstanding 리뷰는 10건인데?)")
print()
for t in raw:
    if t[1].employeeId in ("E005", "E007"):
        print(fmt(t))
# 출력: 경로 흔적 개수: 16 (outstanding 리뷰는 10건인데?)
# 출력:
# 출력: Finance        <- A05(2019-11-11~2024-12-31,primary) <- 정민재(E005) -> R013[2024-H1,outstanding]
# 출력: Engineering    <- A06(2025-01-01~진행중,primary) <- 정민재(E005) -> R013[2024-H1,outstanding]
# 출력: Finance        <- A05(2019-11-11~2024-12-31,primary) <- 정민재(E005) -> R014[2024-H2,outstanding]
# 출력: Engineering    <- A06(2025-01-01~진행중,primary) <- 정민재(E005) -> R014[2024-H2,outstanding]
# 출력: Data Platform  <- A09(2020-02-03~진행중,primary) <- 윤채원(E007) -> R020[2024-H2,outstanding]
# 출력: Engineering    <- A10(2024-07-01~진행중,겸직) <- 윤채원(E007) -> R020[2024-H2,outstanding]
# 출력: Data Platform  <- A09(2020-02-03~진행중,primary) <- 윤채원(E007) -> R021[2025-H1,outstanding]
# 출력: Engineering    <- A10(2024-07-01~진행중,겸직) <- 윤채원(E007) -> R021[2025-H1,outstanding]

# %% [markdown]
# 리뷰는 10건인데 흔적은 16개다. **Employee -> Assignment 가 1:N** 이라
# 스텝 3에서 팬아웃이 일어나고, 같은 리뷰 1건이 여러 부서로 복제된다.
#
# $$|\text{trail}| = \sum_{r \in R_{\text{outstanding}}} \bigl|\text{assignments}(\text{emp}(r))\bigr|$$
#
# 원인은 두 가지다.
#
# * **이동**: E005 의 2024년 리뷰가 옛 부서(Finance)와 새 부서(Engineering)에 **둘 다** 붙는다.
# * **겸직**: E007 의 리뷰가 주배치(Data Platform)와 겸직(Engineering)에 **둘 다** 붙는다.
#
# 경로를 문자 그대로만 따라가면 이렇게 된다. 필터가 필요하다.

# %% [markdown]
# ## 5. 집계 세 가지 — 어느 시점의 배치를 쓸 것인가
#
# | 방식 | 필터 | 의미 |
# |---|---|---|
# | (a) 필터 없음 | 없음 | 경로를 문자 그대로 순회. 중복 계상 |
# | (b) 현재 주배치 | `isPrimary=True and endDate is None` | "지금 이 팀에 있는 사람들의 과거 성적" |
# | (c) 리뷰 기간 정합 | Assignment 구간이 `reviewPeriod` 구간과 겹치고 primary | "그 성과가 실제로 난 팀" |
# | (d) reviewDate 정합 | `startDate <= reviewDate <= endDate` | 흔한 실수 — 리뷰 확정일은 평가 구간보다 뒤다 |

# %%
def overlap_days(a: Assignment, start: date, end: date) -> int:
    a_end = a.endDate or date(9999, 12, 31)
    lo, hi = max(a.startDate, start), min(a_end, end)
    return (hi - lo).days + 1 if lo <= hi else 0


def f_none(a, r):
    return True


def f_current_primary(a, r):
    return a.isPrimary and (a.endDate is None or a.endDate >= AS_OF)


def f_period_primary(a, r):
    start, end = PERIOD_WINDOW[r.reviewPeriod]
    return a.isPrimary and overlap_days(a, start, end) > 0


def f_review_date(a, r):
    return a.isPrimary and a.startDate <= r.reviewDate and (a.endDate is None or a.endDate >= r.reviewDate)


def aggregate(assignment_filter, dedupe_best_overlap=False):
    """부서별 outstanding 리뷰 수. dedupe_best_overlap=True 면 리뷰 1건당 배치 1개만 인정."""
    trails = walk_path(Rating.OUTSTANDING, assignment_filter)
    if dedupe_best_overlap:
        best: dict[str, tuple] = {}
        for t in trails:
            r, e, a, d = t
            start, end = PERIOD_WINDOW[r.reviewPeriod]
            score = overlap_days(a, start, end)
            if r.reviewId not in best or score > best[r.reviewId][0]:
                best[r.reviewId] = (score, t)
        trails = [t for _, t in best.values()]
    counts = {d.departmentId: 0 for d in DEPARTMENTS}
    for _, _, _, d in trails:
        counts[d.departmentId] += 1
    return counts, trails


agg_none, tr_none = aggregate(f_none)
agg_cur, tr_cur = aggregate(f_current_primary)
agg_period, tr_period = aggregate(f_period_primary, dedupe_best_overlap=True)
agg_rdate, tr_rdate = aggregate(f_review_date)

hdr = f"{'부서':<16}{'(a)필터없음':>12}{'(b)현재주배치':>14}{'(c)기간정합':>12}{'(d)reviewDate':>14}"
print(hdr)
for d in DEPARTMENTS:
    print(f"{d.name:<16}{agg_none[d.departmentId]:>12}{agg_cur[d.departmentId]:>14}"
          f"{agg_period[d.departmentId]:>12}{agg_rdate[d.departmentId]:>14}")
print(f"{'합계':<16}{sum(agg_none.values()):>12}{sum(agg_cur.values()):>14}"
      f"{sum(agg_period.values()):>12}{sum(agg_rdate.values()):>14}  (정답 총합 10)")
# 출력: 부서                   (a)필터없음      (b)현재주배치     (c)기간정합 (d)reviewDate
# 출력: Engineering                7             5           3             4
# 출력: Finance                    5             1           4             2
# 출력: Marketing                  2             2           1             2
# 출력: Data Platform              2             2           2             2
# 출력: 합계                        16            10          10            10  (정답 총합 10)

# %% [markdown]
# ## 6. 어느 직원 때문에 답이 갈리는가
#
# (b)현재 주배치와 (c)기간 정합의 차이를 리뷰 단위로 뽑아 범인을 지목한다.

# %%
by_rev_cur = {t[0].reviewId: t for t in tr_cur}
by_rev_period = {t[0].reviewId: t for t in tr_period}

print("리뷰ID  직원        기간      (b)현재주배치 부서 -> (c)기간정합 부서")
for rid in sorted(set(by_rev_cur) | set(by_rev_period)):
    dc = by_rev_cur[rid][3].name if rid in by_rev_cur else "(없음)"
    dp = by_rev_period[rid][3].name if rid in by_rev_period else "(없음)"
    if dc != dp:
        e = EMP[REV[rid].employeeId]
        print(f"{rid}   {e.name}({e.employeeId})  {REV[rid].reviewPeriod}   {dc:<14} -> {dp}")
# 출력: 리뷰ID  직원        기간      (b)현재주배치 부서 -> (c)기간정합 부서
# 출력: R013   정민재(E005)  2024-H1   Engineering    -> Finance
# 출력: R014   정민재(E005)  2024-H2   Engineering    -> Finance
# 출력: R016   강수아(E006)  2024-H1   Marketing      -> Finance

# %% [markdown]
# 이동한 직원의 과거 성과가 **새 부서의 실적으로 잘못 귀속**되는 지점이다.
# Assignment 의 `startDate`/`endDate` 와 리뷰의 `reviewPeriod` 를 맞추지 않으면
# "이 팀이 잘한다"는 결론이 사실은 "이 팀이 잘하는 사람을 데려왔다"일 수 있다.
#
# (d) reviewDate 기준도 위험하다. 리뷰 확정일은 평가 구간보다 **뒤**에 있어서,
# 구간 종료와 확정일 사이에 이동이 일어나면 그 리뷰가 새 부서로 넘어간다.

# %%
print("이동 직후 확정된 리뷰의 귀속:")
for rid in sorted(set(by_rev_period)):
    r = REV[rid]
    dp = by_rev_period[rid][3].name
    dd = next((t[3].name for t in tr_rdate if t[0].reviewId == rid), "(없음)")
    if dp != dd:
        s, e_ = PERIOD_WINDOW[r.reviewPeriod]
        print(f"  {rid} {EMP[r.employeeId].name}: 평가구간 {s}~{e_}, 확정일 {r.reviewDate}"
              f" | 기간정합={dp} / reviewDate={dd}")
# 출력: 이동 직후 확정된 리뷰의 귀속:
# 출력:   R014 정민재: 평가구간 2024-07-01~2024-12-31, 확정일 2025-01-20 | 기간정합=Finance / reviewDate=Engineering
# 출력:   R016 강수아: 평가구간 2024-01-01~2024-06-30, 확정일 2024-07-15 | 기간정합=Finance / reviewDate=Marketing

# %% [markdown]
# ## 7. 겸직 중복 계상
#
# `isPrimary` 를 무시하면 겸직 직원의 리뷰가 두 부서에 동시에 잡힌다.
# (c)에서는 `isPrimary=True` + 겹침 최대 배치 1개만 인정해 중복을 없앴다.

# %%
dup = defaultdict(list)
for r, e, a, d in tr_none:
    dup[(r.reviewId, e.employeeId)].append((d.name, "primary" if a.isPrimary else "겸직"))
print("리뷰 1건이 2개 이상 부서로 복제된 사례:")
for (rid, eid), lst in sorted(dup.items()):
    if len(lst) > 1:
        print(f"  {rid} {EMP[eid].name}({eid}) {REV[rid].reviewPeriod}: {lst}")
# 출력: 리뷰 1건이 2개 이상 부서로 복제된 사례:
# 출력:   R013 정민재(E005) 2024-H1: [('Finance', 'primary'), ('Engineering', 'primary')]
# 출력:   R014 정민재(E005) 2024-H2: [('Finance', 'primary'), ('Engineering', 'primary')]
# 출력:   R016 강수아(E006) 2024-H1: [('Finance', 'primary'), ('Marketing', 'primary')]
# 출력:   R018 강수아(E006) 2025-H1: [('Finance', 'primary'), ('Marketing', 'primary')]
# 출력:   R020 윤채원(E007) 2024-H2: [('Data Platform', 'primary'), ('Engineering', '겸직')]
# 출력:   R021 윤채원(E007) 2025-H1: [('Data Platform', 'primary'), ('Engineering', '겸직')]
#
# 앞의 4건은 '이동'(같은 primary 지만 시점이 다름), 뒤 2건은 '겸직'(같은 시점, primary/부차)이다.
# 원인이 다르므로 처방도 다르다: 이동 -> 날짜 정합, 겸직 -> isPrimary(또는 배분 가중치).

# %% [markdown]
# ## 8. 절대 개수 대신 비율 — 부서 규모 보정
#
# 질문의 "many"를 절대 개수로 읽으면 **큰 부서가 항상 이긴다.**
# 부서 $D$ 에 귀속된 리뷰 전체를 $N_D$, 그중 outstanding 을 $O_D$ 라 하면
#
# $$\text{outstanding 비율}(D) = \frac{O_D}{N_D}$$
#
# 가 규모에 중립적이다. 단, $N_D$ 가 작으면 비율이 극단으로 튀므로 표본 크기를 함께 봐야 한다.
# 아래는 기간 정합 기준으로 **전체 리뷰**를 부서에 귀속시킨 뒤 비율을 낸다.

# %%
def dept_of_review(r: PerformanceReview) -> str | None:
    """리뷰 기간과 가장 많이 겹치는 primary 배치의 부서."""
    start, end = PERIOD_WINDOW[r.reviewPeriod]
    best, best_score = None, 0
    for aid in emp_to_assignments[r.employeeId]:
        a = ASG[aid]
        if not a.isPrimary:
            continue
        score = overlap_days(a, start, end)
        if score > best_score:
            best, best_score = a.departmentId, score
    return best


total_by_dept = {d.departmentId: 0 for d in DEPARTMENTS}
for r in REVIEWS:
    did = dept_of_review(r)
    if did:
        total_by_dept[did] += 1

headcount = {d.departmentId: 0 for d in DEPARTMENTS}
for a in ASSIGNMENTS:
    if a.isPrimary and (a.endDate is None or a.endDate >= AS_OF):
        headcount[a.departmentId] += 1

ratio = {}
print(f"{'부서':<16}{'현재인원':>8}{'귀속리뷰':>8}{'outstanding':>12}{'비율':>8}")
for d in DEPARTMENTS:
    did = d.departmentId
    n, o = total_by_dept[did], agg_period[did]
    ratio[did] = o / n if n else 0.0
    print(f"{d.name:<16}{headcount[did]:>8}{n:>8}{o:>12}{ratio[did]:>8.1%}")
# 출력: 부서                  현재인원    귀속리뷰 outstanding      비율
# 출력: Engineering            4       9           3   33.3%
# 출력: Finance                2       9           4   44.4%
# 출력: Marketing              3       8           1   12.5%
# 출력: Data Platform          1       3           2   66.7%

# %%
rank_cnt = sorted(DEPARTMENTS, key=lambda d: -agg_period[d.departmentId])
rank_ratio = sorted(DEPARTMENTS, key=lambda d: -ratio[d.departmentId])
print("절대 개수 순위:", " > ".join(f"{d.name}({agg_period[d.departmentId]})" for d in rank_cnt))
print("비율 순위    :", " > ".join(f"{d.name}({ratio[d.departmentId]:.0%})" for d in rank_ratio))
print("naive(b) 1위:", max(DEPARTMENTS, key=lambda d: agg_cur[d.departmentId]).name)
print("정합(c) 1위 :", max(DEPARTMENTS, key=lambda d: agg_period[d.departmentId]).name)
# 출력: 절대 개수 순위: Finance(4) > Engineering(3) > Data Platform(2) > Marketing(1)
# 출력: 비율 순위    : Data Platform(67%) > Finance(44%) > Engineering(33%) > Marketing(12%)
# 출력: naive(b) 1위: Engineering
# 출력: 정합(c) 1위 : Finance
#
# 세 가지 답이 모두 다르다:
#   시점 무시 -> Engineering, 시점 정합 -> Finance, 비율 -> Data Platform(단 n=3)

# %% [markdown]
# 비율도 만능은 아니다. Data Platform 은 현재 인원 1명, 귀속 리뷰 3건으로 66.7% 가 나왔다.
# $n=3$ 에서의 비율은 리뷰 1건만 바뀌어도 33%p 씩 흔들린다. 실무에서는 최소 표본 컷
# (예: $N_D \ge 10$)이나 이항 비율 신뢰구간(Wilson score)을 함께 붙여야 순위가 의미를 갖는다.
#
# $$\text{Wilson 하한} = \frac{\hat{p} + \frac{z^2}{2n} - z\sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}$$
#
# ## 9. 시각화 — 같은 경로, 세 가지 답
#
# 왼쪽: 부서별 outstanding 개수를 세 집계 방식으로 나란히.
# 오른쪽: 기간 정합 기준 outstanding **비율**(귀속 리뷰 대비).

# %%
names = [d.name for d in DEPARTMENTS]
ids = [d.departmentId for d in DEPARTMENTS]

fig = make_subplots(
    rows=1, cols=2, column_widths=[0.62, 0.38], horizontal_spacing=0.12,
    subplot_titles=("부서별 outstanding 리뷰 수 (집계 방식별)",
                    "outstanding 비율 (기간 정합 기준)"),
)

series = [
    ("(a) 필터 없음 — 중복 계상", agg_none, "#c0392b"),
    ("(b) 현재 주배치 — 시점 무시", agg_cur, "#e59866"),
    ("(c) 리뷰 기간 정합", agg_period, "#27ae60"),
]
for label, agg, color in series:
    vals = [agg[i] for i in ids]
    fig.add_trace(
        go.Bar(x=names, y=vals, name=label, marker_color=color,
               text=vals, textposition="outside", cliponaxis=False),
        row=1, col=1,
    )

pct = [ratio[i] * 100 for i in ids]
fig.add_trace(
    go.Bar(x=names, y=pct, name="outstanding 비율(%)", marker_color="#2980b9",
           text=[f"{p:.0f}%<br>(n={total_by_dept[i]})" for p, i in zip(pct, ids)],
           textposition="outside", cliponaxis=False, showlegend=True),
    row=1, col=2,
)

fig.update_yaxes(title_text="리뷰 건수", row=1, col=1, rangemode="tozero")
fig.update_yaxes(title_text="비율 (%)", row=1, col=2, range=[0, 100],
                 tickvals=[0, 20, 40, 60, 80])
fig.update_layout(
    title="Department &lt;- Assignment &lt;- Employee -&gt; PerformanceReview (rating=outstanding)"
          "<br><sub>같은 경로라도 어느 시점의 Assignment 를 쓰는지에 따라 1위 부서가 바뀐다</sub>",
    barmode="group", template="plotly_white",
    legend=dict(orientation="h", yanchor="bottom", y=-0.28, x=0),
    width=1050, height=560, margin=dict(t=110, b=120),
)
_show(fig)

png_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(png_path, scale=2)
print("saved:", os.path.basename(png_path), os.path.exists(png_path))
# 출력: saved: expy.png True

# %% [markdown]
# ## 10. 정리 — 왜 이 경로가 가장 긴가
#
# 아티클의 예시 질의 4개를 스텝 수로 세어 보자.
#
# | 질문 | 경로 | 엔티티 수 |
# |---|---|---|
# | 활성 아닌 배치? | `Assignment` | 1 |
# | 역할 변경 직원? | `Employee -> Assignment -> Position` | 3 |
# | 시니어 많은 부서? | `Department <- Assignment <- Employee` | 3 |
# | **outstanding 많은 팀?** | `Department <- Assignment <- Employee -> PerformanceReview` | **4** |
#
# 이유는 단순하다. **PerformanceReview 는 Department 를 모른다.**
# 평가는 사람에게 붙고(`Employee -> PerformanceReview`), 부서 소속도 사람에게 붙는다
# (`Employee -> Assignment -> Department`). 두 사실을 잇는 유일한 노드가 Employee 이고,
# 그 사이에 junction entity Assignment 가 한 칸 더 끼어 있다.
#
# 그리고 그 Assignment 가 **시간 축**을 들고 있기 때문에, 경로가 길어진 만큼
# "언제의 소속인가"라는 질문이 따라붙는다. 경로 표기는 한 줄이지만 실제 구현에서 정해야 할 것은
#
# 1. `isPrimary` — 겸직을 어떻게 셀 것인가
# 2. `startDate`/`endDate` vs `reviewPeriod` — 어느 시점의 소속인가
# 3. 절대 개수 vs 비율 — 부서 규모를 보정할 것인가
#
# 세 가지다. 온톨로지가 주는 것은 **경로**이고, 정책은 여전히 사람이 정해야 한다.
