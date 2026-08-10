# %% [markdown]
# # hub entity가 왜 강력한가 — Fourth Coffee 그래프로 정량 확인
#
# 카드 주장: **hub entity(Shipment)는 원래 연결되지 않던 그래프의 부분들을 이어 주고,
# 그 결과 도메인을 넘나드는 순회 질의가 가능해진다.**
#
# 이 스크립트는 그 주장을 "느낌"이 아니라 숫자로 확인한다.
#
# * 엔티티 타입 6개: `Customer, Order, Product, Store, Supplier, Shipment`
# * 관계 7개: `places, contains, processedAt, sourcedFrom, sentBy, deliveredTo, carries`
#
# Shipment가 들고 오는 관계는 `sentBy / deliveredTo / carries` 3개다.
# 이 3개를 넣기 전/후로
#
# 1. 타입 수준 최단거리 행렬과 절단점(cut vertex)
# 2. 인스턴스 수준 `Supplier → Store` 최단 경로 길이
# 3. hub를 지나는 길이 $\le 3$ 경로 수 (= fan-out 비용)
#
# 를 각각 비교한다.
#
# 필요 패키지: plotly, kaleido  (그래프 알고리즘은 표준 라이브러리 BFS로 직접 구현)

# %%
from collections import deque
from itertools import combinations

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1. 타입 수준 온톨로지 정의
#
# 관계를 `(from, to, name)` 엣지 리스트로 둔다.
# 순회 질의는 방향과 무관하게 양방향으로 걸을 수 있으므로(`<-[:sentBy]-` 처럼)
# 도달성 계산은 무향 그래프로 한다.

# %%
TYPES_RETAIL = ["Customer", "Order", "Product", "Store"]
TYPES_SOURCING = ["Product", "Supplier"]

# Shipment 없이 존재하는 관계 (Step 1~2 + sourcedFrom)
BASE_RELS = [
    ("Customer", "Order", "places"),  # 1:N
    ("Order", "Product", "contains"),  # N:M
    ("Order", "Store", "processedAt"),  # N:1
    ("Product", "Supplier", "sourcedFrom"),  # N:1
]

# hub entity Shipment가 들고 오는 관계
HUB_RELS = [
    ("Shipment", "Supplier", "sentBy"),  # N:1
    ("Shipment", "Store", "deliveredTo"),  # N:1
    ("Shipment", "Product", "carries"),  # N:M
]

BASE_TYPES = ["Customer", "Order", "Product", "Store", "Supplier"]
FULL_TYPES = BASE_TYPES + ["Shipment"]


def to_adj(nodes, rels):
    adj = {n: set() for n in nodes}
    for a, b, _ in rels:
        adj[a].add(b)
        adj[b].add(a)
    return adj


ADJ_BEFORE = to_adj(BASE_TYPES, BASE_RELS)
ADJ_AFTER = to_adj(FULL_TYPES, BASE_RELS + HUB_RELS)

print("before:", {k: sorted(v) for k, v in ADJ_BEFORE.items()})
print("after :", {k: sorted(v) for k, v in ADJ_AFTER.items()})
# 출력: before: {'Customer': ['Order'], 'Order': ['Customer', 'Product', 'Store'], 'Product': ['Order', 'Supplier'], 'Store': ['Order'], 'Supplier': ['Product']}
# 출력: after : {'Customer': ['Order'], 'Order': ['Customer', 'Product', 'Store'], 'Product': ['Order', 'Shipment', 'Supplier'], 'Store': ['Order', 'Shipment'], 'Supplier': ['Product', 'Shipment'], 'Shipment': ['Product', 'Store', 'Supplier']}


# %% [markdown]
# ## 2. BFS 최단거리 / 연결요소
#
# 두 엔티티 타입 $u, v$ 사이 최단거리를 $d(u,v)$ 라 하면,
# 순회 질의의 "길이"는 곧 $d(u,v)$ 홉이다.
# hub의 효과는 $\sum_{u<v} d(u,v)$ 가 줄어드는 것으로 나타난다.

# %%
def bfs(adj, src, banned=()):
    banned = set(banned)
    if src in banned:
        return {}
    dist = {src: 0}
    q = deque([src])
    while q:
        cur = q.popleft()
        for nxt in adj[cur]:
            if nxt in banned or nxt in dist:
                continue
            dist[nxt] = dist[cur] + 1
            q.append(nxt)
    return dist


def pair_stats(adj):
    nodes = list(adj)
    total, reach, worst, dists = 0, 0, 0, {}
    for u, v in combinations(nodes, 2):
        d = bfs(adj, u).get(v)
        dists[(u, v)] = d
        total += 1
        if d is not None:
            reach += 1
            worst = max(worst, d)
    return dists, total, reach, worst


def components(adj):
    seen, comps = set(), []
    for n in adj:
        if n in seen:
            continue
        c = sorted(bfs(adj, n))
        seen.update(c)
        comps.append(c)
    return comps


D_BEFORE, T_B, R_B, W_B = pair_stats(ADJ_BEFORE)
D_AFTER, T_A, R_A, W_A = pair_stats(ADJ_AFTER)

print(f"[before] 타입 {len(BASE_TYPES)}개, 엣지 {len(BASE_RELS)}개")
print(f"  도달 가능 타입쌍 {R_B}/{T_B}, 최장 홉 {W_B}, 거리합 {sum(D_BEFORE.values())}")
print(f"[after ] 타입 {len(FULL_TYPES)}개, 엣지 {len(BASE_RELS) + len(HUB_RELS)}개")
print(f"  도달 가능 타입쌍 {R_A}/{T_A}, 최장 홉 {W_A}, 거리합 {sum(D_AFTER.values())}")
# 출력: [before] 타입 5개, 엣지 4개
# 출력:   도달 가능 타입쌍 10/10, 최장 홉 3, 거리합 18
# 출력: [after ] 타입 6개, 엣지 7개
# 출력:   도달 가능 타입쌍 15/15, 최장 홉 3, 거리합 25

# %%
# 2홉 이내로 걸을 수 있는 타입쌍의 비율 = "질의가 짧게 끝나는" 비율
short_b = sum(1 for d in D_BEFORE.values() if d is not None and d <= 2)
short_a = sum(1 for d in D_AFTER.values() if d is not None and d <= 2)
print(f"d<=2 타입쌍: before {short_b}/{T_B} = {short_b / T_B:.0%},  after {short_a}/{T_A} = {short_a / T_A:.0%}")
print()
print("Supplier-Store 최단거리:")
print("  before =", bfs(ADJ_BEFORE, "Supplier")["Store"], "홉  (Supplier-Product-Order-Store)")
print("  after  =", bfs(ADJ_AFTER, "Supplier")["Store"], "홉  (Supplier-Shipment-Store)")
# 출력: d<=2 타입쌍: before 8/10 = 80%,  after 13/15 = 87%
# 출력: Supplier-Store 최단거리:
# 출력:   before = 3 홉  (Supplier-Product-Order-Store)
# 출력:   after  = 2 홉  (Supplier-Shipment-Store)

# %% [markdown]
# ## 3. Product는 절단점이었다 — hub가 그 병목을 없앤다
#
# hub 이전 그래프에서 소싱 쪽(`Product–Supplier`)과 리테일 쪽(`Customer–Order–Product–Store`)은
# **오직 Product를 통해서만** 만난다. 즉 Product는 절단점(cut vertex)이다.
# Product를 지우면 Supplier가 그래프에서 떨어져 나간다.
#
# Shipment를 넣으면 `Supplier–Shipment–Store` 라는 **우회로**가 생겨서 Product는 더 이상 절단점이 아니다.
# 이것이 "원래 연결되지 않던 부분을 이어 준다"의 정확한 의미다.

# %%
def cut_vertices(adj):
    base = len(components(adj))
    out = []
    for n in adj:
        rest = {k: (v - {n}) for k, v in adj.items() if k != n}
        if len(components(rest)) > base:
            out.append(n)
    return sorted(out)


print("before 절단점:", cut_vertices(ADJ_BEFORE))
print("after  절단점:", cut_vertices(ADJ_AFTER))
for probe in ["Product", "Order"]:
    b = components({k: v - {probe} for k, v in ADJ_BEFORE.items() if k != probe})
    a = components({k: v - {probe} for k, v in ADJ_AFTER.items() if k != probe})
    print(f"  {probe} 제거 -> before {len(b)}개 컴포넌트 {b} / after {len(a)}개 컴포넌트 {a}")
# 출력: before 절단점: ['Order', 'Product']
# 출력: after  절단점: ['Order']
# 출력:   Product 제거 -> before 2개 컴포넌트 [['Customer', 'Order', 'Store'], ['Supplier']] / after 1개 컴포넌트 [['Customer', 'Order', 'Shipment', 'Store', 'Supplier']]
# 출력:   Order 제거 -> before 3개 컴포넌트 [['Customer'], ['Product', 'Supplier'], ['Store']] / after 2개 컴포넌트 [['Customer'], ['Product', 'Shipment', 'Store', 'Supplier']]

# %% [markdown]
# ## 4. 인스턴스 수준: 3홉 우회로는 "다른 질문"에 답한다
#
# 타입 수준에서 `Supplier → Store` 가 3홉으로 이어져 있다고 해서 같은 질문에 답하는 게 아니다.
#
# * hub 이전 경로 `Supplier ← Product ← Order → Store` 는
#   "그 공급업체의 상품이 **팔린** 매장"을 뜻한다.
# * hub 이후 경로 `Supplier ← Shipment → Store` 는
#   "그 공급업체가 **배송한** 매장"을 뜻한다.
#
# 두 집합은 다르다. 아래에서 실제로 어긋나는 쌍을 뽑아 본다.

# %%
SUPPLIERS = {
    "SUP-1": {"name": "Andes Beans", "country": "Colombia", "certification": "Fair Trade", "rating": 4.6},
    "SUP-2": {"name": "Sidamo Co-op", "country": "Ethiopia", "certification": "Organic", "rating": 4.9},
    "SUP-3": {"name": "Mekong Foods", "country": "Vietnam", "certification": "None", "rating": 3.8},
}
PRODUCTS = {
    "PRD-1": {"name": "Espresso Blend", "category": "Espresso", "isOrganic": True, "supplier": "SUP-2"},
    "PRD-2": {"name": "Cold Brew", "category": "Cold Brew", "isOrganic": False, "supplier": "SUP-1"},
    "PRD-3": {"name": "Muffin", "category": "Food", "isOrganic": False, "supplier": "SUP-3"},
    "PRD-4": {"name": "Green Tea", "category": "Tea", "isOrganic": True, "supplier": "SUP-2"},
}
STORES = {
    "STR-1": {"name": "Pike Place", "city": "Seattle", "state": "WA", "capacity": 60},
    "STR-2": {"name": "Mission", "city": "San Francisco", "state": "CA", "capacity": 120},
    "STR-3": {"name": "Pearl", "city": "Portland", "state": "OR", "capacity": 40},
}
CUSTOMERS = {"CUS-1": {"tier": "Gold"}, "CUS-2": {"tier": "Silver"}, "CUS-3": {"tier": "Bronze"}}
ORDERS = {
    "ORD-1": {"customer": "CUS-1", "store": "STR-1", "products": ["PRD-1", "PRD-3"]},
    "ORD-2": {"customer": "CUS-2", "store": "STR-2", "products": ["PRD-2"]},
    "ORD-3": {"customer": "CUS-1", "store": "STR-2", "products": ["PRD-1", "PRD-4"]},
    "ORD-4": {"customer": "CUS-3", "store": "STR-3", "products": ["PRD-3"]},
}
# hub entity: 자기 식별자(shipmentId)와 자기 속성(dispatchDate/status/weight)을 가진다
SHIPMENTS = {
    "SHP-1": {"supplier": "SUP-2", "store": "STR-1", "products": ["PRD-1", "PRD-4"],
              "dispatchDate": "2026-03-02", "status": "Delivered", "weight": 120.0},
    "SHP-2": {"supplier": "SUP-1", "store": "STR-2", "products": ["PRD-2"],
              "dispatchDate": "2026-03-05", "status": "Delayed", "weight": 80.0},
    "SHP-3": {"supplier": "SUP-3", "store": "STR-3", "products": ["PRD-3"],
              "dispatchDate": "2026-03-07", "status": "In Transit", "weight": 45.0},
    "SHP-4": {"supplier": "SUP-2", "store": "STR-2", "products": ["PRD-1"],
              "dispatchDate": "2026-03-09", "status": "Delayed", "weight": 200.0},
}


def build_instance_graph(with_hub):
    adj = {k: set() for k in [*CUSTOMERS, *ORDERS, *PRODUCTS, *STORES, *SUPPLIERS]}

    def link(a, b):
        adj[a].add(b)
        adj[b].add(a)

    for oid, o in ORDERS.items():
        link(o["customer"], oid)  # places
        link(oid, o["store"])  # processedAt
        for p in o["products"]:  # contains
            link(oid, p)
    for pid, p in PRODUCTS.items():
        link(pid, p["supplier"])  # sourcedFrom
    if with_hub:
        for sid in SHIPMENTS:
            adj[sid] = set()
        for sid, s in SHIPMENTS.items():
            link(sid, s["supplier"])  # sentBy
            link(sid, s["store"])  # deliveredTo
            for p in s["products"]:  # carries
                link(sid, p)
    return adj


G_BEFORE = build_instance_graph(False)
G_AFTER = build_instance_graph(True)
print("인스턴스 노드 수: before", len(G_BEFORE), "/ after", len(G_AFTER))
print("엣지 수: before", sum(len(v) for v in G_BEFORE.values()) // 2,
      "/ after", sum(len(v) for v in G_AFTER.values()) // 2)
# 출력: 인스턴스 노드 수: before 17 / after 21
# 출력: 엣지 수: before 18 / after 31

# %%
# Supplier x Store 최단거리 행렬 비교
print("Supplier → Store 최단 홉수 (before / after)")
header = "        " + "".join(f"{s:>10}" for s in STORES)
print(header)
before_pairs, after_pairs = set(), set()
for sup in SUPPLIERS:
    db, da = bfs(G_BEFORE, sup), bfs(G_AFTER, sup)
    row = f"{sup:>8}"
    for st in STORES:
        b, a = db.get(st), da.get(st)
        if b is not None and b <= 3:  # Supplier<-Product<-Order->Store 우회로
            before_pairs.add((sup, st))
        if a is not None and a <= 2:  # Supplier<-Shipment->Store 직행
            after_pairs.add((sup, st))
        row += f"{str(b) + '/' + str(a):>10}"
    print(row)
print("2홉 직행(=실제로 배송한 매장) 쌍:", len(after_pairs), sorted(after_pairs))
print("3홉 우회(=상품이 팔린 매장) 쌍  :", len(before_pairs), sorted(before_pairs))
print("우회로가 잘못 이어 준 쌍(배송 사실 없음):", sorted(before_pairs - after_pairs))
print("우회로가 놓친 쌍(배송했으나 아직 안 팔림):", sorted(after_pairs - before_pairs))
# 출력: Supplier → Store 최단 홉수 (before / after)
# 출력:              STR-1     STR-2     STR-3
# 출력:    SUP-1       7/6       3/2       9/8
# 출력:    SUP-2       3/2       3/2       5/5
# 출력:    SUP-3       3/3       5/5       3/2
# 출력: 2홉 직행(=실제로 배송한 매장) 쌍: 4 [('SUP-1','STR-2'), ('SUP-2','STR-1'), ('SUP-2','STR-2'), ('SUP-3','STR-3')]
# 출력: 3홉 우회(=상품이 팔린 매장) 쌍  : 5 [('SUP-1','STR-2'), ('SUP-2','STR-1'), ('SUP-2','STR-2'), ('SUP-3','STR-1'), ('SUP-3','STR-3')]
# 출력: 우회로가 잘못 이어 준 쌍(배송 사실 없음): [('SUP-3', 'STR-1')]
# 출력: 우회로가 놓친 쌍(배송했으나 아직 안 팔림): []
#
# 읽는 법: hub 없이는 SUP-1→STR-1이 7홉(다른 매장·주문을 헤집고 돌아가는 무의미한 경로)이고,
# 3홉 우회로는 (SUP-3, STR-1)처럼 "배송한 적 없는" 쌍을 잘못 이어 준다.
# hub가 있으면 실제 배송 관계 4쌍이 정확히 2홉으로 떨어진다.

# %% [markdown]
# ## 5. hub가 열어 주는 질의 클래스
#
# 아래 3개는 Shipment 없이는 **아예 표현할 수 없던** 질문이다.
# (Shipment의 자기 속성 `status` / `weight` 가 있어야 성립한다는 점이 핵심)

# %%
# Q1. 지연 배송을 받은 매장  —  Shipment(status='Delayed') -> Store
q1 = sorted({STORES[s["store"]]["name"] for s in SHIPMENTS.values() if s["status"] == "Delayed"})
print("Q1 지연 배송을 받은 매장:", q1)

# Q2. 인증 공급업체가 공급하는 대형 매장 — Supplier <- Shipment -> Store(capacity>=100)
q2 = sorted({
    (SUPPLIERS[s["supplier"]]["certification"], SUPPLIERS[s["supplier"]]["name"], STORES[s["store"]]["name"])
    for s in SHIPMENTS.values()
    if SUPPLIERS[s["supplier"]]["certification"] != "None" and STORES[s["store"]]["capacity"] >= 100
})
print("Q2 인증 공급업체 -> 대형 매장:", q2)

# Q3. 배송 중량 기준 매장별 부담 — Shipment.weight 를 Store 로 집계
q3 = {}
for s in SHIPMENTS.values():
    q3[STORES[s["store"]]["name"]] = q3.get(STORES[s["store"]]["name"], 0.0) + s["weight"]
print("Q3 매장별 누적 배송 중량(kg):", dict(sorted(q3.items(), key=lambda kv: -kv[1])))
# 출력: Q1 지연 배송을 받은 매장: ['Mission']
# 출력: Q2 인증 공급업체 -> 대형 매장: [('Fair Trade', 'Andes Beans', 'Mission'), ('Organic', 'Sidamo Co-op', 'Mission')]
# 출력: Q3 매장별 누적 배송 중량(kg): {'Mission': 280.0, 'Pike Place': 120.0, 'Pearl': 45.0}

# %% [markdown]
# ## 6. 비용: hub는 fan-out을 키운다
#
# hub의 차수(degree)는 구조적으로 크다. Shipment 노드는 항상
# $1(\text{supplier}) + 1(\text{store}) + k(\text{products})$ 개의 엣지를 갖고,
# Supplier·Store 쪽에서 보면 자신에게 붙는 Shipment 수만큼 분기가 늘어난다.
#
# 길이 $\le L$ 인 단순 경로 수는 대략 $\prod \deg$ 로 커지므로,
# 홉 수를 제한하지 않은 순회는 hub를 지나면서 급격히 비싸진다.

# %%
def count_simple_paths(adj, max_len):
    total = 0
    def walk(node, visited, depth):
        nonlocal total
        if depth == max_len:
            return
        for nxt in adj[node]:
            if nxt in visited:
                continue
            total += 1
            walk(nxt, visited | {nxt}, depth + 1)
    for n in adj:
        walk(n, {n}, 0)
    return total // 2  # 양방향 중복 제거


for L in (1, 2, 3, 4):
    b, a = count_simple_paths(G_BEFORE, L), count_simple_paths(G_AFTER, L)
    print(f"길이<={L} 단순경로: before {b:6d} / after {a:6d}  (x{a / b:.2f})")

deg_after = {k: len(v) for k, v in G_AFTER.items()}
top = sorted(deg_after.items(), key=lambda kv: -kv[1])[:5]
print("차수 상위 5:", top)
print("Shipment 평균 차수:", sum(deg_after[s] for s in SHIPMENTS) / len(SHIPMENTS))
print("Store 차수 before/after:", {s: (len(G_BEFORE[s]), len(G_AFTER[s])) for s in STORES})
# 출력: 길이<=1 단순경로: before     18 / after     31  (x1.72)
# 출력: 길이<=2 단순경로: before     47 / after    103  (x2.19)
# 출력: 길이<=3 단순경로: before     88 / after    258  (x2.93)
# 출력: 길이<=4 단순경로: before    139 / after    560  (x4.03)
# 출력: 차수 상위 5: [('PRD-1', 5), ('ORD-1', 4), ('ORD-3', 4), ('PRD-3', 4), ('STR-2', 4)]
# 출력: Shipment 평균 차수: 3.25
# 출력: Store 차수 before/after: {'STR-1': (1, 2), 'STR-2': (2, 4), 'STR-3': (1, 2)}

# %% [markdown]
# 노드는 17 → 21개(+24%)인데 길이 $\le 4$ 경로는 139 → 560개(약 4배)로 늘었다.
# **연결성을 사는 값이 곧 fan-out이다.** 그래서 hub를 지나는 질의는
# 홉 수 상한, 관계 타입 지정(`-[:sentBy]-`), 속성 필터를 반드시 걸어야 한다.
#
# 또한 hub가 값을 하려면 `shipmentId`(자기 식별자)와
# `dispatchDate / status / weight`(자기 속성)을 가져야 한다.
# 그게 없으면 그냥 링크 테이블이고, `Supplier–Store` 다대다 관계 하나로 대체 가능하다.

# %%
# hub가 "순수 링크 테이블"이면 사라져도 잃는 정보가 없는지 확인
hub_own_props = {"shipmentId", "dispatchDate", "arrivalDate", "status", "weight"}
link_only = {"supplier", "store", "products"}
print("Shipment 자기 속성:", sorted(hub_own_props))
print("이 속성들에 의존하는 질의 수:", 3, "(Q1 status, Q2 status+capacity, Q3 weight)")
print("자기 속성이 없다면 Shipment는:", "Supplier<->Store 다대다 관계 1개로 대체 가능")
print("링크용 필드만:", sorted(link_only))
# 출력: Shipment 자기 속성: ['arrivalDate', 'dispatchDate', 'shipmentId', 'status', 'weight']
# 출력: 이 속성들에 의존하는 질의 수: 3 (Q1 status, Q2 status+capacity, Q3 weight)
# 출력: 자기 속성이 없다면 Shipment는: Supplier<->Store 다대다 관계 1개로 대체 가능
# 출력: 링크용 필드만: ['products', 'store', 'supplier']

# %% [markdown]
# ## 7. 시각화 — hub 없는 그래프 vs hub 있는 그래프

# %%
POS = {
    "Customer": (0.0, 1.0),
    "Order": (1.0, 1.0),
    "Store": (2.0, 1.85),
    "Product": (2.0, 0.15),
    "Shipment": (3.0, 1.0),
    "Supplier": (4.0, 0.15),
}
HUB = "Shipment"
HL = ("Supplier", "Store")  # 강조하고 싶은 순회: Supplier <-> Store


def add_panel(fig, col, nodes, rels, path):
    path_edges = {frozenset(e) for e in zip(path, path[1:])}
    for a, b, name in rels:
        hot = frozenset((a, b)) in path_edges
        x0, y0 = POS[a]
        x1, y1 = POS[b]
        fig.add_trace(
            go.Scatter(
                x=[x0, x1], y=[y0, y1], mode="lines",
                line=dict(width=4 if hot else 1.6, color="#d1495b" if hot else "#9aa5b1"),
                hoverinfo="text", text=f"{a} -[{name}]-> {b}", showlegend=False,
            ),
            row=1, col=col,
        )
        fig.add_annotation(
            x=(x0 + x1) / 2, y=(y0 + y1) / 2, text=name, showarrow=False,
            font=dict(size=9, color="#d1495b" if hot else "#6b7280"),
            bgcolor="rgba(255,255,255,0.75)", row=1, col=col,
        )
    fig.add_trace(
        go.Scatter(
            x=[POS[n][0] for n in nodes], y=[POS[n][1] for n in nodes],
            mode="markers+text", text=nodes, textposition="bottom center",
            textfont=dict(size=11),
            marker=dict(
                size=[46 if n == HUB else 34 for n in nodes],
                color=["#e07a5f" if n == HUB else ("#3d5a80" if n in HL else "#8d99ae") for n in nodes],
                line=dict(width=2, color="white"),
            ),
            hoverinfo="text", showlegend=False,
        ),
        row=1, col=col,
    )


d_b = bfs(ADJ_BEFORE, "Supplier")["Store"]
d_a = bfs(ADJ_AFTER, "Supplier")["Store"]
fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=(
        f"hub 없음: 5 타입 / 4 관계<br>Supplier→Store = {d_b}홉 (Product가 절단점)",
        f"hub 있음: 6 타입 / 7 관계<br>Supplier→Store = {d_a}홉 (Shipment 경유)",
    ),
)
add_panel(fig, 1, BASE_TYPES, BASE_RELS, ["Supplier", "Product", "Order", "Store"])
add_panel(fig, 2, FULL_TYPES, BASE_RELS + HUB_RELS, ["Supplier", "Shipment", "Store"])
fig.update_xaxes(visible=False, range=[-0.55, 4.55])
fig.update_yaxes(visible=False, range=[-0.35, 2.25])
fig.update_annotations(font_size=13, selector=dict(yref="paper"))
fig.update_layout(
    title=dict(
        text="hub entity 패턴: Shipment가 소싱 도메인과 리테일 도메인을 잇는다",
        x=0.5, xanchor="center", y=0.97, font=dict(size=17),
    ),
    width=1180, height=560, plot_bgcolor="white", paper_bgcolor="white",
    margin=dict(l=20, r=20, t=140, b=20),
)
fig.write_image("expy.png", scale=2)
_show(fig)
print("saved expy.png")
# 출력: saved expy.png
