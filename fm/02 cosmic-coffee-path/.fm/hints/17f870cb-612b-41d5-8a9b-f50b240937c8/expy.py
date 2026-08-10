# %% [markdown]
# # Fourth Coffee: `Supplier <-[:sentBy]- Shipment -[:deliveredTo]-> Store` 패턴 해부
#
# 목표 질의:
#
# ```gql
# MATCH (sup:Supplier)<-[:sentBy]-(s:Shipment)-[:deliveredTo]->(st:Store)
# WHERE sup.certification = 'Fair Trade' AND st.state = 'CA'
# RETURN sup.name, st.name, s.status
# ```
#
# 이 노트북은 GQL 엔진 없이 **순수 Python으로 같은 일을 손으로 해보면서** 다음을 확인한다.
#
# 1. `MATCH` 패턴이 기계적으로 어떤 중첩 순회(join)인지
# 2. 화살표 방향 `<-`가 딕셔너리 조회 방향을 어떻게 결정하는지
# 3. 순회 순서를 바꿔도 결과 집합이 같다는 것(= 질의는 선언적)
# 4. 그래프 구조와 매칭된 경로를 plotly로 시각화
#
# 필요 패키지: `plotly`, `kaleido` (필수) / `networkx` (선택, 없으면 자동 우회)

# %%
# 필요 패키지: plotly, kaleido  (networkx는 선택 사항)
from collections import defaultdict


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


print("helper ready")
# 출력: helper ready

# %% [markdown]
# ## 1. Fourth Coffee 온톨로지를 in-memory 데이터로 구성
#
# 온톨로지 스펙 그대로:
#
# | 엔터티 | 식별자 | 이 예제에서 쓰는 속성 |
# |---|---|---|
# | `Supplier` | `supplierId` | `name`, `country`, `certification`(enum), `rating` |
# | `Shipment` | `shipmentId` | `status`(enum), `weight`, `dispatchDate`, `arrivalDate` |
# | `Store` | `storeId` | `name`, `city`, `state`, `capacity` |
# | `Product` | `productId` | `name`, `category`, `isOrganic` |
#
# 관계는 **선언된 방향 그대로** 배송(Shipment) 쪽에 외래키처럼 저장한다.
# `sentBy: Shipment → Supplier`, `deliveredTo: Shipment → Store`, `carries: Shipment → Product`.

# %%
# --- Supplier: certification 을 섞어서 5개 ---
suppliers = [
    {"supplierId": "SUP-1", "name": "Andes Highland Beans", "country": "Peru", "certification": "Fair Trade", "rating": 4.7},
    {"supplierId": "SUP-2", "name": "Kilimanjaro Estates", "country": "Tanzania", "certification": "Fair Trade", "rating": 4.4},
    {"supplierId": "SUP-3", "name": "Sumatra Volcanic Co.", "country": "Indonesia", "certification": "Organic", "rating": 4.1},
    {"supplierId": "SUP-4", "name": "Yirgacheffe Union", "country": "Ethiopia", "certification": "Rainforest Alliance", "rating": 4.9},
    {"supplierId": "SUP-5", "name": "Bulk Bean Traders", "country": "Brazil", "certification": "None", "rating": 3.2},
]

# --- Store: CA / WA / NY 에 걸쳐 5개 ---
stores = [
    {"storeId": "ST-1", "name": "Market Street", "city": "San Francisco", "state": "CA", "capacity": 80},
    {"storeId": "ST-2", "name": "Sunset Roastery", "city": "Los Angeles", "state": "CA", "capacity": 120},
    {"storeId": "ST-3", "name": "Pike Place Bar", "city": "Seattle", "state": "WA", "capacity": 45},
    {"storeId": "ST-4", "name": "Bryant Park Kiosk", "city": "New York", "state": "NY", "capacity": 30},
    {"storeId": "ST-5", "name": "Palo Alto Lab", "city": "Palo Alto", "state": "CA", "capacity": 60},
]

# --- Product ---
products = [
    {"productId": "P-1", "name": "House Espresso", "category": "Espresso", "isOrganic": False},
    {"productId": "P-2", "name": "Organic Cold Brew", "category": "Cold Brew", "isOrganic": True},
    {"productId": "P-3", "name": "Single Origin Drip", "category": "Brewed", "isOrganic": True},
    {"productId": "P-4", "name": "Chai Blend", "category": "Tea", "isOrganic": False},
]

# --- Shipment: 허브 엔터티. sentBy / deliveredTo / carries 를 모두 들고 있다 ---
shipments = [
    {"shipmentId": "SH-1", "status": "Delivered",  "weight": 240.0, "dispatchDate": "2026-01-05", "arrivalDate": "2026-01-19",
     "sentBy": "SUP-1", "deliveredTo": "ST-1", "carries": ["P-1", "P-3"]},
    {"shipmentId": "SH-2", "status": "In Transit", "weight": 180.5, "dispatchDate": "2026-02-02", "arrivalDate": "2026-02-20",
     "sentBy": "SUP-1", "deliveredTo": "ST-2", "carries": ["P-2"]},
    {"shipmentId": "SH-3", "status": "Delayed",    "weight": 310.0, "dispatchDate": "2026-01-11", "arrivalDate": "2026-02-08",
     "sentBy": "SUP-2", "deliveredTo": "ST-5", "carries": ["P-3", "P-4"]},
    {"shipmentId": "SH-4", "status": "Delivered",  "weight": 95.0,  "dispatchDate": "2026-01-22", "arrivalDate": "2026-02-01",
     "sentBy": "SUP-2", "deliveredTo": "ST-3", "carries": ["P-1"]},
    {"shipmentId": "SH-5", "status": "Delivered",  "weight": 420.0, "dispatchDate": "2026-01-09", "arrivalDate": "2026-01-30",
     "sentBy": "SUP-3", "deliveredTo": "ST-2", "carries": ["P-2", "P-3"]},
    {"shipmentId": "SH-6", "status": "Delayed",    "weight": 150.0, "dispatchDate": "2026-02-14", "arrivalDate": "2026-03-10",
     "sentBy": "SUP-4", "deliveredTo": "ST-4", "carries": ["P-3"]},
    {"shipmentId": "SH-7", "status": "In Transit", "weight": 275.0, "dispatchDate": "2026-02-18", "arrivalDate": "2026-03-05",
     "sentBy": "SUP-5", "deliveredTo": "ST-1", "carries": ["P-1", "P-4"]},
    {"shipmentId": "SH-8", "status": "Delivered",  "weight": 200.0, "dispatchDate": "2026-01-28", "arrivalDate": "2026-02-12",
     "sentBy": "SUP-2", "deliveredTo": "ST-1", "carries": ["P-4"]},
]

# 식별자 -> 노드 딕셔너리 (그래프 엔진의 노드 인덱스 역할)
SUP = {n["supplierId"]: n for n in suppliers}
STORE = {n["storeId"]: n for n in stores}
PROD = {n["productId"]: n for n in products}
SHIP = {n["shipmentId"]: n for n in shipments}

print(f"Supplier={len(SUP)}  Shipment={len(SHIP)}  Store={len(STORE)}  Product={len(PROD)}")
print("Fair Trade 공급업체:", [s["name"] for s in suppliers if s["certification"] == "Fair Trade"])
print("CA 매장:", [s["name"] for s in stores if s["state"] == "CA"])
# 출력: Supplier=5  Shipment=8  Store=5  Product=4
# 출력: Fair Trade 공급업체: ['Andes Highland Beans', 'Kilimanjaro Estates']
# 출력: CA 매장: ['Market Street', 'Sunset Roastery', 'Palo Alto Lab']

# %% [markdown]
# ## 2. 관계 방향을 인덱스로 만들기 — `<-` 가 무엇을 뜻하는지
#
# 관계는 선언된 방향이 하나뿐이다.
#
# $$\texttt{sentBy}:\ \text{Shipment} \longrightarrow \text{Supplier}$$
# $$\texttt{deliveredTo}:\ \text{Shipment} \longrightarrow \text{Store}$$
#
# 데이터에는 `shipment["sentBy"] = "SUP-1"` 처럼 **Shipment에서 Supplier로 나가는** 형태로만 저장돼 있다.
# 따라서 방향에 따라 조회 비용이 다르다.
#
# | 패턴 표기 | 시작점 | 필요한 자료구조 |
# |---|---|---|
# | `(s:Shipment)-[:sentBy]->(sup:Supplier)` | Shipment | `shipment["sentBy"]` 직접 참조 (O(1)) |
# | `(sup:Supplier)<-[:sentBy]-(s:Shipment)` | Supplier | **역인덱스** supplier → shipment 목록 필요 |
#
# 역방향 화살표 `<-` 는 "**저장된 방향을 거슬러 올라간다**"는 뜻이고,
# 실제 엔진은 이를 위해 양방향 인접 리스트를 유지한다. 아래에서 그 역인덱스를 직접 만든다.

# %%
# 순방향(선언 방향) 인접: 이미 데이터에 들어 있으므로 그대로 읽으면 됨
fwd_sentBy = {sh["shipmentId"]: sh["sentBy"] for sh in shipments}          # Shipment -> Supplier
fwd_deliveredTo = {sh["shipmentId"]: sh["deliveredTo"] for sh in shipments}  # Shipment -> Store

# 역방향 인접: <-[:sentBy]- 를 밟기 위해 필요
rev_sentBy = defaultdict(list)      # Supplier -> [Shipment...]
for sh in shipments:
    rev_sentBy[sh["sentBy"]].append(sh["shipmentId"])

rev_deliveredTo = defaultdict(list)  # Store -> [Shipment...]
for sh in shipments:
    rev_deliveredTo[sh["deliveredTo"]].append(sh["shipmentId"])

for sid in SUP:
    print(f"{sid} ({SUP[sid]['name']:22s}) <-[:sentBy]- {rev_sentBy[sid]}")
# 출력: SUP-1 (Andes Highland Beans  ) <-[:sentBy]- ['SH-1', 'SH-2']
# 출력: SUP-2 (Kilimanjaro Estates   ) <-[:sentBy]- ['SH-3', 'SH-4', 'SH-8']
# 출력: SUP-3 (Sumatra Volcanic Co.  ) <-[:sentBy]- ['SH-5']
# 출력: SUP-4 (Yirgacheffe Union     ) <-[:sentBy]- ['SH-6']
# 출력: SUP-5 (Bulk Bean Traders     ) <-[:sentBy]- ['SH-7']

# %% [markdown]
# ## 3. `MATCH ... WHERE ... RETURN` 을 손으로 구현 (Supplier부터 시작)
#
# 패턴을 왼쪽에서 오른쪽으로 읽으면 그대로 중첩 루프가 된다.
#
# ```
# MATCH (sup:Supplier) <-[:sentBy]- (s:Shipment) -[:deliveredTo]-> (st:Store)
#        ↓ 바깥 루프         ↓ 역인덱스 조회      ↓ 안쪽 루프        ↓ 순방향 조회
# ```
#
# `WHERE` 술어는 각 변수가 바인딩된 직후에 걸면 탐색 공간이 줄어든다(**술어 푸시다운**).

# %%
def match_from_supplier(certification="Fair Trade", state="CA", verbose=True):
    """MATCH (sup:Supplier)<-[:sentBy]-(s:Shipment)-[:deliveredTo]->(st:Store)
       WHERE sup.certification = ? AND st.state = ?
       RETURN sup.name, st.name, s.status"""
    rows = []
    visited_nodes = 0
    for sup_id, sup in SUP.items():                      # (sup:Supplier) 바인딩
        visited_nodes += 1
        if sup["certification"] != certification:        # WHERE sup.certification = ...
            continue
        for sh_id in rev_sentBy[sup_id]:                 # <-[:sentBy]- 역방향 순회
            sh = SHIP[sh_id]                             # (s:Shipment) 바인딩
            visited_nodes += 1
            st_id = fwd_deliveredTo[sh_id]               # -[:deliveredTo]-> 순방향 조회
            st = STORE[st_id]                            # (st:Store) 바인딩
            visited_nodes += 1
            if st["state"] != state:                     # WHERE st.state = ...
                continue
            rows.append((sup["name"], st["name"], sh["status"]))  # RETURN 투영
    if verbose:
        print(f"[Supplier부터] 방문 노드 {visited_nodes}개, 결과 {len(rows)}행")
    return rows


rows_a = match_from_supplier()
print(f"{'sup.name':24s} {'st.name':20s} s.status")
print("-" * 56)
for r in rows_a:
    print(f"{r[0]:24s} {r[1]:20s} {r[2]}")
# 출력: [Supplier부터] 방문 노드 15개, 결과 4행
# 출력: sup.name                 st.name              s.status
# 출력: --------------------------------------------------------
# 출력: Andes Highland Beans     Market Street        Delivered
# 출력: Andes Highland Beans     Sunset Roastery      In Transit
# 출력: Kilimanjaro Estates      Palo Alto Lab        Delayed
# 출력: Kilimanjaro Estates      Market Street        Delivered

# %% [markdown]
# 4행이 나왔다. 확인해 보면:
#
# - `SH-1` Andes → Market Street (CA) ✓
# - `SH-2` Andes → Sunset Roastery (CA) ✓
# - `SH-3` Kilimanjaro → Palo Alto Lab (CA) ✓
# - `SH-4` Kilimanjaro → Pike Place Bar (**WA**) ✗ `st.state = 'CA'` 에서 탈락
# - `SH-8` Kilimanjaro → Market Street (CA) ✓
# - `SH-5` Sumatra(**Organic**) ✗, `SH-6` Yirgacheffe(**Rainforest Alliance**) ✗, `SH-7` Bulk(**None**) ✗
#
# `Kilimanjaro Estates`는 배송 3건 중 2건만 CA로 갔으므로 2행만 나온다.
# 즉 결과의 **행 수 = 조건을 만족하는 경로(=Shipment) 수**이지 공급업체 수가 아니다.

# %% [markdown]
# ## 4. 같은 패턴, 다른 순회 순서 — 질의는 선언적이다
#
# `MATCH`는 "찾을 모양"만 말한다. 어디서 시작할지는 **엔진의 옵티마이저**가 통계를 보고 정한다.
# 같은 패턴을 세 가지 순서로 구현해 결과 집합이 동일함을 확인한다.
#
# - (A) Supplier부터: 인증 필터 먼저 → 배송 → 매장
# - (B) Store부터: CA 필터 먼저 → 배송 역추적 → 공급업체 인증
# - (C) Shipment(허브)부터: 모든 배송을 훑고 양쪽 끝 검사
#
# 선택성이 높은 쪽을 먼저 고정할수록 방문 노드 수가 줄어든다.

# %%
def match_from_store(certification="Fair Trade", state="CA", verbose=True):
    """오른쪽 끝(Store)부터 거꾸로 시작. 화살표를 반대로 읽는 셈."""
    rows = []
    visited_nodes = 0
    for st_id, st in STORE.items():                 # (st:Store) 먼저 바인딩
        visited_nodes += 1
        if st["state"] != state:                    # WHERE st.state = ... 를 먼저 적용
            continue
        for sh_id in rev_deliveredTo[st_id]:        # deliveredTo 를 거슬러 올라감
            sh = SHIP[sh_id]
            visited_nodes += 1
            sup = SUP[fwd_sentBy[sh_id]]            # sentBy 는 순방향 조회로 충분
            visited_nodes += 1
            if sup["certification"] != certification:
                continue
            rows.append((sup["name"], st["name"], sh["status"]))
    if verbose:
        print(f"[Store부터]    방문 노드 {visited_nodes}개, 결과 {len(rows)}행")
    return rows


def match_from_shipment(certification="Fair Trade", state="CA", verbose=True):
    """허브(Shipment)부터. 가운데를 고정하면 양쪽이 O(1) 조회로 끝난다."""
    rows = []
    visited_nodes = 0
    for sh_id, sh in SHIP.items():                  # (s:Shipment) 먼저 바인딩
        visited_nodes += 1
        sup = SUP[fwd_sentBy[sh_id]]
        st = STORE[fwd_deliveredTo[sh_id]]
        visited_nodes += 2
        if sup["certification"] == certification and st["state"] == state:
            rows.append((sup["name"], st["name"], sh["status"]))
    if verbose:
        print(f"[Shipment부터] 방문 노드 {visited_nodes}개, 결과 {len(rows)}행")
    return rows


rows_b = match_from_store()
rows_c = match_from_shipment()

print()
print("결과 집합 동일? A==B:", sorted(rows_a) == sorted(rows_b), "| A==C:", sorted(rows_a) == sorted(rows_c))
print("행 순서는 다를 수 있음 (ORDER BY 없으면 순서 미보장):")
print("  A:", [r[2] for r in rows_a])
print("  B:", [r[2] for r in rows_b])
# 출력: [Store부터]    방문 노드 17개, 결과 4행
# 출력: [Shipment부터] 방문 노드 24개, 결과 4행
# 출력:
# 출력: 결과 집합 동일? A==B: True | A==C: True
# 출력: 행 순서는 다를 수 있음 (ORDER BY 없으면 순서 미보장):
# 출력:   A: ['Delivered', 'In Transit', 'Delayed', 'Delivered']
# 출력:   B: ['Delivered', 'Delivered', 'In Transit', 'Delayed']

# %% [markdown]
# 세 구현 모두 **같은 4행**을 낸다. 다만 방문 노드 수는 (A) 15 / (B) 17 / (C) 24로 다르다.
# 허브부터 시작하는 (C)가 가장 비싸다 — 필터를 나중에 적용해 8개 배송을 전부 훑기 때문.
#
# 데이터가 커지면 차이가 벌어진다. CA 매장이 3개인데 Fair Trade 공급업체가 500개라면
# (B) Store부터 시작하는 계획이 압도적으로 유리하다. **질의 작성자는 이 선택을 하지 않는다.**

# %% [markdown]
# ## 5. 화살표를 잘못 쓰면 어떻게 되는가
#
# `sentBy`는 `Shipment → Supplier` 선언이므로, Supplier에서 나가는 `sentBy` 엣지는 존재하지 않는다.
#
# ```gql
# MATCH (sup:Supplier)-[:sentBy]->(s:Shipment)   -- ✗ 방향 반대
# ```
#
# 문법 오류가 아니라 **조용히 0행**이 나온다. 이것이 방향 실수가 잡기 어려운 이유다.

# %%
def match_wrong_direction(certification="Fair Trade", state="CA"):
    """(sup:Supplier)-[:sentBy]->(s:Shipment) 를 흉내낸 것.
    Supplier 에서 나가는 sentBy 엣지 집합은 공집합이다."""
    out_sentBy_from_supplier = defaultdict(list)  # 어떤 shipment 도 여기에 등록되지 않는다
    rows = []
    for sup_id, sup in SUP.items():
        if sup["certification"] != certification:
            continue
        for sh_id in out_sentBy_from_supplier[sup_id]:  # 항상 빈 리스트
            rows.append((sup["name"], sh_id))
    return rows


print("잘못된 방향 결과:", match_wrong_direction(), f"({len(match_wrong_direction())}행)")
print("올바른 방향 결과:", f"({len(rows_a)}행)")
# 출력: 잘못된 방향 결과: [] (0행)
# 출력: 올바른 방향 결과: (4행)

# %% [markdown]
# ## 6. 변형 질의들을 같은 방식으로 구현
#
# - (a) `AND s.status = 'Delayed'` — 허브 노드에도 술어를 건다
# - (b) `carries` 로 Product 를 붙여 3-hop 확장 (many-to-many → fan-out)
# - (c) `ORDER BY st.capacity DESC` — 매장 규모순
# - (d) 집계: 공급업체별 CA 배송 건수/총 중량

# %%
# (a) 지연된 배송만
delayed = [
    (SUP[sh["sentBy"]]["name"], STORE[sh["deliveredTo"]]["name"], sh["dispatchDate"], sh["arrivalDate"])
    for sh in shipments
    if SUP[sh["sentBy"]]["certification"] == "Fair Trade"
    and STORE[sh["deliveredTo"]]["state"] == "CA"
    and sh["status"] == "Delayed"
]
print("(a) s.status = 'Delayed':", delayed)
# 출력: (a) s.status = 'Delayed': [('Kilimanjaro Estates', 'Palo Alto Lab', '2026-01-11', '2026-02-08')]

# (b) carries 로 Product 추가 + p.isOrganic = true  → fan-out 확인
with_product = [
    (SUP[sh["sentBy"]]["name"], STORE[sh["deliveredTo"]]["name"], PROD[pid]["name"], PROD[pid]["category"])
    for sh in shipments
    if SUP[sh["sentBy"]]["certification"] == "Fair Trade" and STORE[sh["deliveredTo"]]["state"] == "CA"
    for pid in sh["carries"]
    if PROD[pid]["isOrganic"]
]
print(f"(b) +carries, isOrganic=true → {len(with_product)}행")
for r in with_product:
    print("   ", r)
# 출력: (b) +carries, isOrganic=true → 3행
# 출력:     ('Andes Highland Beans', 'Market Street', 'Single Origin Drip', 'Brewed')
# 출력:     ('Andes Highland Beans', 'Sunset Roastery', 'Organic Cold Brew', 'Cold Brew')
# 출력:     ('Kilimanjaro Estates', 'Palo Alto Lab', 'Single Origin Drip', 'Brewed')

# (c) 인증이 있는 모든 공급업체, 매장 capacity 내림차순
by_capacity = sorted(
    (
        (SUP[sh["sentBy"]]["name"], STORE[sh["deliveredTo"]]["name"], STORE[sh["deliveredTo"]]["capacity"], SUP[sh["sentBy"]]["rating"])
        for sh in shipments
        if SUP[sh["sentBy"]]["certification"] != "None"
    ),
    key=lambda r: -r[2],
)
print("(c) ORDER BY st.capacity DESC (상위 4):")
for r in by_capacity[:4]:
    print("   ", r)
# 출력: (c) ORDER BY st.capacity DESC (상위 4):
# 출력:     ('Andes Highland Beans', 'Sunset Roastery', 120, 4.7)
# 출력:     ('Sumatra Volcanic Co.', 'Sunset Roastery', 120, 4.1)
# 출력:     ('Andes Highland Beans', 'Market Street', 80, 4.7)
# 출력:     ('Kilimanjaro Estates', 'Market Street', 80, 4.4)

# (d) 집계: CA 배송만, 공급업체별 count(s) / sum(s.weight)
agg = defaultdict(lambda: [0, 0.0])
for sh in shipments:
    if STORE[sh["deliveredTo"]]["state"] == "CA":
        key = (SUP[sh["sentBy"]]["name"], SUP[sh["sentBy"]]["certification"])
        agg[key][0] += 1
        agg[key][1] += sh["weight"]
print("(d) 공급업체별 CA 배송 집계:")
for (nm, cert), (cnt, kg) in sorted(agg.items(), key=lambda kv: -kv[1][0]):
    print(f"    {nm:24s} {cert:20s} shipments={cnt} totalKg={kg}")
# 출력: (d) 공급업체별 CA 배송 집계:
# 출력:     Andes Highland Beans     Fair Trade           shipments=2 totalKg=420.5
# 출력:     Kilimanjaro Estates      Fair Trade           shipments=2 totalKg=510.0
# 출력:     Sumatra Volcanic Co.     Organic              shipments=1 totalKg=420.0
# 출력:     Bulk Bean Traders        None                 shipments=1 totalKg=275.0

# %% [markdown]
# ## 7. (선택) networkx 로 그래프 구조 확인
#
# 설치돼 있으면 방향 그래프를 만들어 최단 경로와 차수를 본다. 없으면 조용히 넘어간다.
# Supplier–Store 사이에는 직접 엣지가 없고 **항상 Shipment를 경유**하므로 최단 경로 길이는 2다.

# %%
try:
    import networkx as nx

    G = nx.DiGraph()
    for n in suppliers:
        G.add_node(n["supplierId"], label="Supplier")
    for n in stores:
        G.add_node(n["storeId"], label="Store")
    for n in products:
        G.add_node(n["productId"], label="Product")
    for sh in shipments:
        G.add_node(sh["shipmentId"], label="Shipment")
        G.add_edge(sh["shipmentId"], sh["sentBy"], type="sentBy")
        G.add_edge(sh["shipmentId"], sh["deliveredTo"], type="deliveredTo")
        for pid in sh["carries"]:
            G.add_edge(sh["shipmentId"], pid, type="carries")

    U = G.to_undirected()  # 방향 무시하고 경로 존재만 확인
    print("노드", G.number_of_nodes(), "엣지", G.number_of_edges())
    print("SUP-1 -> ST-1 최단경로:", nx.shortest_path(U, "SUP-1", "ST-1"))
    print("Shipment 평균 out-degree:", sum(G.out_degree(s["shipmentId"]) for s in shipments) / len(shipments))
except ImportError:
    print("networkx 미설치 — 건너뜀 (plotly 시각화만으로 충분)")
# 출력: networkx 미설치 — 건너뜀 (plotly 시각화만으로 충분)

# %% [markdown]
# ## 8. plotly 노드-링크 다이어그램
#
# 3열 레이아웃으로 그린다: 왼쪽 Supplier, 가운데 Shipment(허브), 오른쪽 Store.
# **매칭된 경로**(Fair Trade + CA)의 엣지는 굵은 강조선, 탈락한 엣지는 흐린 회색으로 표시한다.
#
# 매칭 조건을 수식으로 쓰면:
#
# $$R = \{(sup, s, st) \mid s \xrightarrow{\texttt{sentBy}} sup \ \wedge\  s \xrightarrow{\texttt{deliveredTo}} st \ \wedge\  sup.certification = \texttt{'Fair Trade'} \ \wedge\  st.state = \texttt{'CA'}\}$$

# %%
import plotly.graph_objects as go

MATCH_CERT, MATCH_STATE = "Fair Trade", "CA"


def is_matched(sh):
    return (
        SUP[sh["sentBy"]]["certification"] == MATCH_CERT
        and STORE[sh["deliveredTo"]]["state"] == MATCH_STATE
    )


matched_ships = {sh["shipmentId"] for sh in shipments if is_matched(sh)}
matched_sups = {sh["sentBy"] for sh in shipments if is_matched(sh)}
matched_stores = {sh["deliveredTo"] for sh in shipments if is_matched(sh)}
print("매칭 경로:", sorted(matched_ships), "| 공급업체:", sorted(matched_sups), "| 매장:", sorted(matched_stores))
# 출력: 매칭 경로: ['SH-1', 'SH-2', 'SH-3', 'SH-8'] | 공급업체: ['SUP-1', 'SUP-2'] | 매장: ['ST-1', 'ST-2', 'ST-5']


def _spread(n, span=9.0):
    """n개 노드를 y축 [0, span] 에 균등 배치."""
    if n == 1:
        return [span / 2]
    step = span / (n - 1)
    return [i * step for i in range(n)]


pos = {}
for sid, y in zip(SUP, _spread(len(SUP))):
    pos[sid] = (0.0, y)
for sid, y in zip(SHIP, _spread(len(SHIP))):
    pos[sid] = (1.0, y)
for sid, y in zip(STORE, _spread(len(STORE))):
    pos[sid] = (2.0, y)

DIM, HL_SENT, HL_DELIV = "#c9ccd4", "#d95f02", "#1b7f4d"

edge_traces = []
for sh in shipments:
    sh_id = sh["shipmentId"]
    hit = sh_id in matched_ships
    for target, hl_color, rel in ((sh["sentBy"], HL_SENT, "sentBy"), (sh["deliveredTo"], HL_DELIV, "deliveredTo")):
        x0, y0 = pos[sh_id]
        x1, y1 = pos[target]
        edge_traces.append(
            go.Scatter(
                x=[x0, x1], y=[y0, y1], mode="lines",
                line=dict(width=3.4 if hit else 1.0, color=hl_color if hit else DIM),
                opacity=1.0 if hit else 0.5,
                hoverinfo="text",
                hovertext=f"{sh_id} -[:{rel}]-> {target}" + ("  ✔ matched" if hit else ""),
                showlegend=False,
            )
        )


def node_trace(ids, label_of, hover_of, matched_set, base_color, symbol, name):
    xs = [pos[i][0] for i in ids]
    ys = [pos[i][1] for i in ids]
    return go.Scatter(
        x=xs, y=ys, mode="markers+text",
        marker=dict(
            size=[30 if i in matched_set else 20 for i in ids],
            color=[base_color if i in matched_set else DIM for i in ids],
            symbol=symbol,
            line=dict(width=[2.5 if i in matched_set else 1 for i in ids], color="#2b2f38"),
        ),
        text=[label_of(i) for i in ids],
        textposition=["middle left"] * len(ids) if name == "Supplier" else (["middle right"] * len(ids) if name == "Store" else ["top center"] * len(ids)),
        textfont=dict(size=10),
        hoverinfo="text", hovertext=[hover_of(i) for i in ids],
        name=name, showlegend=True,
    )


fig = go.Figure(edge_traces)
fig.add_trace(node_trace(
    list(SUP), lambda i: SUP[i]["name"],
    lambda i: f"{i} {SUP[i]['name']}<br>certification={SUP[i]['certification']}<br>rating={SUP[i]['rating']}",
    matched_sups, "#d95f02", "circle", "Supplier"))
fig.add_trace(node_trace(
    list(SHIP), lambda i: f"{i} · {SHIP[i]['status']}",
    lambda i: f"{i}<br>status={SHIP[i]['status']}<br>weight={SHIP[i]['weight']}kg<br>carries={SHIP[i]['carries']}",
    matched_ships, "#7570b3", "diamond", "Shipment (hub)"))
fig.add_trace(node_trace(
    list(STORE), lambda i: f"{STORE[i]['name']} ({STORE[i]['state']})",
    lambda i: f"{i} {STORE[i]['name']}<br>state={STORE[i]['state']}<br>capacity={STORE[i]['capacity']}",
    matched_stores, "#1b7f4d", "square", "Store"))

fig.add_annotation(x=0.0, y=11.0, text="<b>Supplier</b><br>certification = 'Fair Trade'", showarrow=False, font=dict(size=12, color="#d95f02"))
fig.add_annotation(x=1.0, y=11.0, text="<b>Shipment</b><br>허브 엔터티", showarrow=False, font=dict(size=12, color="#7570b3"))
fig.add_annotation(x=2.0, y=11.0, text="<b>Store</b><br>state = 'CA'", showarrow=False, font=dict(size=12, color="#1b7f4d"))
fig.add_annotation(x=0.5, y=-1.2, text="<-[:sentBy]-  (역방향 순회)", showarrow=False, font=dict(size=12, color="#d95f02"))
fig.add_annotation(x=1.5, y=-1.2, text="-[:deliveredTo]->  (순방향)", showarrow=False, font=dict(size=12, color="#1b7f4d"))

fig.update_layout(
    title=dict(text="MATCH (sup:Supplier)&lt;-[:sentBy]-(s:Shipment)-[:deliveredTo]-&gt;(st:Store)"
                    "<br><sub>굵은 색선 = WHERE 조건을 통과한 4개 경로 / 흐린 회색선 = 탈락</sub>", x=0.5),
    xaxis=dict(visible=False, range=[-0.75, 2.8]),
    yaxis=dict(visible=False, range=[-1.9, 12.0]),
    plot_bgcolor="white", paper_bgcolor="white",
    width=1060, height=860,
    legend=dict(orientation="h", y=-0.04, x=0.5, xanchor="center"),
    margin=dict(l=40, r=40, t=100, b=90),
)

_show(fig)
fig.write_image("expy.png", scale=2)
print("saved expy.png")
# 출력: saved expy.png

# %% [markdown]
# ## 9. 정리
#
# | 질문 | 답 |
# |---|---|
# | `MATCH` 패턴은 기계적으로 무엇인가 | 노드 바인딩 + 인접 리스트 순회의 중첩 루프 (= join) |
# | 왜 `<-[:sentBy]-` 인가 | `sentBy`는 `Shipment → Supplier` 선언. Supplier에서 시작하면 역방향 순회 |
# | 왜 `-[:deliveredTo]->` 는 그대로인가 | `deliveredTo`도 `Shipment → Store` 선언. 패턴 방향과 일치 |
# | 왜 Shipment가 가운데인가 | Supplier–Store 직접 엣지가 없다. Shipment가 두 도메인을 잇는 허브 |
# | Shipment를 노드로 둔 이득 | `status`/`weight`/날짜 같은 "관계의 속성"을 조회·필터할 수 있다 (reification) |
# | 순회 순서는 누가 정하나 | 엔진의 옵티마이저. 작성자는 모양만 선언한다 |
# | 결과 행 수의 의미 | 조건을 만족하는 **경로(Shipment) 수**. 공급업체 수가 아니다 |
