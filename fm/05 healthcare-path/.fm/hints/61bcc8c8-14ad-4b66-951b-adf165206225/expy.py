# %% [markdown]
# # 관계의 부재를 쿼리하기 — anti-join으로 care gap 찾기
#
# Healthcare 온톨로지의 care chain은 다음과 같다.
#
# $$\text{Patient} \xrightarrow{\;diagnosed\_with\;} \text{Diagnosis} \xrightarrow{\;treated\_by\;} \text{Prescription}$$
#
# 대부분의 쿼리는 **경로가 있는 것**을 찾는다(`MATCH`). 하지만 임상적으로 가장
# 위험한 신호는 **경로가 끊긴 것**이다: `severity = 'severe'` 인데 `treated_by`
# out-edge가 하나도 없는 Diagnosis. 즉 "중증 진단은 내려졌지만 처방이 없는 환자".
#
# 집합으로 쓰면 이렇다. $R$ 을 `treated_by` 관계, $\pi_d(R)$ 을 그 관계에 등장하는
# Diagnosis 집합이라 할 때
#
# $$\text{CareGap} \;=\; \{\, d \in D \;:\; d.\text{severity} = \text{severe} \,\} \;\setminus\; \pi_d(R)$$
#
# 관계대수 용어로는 **anti-join** $D \triangleright R$ 이고,
# 반대편(치료가 연결된 케이스)은 **semi-join** $D \ltimes R$ 이다.
#
# $$D \;=\; (D \ltimes R) \;\uplus\; (D \triangleright R)$$
#
# 이 노트북은 networkx로 작은 인스턴스 그래프를 만들고, GQL의
# `WHERE NOT (d)-[:treated_by]->()` 를 순수 파이썬 anti-join으로 구현해 본다.

# %%
# 필요 패키지: networkx, plotly, kaleido (expy.png 저장용)
from collections import defaultdict

import networkx as nx
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


print("networkx", nx.__version__)
# 출력: networkx 3.2.1

# %% [markdown]
# ## 1. 인스턴스 그래프 만들기
#
# 온톨로지 스키마(5 entity / 6 relationship)의 일부를 그대로 인스턴스로 채운다.
# 노드에 `kind` 를 두어 타입을 구분하고, 엣지에 `rel` 로 관계 이름을 붙인다.
# 관계 이름을 엣지 속성으로 들고 있어야 나중에 `-[:treated_by]->` 처럼
# **특정 관계만** 골라 부재 검사를 할 수 있다.

# %%
G = nx.MultiDiGraph()

# --- Patient ---
G.add_node("P1", kind="Patient", mrn="MRN-0001", name="김민수", bloodType="A+")
G.add_node("P2", kind="Patient", mrn="MRN-0002", name="이서연", bloodType="O-")
G.add_node("P3", kind="Patient", mrn="MRN-0003", name="박준호", bloodType="B+")

# --- Provider ---
G.add_node("PR1", kind="Provider", name="정하늘", specialty="Cardiology", department="심장내과")
G.add_node("PR2", kind="Provider", name="최유진", specialty="Endocrinology", department="내분비내과")

# --- Diagnosis (icdCode / description / severity) ---
DIAGNOSES = [
    ("D1", "I21.9", "급성 심근경색", "severe"),
    ("D2", "E11.9", "2형 당뇨병", "moderate"),
    ("D3", "I50.9", "심부전", "severe"),
    ("D4", "J45.9", "천식", "mild"),
    ("D5", "N18.5", "만성 신장병 5기", "severe"),
    ("D6", "I10", "본태성 고혈압", "severe"),
]
for did, icd, desc, sev in DIAGNOSES:
    G.add_node(did, kind="Diagnosis", icdCode=icd, description=desc, severity=sev)

# --- Prescription (rxNumber / medication / refillsRemaining) ---
PRESCRIPTIONS = [
    ("RX1", "아스피린 100mg", 2),
    ("RX2", "메트포르민 500mg", 0),
    ("RX3", "리시노프릴 10mg", 1),
    ("RX4", "암로디핀 5mg", 3),
]
for rx, med, refills in PRESCRIPTIONS:
    G.add_node(rx, kind="Prescription", medication=med, refillsRemaining=refills)

# --- 관계 ---
EDGES = [
    # Patient -[:diagnosed_with]-> Diagnosis
    ("P1", "D1", "diagnosed_with"),
    ("P1", "D5", "diagnosed_with"),
    ("P2", "D2", "diagnosed_with"),
    ("P2", "D4", "diagnosed_with"),
    ("P2", "D6", "diagnosed_with"),
    ("P3", "D3", "diagnosed_with"),
    # Provider -[:diagnoses]-> Diagnosis
    ("PR1", "D1", "diagnoses"),
    ("PR1", "D3", "diagnoses"),
    ("PR1", "D5", "diagnoses"),
    ("PR1", "D6", "diagnoses"),
    ("PR2", "D2", "diagnoses"),
    ("PR2", "D4", "diagnoses"),
    # Diagnosis -[:treated_by]-> Prescription   ← 여기 부재가 care gap
    ("D1", "RX1", "treated_by"),
    ("D2", "RX2", "treated_by"),
    ("D6", "RX3", "treated_by"),
    ("D6", "RX4", "treated_by"),
    # Provider -[:prescribes]-> Prescription
    ("PR1", "RX1", "prescribes"),
    ("PR1", "RX3", "prescribes"),
    ("PR1", "RX4", "prescribes"),
    ("PR2", "RX2", "prescribes"),
]
for s, t, rel in EDGES:
    G.add_edge(s, t, rel=rel)

kinds = defaultdict(int)
for _, d in G.nodes(data=True):
    kinds[d["kind"]] += 1
print("노드:", dict(kinds), "| 엣지:", G.number_of_edges())
# 출력: 노드: {'Patient': 3, 'Provider': 2, 'Diagnosis': 6, 'Prescription': 4} | 엣지: 20

# %% [markdown]
# ## 2. 먼저 "있는 것"을 찾는 평범한 MATCH
#
# ```gql
# MATCH (p:Patient)-[:diagnosed_with]->(d:Diagnosis)-[:treated_by]->(rx:Prescription)
# WHERE d.severity = 'severe'
# RETURN p.patientId, d.description, rx.medication
# ```
#
# 이건 **inner join** 이다. 경로가 완성된 행만 살아남는다. 그래서 이 쿼리 결과만
# 보고 있으면 "치료가 안 된 환자"는 애초에 결과에 등장하지 않는다 — 문제가
# 조용히 사라진다. 이것이 부재 쿼리가 필요한 근본 이유다.

# %%
def out_rel(g, node, rel):
    """node 에서 나가는 rel 관계의 타깃 목록 (GQL의 -[:rel]->()에 해당)."""
    return [t for _, t, d in g.out_edges(node, data=True) if d["rel"] == rel]


def in_rel(g, node, rel):
    return [s for s, _, d in g.in_edges(node, data=True) if d["rel"] == rel]


severe = [n for n, d in G.nodes(data=True) if d["kind"] == "Diagnosis" and d["severity"] == "severe"]
print("severe 진단:", severe)
# 출력: severe 진단: ['D1', 'D3', 'D5', 'D6']

print("\n[MATCH] 경로가 완성된 행만 (inner join)")
for d in severe:
    for rx in out_rel(G, d, "treated_by"):
        pat = in_rel(G, d, "diagnosed_with")[0]
        print(f"  {G.nodes[pat]['name']:4s} | {G.nodes[d]['description']:12s} | {G.nodes[rx]['medication']}")
# 출력:
# [MATCH] 경로가 완성된 행만 (inner join)
#   김민수 | 급성 심근경색     | 아스피린 100mg
#   이서연 | 본태성 고혈압     | 리시노프릴 10mg
#   이서연 | 본태성 고혈압     | 암로디핀 5mg
# → D3(심부전), D5(만성 신장병)는 결과에서 완전히 사라졌다.

# %% [markdown]
# ## 3. semi-join vs anti-join
#
# 세 가지 표현이 모두 같은 결과를 낸다.
#
# | 패러다임 | 표현 |
# |---|---|
# | GQL / Cypher — 패턴 부정 | `WHERE NOT (d)-[:treated_by]->()` |
# | GQL / Cypher — OPTIONAL MATCH | `OPTIONAL MATCH (d)-[:treated_by]->(rx) WITH d, rx WHERE rx IS NULL` |
# | SQL — NOT EXISTS | `WHERE NOT EXISTS (SELECT 1 FROM treated_by t WHERE t.diagnosis_id = d.id)` |
#
# 파이썬으로는 `treated_by` 의 소스 쪽 projection $\pi_d(R)$ 을 **집합으로 한 번
# 만들어 두고** 차집합을 취하면 된다. 이것이 DB 엔진의 hash anti-join과 같은
# 전략이며, 비용은 중첩 루프 $O(|D|\cdot|R|)$ 에서 $O(|D|+|R|)$ 로 떨어진다.

# %%
# π_d(R): treated_by 관계에 소스로 등장하는 Diagnosis 집합 (해시 빌드 단계)
treated_index = {s for s, _, d in G.edges(data=True) if d["rel"] == "treated_by"}
print("π_d(treated_by) =", sorted(treated_index))
# 출력: π_d(treated_by) = ['D1', 'D2', 'D6']

severe_set = set(severe)
semi = sorted(severe_set & treated_index)  # D ⋉ R : 치료가 연결된 중증
anti = sorted(severe_set - treated_index)  # D ▷ R : 치료가 없는 중증 = care gap

print("semi-join (치료 있음):", semi)
print("anti-join (치료 없음 = care gap):", anti)
print("분할 검증:", set(semi) | set(anti) == severe_set, "|", set(semi) & set(anti) == set())
# 출력:
# semi-join (치료 있음): ['D1', 'D6']
# anti-join (치료 없음 = care gap): ['D3', 'D5']
# 분할 검증: True | True

# %% [markdown]
# ### 관계 이름과 severity 조건을 함께 거는 실제 쿼리
#
# ```gql
# MATCH (p:Patient)-[:diagnosed_with]->(d:Diagnosis)
# WHERE d.severity = 'severe' AND NOT (d)-[:treated_by]->()
# RETURN p.mrn, p.patientId, d.icdCode, d.description
# ```
#
# 주의: `NOT (d)-[:treated_by]->()` 의 `()` 는 **어떤 타깃이든**을 뜻한다.
# 관계 이름을 생략하면 `prescribes` 같은 다른 관계까지 세어 gap을 놓친다.

# %%
print("[ANTI-JOIN] 미처리 중증 진단 — 임상 워크리스트")
print(f"{'MRN':10s} {'환자':6s} {'ICD':8s} {'진단':16s} {'담당의':6s} {'전문과':6s}")
rows = []
for d in anti:
    pat = in_rel(G, d, "diagnosed_with")[0]
    prov = in_rel(G, d, "diagnoses")[0]
    nd, np_, npr = G.nodes[d], G.nodes[pat], G.nodes[prov]
    rows.append((np_["mrn"], np_["name"], nd["icdCode"], nd["description"], npr["name"], npr["department"]))
    print(f"{np_['mrn']:10s} {np_['name']:6s} {nd['icdCode']:8s} {nd['description']:16s} {npr['name']:6s} {npr['department']:6s}")
# 출력:
# [ANTI-JOIN] 미처리 중증 진단 — 임상 워크리스트
# MRN        환자     ICD      진단               담당의    전문과
# MRN-0003   박준호      I50.9    심부전                정하늘      심장내과
# MRN-0001   김민수      N18.5    만성 신장병 5기          정하늘      심장내과
# → provider까지 함께 뽑히기 때문에 "누구에게 알릴지"가 바로 정해진다.

# %% [markdown]
# ## 4. OPTIONAL MATCH = LEFT OUTER JOIN 관점
#
# anti-join은 "left outer join 후 오른쪽이 NULL인 행"과 같다. 전체 표를 한 번
# 만들어 보면 부재가 왜 **데이터의 한 값**으로 취급되는지 보인다.
#
# $$\text{AntiJoin} \;=\; \sigma_{rx = \text{NULL}}\bigl(D \mathbin{⟕} R\bigr)$$

# %%
print(f"{'dx':4s} {'severity':9s} {'처방(rx)':16s} {'gap?':5s}")
for did, icd, desc, sev in DIAGNOSES:
    rxs = out_rel(G, did, "treated_by") or [None]  # OPTIONAL MATCH: 없으면 NULL 한 행
    for rx in rxs:
        label = G.nodes[rx]["medication"] if rx else "NULL"
        gap = "◀ GAP" if (rx is None and sev == "severe") else ""
        print(f"{did:4s} {sev:9s} {label:16s} {gap}")
# 출력:
# dx   severity  처방(rx)          gap?
# D1   severe    아스피린 100mg
# D2   moderate  메트포르민 500mg
# D3   severe    NULL             ◀ GAP
# D4   mild      NULL
# D5   severe    NULL             ◀ GAP
# D6   severe    리시노프릴 10mg
# D6   severe    암로디핀 5mg
# → D4도 NULL이지만 severity 필터 때문에 gap이 아니다.
#   "부재"만으로는 부족하고 "있어야 했는가"라는 기준(severe)이 함께 필요하다.

# %% [markdown]
# ## 5. care gap analysis — 임상 품질 지표로 승격시키기
#
# 임상 품질 측정(HEDIS, CMS Star Ratings 등)은 언제나
# **분모(denominator) = 치료 대상 모집단**, **분자(numerator) = 실제로 치료를
# 받은 사람** 형태로 정의된다. anti-join은 정확히 그 차이를 뽑아낸다.
#
# $$\text{GapRate} \;=\; \frac{|D_{\text{severe}} \triangleright R|}{|D_{\text{severe}}|}
#   \;=\; 1 - \frac{|D_{\text{severe}} \ltimes R|}{|D_{\text{severe}}|}$$
#
# 즉 부재 쿼리는 "버그 리스트"가 아니라 **측정 가능한 지표**가 된다.

# %%
by_sev = defaultdict(lambda: {"total": 0, "treated": 0})
for did, icd, desc, sev in DIAGNOSES:
    by_sev[sev]["total"] += 1
    if did in treated_index:
        by_sev[sev]["treated"] += 1

print(f"{'severity':9s} {'분모':>4s} {'분자':>4s} {'gap':>4s} {'gap rate':>9s}")
for sev in ("severe", "moderate", "mild"):
    s = by_sev[sev]
    gap_n = s["total"] - s["treated"]
    print(f"{sev:9s} {s['total']:4d} {s['treated']:4d} {gap_n:4d} {gap_n / s['total']:8.0%}")
# 출력:
# severity   분모   분자  gap  gap rate
# severe       4    2    2      50%
# moderate     1    1    0       0%
# mild         1    0    1     100%

sev_stat = by_sev["severe"]
print(f"\n중증 미처리율 = {(sev_stat['total'] - sev_stat['treated']) / sev_stat['total']:.0%} → 개선 목표 지표")
# 출력: 중증 미처리율 = 50% → 개선 목표 지표

# %% [markdown]
# ## 6. 흔한 함정 두 가지
#
# 1. **부재 ≠ 진짜 누락.** 처방이 정말 없는 것인지, 약국 시스템 연동이 끊겨
#    엣지가 적재되지 않은 것인지 구분해야 한다. property graph는 보통
#    닫힌 세계(closed world) 가정을 쓰므로 "모르는 것"과 "없는 것"을 같게
#    취급한다. OWL 같은 열린 세계(open world) 모델에서는 부재를 곧바로
#    거짓으로 결론 내릴 수 없다.
# 2. **관계 방향과 이름을 흘리면 오탐.** 방향을 빼면(`-[:treated_by]-`)
#    엉뚱한 매칭이 생기고, 이름을 빼면 다른 관계가 gap을 덮어 위험한
#    거짓 음성(false negative)이 된다.

# %%
# 방향을 흘렸을 때: in-edge(diagnoses / diagnosed_with)까지 세면 gap이 사라진다
undirected_wrong = sorted(severe_set - {n for n in G.nodes if G.degree(n) > 0})
print("방향 무시 -[:treated_by]- :", undirected_wrong, "→ gap 전멸 (false negative)")
# 출력: 방향 무시 -[:treated_by]- : [] → gap 전멸 (false negative)

# 관계 이름을 흘렸을 때: Diagnosis에 다른 out-relation이 하나 생기면 즉시 무너진다.
H = G.copy()
H.add_edge("D3", "D5", rel="comorbid_with")  # 치료와 무관한 관계 하나 추가
loose = sorted(severe_set - {n for n in H.nodes if H.out_degree(n) > 0})
strict = sorted(severe_set - {s for s, _, d in H.edges(data=True) if d["rel"] == "treated_by"})
print("관계명 생략 -->() :", loose)
print("관계명 명시 -[:treated_by]->() :", strict)
print("→ 놓친 gap:", sorted(set(strict) - set(loose)))
# 출력:
# 관계명 생략 -->() : ['D5']
# 관계명 명시 -[:treated_by]->() : ['D3', 'D5']
# → 놓친 gap: ['D3']

# %% [markdown]
# ## 7. 시각화 — 끊긴 care chain
#
# 왼쪽은 인스턴스 그래프. 빨간 X로 끝나는 점선은 **존재하지 않는 엣지**,
# 즉 anti-join이 잡아낸 gap이다. 오른쪽은 severity별 분모/분자 스택.

# %%
POS = {
    "P1": (0, 3.0), "P2": (0, 2.0), "P3": (0, 1.0),
    "PR1": (0, -0.6), "PR2": (0, -1.6),
    "D1": (1, 3.4), "D2": (1, 2.4), "D3": (1, 1.4),
    "D4": (1, 0.4), "D5": (1, -0.8), "D6": (1, -1.8),
    "RX1": (2, 3.2), "RX2": (2, 2.2), "RX3": (2, 0.6), "RX4": (2, -0.4),
}

fig = make_subplots(
    rows=1, cols=2, column_widths=[0.66, 0.34],
    subplot_titles=("인스턴스 그래프: treated_by 부재 = care gap", "severity별 치료 커버리지"),
)

EDGE_STYLE = {
    "diagnosed_with": ("#5b6b7c", 2.0, "solid"),
    "treated_by": ("#1f9d55", 2.6, "solid"),
    "diagnoses": ("#b8c2cc", 1.2, "dot"),
    "prescribes": ("#b8c2cc", 1.2, "dot"),
}
for rel, (color, width, dash) in EDGE_STYLE.items():
    xs, ys = [], []
    for s, t, dd in G.edges(data=True):
        if dd["rel"] != rel:
            continue
        (x0, y0), (x1, y1) = POS[s], POS[t]
        xs += [x0, x1, None]
        ys += [y0, y1, None]
    fig.add_trace(
        go.Scatter(x=xs, y=ys, mode="lines", name=rel, legendgroup=rel,
                   line=dict(color=color, width=width, dash=dash), hoverinfo="skip"),
        row=1, col=1,
    )

# 존재하지 않는 treated_by 를 명시적으로 그린다 (부재의 시각화)
gx, gy, mx, my = [], [], [], []
for d in anti:
    x0, y0 = POS[d]
    gx += [x0, x0 + 0.62, None]
    gy += [y0, y0, None]
    mx.append(x0 + 0.62)
    my.append(y0)
fig.add_trace(
    go.Scatter(x=gx, y=gy, mode="lines", name="treated_by 부재",
               line=dict(color="#e3342f", width=2.4, dash="dash"), hoverinfo="skip"),
    row=1, col=1,
)
fig.add_trace(
    go.Scatter(x=mx, y=my, mode="markers+text", showlegend=False,
               marker=dict(symbol="x-thin", size=14, line=dict(color="#e3342f", width=3)),
               text=["처방 없음"] * len(mx), textposition="middle right",
               textfont=dict(color="#e3342f", size=10), hoverinfo="skip"),
    row=1, col=1,
)

others = [did for did, _, _, sev in DIAGNOSES if sev != "severe"]
GROUPS = [
    ("Patient", [n for n, d in G.nodes(data=True) if d["kind"] == "Patient"], "#3490dc", "circle"),
    ("Provider", [n for n, d in G.nodes(data=True) if d["kind"] == "Provider"], "#9561e2", "diamond"),
    ("Prescription", [n for n, d in G.nodes(data=True) if d["kind"] == "Prescription"], "#38c172", "square"),
    ("Diagnosis (severe, 치료 O)", semi, "#f6993f", "circle"),
    ("Diagnosis (severe, 치료 X)", anti, "#e3342f", "circle"),
    ("Diagnosis (기타 severity)", others, "#a0aec0", "circle"),
]

for name, nodes, color, symbol in GROUPS:
    labels, hovers = [], []
    for n in nodes:
        nd = G.nodes[n]
        labels.append(nd.get("name") or nd.get("description") or nd.get("medication") or n)
        hovers.append("<br>".join(f"{k}={v}" for k, v in nd.items()))
    fig.add_trace(
        go.Scatter(
            x=[POS[n][0] for n in nodes], y=[POS[n][1] for n in nodes],
            mode="markers+text", name=name,
            marker=dict(size=20, color=color, line=dict(color="#2d3748", width=1.2), symbol=symbol),
            text=labels, textposition="top center", textfont=dict(size=10),
            hovertext=hovers, hoverinfo="text",
        ),
        row=1, col=1,
    )

sev_order = ["severe", "moderate", "mild"]
fig.add_trace(
    go.Bar(x=sev_order, y=[by_sev[s]["treated"] for s in sev_order],
           name="치료 연결됨 (분자)", marker_color="#38c172"),
    row=1, col=2,
)
fig.add_trace(
    go.Bar(x=sev_order, y=[by_sev[s]["total"] - by_sev[s]["treated"] for s in sev_order],
           name="care gap", marker_color="#e3342f"),
    row=1, col=2,
)

fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, row=1, col=1)
fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False, row=1, col=1)
fig.update_xaxes(title_text="severity", title_standoff=6, row=1, col=2)
fig.update_yaxes(title_text="Diagnosis 수", dtick=1, row=1, col=2)
fig.update_layout(
    barmode="stack", template="plotly_white", height=720, width=1250,
    title="관계의 부재 쿼리: NOT (d)-[:treated_by]->() 로 미처리 중증 진단 찾기",
    legend=dict(orientation="h", yanchor="top", y=-0.13, x=0),
    margin=dict(l=40, r=40, t=80, b=170),
)

_show(fig)

try:
    fig.write_image("expy.png", scale=2)
    print("expy.png 저장 완료")
except Exception as exc:  # kaleido 미설치 등
    print("이미지 저장 건너뜀:", exc)
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# - `MATCH` 만으로는 **끊긴 경로가 결과에서 사라진다**. 부재 조건
#   (`NOT (d)-[:treated_by]->()`, `NOT EXISTS`, `OPTIONAL MATCH ... IS NULL`)이
#   있어야 누락을 볼 수 있다.
# - 구현은 anti-join: 대상 관계의 projection $\pi_d(R)$ 을 해시 집합으로 만들고
#   차집합을 취한다 → $O(|D|+|R|)$.
# - 온톨로지가 있으면 "**있어야 할 관계**"가 스키마로 선언되어 있으므로,
#   무엇의 부재를 물어야 하는지가 명확해진다. severity 같은 속성이 분모를
#   정의해 주어 gap이 **임상적으로 의미 있는** 집합이 된다.
# - 결과는 단순 목록이 아니라 care gap analysis 지표
#   ($\text{GapRate} = |D \triangleright R| / |D|$)로 승격되어, 워크리스트와
#   품질 개선 목표를 동시에 만들어 낸다.
