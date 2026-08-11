# 필요 패키지: networkx, plotly, kaleido
#   pip install networkx plotly kaleido

# %% [markdown]
# # severe 진단 + 처방 소진 환자 찾기 — GQL 쿼리를 파이썬으로 분해하기
#
# 대상 쿼리:
#
# ```gql
# MATCH (p:Patient)-[:diagnosed_with]->(d:Diagnosis)-[:treated_by]->(rx:Prescription)
# WHERE d.severity = 'severe' AND rx.refillsRemaining <= 1
# RETURN p.patientId, d.description, rx.medication, rx.refillsRemaining
# ```
#
# 그래프 질의는 세 단계 파이프라인이다. 각 단계는 **행(row) 집합**을 입출력한다.
#
# $$\underbrace{G}_{\text{그래프}} \;\xrightarrow{\;\text{MATCH}\;}\;
#   R_0 \;\xrightarrow{\;\text{WHERE}\;}\; R_1 \;\xrightarrow{\;\text{RETURN}\;}\; R_2$$
#
# - **MATCH**: 그래프에서 패턴에 맞는 경로를 모두 열거해 바인딩 행 $R_0$ 생성
#   $$R_0 = \{(p,d,rx) \mid p \xrightarrow{\text{diagnosed\_with}} d \xrightarrow{\text{treated\_by}} rx\}$$
# - **WHERE**: 술어로 걸러 $R_1 = \{r \in R_0 \mid \phi(r)\}$
#   $$\phi(p,d,rx) \equiv (d.severity = \texttt{'severe'}) \land (rx.refillsRemaining \le 1)$$
# - **RETURN**: 각 행에서 원하는 프로퍼티만 투영(projection)해 $R_2$ 생성
#
# 이 노트북은 networkx로 작은 인스턴스 그래프를 만들고 위 3단계를
# **순수 파이썬 루프**로 재현하면서, 단계마다 남는 행 수를 세어 본다.

# %%
# --- 공통 셋업: 시각화 헬퍼 (fig.show()를 직접 호출하지 않는다) ---
import pathlib

import networkx as nx


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


HERE = pathlib.Path(__file__).parent if "__file__" in globals() else pathlib.Path.cwd()
print("networkx", nx.__version__)
# 출력: networkx 3.2.1

# %% [markdown]
# ## 1. 인스턴스 그래프 만들기
#
# 온톨로지(스키마)는 "Patient 는 diagnosed_with 로 Diagnosis 를 가리킨다"는 **타입 수준** 규칙이고,
# 인스턴스 그래프는 그 규칙을 따르는 **개별 노드/엣지**다. MATCH 는 인스턴스 그래프를 훑는다.
#
# | 엔티티 | 식별자 | 이 예제에서 쓰는 프로퍼티 |
# |---|---|---|
# | `Patient` | `patientId` | — |
# | `Diagnosis` | `diagnosisId` | `description`, `severity`, `icdCode` |
# | `Prescription` | `rxNumber` | `medication`, `refillsRemaining` |
#
# 관계는 방향이 있는 두 개: `diagnosed_with` (Patient → Diagnosis),
# `treated_by` (Diagnosis → Prescription). 둘 다 one-to-many 이므로
# 한 환자가 진단 여러 개를, 한 진단이 처방 여러 개를 가질 수 있다.

# %%
G = nx.MultiDiGraph()  # 같은 두 노드 사이 여러 관계 타입을 허용하려면 MultiDiGraph

patients = [
    ("P-001", {"patientId": "P-001", "mrn": "MRN-88121", "bloodType": "A+"}),
    ("P-002", {"patientId": "P-002", "mrn": "MRN-88122", "bloodType": "O-"}),
    ("P-003", {"patientId": "P-003", "mrn": "MRN-88123", "bloodType": "B+"}),
    ("P-004", {"patientId": "P-004", "mrn": "MRN-88124", "bloodType": "AB+"}),
]
diagnoses = [
    ("D-1", {"diagnosisId": "D-1", "icdCode": "I50.9", "description": "Heart failure", "severity": "severe"}),
    ("D-2", {"diagnosisId": "D-2", "icdCode": "E11.9", "description": "Type 2 diabetes", "severity": "moderate"}),
    ("D-3", {"diagnosisId": "D-3", "icdCode": "J45.5", "description": "Severe asthma", "severity": "severe"}),
    ("D-4", {"diagnosisId": "D-4", "icdCode": "N18.5", "description": "Kidney failure", "severity": "severe"}),
    ("D-5", {"diagnosisId": "D-5", "icdCode": "M54.5", "description": "Low back pain", "severity": "mild"}),
]
prescriptions = [
    ("RX-100", {"rxNumber": "RX-100", "medication": "Furosemide", "dosage": "40mg", "refillsRemaining": 0}),
    ("RX-101", {"rxNumber": "RX-101", "medication": "Carvedilol", "dosage": "12.5mg", "refillsRemaining": 3}),
    ("RX-102", {"rxNumber": "RX-102", "medication": "Metformin", "dosage": "500mg", "refillsRemaining": 1}),
    ("RX-103", {"rxNumber": "RX-103", "medication": "Fluticasone", "dosage": "250mcg", "refillsRemaining": 1}),
    ("RX-104", {"rxNumber": "RX-104", "medication": "Epoetin alfa", "dosage": "4000IU", "refillsRemaining": 5}),
    ("RX-105", {"rxNumber": "RX-105", "medication": "Ibuprofen", "dosage": "400mg", "refillsRemaining": 0}),
]

for nid, props in patients:
    G.add_node(nid, label="Patient", **props)
for nid, props in diagnoses:
    G.add_node(nid, label="Diagnosis", **props)
for nid, props in prescriptions:
    G.add_node(nid, label="Prescription", **props)

# diagnosed_with: Patient -> Diagnosis
for src, dst in [("P-001", "D-1"), ("P-001", "D-2"), ("P-002", "D-3"), ("P-003", "D-4"), ("P-004", "D-5")]:
    G.add_edge(src, dst, key="diagnosed_with", type="diagnosed_with")

# treated_by: Diagnosis -> Prescription
for src, dst in [
    ("D-1", "RX-100"),
    ("D-1", "RX-101"),  # 한 진단에 처방 2개 (one-to-many)
    ("D-2", "RX-102"),
    ("D-3", "RX-103"),
    ("D-4", "RX-104"),
    ("D-5", "RX-105"),
]:
    G.add_edge(src, dst, key="treated_by", type="treated_by")

print("nodes:", G.number_of_nodes(), "edges:", G.number_of_edges())
print("D-4 는 treated_by 로 RX-104(refills=5) 만 가짐 →", list(G.successors("D-4")))
# 출력: nodes: 15 edges: 11
# 출력: D-4 는 treated_by 로 RX-104(refills=5) 만 가짐 → ['RX-104']

# %% [markdown]
# ## 2. MATCH — 3-hop 경로 열거
#
# ```
# (p:Patient)-[:diagnosed_with]->(d:Diagnosis)-[:treated_by]->(rx:Prescription)
# ```
#
# 문법을 조각으로 읽는다:
#
# | 조각 | 의미 |
# |---|---|
# | `(p:Patient)` | 소괄호 = **노드**. `p` 는 변수(바인딩 이름), `:Patient` 는 라벨/타입 제약 |
# | `-[:diagnosed_with]->` | 대괄호 = **관계**. `:diagnosed_with` 는 관계 타입, `->` 는 방향 |
# | `(d:Diagnosis)` | 중간 노드. `d` 로 바인딩해 WHERE/RETURN 에서 재사용 |
# | `-[:treated_by]->` | 두 번째 hop |
# | `(rx:Prescription)` | 종점 노드 |
#
# 노드가 3개이므로 **2 hop**(엣지 2개)이고, 노드까지 세면 3-노드 경로다.
# 관계에는 변수를 안 붙였다(`-[:treated_by]->`) — 관계 프로퍼티를 쓸 일이 없기 때문.
# 필요하면 `-[t:treated_by]->` 처럼 이름을 줄 수 있다.
#
# **방향이 왜 중요한가**: `->` 를 `<-` 로 바꾸면 "처방이 진단을 치료한다"는 반대 의미가 되어
# 매칭 결과가 0행이 된다. 온톨로지에서 `treated_by` 는 `Diagnosis → Prescription` 으로
# 선언됐으므로 진단 쪽에서 나가는 화살표만 존재한다.
#
# MATCH 의 출력은 하나의 노드가 아니라 **변수 → 노드** 바인딩 행들이다:
#
# $$R_0 \subseteq V_{\text{Patient}} \times V_{\text{Diagnosis}} \times V_{\text{Prescription}}$$

# %%
def out_edges_of_type(g, node, rel_type):
    """node 에서 나가는 rel_type 엣지의 목적지들 (화살표 방향 -> 을 그대로 구현)."""
    return [dst for _, dst, data in g.out_edges(node, data=True) if data["type"] == rel_type]


def match_pattern(g):
    """(p:Patient)-[:diagnosed_with]->(d:Diagnosis)-[:treated_by]->(rx:Prescription)"""
    rows = []
    for p in [n for n, a in g.nodes(data=True) if a["label"] == "Patient"]:  # (p:Patient)
        for d in out_edges_of_type(g, p, "diagnosed_with"):  # -[:diagnosed_with]->
            if g.nodes[d]["label"] != "Diagnosis":  # (d:Diagnosis) 라벨 제약
                continue
            for rx in out_edges_of_type(g, d, "treated_by"):  # -[:treated_by]->
                if g.nodes[rx]["label"] != "Prescription":  # (rx:Prescription)
                    continue
                rows.append({"p": p, "d": d, "rx": rx})
    return rows


R0 = match_pattern(G)
print(f"MATCH 결과: {len(R0)} 행")
for r in R0:
    print("   ", r["p"], "->", r["d"], "->", r["rx"])
# 출력: MATCH 결과: 6 행
# 출력:     P-001 -> D-1 -> RX-100
# 출력:     P-001 -> D-1 -> RX-101
# 출력:     P-001 -> D-2 -> RX-102
# 출력:     P-002 -> D-3 -> RX-103
# 출력:     P-003 -> D-4 -> RX-104
# 출력:     P-004 -> D-5 -> RX-105

# %% [markdown]
# 주의: `P-001` 이 **두 번** 나온다. 진단 `D-1` 에 처방이 2개(`RX-100`, `RX-101`)라
# 경로가 갈라졌기 때문이다. 그래프 질의의 결과는 "환자 목록"이 아니라 **경로 목록**이다.
# 환자 단위로 접고 싶으면 `RETURN DISTINCT p.patientId` 또는 집계를 써야 한다.
#
# ## 3. WHERE — 두 개의 술어를 AND 로 결합
#
# ```
# WHERE d.severity = 'severe' AND rx.refillsRemaining <= 1
# ```
#
# | 술어 | 바인딩 | 종류 | 의도 |
# |---|---|---|---|
# | `d.severity = 'severe'` | 중간 노드 `d` | 문자열 동등 비교 | 위험도 층화(risk stratification) — 중증만 |
# | `rx.refillsRemaining <= 1` | 종점 노드 `rx` | 정수 범위 비교 | 소진 임박 재고 |
#
# 두 조건이 **서로 다른 변수**에 걸린다는 게 핵심이다. MATCH 가 `p`, `d`, `rx` 를
# 한 행에 묶어 놨기 때문에, 경로를 따로 조인하지 않고도 진단 속성과 처방 속성을
# 같은 술어에서 함께 볼 수 있다.
#
# GQL/Cypher 에서 `=` 는 **비교** 연산자다(대입이 아니다). 문자열 리터럴은 작은따옴표.
# `severity` 는 온톨로지에서 string 타입이므로 `= 'severe'` 처럼 정확히 일치해야 하고,
# `'Severe'` 는 매칭되지 않는다(대소문자 구분).
#
# ### `<= 1` 을 쓰는 임상적 의도
#
# 원문 시나리오는 `refillsRemaining = 0` 을 예로 들었지만, 이 쿼리는 `<= 1` 을 쓴다.
#
# - `= 0` → 이미 **바닥난** 환자만. 발견 시점에 치료가 끊긴 상태 = 사후 대응.
# - `<= 1` → 0 과 1 을 함께. 마지막 리필 1회가 남은 환자까지 포함 = **사전 개입**.
#   중증 환자에게 약이 끊기는 것은 재입원·악화로 직결되므로, 처방 갱신 리드타임을
#   확보하려면 "곧 소진될" 구간을 미리 잡아야 한다.
# - `refillsRemaining` 이 정수 타입이라 이런 범위 비교가 가능하다. string 이었다면
#   사전식 비교로 떨어져 `"10" < "2"` 같은 오답이 나온다.
#
# 임계값 1 은 도메인 파라미터다. 갱신에 며칠 걸리는 전문의약품이라면 `<= 2` 로 넓힐 수 있다.

# %%
def where_clause(row, g):
    d_props = g.nodes[row["d"]]
    rx_props = g.nodes[row["rx"]]
    cond_severity = d_props["severity"] == "severe"  # d.severity = 'severe'
    cond_refills = rx_props["refillsRemaining"] <= 1  # rx.refillsRemaining <= 1
    return cond_severity and cond_refills, cond_severity, cond_refills


print(f"{'행':<22}{'severe?':<10}{'refills<=1?':<14}{'AND':<6}")
for r in R0:
    ok, c1, c2 = where_clause(r, G)
    path = f"{r['p']}/{r['d']}/{r['rx']}"
    print(f"{path:<22}{str(c1):<10}{str(c2):<14}{str(ok):<6}")

# 조건별로 몇 행이 살아남는지 (AND 가 왜 좁히는지 확인)
only_sev = [r for r in R0 if where_clause(r, G)[1]]
only_ref = [r for r in R0 if where_clause(r, G)[2]]
R1 = [r for r in R0 if where_clause(r, G)[0]]
print()
print(f"MATCH 전체                : {len(R0)} 행")
print(f"severity='severe' 만      : {len(only_sev)} 행")
print(f"refillsRemaining<=1 만    : {len(only_ref)} 행")
print(f"AND (WHERE 최종)          : {len(R1)} 행")
# 출력: 행                    severe?   refills<=1?   AND
# 출력: P-001/D-1/RX-100      True      True          True
# 출력: P-001/D-1/RX-101      True      False         False
# 출력: P-001/D-2/RX-102      False     True          False
# 출력: P-002/D-3/RX-103      True      True          True
# 출력: P-003/D-4/RX-104      True      False         False
# 출력: P-004/D-5/RX-105      False     True          False
# 출력:
# 출력: MATCH 전체                : 6 행
# 출력: severity='severe' 만      : 4 행
# 출력: refillsRemaining<=1 만    : 4 행
# 출력: AND (WHERE 최종)          : 2 행

# %% [markdown]
# 각 조건 단독으로는 4행이지만 AND 는 2행만 남긴다.
# 필터를 따로 돌려 교집합을 구하는 것과 결과가 같다:
#
# $$|R_1| = |\{severe\} \cap \{refills \le 1\}| = 2$$
#
# 탈락 이유를 하나씩 보면 술어의 역할이 분명해진다:
#
# - `P-001/D-1/RX-101` — 중증이지만 리필 3회 남음 → 아직 급하지 않다
# - `P-001/D-2/RX-102` — 리필 1회지만 moderate → 우선순위 낮다
# - `P-003/D-4/RX-104` — 중증 신부전이지만 리필 5회 → 여유 있다
# - `P-004/D-5/RX-105` — 리필 0회지만 mild(요통) → 진통제라 응급 아님
#
# ## 4. RETURN — 프로젝션
#
# ```
# RETURN p.patientId, d.description, rx.medication, rx.refillsRemaining
# ```
#
# 노드 전체를 돌려주지 않고 **프로퍼티 4개만** 뽑는다(projection).
# `p.patientId` 처럼 `변수.프로퍼티` 형태이고, 각 항목이 결과 테이블의 컬럼이 된다.
#
# 컬럼 선택에도 의도가 있다 — 이 결과는 그대로 **콜 리스트(call list)** 로 쓸 수 있다:
# 누구에게(`patientId`) 왜(`description`) 어떤 약을(`medication`)
# 얼마나 급하게(`refillsRemaining`) 연락할지가 한 행에 담긴다.
# `refillsRemaining` 은 WHERE 에서 이미 걸렀지만, 0 과 1 을 구분해 **우선순위**를
# 정하려면 값 자체가 필요하므로 RETURN 에 다시 등장한다.

# %%
def return_clause(rows, g):
    out = []
    for r in rows:
        out.append(
            {
                "p.patientId": g.nodes[r["p"]]["patientId"],
                "d.description": g.nodes[r["d"]]["description"],
                "rx.medication": g.nodes[r["rx"]]["medication"],
                "rx.refillsRemaining": g.nodes[r["rx"]]["refillsRemaining"],
            }
        )
    return out


R2 = return_clause(R1, G)

cols = ["p.patientId", "d.description", "rx.medication", "rx.refillsRemaining"]
widths = [max(len(c), *(len(str(row[c])) for row in R2)) + 2 for c in cols]
print("".join(c.ljust(w) for c, w in zip(cols, widths)))
print("".join("-" * (w - 2) + "  " for w in widths))
for row in sorted(R2, key=lambda r: r["rx.refillsRemaining"]):  # 급한 순
    print("".join(str(row[c]).ljust(w) for c, w in zip(cols, widths)))
print(f"\n최종: {len(R2)} 행  (MATCH {len(R0)} → WHERE {len(R1)} → RETURN {len(R2)})")
# 출력: p.patientId  d.description  rx.medication  rx.refillsRemaining
# 출력: -----------  -------------  -------------  -------------------
# 출력: P-001        Heart failure  Furosemide     0
# 출력: P-002        Severe asthma  Fluticasone    1
# 출력:
# 출력: 최종: 2 행  (MATCH 6 → WHERE 2 → RETURN 2)

# %% [markdown]
# RETURN 은 행 수를 바꾸지 않는다(집계나 DISTINCT 가 없으므로). 컬럼 폭만 줄인다.
# 전체 파이프라인의 행 수 변화:
#
# $$15\ \text{노드} \xrightarrow{\text{MATCH}} 6 \xrightarrow{\text{WHERE}} 2 \xrightarrow{\text{RETURN}} 2$$
#
# ## 5. 시각화 — 그래프에서 어느 경로가 살아남았나
#
# 왼쪽: 인스턴스 그래프. 매칭에 성공한 경로를 굵게 표시.
# 오른쪽: 단계별 잔존 행 수(퍼널).

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 계층 레이아웃: Patient(x=0), Diagnosis(x=1), Prescription(x=2)
COL_X = {"Patient": 0.0, "Diagnosis": 1.0, "Prescription": 2.0}
pos = {}
for label in COL_X:
    nodes_in_col = [n for n, a in G.nodes(data=True) if a["label"] == label]
    n = len(nodes_in_col)
    for i, nid in enumerate(nodes_in_col):
        pos[nid] = (COL_X[label], -(i - (n - 1) / 2))

matched_edges = set()
matched_nodes = set()
for r in R1:
    matched_edges.add((r["p"], r["d"]))
    matched_edges.add((r["d"], r["rx"]))
    matched_nodes.update([r["p"], r["d"], r["rx"]])

fig = make_subplots(
    rows=1,
    cols=2,
    column_widths=[0.66, 0.34],
    subplot_titles=(
        "인스턴스 그래프 — 굵은 경로가 WHERE 통과",
        "단계별 잔존 행 수",
    ),
    specs=[[{"type": "scatter"}, {"type": "bar"}]],
)

# 엣지: 매칭 여부로 두 그룹
for is_matched, color, width, dash in [(False, "#c8ccd4", 1.2, "dot"), (True, "#d1495b", 3.2, "solid")]:
    xs, ys = [], []
    for u, v, data in G.edges(data=True):
        if ((u, v) in matched_edges) != is_matched:
            continue
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        xs += [x0, x1, None]
        ys += [y0, y1, None]
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="lines",
            line=dict(color=color, width=width, dash=dash),
            hoverinfo="skip",
            name="매칭 경로" if is_matched else "비매칭 엣지",
        ),
        row=1,
        col=1,
    )

# 노드
SHAPE = {"Patient": "circle", "Diagnosis": "square", "Prescription": "diamond"}
BASE = {"Patient": "#2a6f97", "Diagnosis": "#e09f3e", "Prescription": "#468c98"}
for label in COL_X:
    nodes_in_col = [n for n, a in G.nodes(data=True) if a["label"] == label]
    texts, hovers, colors, lws, lcs = [], [], [], [], []
    for nid in nodes_in_col:
        a = G.nodes[nid]
        if label == "Diagnosis":
            texts.append(f"{nid}<br>{a['severity']}")
            hovers.append(f"{a['description']}<br>severity={a['severity']}<br>icd={a['icdCode']}")
        elif label == "Prescription":
            texts.append(f"{nid}<br>r={a['refillsRemaining']}")
            hovers.append(f"{a['medication']} {a['dosage']}<br>refillsRemaining={a['refillsRemaining']}")
        else:
            texts.append(nid)
            hovers.append(f"patientId={a['patientId']}<br>mrn={a['mrn']}")
        hit = nid in matched_nodes
        colors.append(BASE[label] if hit else "#eef1f4")
        lws.append(2.8 if hit else 1.0)
        lcs.append("#d1495b" if hit else "#b9bfc7")
    fig.add_trace(
        go.Scatter(
            x=[pos[n][0] for n in nodes_in_col],
            y=[pos[n][1] for n in nodes_in_col],
            mode="markers+text",
            marker=dict(
                size=40,
                symbol=SHAPE[label],
                color=colors,
                line=dict(color=lcs, width=lws),
            ),
            text=texts,
            textposition="middle center",
            textfont=dict(size=8, color="#111"),
            hovertext=hovers,
            hoverinfo="text",
            name=label,
        ),
        row=1,
        col=1,
    )

# 퍼널
stages = ["MATCH", "severe 만", "refills<=1 만", "WHERE(AND)", "RETURN"]
counts = [len(R0), len(only_sev), len(only_ref), len(R1), len(R2)]
fig.add_trace(
    go.Bar(
        x=stages,
        y=counts,
        text=[f"{c} 행" for c in counts],
        textposition="outside",
        marker_color=["#2a6f97", "#e09f3e", "#e09f3e", "#d1495b", "#d1495b"],
        showlegend=False,
    ),
    row=1,
    col=2,
)

fig.update_xaxes(visible=False, range=[-0.35, 2.35], row=1, col=1)
fig.update_yaxes(visible=False, range=[-3.1, 3.9], row=1, col=1)
fig.update_yaxes(range=[0, len(R0) + 1.5], row=1, col=2)
fig.update_layout(
    title="GQL 3단계 파이프라인: MATCH → WHERE → RETURN",
    template="plotly_white",
    width=1180,
    height=560,
    legend=dict(orientation="h", yanchor="bottom", y=-0.12, x=0),
    margin=dict(l=40, r=30, t=90, b=70),
)

# 컬럼 라벨 주석
for label, x in COL_X.items():
    fig.add_annotation(x=x, y=3.5, text=f"<b>{label}</b>", showarrow=False, font=dict(size=12), row=1, col=1)

_show(fig)
fig.write_image(str(HERE / "expy.png"), scale=2)
print("saved:", HERE / "expy.png")
# 출력: saved: .../expy.png

# %% [markdown]
# ## 6. 정리
#
# | 절 | 하는 일 | 이 예제에서 |
# |---|---|---|
# | `MATCH (p:Patient)-[:diagnosed_with]->(d:Diagnosis)-[:treated_by]->(rx:Prescription)` | 2-hop 경로를 열거해 `(p,d,rx)` 바인딩 행 생성 | 6 행 |
# | `WHERE d.severity = 'severe' AND rx.refillsRemaining <= 1` | 서로 다른 변수의 술어를 AND 결합 | 2 행 |
# | `RETURN p.patientId, d.description, rx.medication, rx.refillsRemaining` | 프로퍼티 4개 투영 | 2 행 × 4 컬럼 |
#
# 기억할 점:
#
# 1. **변수 바인딩**이 조인을 대신한다 — `p`, `d`, `rx` 가 한 행에 있으므로
#    환자·진단·처방 속성을 한 WHERE 에서 함께 본다.
# 2. **화살표 방향**은 온톨로지 선언(`Diagnosis → Prescription`)을 따라야 한다.
#    뒤집으면 0행.
# 3. **행 = 경로**, 행 ≠ 환자. 한 진단에 처방이 여럿이면 같은 환자가 여러 행에 나온다.
# 4. **`<= 1`** 은 "이미 끊긴" 환자(`= 0`)보다 한 걸음 앞서 개입하기 위한 임계값이며,
#    `refillsRemaining` 이 integer 타입이라 성립한다.
