# %% [markdown]
# # Transitive Query(전이 질의) 실험실
#
# **transitive query**란 *직접 관계가 없는 엔티티들을 중간 노드를 거쳐 여러 관계를 연달아 타고 연결하는 질의*다.
#
# University 온톨로지(5 엔티티 / 6 관계)에서 `Professor`와 `Student` 사이에는
# `teaches`, `enrolls_in` 같은 **직접 간선이 존재하지 않는다**(단, `advises`는 별개의 직접 관계다).
# 그럼에도 아래 경로를 타면 둘을 연결할 수 있다.
#
# $$\text{Professor} \xrightarrow{teaches} \text{Course} \xleftarrow{for\_course} \text{Enrollment} \xleftarrow{enrolls\_in} \text{Student}$$
#
# 경로(path)를 형식화하면 간선 라벨 $r_i$ 로 이어지는 노드 열이다.
#
# $$p = v_0 \xrightarrow{r_1} v_1 \xrightarrow{r_2} \cdots \xrightarrow{r_k} v_k, \qquad |p| = k \;(\text{hop 수})$$
#
# - $k = 1$ : **1홉 질의** — 인접 리스트 한 번 조회
# - $k \ge 2$ : **다홉 = 전이 질의** — 중간 노드를 경유
#
# 필요 패키지: plotly, kaleido (설치: `pip install plotly kaleido`)

# %%
from collections import defaultdict, deque
from itertools import count

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


print("ready")
# 출력: ready

# %% [markdown]
# ## 1. 스키마 레벨: 5 엔티티 / 6 관계
#
# 온톨로지 스키마 자체도 그래프다. 먼저 엔티티 타입 사이의 관계를 인접 리스트로 만든다.

# %%
SCHEMA_EDGES = [
    ("Student", "enrolls_in", "Enrollment"),
    ("Enrollment", "for_course", "Course"),
    ("Professor", "teaches", "Course"),
    ("Professor", "advises", "Student"),
    ("Professor", "belongs_to", "Department"),
    ("Department", "offers", "Course"),
]

schema_adj = defaultdict(list)
for src, rel, dst in SCHEMA_EDGES:
    schema_adj[src].append((rel, dst))

for node in ["Department", "Professor", "Course", "Enrollment", "Student"]:
    print(f"{node:12s} -> {schema_adj[node]}")
# 출력: Department   -> [('offers', 'Course')]
# 출력: Professor    -> [('teaches', 'Course'), ('advises', 'Student'), ('belongs_to', 'Department')]
# 출력: Course       -> []            <- 나가는 간선 없음. 역방향 traversal이 필요한 이유
# 출력: Enrollment   -> [('for_course', 'Course')]
# 출력: Student      -> [('enrolls_in', 'Enrollment')]

# %% [markdown]
# ## 2. 인스턴스 데이터
#
# 실제 질의는 인스턴스 그래프 위에서 돈다. 작은 학사 데이터를 만든다.

# %%
NODES = {
    # id: (type, label, props)
    "D_CS": ("Department", "CS", {}),
    "D_MA": ("Department", "Math", {}),
    "P_SMITH": ("Professor", "Smith", {"tenured": True}),
    "P_LEE": ("Professor", "Lee", {"tenured": False}),
    "P_KIM": ("Professor", "Kim", {"tenured": True}),
    "C101": ("Course", "Intro Prog", {"level": 100}),
    "C201": ("Course", "Databases", {"level": 200}),
    "C301": ("Course", "Algorithms", {"level": 300}),
    "M201": ("Course", "Linear Alg", {"level": 200}),
    "E1": ("Enrollment", "E1", {"grade": "A"}),
    "E2": ("Enrollment", "E2", {"grade": "C"}),
    "E3": ("Enrollment", "E3", {"grade": "B"}),
    "E4": ("Enrollment", "E4", {"grade": "A"}),
    "E5": ("Enrollment", "E5", {"grade": "F"}),
    "E6": ("Enrollment", "E6", {"grade": "D"}),
    "E7": ("Enrollment", "E7", {"grade": "B"}),
    "S1": ("Student", "Ann", {}),
    "S2": ("Student", "Ben", {}),
    "S3": ("Student", "Cho", {}),
    "S4": ("Student", "Dan", {}),
}

EDGES = [
    ("P_SMITH", "belongs_to", "D_CS"),
    ("P_LEE", "belongs_to", "D_CS"),
    ("P_KIM", "belongs_to", "D_MA"),
    ("D_CS", "offers", "C101"),
    ("D_CS", "offers", "C201"),
    ("D_CS", "offers", "C301"),
    ("D_MA", "offers", "M201"),
    ("P_SMITH", "teaches", "C101"),
    ("P_SMITH", "teaches", "C301"),
    ("P_LEE", "teaches", "C201"),
    ("P_KIM", "teaches", "M201"),
    ("P_SMITH", "advises", "S1"),
    ("S1", "enrolls_in", "E1"),
    ("E1", "for_course", "C101"),
    ("S2", "enrolls_in", "E2"),
    ("E2", "for_course", "C101"),
    ("S1", "enrolls_in", "E3"),
    ("E3", "for_course", "C301"),
    ("S3", "enrolls_in", "E4"),
    ("E4", "for_course", "C201"),
    ("S4", "enrolls_in", "E5"),
    ("E5", "for_course", "M201"),
    ("S2", "enrolls_in", "E6"),
    ("E6", "for_course", "C301"),
    ("S3", "enrolls_in", "E7"),
    ("E7", "for_course", "M201"),
]

print(f"nodes={len(NODES)}, edges={len(EDGES)}")
# 출력: nodes=20, edges=26

# %% [markdown]
# ## 3. 양방향 인접 리스트
#
# GQL 패턴 `(p)-[:teaches]->(c)<-[:for_course]-(e)` 처럼 **간선을 역방향으로도 탄다**.
# 역방향 traversal은 라벨 앞에 `~` 를 붙여 구분한다.

# %%
adj = defaultdict(list)  # node -> [(rel, neighbor, direction)]
for src, rel, dst in EDGES:
    adj[src].append((rel, dst, "out"))
    adj[dst].append(("~" + rel, src, "in"))

for rel, nb, d in adj["C101"]:
    print(f"C101 --{rel:12s}--> {nb:8s} ({d})")
# 출력: C101 --~offers     --> D_CS     (in)
# 출력: C101 --~teaches    --> P_SMITH  (in)
# 출력: C101 --~for_course --> E1       (in)
# 출력: C101 --~for_course --> E2       (in)

# %% [markdown]
# ## 4. 1홉 질의 vs 전이 질의
#
# **1홉**: "Smith 교수가 가르치는 과목은?" — 인접 리스트 한 번이면 끝난다.
#
# **전이(3홉)**: "Smith 교수의 수업을 듣는 학생은?" — Professor와 Student 사이에는
# `teaches`/`enrolls_in` 경로상의 직접 간선이 없으므로 Course, Enrollment 두 중간 노드를 경유해야 한다.

# %%
def one_hop(node, rel):
    """1홉 질의: 특정 라벨로 인접 노드만 가져온다."""
    return [nb for r, nb, _ in adj[node] if r == rel]


def path_query(start, rel_pattern):
    """전이 질의: 라벨 시퀀스를 순서대로 타며 모든 경로를 반환한다."""
    paths = [[start]]
    for rel in rel_pattern:
        nxt = []
        for p in paths:
            for r, nb, _ in adj[p[-1]]:
                if r == rel and nb not in p:  # 단순 경로(노드 재방문 금지)
                    nxt.append(p + [nb])
        paths = nxt
    return paths


print("1-hop  teaches :", one_hop("P_SMITH", "teaches"))
# 출력: 1-hop  teaches : ['C101', 'C301']

PATTERN = ["teaches", "~for_course", "~enrolls_in"]
paths = path_query("P_SMITH", PATTERN)
for p in paths:
    print(" -> ".join(f"{n}({NODES[n][1]})" for n in p))
# 출력: P_SMITH(Smith) -> C101(Intro Prog) -> E1(E1) -> S1(Ann)
# 출력: P_SMITH(Smith) -> C101(Intro Prog) -> E2(E2) -> S2(Ben)
# 출력: P_SMITH(Smith) -> C301(Algorithms) -> E3(E3) -> S1(Ann)
# 출력: P_SMITH(Smith) -> C301(Algorithms) -> E6(E6) -> S2(Ben)

students = sorted({NODES[p[-1]][1] for p in paths})
print("Smith 교수 수업 수강생:", students)
# 출력: Smith 교수 수업 수강생: ['Ann', 'Ben']

# %% [markdown]
# ## 5. 중간 노드 속성으로 필터링
#
# 전이 질의의 진짜 힘은 **경로 중간 노드의 속성**까지 조건으로 걸 수 있다는 점이다.
#
# ```gql
# MATCH (d:Department)-[:offers]->(c:Course)<-[:for_course]-(e:Enrollment)<-[:enrolls_in]-(s:Student)
# WHERE e.grade IN ['C','D','F']
# RETURN d.name, COUNT(e)
# ```

# %%
struggling = defaultdict(list)
for dept in ["D_CS", "D_MA"]:
    for p in path_query(dept, ["offers", "~for_course", "~enrolls_in"]):
        _, course, enroll, student = p
        if NODES[enroll][2]["grade"] in ("C", "D", "F"):
            struggling[NODES[dept][1]].append((NODES[course][1], NODES[student][1], NODES[enroll][2]["grade"]))

for dept, rows in struggling.items():
    print(f"{dept}: count={len(rows)} {rows}")
# 출력: CS: count=2 [('Intro Prog', 'Ben', 'C'), ('Algorithms', 'Ben', 'D')]
# 출력: Math: count=1 [('Linear Alg', 'Dan', 'F')]

# 종신교수(tenured) 수업을 듣는 학생 — Professor 속성 + 3홉 경로
tenured_students = set()
for pid, (typ, name, props) in NODES.items():
    if typ == "Professor" and props.get("tenured"):
        for p in path_query(pid, PATTERN):
            tenured_students.add(NODES[p[-1]][1])
print("tenured 교수 수업 수강생:", sorted(tenured_students))
# 출력: tenured 교수 수업 수강생: ['Ann', 'Ben', 'Cho', 'Dan']

# %% [markdown]
# ## 6. 홉 수가 늘면 무엇이 커지는가
#
# - **도달 가능 노드** $R_k = \{v : dist(v_0, v) \le k\}$ — BFS로 구하며 노드 수 $|V|$ 로 포화된다.
# - **단순 경로 수** $P_k$ — 분기(branching)가 곱해져 도달 노드보다 훨씬 크게 불어난다.
#
# 즉 전이 질의의 비용은 "몇 개 노드에 닿느냐"가 아니라 **탐색해야 하는 경로 수**가 지배한다.

# %%
def reachable_within(start, max_hop):
    """홉별 누적 도달 노드 수."""
    dist = {start: 0}
    q = deque([start])
    while q:
        cur = q.popleft()
        for _, nb, _ in adj[cur]:
            if nb not in dist:
                dist[nb] = dist[cur] + 1
                q.append(nb)
    return [sum(1 for v in dist.values() if 0 < v <= k) for k in range(max_hop + 1)]


def simple_path_count(start, max_hop):
    """길이가 정확히 k인 단순 경로 수."""
    counts = []
    frontier = [[start]]
    for _ in range(max_hop):
        nxt = [p + [nb] for p in frontier for _, nb, _ in adj[p[-1]] if nb not in p]
        counts.append(len(nxt))
        frontier = nxt
    return [0] + counts


MAX_HOP = 9
reach = reachable_within("P_SMITH", MAX_HOP)
pcount = simple_path_count("P_SMITH", MAX_HOP)
print("hop :", list(range(MAX_HOP + 1)))
print("도달 노드 수(누적):", reach)
print("단순 경로 수(정확히 k홉):", pcount)
# 출력: hop : [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
# 출력: 도달 노드 수(누적): [0, 4, 10, 12, 13, 14, 15, 18, 19, 19]
# 출력: 단순 경로 수(정확히 k홉): [0, 4, 12, 19, 24, 26, 34, 32, 44, 35]

print(f"도달 노드는 8홉에서 |V|-1 = {len(NODES) - 1} 로 포화, 경로 수는 그 뒤에도 계속 오르내린다")
# 출력: 도달 노드는 8홉에서 |V|-1 = 19 로 포화, 경로 수는 그 뒤에도 계속 오르내린다

# %% [markdown]
# ## 7. 시각화
#
# 왼쪽: 인스턴스 그래프 위에 `Professor → Course → Enrollment → Student` 3홉 경로 강조.
# 오른쪽: 홉 수 대비 도달 노드 수(포화)와 단순 경로 수(폭발) 비교.

# %%
LAYER_X = {"Department": 0.0, "Professor": 1.0, "Course": 2.0, "Enrollment": 3.0, "Student": 4.0}
COLOR = {
    "Department": "#8C8C8C",
    "Professor": "#2A6FDB",
    "Course": "#14A38B",
    "Enrollment": "#E8A33D",
    "Student": "#C7457A",
}

pos = {}
by_layer = defaultdict(list)
for nid, (typ, _, _) in NODES.items():
    by_layer[typ].append(nid)
for typ, ids in by_layer.items():
    n = len(ids)
    for i, nid in enumerate(ids):
        pos[nid] = (LAYER_X[typ], (n - 1) / 2 - i)

HL_PATH = ["P_SMITH", "C101", "E1", "S1"]
hl_edges = {(HL_PATH[i], HL_PATH[i + 1]) for i in range(len(HL_PATH) - 1)}

fig = make_subplots(
    rows=1,
    cols=2,
    column_widths=[0.58, 0.42],
    subplot_titles=("Instance graph: 3-hop transitive path", "Hop 수 대비 도달 노드 / 경로 수"),
    specs=[[{"type": "xy"}, {"type": "xy"}]],
)

# --- 배경 간선
bx, by = [], []
for src, _, dst in EDGES:
    if (src, dst) in hl_edges or (dst, src) in hl_edges:
        continue
    bx += [pos[src][0], pos[dst][0], None]
    by += [pos[src][1], pos[dst][1], None]
fig.add_trace(
    go.Scatter(x=bx, y=by, mode="lines", line=dict(color="rgba(140,140,140,0.35)", width=1), hoverinfo="skip",
               showlegend=False),
    row=1, col=1,
)

# --- 강조 경로
hx, hy = [], []
for a, b in zip(HL_PATH, HL_PATH[1:]):
    hx += [pos[a][0], pos[b][0], None]
    hy += [pos[a][1], pos[b][1], None]
fig.add_trace(
    go.Scatter(x=hx, y=hy, mode="lines", line=dict(color="#D6455D", width=4),
               name="teaches → ~for_course → ~enrolls_in"),
    row=1, col=1,
)

# --- 노드
for typ, ids in by_layer.items():
    fig.add_trace(
        go.Scatter(
            x=[pos[i][0] for i in ids],
            y=[pos[i][1] for i in ids],
            mode="markers+text",
            marker=dict(size=[22 if i in HL_PATH else 14 for i in ids], color=COLOR[typ],
                        line=dict(color="white", width=1.5)),
            text=[NODES[i][1] for i in ids],
            textposition="bottom center",
            textfont=dict(size=9),
            name=typ,
            hovertext=[f"{i} ({typ})" for i in ids],
            hoverinfo="text",
        ),
        row=1, col=1,
    )

# --- 홉 증가 곡선
hops = list(range(MAX_HOP + 1))
fig.add_trace(
    go.Scatter(x=hops, y=reach, mode="lines+markers", name="도달 노드 수 (누적)",
               line=dict(color="#2A6FDB", width=3)),
    row=1, col=2,
)
fig.add_trace(
    go.Scatter(x=hops, y=pcount, mode="lines+markers", name="단순 경로 수 (k홉)",
               line=dict(color="#D6455D", width=3, dash="dot")),
    row=1, col=2,
)
fig.add_hline(y=len(NODES) - 1, line=dict(color="#8C8C8C", dash="dash"),
              annotation_text="|V|-1 포화", row=1, col=2)

fig.update_xaxes(visible=False, row=1, col=1)
fig.update_yaxes(visible=False, row=1, col=1)
fig.update_xaxes(title_text="hop (k)", row=1, col=2)
fig.update_yaxes(title_text="count", row=1, col=2)
fig.update_layout(
    title="Transitive query: 중간 노드를 거쳐 Professor와 Student를 잇는다",
    template="plotly_white",
    width=1250,
    height=560,
    legend=dict(orientation="h", y=-0.12),
)

_show(fig)
fig.write_image("expy.png", scale=2)
print("saved expy.png")
# 출력: saved expy.png

# %% [markdown]
# ## 정리
#
# 1. **1홉 질의**는 인접 리스트 한 번 조회 — 관계형 DB의 단일 JOIN과 다르지 않다.
# 2. **전이 질의**는 라벨 시퀀스를 따라 여러 관계를 연달아 타며, 간선을 역방향(`~rel`)으로도 탄다.
# 3. `Professor → Course → Enrollment → Student` 처럼 **직접 간선이 없는 두 엔티티**를
#    Course·Enrollment 같은 중간(junction) 노드로 연결하는 것이 그래프 온톨로지의 핵심 강점이다.
# 4. 경로 중간 노드의 속성(`Enrollment.grade`, `Professor.tenured`)까지 조건에 넣을 수 있어
#    "종신교수 수업에서 C 이하를 받은 학생" 같은 질문이 한 패턴으로 표현된다.
# 5. 홉이 늘면 도달 노드 수는 $|V|$ 로 포화하지만 탐색할 경로 수는 그보다 훨씬 크게 불어난다
#    → 실무 질의에는 반드시 **홉 수 상한**과 방문 노드 중복 제거가 필요하다.
