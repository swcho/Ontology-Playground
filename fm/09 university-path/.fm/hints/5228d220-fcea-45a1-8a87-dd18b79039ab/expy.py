# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
# %% [markdown]
# # junction entity 패턴 실험
#
# **질문**: junction entity 패턴은 언제 사용하는가?
#
# **답**: 두 엔티티가 다대다(many-to-many) 관계이면서 **그 관계 자체에 속성이 붙을 때**.
# 학생은 여러 강좌를, 강좌는 여러 학생을 갖고, 그 사이에 `Enrollment`가 성적·학기·상태를 싣는다.
#
# 이 노트북은 다음 순서로 진행한다.
#
# 1. 직접 다대다 매핑(집합/딕셔너리)으로 모델링 → 성적·학기를 실을 곳이 없음을 확인
# 2. 억지로 끼워넣기 시도 → 재수강 같은 케이스에서 무너짐을 확인
# 3. `Enrollment` junction 레코드 도입 → 같은 질의가 가능해짐
# 4. junction을 통한 조인 질의 (학생별 GPA, 강좌별 평균 성적)
# 5. 이분 그래프 vs 3-레이어 그래프 시각화 비교

# %%
from __future__ import annotations  # `str | None` 표기를 Python 3.9에서도 사용하기 위함

from collections import defaultdict


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# asset(university-path.md)의 엔티티 정의를 그대로 따른다.
STUDENTS = {
    "S001": {"name": "김민준", "enrollmentYear": 2023, "major": "CS"},
    "S002": {"name": "이서연", "enrollmentYear": 2023, "major": "CS"},
    "S003": {"name": "박도윤", "enrollmentYear": 2024, "major": "Math"},
}

COURSES = {
    "C101": {"title": "Intro to Programming", "credits": 3, "level": "100", "maxEnrollment": 60},
    "C201": {"title": "Data Structures", "credits": 4, "level": "200", "maxEnrollment": 40},
    "C301": {"title": "Databases", "credits": 3, "level": "300", "maxEnrollment": 30},
}

print("students:", list(STUDENTS))
print("courses :", list(COURSES))
# 출력: students: ['S001', 'S002', 'S003']
# 출력: courses : ['C101', 'C201', 'C301']

# %% [markdown]
# ## 1. 직접 다대다 매핑 — 표현할 수 있는 것은 "듣는다" 뿐
#
# 관계를 자료구조로 직접 표현하면 인접 집합(adjacency set)이 된다.
#
# $$\text{takes} \subseteq \text{Student} \times \text{Course}$$
#
# 이 집합의 원소는 `(studentId, courseId)` 쌍이다. 쌍 그 자체 외에 **더 담을 칸이 없다**.

# %%
takes: dict[str, set[str]] = {
    "S001": {"C101", "C201"},
    "S002": {"C101", "C301"},
    "S003": {"C201"},
}

# 역방향도 만들어야 "강좌 → 학생" 질의가 된다 (같은 사실의 중복 표현)
taken_by: dict[str, set[str]] = defaultdict(set)
for sid, cids in takes.items():
    for cid in cids:
        taken_by[cid].add(sid)

print("S001이 듣는 강좌:", sorted(takes["S001"]))
print("C101 수강생   :", sorted(taken_by["C101"]))
# 출력: S001이 듣는 강좌: ['C101', 'C201']
# 출력: C101 수강생   : ['S001', 'S002']

# 여기까지는 잘 된다. 그런데:
question = "S001이 C101에서 받은 성적은?"
print(question, "->", "표현 불가 (쌍만 저장되어 있음)")
# 출력: S001이 C101에서 받은 성적은? -> 표현 불가 (쌍만 저장되어 있음)

# %% [markdown]
# ### 성적을 어느 한쪽에 밀어넣으면?
#
# | 시도 | 잃는 정보 |
# |---|---|
# | `Student.grade` | "어느 강좌의 성적인지" |
# | `Course.grade` | "누구의 성적인지" |
#
# `grade`는 학생의 속성도, 강좌의 속성도 아니다. **짝(pair)의 속성**이다.

# %%
# 시도 A: Student에 grade를 넣는다
bad_student = dict(STUDENTS["S001"], grade="A")
print("Student에 grade:", bad_student)
print("  -> C101 성적인지 C201 성적인지 알 수 없음")
# 출력: Student에 grade: {'name': '김민준', 'enrollmentYear': 2023, 'major': 'CS', 'grade': 'A'}
# 출력:   -> C101 성적인지 C201 성적인지 알 수 없음

# 시도 B: Course에 grade를 넣는다
bad_course = dict(COURSES["C101"], grade="A")
print("Course에 grade :", bad_course)
print("  -> S001 성적인지 S002 성적인지 알 수 없음")
# 출력: Course에 grade : {'title': 'Intro to Programming', 'credits': 3, 'level': '100', 'maxEnrollment': 60, 'grade': 'A'}
# 출력:   -> S001 성적인지 S002 성적인지 알 수 없음

# %% [markdown]
# ## 2. 차선책: 쌍을 키로 쓰는 사이드 딕셔너리 — 왜 부족한가
#
# `(studentId, courseId)`를 키로 하는 별도 딕셔너리를 두면 성적을 붙일 수는 있다.
# 하지만 이것은 이미 **junction entity를 어설프게 흉내낸 것**이며, 결정적으로 깨지는 지점이 있다.
#
# **같은 학생이 같은 강좌를 재수강**하면 키가 충돌한다.

# %%
grade_of: dict[tuple[str, str], str] = {}
grade_of[("S001", "C101")] = "D"  # 2024-Spring 수강, D를 받음
grade_of[("S001", "C101")] = "A"  # 2024-Fall 재수강, A를 받음  <-- 앞의 기록을 덮어씀

print("재수강 후 남은 기록 수:", len(grade_of))
print("보존된 값:", grade_of[("S001", "C101")])
print("  -> D 기록이 소실됨. 학기(semester) 정보도 애초에 담을 자리가 없음")
# 출력: 재수강 후 남은 기록 수: 1
# 출력: 보존된 값: A
# 출력:   -> D 기록이 소실됨. 학기(semester) 정보도 애초에 담을 자리가 없음

# 키에 학기를 추가하면? -> 키가 점점 부풀고, 결국 '레코드'가 필요하다는 신호다
grade_of2: dict[tuple[str, str, str], str] = {
    ("S001", "C101", "2024-Spring"): "D",
    ("S001", "C101", "2024-Fall"): "A",
}
print("학기를 키에 넣으면 보존됨:", len(grade_of2), "건")
print("  -> status, enrollDate가 추가되면 키가 계속 늘어남 = 엔티티로 승격할 때")
# 출력: 학기를 키에 넣으면 보존됨: 2 건
# 출력:   -> status, enrollDate가 추가되면 키가 계속 늘어남 = 엔티티로 승격할 때

# %% [markdown]
# ## 3. junction entity 도입 — `Enrollment`
#
# 다대다 하나를 **1:N + N:1 두 개**로 분해한다.
#
# $$\text{Student} \xrightarrow{\;\text{enrolls\_in}\;(1:N)\;} \text{Enrollment} \xrightarrow{\;\text{for\_course}\;(N:1)\;} \text{Course}$$
#
# `Enrollment`는 자체 식별자 `enrollmentId`를 갖는 **1급 엔티티**다.
# 단순 연결선이 아니라 조회·수정·참조가 가능한 독립 개체다.

# %%
# Enrollment: enrollmentId(✓), semester, grade, enrollDate, status
ENROLLMENTS = [
    {"enrollmentId": "E001", "studentId": "S001", "courseId": "C101",
     "semester": "2024-Spring", "grade": "D", "enrollDate": "2024-03-02", "status": "completed"},
    {"enrollmentId": "E002", "studentId": "S001", "courseId": "C101",
     "semester": "2024-Fall", "grade": "A", "enrollDate": "2024-09-01", "status": "completed"},
    {"enrollmentId": "E003", "studentId": "S001", "courseId": "C201",
     "semester": "2024-Fall", "grade": "B", "enrollDate": "2024-09-01", "status": "completed"},
    {"enrollmentId": "E004", "studentId": "S002", "courseId": "C101",
     "semester": "2024-Spring", "grade": "A", "enrollDate": "2024-03-02", "status": "completed"},
    {"enrollmentId": "E005", "studentId": "S002", "courseId": "C301",
     "semester": "2024-Fall", "grade": "B", "enrollDate": "2024-09-01", "status": "completed"},
    {"enrollmentId": "E006", "studentId": "S003", "courseId": "C201",
     "semester": "2024-Fall", "grade": "C", "enrollDate": "2024-09-03", "status": "withdrawn"},
]

print("enrollment 레코드 수:", len(ENROLLMENTS))
print("재수강 두 건 모두 보존:",
      [e["enrollmentId"] + ":" + e["semester"] + ":" + e["grade"]
       for e in ENROLLMENTS if e["studentId"] == "S001" and e["courseId"] == "C101"])
# 출력: enrollment 레코드 수: 6
# 출력: 재수강 두 건 모두 보존: ['E001:2024-Spring:D', 'E002:2024-Fall:A']

# %% [markdown]
# ### 아까 "표현 불가"였던 질의가 전부 가능해진다

# %%
def q_grade(sid: str, cid: str, semester: str | None = None):
    """관계 위에 걸린 필터 — junction 없이는 쓸 자리가 없던 WHERE절."""
    return [e for e in ENROLLMENTS
            if e["studentId"] == sid and e["courseId"] == cid
            and (semester is None or e["semester"] == semester)]


print("Q1. S001의 C101 성적 전체:",
      [(e["semester"], e["grade"]) for e in q_grade("S001", "C101")])
# 출력: Q1. S001의 C101 성적 전체: [('2024-Spring', 'D'), ('2024-Fall', 'A')]

print("Q2. S001의 2024-Fall C101 성적:",
      [e["grade"] for e in q_grade("S001", "C101", "2024-Fall")])
# 출력: Q2. S001의 2024-Fall C101 성적: ['A']

print("Q3. 철회(withdrawn) 건:",
      [e["enrollmentId"] for e in ENROLLMENTS if e["status"] == "withdrawn"])
# 출력: Q3. 철회(withdrawn) 건: ['E006']

# GQL 예시의 WHERE e.grade IN ['C','D','F'] 에 해당
struggling = [e for e in ENROLLMENTS if e["grade"] in ("C", "D", "F")]
print("Q4. 고전 중인 수강기록:",
      [(e["enrollmentId"], e["studentId"], e["courseId"], e["grade"]) for e in struggling])
# 출력: Q4. 고전 중인 수강기록: [('E001', 'S001', 'C101', 'D'), ('E006', 'S003', 'C201', 'C')]

# %% [markdown]
# ## 4. junction을 통한 조인 질의
#
# junction은 양쪽으로 조인 경로를 열어준다.
#
# - `Student → Enrollment` 로 모으면 **학생별 GPA**
# - `Course ← Enrollment` 로 모으면 **강좌별 평균 성적**
#
# GPA는 학점(credits) 가중 평균이다.
#
# $$\mathrm{GPA}(s)=\frac{\sum_{e \in E(s)} \mathrm{point}(e.\text{grade}) \cdot \mathrm{credits}(e.\text{course})}{\sum_{e \in E(s)} \mathrm{credits}(e.\text{course})}$$
#
# 여기서 $E(s)$는 학생 $s$의 `status == "completed"`인 수강기록 집합이다.

# %%
POINT = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}


def student_gpa(sid: str) -> float | None:
    """Student → Enrollment → Course 조인 후 가중 평균."""
    num = den = 0.0
    for e in ENROLLMENTS:
        if e["studentId"] != sid or e["status"] != "completed":
            continue
        cr = COURSES[e["courseId"]]["credits"]  # for_course 홉
        num += POINT[e["grade"]] * cr
        den += cr
    return round(num / den, 3) if den else None


for sid in STUDENTS:
    print(f"{sid} {STUDENTS[sid]['name']} GPA = {student_gpa(sid)}")
# 출력: S001 김민준 GPA = 2.7   (D×3 + A×3 + B×4 = 27, credits 10 → 2.7)
# 출력: S002 이서연 GPA = 3.5
# 출력: S003 박도윤 GPA = None

# S003은 withdrawn 뿐이라 GPA 없음 -> status 속성이 junction에 있어야 가능한 구분

# %%
def course_avg(cid: str):
    """Course ← Enrollment 역방향 조인."""
    pts = [POINT[e["grade"]] for e in ENROLLMENTS
           if e["courseId"] == cid and e["status"] == "completed"]
    return (round(sum(pts) / len(pts), 3), len(pts)) if pts else (None, 0)


for cid, c in COURSES.items():
    avg, n = course_avg(cid)
    fill = f"{n}/{c['maxEnrollment']}"
    print(f"{cid} {c['title']:<22} avg={avg} n={fill}")
# 출력: C101 Intro to Programming   avg=3.0 n=3/60   (재수강 E001·E002가 별개로 집계됨)
# 출력: C201 Data Structures        avg=3.0 n=1/40
# 출력: C301 Databases              avg=3.0 n=1/30

# %% [markdown]
# ### transitive query: 직접 관계가 없는 엔티티 잇기
#
# `Department → Course ← Enrollment ← Student`.
# Department와 Student 사이에는 직접 관계가 **하나도 없다**. junction이 징검다리가 된다.

# %%
DEPARTMENTS = {"D01": {"name": "Computer Science"}, "D02": {"name": "Mathematics"}}
OFFERS = {"C101": "D01", "C201": "D01", "C301": "D01"}  # Department --offers--> Course

by_dept: dict[str, list[str]] = defaultdict(list)
for e in struggling:  # grade IN ['C','D','F']
    by_dept[OFFERS[e["courseId"]]].append(f"{e['studentId']}@{e['courseId']}")

for did, items in by_dept.items():
    print(f"{DEPARTMENTS[did]['name']}: struggling_count={len(items)} {items}")
# 출력: Computer Science: struggling_count=2 ['S001@C101', 'S003@C201']

# %% [markdown]
# ## 5. 시각화 — 이분 그래프 vs 3-레이어 그래프
#
# - **왼쪽**: 직접 다대다. 엣지 위에 성적/학기를 쓸 자리가 없다. 재수강 두 건이 하나의 선으로 뭉갠다.
# - **오른쪽**: junction 삽입. 모든 엣지가 `1:N` 또는 `N:1`이고, 가운데 노드가 속성을 싣는다.

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

C_STU, C_CRS, C_ENR = "#4C78A8", "#E45756", "#72B7B2"


def add_edge(fig, x0, y0, x1, y1, row, col, color="#B0B0B0", width=1.6, dash=None):
    fig.add_trace(go.Scatter(x=[x0, x1], y=[y0, y1], mode="lines",
                             line=dict(color=color, width=width, dash=dash),
                             hoverinfo="skip", showlegend=False), row=row, col=col)


def add_nodes(fig, xs, ys, labels, color, row, col, name, hover=None, size=34):
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers+text", text=labels,
                             textposition="middle center",
                             textfont=dict(color="white", size=10),
                             marker=dict(size=size, color=color,
                                         line=dict(color="white", width=1.5)),
                             hovertext=hover or labels, hoverinfo="text",
                             name=name, showlegend=False), row=row, col=col)


fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.09,
                    subplot_titles=("① 직접 다대다 — 성적/학기를 실을 곳이 없음",
                                    "② junction entity — Enrollment가 속성을 싣는다"))

s_ids = list(STUDENTS)
c_ids = list(COURSES)
sy = {s: 2 - i for i, s in enumerate(s_ids)}
cy = {c: 2 - i for i, c in enumerate(c_ids)}

# --- (1) 이분 그래프: (student, course) 중복 제거된 쌍만 남는다 ---
pairs = sorted({(e["studentId"], e["courseId"]) for e in ENROLLMENTS})
for sid, cid in pairs:
    add_edge(fig, 0, sy[sid], 1, cy[cid], 1, 1)
add_nodes(fig, [0] * len(s_ids), [sy[s] for s in s_ids], s_ids, C_STU, 1, 1, "Student",
          hover=[f"{s}<br>{STUDENTS[s]['name']}" for s in s_ids])
add_nodes(fig, [1] * len(c_ids), [cy[c] for c in c_ids], c_ids, C_CRS, 1, 1, "Course",
          hover=[f"{c}<br>{COURSES[c]['title']}" for c in c_ids])
fig.add_annotation(x=0.5, y=-1.2, xref="x", yref="y", showarrow=False,
                   text=f"엣지 {len(pairs)}개 = 저장 가능한 사실 {len(pairs)}개<br>"
                        f"재수강 2건(E001 D / E002 A)이 선 1개로 뭉개짐",
                   font=dict(size=11, color="#C0392B"))

# --- (2) 3-레이어: Student → Enrollment → Course ---
_gap = 0.55
ey = {e["enrollmentId"]: 1 + (len(ENROLLMENTS) - 1) / 2 * _gap - i * _gap
      for i, e in enumerate(ENROLLMENTS)}
for e in ENROLLMENTS:
    eid, y = e["enrollmentId"], ey[e["enrollmentId"]]
    add_edge(fig, 0, sy[e["studentId"]], 1, y, 1, 2, color=C_STU, width=1.2)
    add_edge(fig, 1, y, 2, cy[e["courseId"]], 1, 2, color=C_CRS, width=1.2,
             dash="dot" if e["status"] == "withdrawn" else None)
add_nodes(fig, [0] * len(s_ids), [sy[s] for s in s_ids], s_ids, C_STU, 1, 2, "Student",
          hover=[f"{s}<br>{STUDENTS[s]['name']}" for s in s_ids])
add_nodes(fig, [1] * len(ENROLLMENTS), [ey[e["enrollmentId"]] for e in ENROLLMENTS],
          [e["enrollmentId"] for e in ENROLLMENTS], C_ENR, 1, 2, "Enrollment",
          hover=[f"{e['enrollmentId']}<br>semester={e['semester']}"
                 f"<br>grade={e['grade']}<br>status={e['status']}" for e in ENROLLMENTS],
          size=30)
add_nodes(fig, [2] * len(c_ids), [cy[c] for c in c_ids], c_ids, C_CRS, 1, 2, "Course",
          hover=[f"{c}<br>{COURSES[c]['title']}" for c in c_ids])
for e in ENROLLMENTS:
    fig.add_annotation(x=1, y=ey[e["enrollmentId"]] + 0.27, xref="x2", yref="y2",
                       showarrow=False, font=dict(size=9, color="#20605C"),
                       bgcolor="rgba(255,255,255,0.85)",
                       text=f"{e['semester']} · {e['grade']} · {e['status']}")
fig.add_annotation(x=0.5, y=-1.2, xref="x2", yref="y2", showarrow=False,
                   text="enrolls_in (1:N)", font=dict(size=11, color=C_STU))
fig.add_annotation(x=1.5, y=-1.2, xref="x2", yref="y2", showarrow=False,
                   text="for_course (N:1)", font=dict(size=11, color=C_CRS))

fig.update_xaxes(visible=False, range=[-0.35, 1.35], row=1, col=1)
fig.update_xaxes(visible=False, range=[-0.4, 2.4], row=1, col=2)
fig.update_yaxes(visible=False, range=[-1.6, 2.9], row=1, col=1)
fig.update_yaxes(visible=False, range=[-1.6, 2.9], row=1, col=2)
fig.update_layout(
    title="junction entity 패턴: 다대다 + 관계 속성일 때 관계를 엔티티로 승격",
    width=1180, height=620, plot_bgcolor="white", paper_bgcolor="white",
    margin=dict(l=30, r=30, t=90, b=30),
)

_show(fig)

import pathlib

_out = pathlib.Path(__file__).resolve().parent / "expy.png" if "__file__" in dir() \
    else pathlib.Path("expy.png")
fig.write_image(str(_out), scale=2)
print("saved:", _out.name)
# 출력: saved: expy.png

# %% [markdown]
# ## 정리
#
# | 조건 | junction entity 필요? |
# |---|---|
# | 다대일 (`Professor → Department`) | ✗ 외래키 하나면 충분 |
# | 다대다인데 속성 없음 | △ 순수 조인 테이블/엣지로 충분 |
# | **다대다 + 관계에 속성** | **✓ junction entity** |
# | 같은 짝이 반복 발생 (재수강) | ✓ 자체 식별자가 필요 |
# | 관계에 생명주기/상태 전이 존재 | ✓ enrolled → withdrawn/completed |
#
# **판별 질문**: *"이 속성은 A의 것인가, B의 것인가?"*
# 어느 쪽도 아니라면 — 그건 **관계의 속성**이고, 관계를 엔티티로 승격시켜야 한다.
#
# 다른 이름: associative entity(ER), join/bridge table(RDB),
# association class(UML), reification(RDF), fact table(DW).
