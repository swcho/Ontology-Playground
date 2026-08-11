# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
# %% [markdown]
# # MATCH 두 경로 결합의 카티션 곱 함정
#
# 카드 질의:
#
# ```gql
# MATCH (c:Customer)-[:holds]->(inv:Investment),
#       (c)-[:has_loan]->(loan:Loan)
# WITH c, SUM(inv.currentValue) AS portfolio, SUM(loan.principal) AS debt
# WHERE portfolio > debt
# RETURN c.name, portfolio, debt
# ```
#
# 이 노트북은 **GQL 엔진 없이 순수 파이썬으로 질의 의미론을 재현**한다.
#
# 핵심 주장: 같은 변수 `c`를 공유하는 두 경로를 쉼표로 나열하면 결과 테이블은
# 고객별로 **투자 행 × 대출 행**의 카티션 곱이 되고, 그 위에서 `SUM`을 돌리면
#
# $$\widehat{portfolio}_c = n^{loan}_c \cdot \sum_i v_i, \qquad
#   \widehat{debt}_c = n^{inv}_c \cdot \sum_j p_j$$
#
# 즉 각 합계가 **상대 경로의 행 수만큼** 부풀려진다.

# %%
def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1. 그래프 데이터 (노드 + 엣지)
#
# Banking & Finance 온톨로지의 일부만 쓴다: `Customer -[:holds]-> Investment`,
# `Customer -[:has_loan]-> Loan`.

# %%
customers = {
    "C1": {"customerId": "C1", "name": "Alice"},
    "C2": {"customerId": "C2", "name": "Bob"},
    "C3": {"customerId": "C3", "name": "Carol"},
    "C4": {"customerId": "C4", "name": "Dave"},
    "C5": {"customerId": "C5", "name": "Erin"},
}

investments = {
    "H1": {"holdingId": "H1", "symbol": "MSFT", "currentValue": 40000},
    "H2": {"holdingId": "H2", "symbol": "AAPL", "currentValue": 30000},
    "H3": {"holdingId": "H3", "symbol": "NVDA", "currentValue": 20000},
    "H4": {"holdingId": "H4", "symbol": "TSLA", "currentValue": 50000},
    "H5": {"holdingId": "H5", "symbol": "AMZN", "currentValue": 10000},
    "H6": {"holdingId": "H6", "symbol": "GOOG", "currentValue": 10000},
    "H7": {"holdingId": "H7", "symbol": "META", "currentValue": 10000},
    "H8": {"holdingId": "H8", "symbol": "NFLX", "currentValue": 10000},
    "H9": {"holdingId": "H9", "symbol": "AMD", "currentValue": 60000},
    "H10": {"holdingId": "H10", "symbol": "INTC", "currentValue": 15000},
}

loans = {
    "L1": {"loanId": "L1", "principal": 30000, "status": "active"},
    "L2": {"loanId": "L2", "principal": 20000, "status": "active"},
    "L3": {"loanId": "L3", "principal": 30000, "status": "active"},
    "L4": {"loanId": "L4", "principal": 15000, "status": "active"},
    "L5": {"loanId": "L5", "principal": 10000, "status": "active"},
    "L6": {"loanId": "L6", "principal": 35000, "status": "active"},
    "L7": {"loanId": "L7", "principal": 25000, "status": "active"},
}

# (customer, investment) 엣지 — :holds
holds = [
    ("C1", "H1"), ("C1", "H2"), ("C1", "H3"),          # Alice: 투자 3건
    ("C2", "H4"),                                        # Bob:   투자 1건
    ("C3", "H5"), ("C3", "H6"), ("C3", "H7"), ("C3", "H8"),  # Carol: 투자 4건
    ("C4", "H9"), ("C4", "H10"),                         # Dave:  투자 2건
    # Erin(C5): 투자 없음
]

# (customer, loan) 엣지 — :has_loan
has_loan = [
    ("C1", "L1"), ("C1", "L2"),                          # Alice: 대출 2건
    ("C2", "L3"), ("C2", "L4"), ("C2", "L5"),            # Bob:   대출 3건
    ("C3", "L6"),                                        # Carol: 대출 1건
    # Dave(C4): 대출 없음
    ("C5", "L7"),                                        # Erin:  대출 1건
]

for cid, cust in customers.items():
    n_inv = sum(1 for c, _ in holds if c == cid)
    n_loan = sum(1 for c, _ in has_loan if c == cid)
    print(f"{cid} {cust['name']:6s} 투자 {n_inv}건 / 대출 {n_loan}건")

# 출력:
# C1 Alice  투자 3건 / 대출 2건
# C2 Bob    투자 1건 / 대출 3건
# C3 Carol  투자 4건 / 대출 1건
# C4 Dave   투자 2건 / 대출 0건
# C5 Erin   투자 0건 / 대출 1건

# %% [markdown]
# ## 2. `MATCH` 두 경로 결합 = 중첩 루프 (inner join)
#
# 쉼표로 나열된 두 경로는 `c`를 공유하므로, 엔진은 `c`가 같은 행끼리 조인한다.
# 파이썬으로는 그냥 이중 루프다.

# %%
def match_two_paths():
    """MATCH (c)-[:holds]->(inv), (c)-[:has_loan]->(loan) 의 결과 테이블."""
    rows = []
    for cid in customers:                                 # (c:Customer)
        inv_ids = [i for c, i in holds if c == cid]        # -[:holds]->(inv)
        loan_ids = [l for c, l in has_loan if c == cid]    # -[:has_loan]->(loan)
        for i in inv_ids:                                  # 카티션 곱 발생 지점
            for l in loan_ids:
                rows.append({"c": cid, "inv": i, "loan": l})
    return rows


rows = match_two_paths()
print(f"결과 행 수 = {len(rows)}")
print("Alice(C1) 행:")
for r in rows:
    if r["c"] == "C1":
        print("  ", r)

# 출력:
# 결과 행 수 = 13        (= 6 + 3 + 4 + 0 + 0)
# Alice(C1) 행:
#    {'c': 'C1', 'inv': 'H1', 'loan': 'L1'}
#    {'c': 'C1', 'inv': 'H1', 'loan': 'L2'}
#    {'c': 'C1', 'inv': 'H2', 'loan': 'L1'}
#    {'c': 'C1', 'inv': 'H2', 'loan': 'L2'}
#    {'c': 'C1', 'inv': 'H3', 'loan': 'L1'}
#    {'c': 'C1', 'inv': 'H3', 'loan': 'L2'}

# %%
# 고객별 행 수 = 투자 수 × 대출 수. 한쪽이 0이면 행이 아예 없다(inner join 탈락).
from collections import Counter  # noqa: E402

row_count = Counter(r["c"] for r in rows)
for cid, cust in customers.items():
    n_inv = sum(1 for c, _ in holds if c == cid)
    n_loan = sum(1 for c, _ in has_loan if c == cid)
    print(f"{cust['name']:6s} {n_inv} x {n_loan} = {n_inv * n_loan:2d} 행 "
          f"(실제 {row_count.get(cid, 0)}) "
          f"{'<- MATCH 결합에서 탈락' if row_count.get(cid, 0) == 0 else ''}")

# 출력:
# Alice  3 x 2 =  6 행 (실제 6)
# Bob    1 x 3 =  3 행 (실제 3)
# Carol  4 x 1 =  4 행 (실제 4)
# Dave   2 x 0 =  0 행 (실제 0) <- MATCH 결합에서 탈락
# Erin   0 x 1 =  0 행 (실제 0) <- MATCH 결합에서 탈락

# %% [markdown]
# ## 3. `WITH ... SUM(...)` — 집계 경계와 부풀림
#
# `WITH c, SUM(inv.currentValue) AS portfolio, SUM(loan.principal) AS debt`는
# 비집계 항목인 `c`를 **그룹 키**로 삼아 행을 고객별로 묶는다.
# 문제는 묶기 전 행들이 이미 카티션 곱이라는 점이다.

# %%
def aggregate_naive(rows):
    """카드 질의 그대로: 결합된 행 위에서 SUM → 부풀려진 값."""
    acc = {}
    for r in rows:
        a = acc.setdefault(r["c"], {"portfolio": 0, "debt": 0})
        a["portfolio"] += investments[r["inv"]]["currentValue"]
        a["debt"] += loans[r["loan"]]["principal"]
    return acc


def aggregate_correct():
    """경로별로 따로 집계 → 정확한 값 (대출/투자 없는 고객은 0)."""
    acc = {}
    for cid in customers:
        acc[cid] = {
            "portfolio": sum(investments[i]["currentValue"] for c, i in holds if c == cid),
            "debt": sum(loans[l]["principal"] for c, l in has_loan if c == cid),
        }
    return acc


naive = aggregate_naive(rows)
correct = aggregate_correct()

hdr = f"{'name':6s} {'portfolio(부풀림)':>18s} {'portfolio(정확)':>16s} {'debt(부풀림)':>14s} {'debt(정확)':>12s}"
print(hdr)
for cid, cust in customers.items():
    n = naive.get(cid, {"portfolio": 0, "debt": 0})
    k = correct[cid]
    print(f"{cust['name']:6s} {n['portfolio']:>18,d} {k['portfolio']:>16,d} "
          f"{n['debt']:>14,d} {k['debt']:>12,d}")

# 출력:
# name       portfolio(부풀림)  portfolio(정확)     debt(부풀림)   debt(정확)
# Alice             180,000           90,000        150,000       50,000
# Bob               150,000           50,000         55,000       55,000
# Carol              40,000           40,000        140,000       35,000
# Dave                    0           75,000              0            0
# Erin                    0                0              0       25,000

# %% [markdown]
# ## 4. 부풀림 배수 확인
#
# 이론값: $\widehat{portfolio}/portfolio = n^{loan}$, $\widehat{debt}/debt = n^{inv}$.

# %%
print(f"{'name':6s} {'n_inv':>5s} {'n_loan':>6s} {'pf 배수':>8s} {'debt 배수':>9s}")
for cid, cust in customers.items():
    n_inv = sum(1 for c, _ in holds if c == cid)
    n_loan = sum(1 for c, _ in has_loan if c == cid)
    n, k = naive.get(cid, {"portfolio": 0, "debt": 0}), correct[cid]
    pf_x = n["portfolio"] / k["portfolio"] if k["portfolio"] else float("nan")
    dt_x = n["debt"] / k["debt"] if k["debt"] else float("nan")
    print(f"{cust['name']:6s} {n_inv:>5d} {n_loan:>6d} {pf_x:>8.1f} {dt_x:>9.1f}")

# 출력:
# name   n_inv n_loan   pf 배수  debt 배수
# Alice      3      2      2.0       3.0
# Bob        1      3      3.0       1.0
# Carol      4      1      1.0       4.0
# Dave       2      0      0.0       nan
# Erin       0      1      nan       0.0

# %% [markdown]
# ## 5. `WHERE portfolio > debt` — 두 방식의 판정이 갈린다
#
# `WHERE`가 `WITH` **뒤**에 있으므로 집계 결과(`portfolio`, `debt`)를 필터할 수 있다.
# 하지만 필터에 들어오는 값 자체가 틀렸으면 판정도 틀린다.

# %%
print(f"{'name':6s} {'부풀림 판정':>12s} {'정확 판정':>10s}  비고")
for cid, cust in customers.items():
    n, k = naive.get(cid), correct[cid]
    naive_v = None if n is None else n["portfolio"] > n["debt"]
    corr_v = k["portfolio"] > k["debt"]
    if naive_v is None:
        note = "MATCH 결합에서 탈락 (행 없음)"
    elif naive_v and not corr_v:
        note = "!! 거짓 양성 — 잘못 포함"
    elif corr_v and not naive_v:
        note = "!! 거짓 음성 — 잘못 제외"
    else:
        note = "일치"
    print(f"{cust['name']:6s} {str(naive_v):>12s} {str(corr_v):>10s}  {note}")

print("\n카드 질의(부풀림)의 RETURN 결과:",
      sorted(customers[c]["name"] for c, v in naive.items() if v["portfolio"] > v["debt"]))
print("정확한 집계의 RETURN 결과   :",
      sorted(customers[c]["name"] for c, v in correct.items()
             if v["portfolio"] > v["debt"] and sum(1 for x, _ in has_loan if x == c)))
print("OPTIONAL MATCH 보정 결과    :",
      sorted(customers[c]["name"] for c, v in correct.items() if v["portfolio"] > v["debt"]))

# 출력:
# name    부풀림 판정   정확 판정  비고
# Alice          True       True  일치
# Bob            True      False  !! 거짓 양성 — 잘못 포함
# Carol         False       True  !! 거짓 음성 — 잘못 제외
# Dave           None       True  MATCH 결합에서 탈락 (행 없음)
# Erin           None      False  MATCH 결합에서 탈락 (행 없음)
#
# 카드 질의(부풀림)의 RETURN 결과: ['Alice', 'Bob']
# 정확한 집계의 RETURN 결과   : ['Alice', 'Carol']
# OPTIONAL MATCH 보정 결과    : ['Alice', 'Carol', 'Dave']

# %% [markdown]
# ## 6. 부풀림을 피하는 세 가지 재작성
#
# ### (a) `DISTINCT` 로 중복 제거 후 집계
# 카티션 곱 행은 그대로 두고, 집계 대상만 유일한 노드로 줄인다.
# Cypher에서는 `SUM(DISTINCT inv.currentValue)`가 **값** 기준 중복 제거라 위험하다
# (같은 금액의 서로 다른 보유가 하나로 합쳐진다). 아래 두 구현을 비교해 본다.

# %%
def aggregate_distinct_by_id(rows):
    """노드 ID 기준 중복 제거 — 정확."""
    acc = {}
    for r in rows:
        a = acc.setdefault(r["c"], {"inv": set(), "loan": set()})
        a["inv"].add(r["inv"])
        a["loan"].add(r["loan"])
    return {
        c: {
            "portfolio": sum(investments[i]["currentValue"] for i in a["inv"]),
            "debt": sum(loans[l]["principal"] for l in a["loan"]),
        }
        for c, a in acc.items()
    }


def aggregate_distinct_by_value(rows):
    """SUM(DISTINCT inv.currentValue) 처럼 '값' 기준 중복 제거 — 위험."""
    acc = {}
    for r in rows:
        a = acc.setdefault(r["c"], {"pf": set(), "dt": set()})
        a["pf"].add(investments[r["inv"]]["currentValue"])
        a["dt"].add(loans[r["loan"]]["principal"])
    return {c: {"portfolio": sum(a["pf"]), "debt": sum(a["dt"])} for c, a in acc.items()}


by_id = aggregate_distinct_by_id(rows)
by_val = aggregate_distinct_by_value(rows)
print(f"{'name':6s} {'ID-DISTINCT pf':>15s} {'값-DISTINCT pf':>15s} {'ID debt':>9s} {'값 debt':>9s}")
for cid in ["C1", "C2", "C3"]:
    a, b = by_id[cid], by_val[cid]
    print(f"{customers[cid]['name']:6s} {a['portfolio']:>15,d} {b['portfolio']:>15,d} "
          f"{a['debt']:>9,d} {b['debt']:>9,d}")
print("\nCarol은 10,000 짜리 보유 4건 → 값 기준 DISTINCT가 40,000을 10,000으로 붕괴시킨다.")
print("Bob은 30,000/15,000/10,000 대출 → 값 기준으로도 우연히 맞지만 보장은 없다.")

# 출력:
# name    ID-DISTINCT pf  값-DISTINCT pf   ID debt   값 debt
# Alice           90,000          90,000    50,000    50,000
# Bob             50,000          50,000    55,000    55,000
# Carol           40,000          10,000    35,000    35,000
#
# Carol은 10,000 짜리 보유 4건 → 값 기준 DISTINCT가 40,000을 10,000으로 붕괴시킨다.
# Bob은 30,000/15,000/10,000 대출 → 값 기준으로도 우연히 맞지만 보장은 없다.

# %% [markdown]
# ### (b) 경로를 순차 집계 — 각 `MATCH` 뒤에 `WITH`
#
# ```gql
# MATCH (c:Customer)-[:holds]->(inv:Investment)
# WITH c, SUM(inv.currentValue) AS portfolio        // 여기서 투자 경로가 닫힌다
# MATCH (c)-[:has_loan]->(loan:Loan)
# WITH c, portfolio, SUM(loan.principal) AS debt    // 대출 경로만 새로 곱해진다
# WHERE portfolio > debt
# RETURN c.name, portfolio, debt
# ```
#
# ### (c) 서브질의(패턴 내 집계)로 분리
#
# ```gql
# MATCH (c:Customer)
# WITH c,
#      COUNT { (c)-[:has_loan]->() } AS n_loan,
#      [ (c)-[:holds]->(i:Investment) | i.currentValue ] AS pf_vals,
#      [ (c)-[:has_loan]->(l:Loan)    | l.principal    ] AS debt_vals
# WITH c, REDUCE(s = 0.0, v IN pf_vals   | s + v) AS portfolio,
#         REDUCE(s = 0.0, v IN debt_vals | s + v) AS debt
# WHERE portfolio > debt
# RETURN c.name, portfolio, debt
# ```
#
# (b)는 대출이 없는 고객을 여전히 떨어뜨리지만, (c)는 리스트가 빈 배열이 되어
# `portfolio > 0` 으로 살아남는다. 아래에서 그 차이를 확인한다.

# %%
def aggregate_sequential():
    """(b) 순차 집계: 두 번째 MATCH가 inner join이므로 대출 없는 고객은 여전히 탈락."""
    out = {}
    for cid in customers:
        pf = sum(investments[i]["currentValue"] for c, i in holds if c == cid)
        loan_ids = [l for c, l in has_loan if c == cid]
        if not loan_ids:            # MATCH (c)-[:has_loan]->(loan) 이 실패 → 행 소멸
            continue
        out[cid] = {"portfolio": pf, "debt": sum(loans[l]["principal"] for l in loan_ids)}
    return out


def aggregate_subquery():
    """(c) 패턴 컴프리헨션: 빈 리스트 → 0. 대출 없는 고객도 유지."""
    return {
        cid: {
            "portfolio": sum(investments[i]["currentValue"] for c, i in holds if c == cid),
            "debt": sum(loans[l]["principal"] for c, l in has_loan if c == cid),
        }
        for cid in customers
    }


seq, sub = aggregate_sequential(), aggregate_subquery()
print("(b) 순차 집계 결과 :",
      sorted(customers[c]["name"] for c, v in seq.items() if v["portfolio"] > v["debt"]))
print("(c) 서브질의 결과  :",
      sorted(customers[c]["name"] for c, v in sub.items() if v["portfolio"] > v["debt"]))

# 출력:
# (b) 순차 집계 결과 : ['Alice', 'Carol']
# (c) 서브질의 결과  : ['Alice', 'Carol', 'Dave']

# %% [markdown]
# ## 7. `OPTIONAL MATCH` 보정
#
# ```gql
# MATCH (c:Customer)
# OPTIONAL MATCH (c)-[:holds]->(inv:Investment)
# WITH c, SUM(inv.currentValue) AS portfolio          // 없으면 SUM(null)=0
# OPTIONAL MATCH (c)-[:has_loan]->(loan:Loan)
# WITH c, portfolio, SUM(loan.principal) AS debt
# WHERE portfolio > debt
# RETURN c.name, portfolio, debt
# ```
#
# `OPTIONAL MATCH`는 매칭 실패 시 변수를 `null`로 채워 행을 유지하고,
# Cypher의 `SUM`은 `null`을 무시하므로 합계가 `0`이 된다.

# %%
def aggregate_optional():
    """OPTIONAL MATCH: 매칭 실패 → null 행 유지 → SUM(null) = 0."""
    out = {}
    for cid in customers:
        inv_vals = [investments[i]["currentValue"] for c, i in holds if c == cid] or [None]
        pf = sum(v for v in inv_vals if v is not None)          # SUM은 null 무시
        loan_vals = [loans[l]["principal"] for c, l in has_loan if c == cid] or [None]
        dt = sum(v for v in loan_vals if v is not None)
        out[cid] = {"portfolio": pf, "debt": dt}
    return out


opt = aggregate_optional()
for cid, v in opt.items():
    verdict = "포함" if v["portfolio"] > v["debt"] else "제외"
    print(f"{customers[cid]['name']:6s} portfolio={v['portfolio']:>7,d} "
          f"debt={v['debt']:>7,d} -> {verdict}")

# 출력:
# Alice  portfolio= 90,000 debt= 50,000 -> 포함
# Bob    portfolio= 50,000 debt= 55,000 -> 제외
# Carol  portfolio= 40,000 debt= 35,000 -> 포함
# Dave   portfolio= 75,000 debt=      0 -> 포함
# Erin   portfolio=      0 debt= 25,000 -> 제외

# %% [markdown]
# ## 8. 집계 전 `WHERE` vs 집계 후 `WHERE`
#
# `WHERE`의 위치가 의미를 바꾼다.
#
# - `MATCH ... WHERE loan.status = 'active'` → **행 단위** 필터(집계 전). 집계 변수 사용 불가.
# - `WITH ... WHERE portfolio > debt` → **그룹 단위** 필터(집계 후). SQL의 `HAVING`에 해당.
#
# 표준 GQL에서는 후자를 `FILTER` 문으로 쓴다.

# %%
# 집계 전 WHERE: status='active' 인 대출만 (여기선 전부 active라 결과 동일)
# 집계 후 WHERE를 집계 전에 쓰면? portfolio/debt가 아직 존재하지 않아 컴파일 에러.
try:
    _ = rows[0]["portfolio"]     # 집계 전 행에는 portfolio 컬럼이 없다
except KeyError as e:
    print("집계 전 행에 집계 변수 없음 ->", type(e).__name__, e)

# 출력: 집계 전 행에 집계 변수 없음 -> KeyError 'portfolio'

# %% [markdown]
# ## 9. 시각화
#
# 왼쪽: 고객별 `portfolio` vs `debt` 산점도. 기준선 $y = x$ 위쪽이 순부채,
# 아래쪽이 순자산 우위(`portfolio > debt`) 구간이다.
# 오른쪽: 부풀린 합계 vs 정확한 합계 비교.

# %%
import plotly.graph_objects as go  # noqa: E402
from plotly.subplots import make_subplots  # noqa: E402

order = ["C1", "C2", "C3", "C4", "C5"]
names = [customers[c]["name"] for c in order]
pf_ok = [correct[c]["portfolio"] for c in order]
dt_ok = [correct[c]["debt"] for c in order]
pf_bad = [naive.get(c, {"portfolio": 0})["portfolio"] for c in order]
dt_bad = [naive.get(c, {"debt": 0})["debt"] for c in order]

fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=("정확한 집계: portfolio vs debt (기준선 y=x)",
                    "부풀린 합계 vs 정확한 합계"),
)

lim = max(pf_ok + dt_ok + pf_bad + dt_bad) * 1.1
fig.add_trace(go.Scatter(x=[0, lim], y=[0, lim], mode="lines", name="y = x (손익분기)",
                         line=dict(dash="dash", color="#888")), row=1, col=1)

win = [i for i, _ in enumerate(order) if pf_ok[i] > dt_ok[i]]
lose = [i for i, _ in enumerate(order) if pf_ok[i] <= dt_ok[i]]
fig.add_trace(go.Scatter(
    x=[dt_ok[i] for i in win], y=[pf_ok[i] for i in win], mode="markers+text",
    text=[names[i] for i in win], textposition="top center", name="portfolio > debt",
    marker=dict(size=14, color="#2ca02c", symbol="circle")), row=1, col=1)
fig.add_trace(go.Scatter(
    x=[dt_ok[i] for i in lose], y=[pf_ok[i] for i in lose], mode="markers+text",
    text=[names[i] for i in lose], textposition="top center", name="portfolio <= debt",
    marker=dict(size=14, color="#d62728", symbol="x")), row=1, col=1)

fig.add_trace(go.Bar(x=names, y=pf_bad, name="portfolio (부풀림)",
                     marker_color="#9ecae1"), row=1, col=2)
fig.add_trace(go.Bar(x=names, y=pf_ok, name="portfolio (정확)",
                     marker_color="#1f77b4"), row=1, col=2)
fig.add_trace(go.Bar(x=names, y=dt_bad, name="debt (부풀림)",
                     marker_color="#ffb996"), row=1, col=2)
fig.add_trace(go.Bar(x=names, y=dt_ok, name="debt (정확)",
                     marker_color="#ff7f0e"), row=1, col=2)

fig.update_xaxes(title_text="debt (총 대출 원금)", range=[-18000, lim], row=1, col=1)
fig.update_yaxes(title_text="portfolio (총 투자 평가액)", range=[-12000, lim], row=1, col=1)
fig.update_xaxes(title_text="고객", row=1, col=2)
fig.update_yaxes(title_text="USD", row=1, col=2)
fig.update_layout(
    title_text="MATCH 두 경로 결합의 카티션 곱: 합계 부풀림과 순자산 판정",
    barmode="group", height=520, width=1250, template="plotly_white",
    legend=dict(orientation="h", y=-0.18),
)

_show(fig)

import os  # noqa: E402

_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(_png, scale=2)
print("saved:", _png)

# 출력: saved: .../87818820-709e-4fd8-a50a-a98291bb4f7f/expy.png

# %% [markdown]
# ## 정리
#
# | 작성법 | Alice | Bob | Carol | Dave | 결과 집합 |
# |---|---|---|---|---|---|
# | 카드 질의(두 경로 한 `MATCH`) | O | **O(오답)** | **X(오답)** | 탈락 | Alice, Bob |
# | `DISTINCT` (노드 ID 기준) | O | X | O | 탈락 | Alice, Carol |
# | 순차 집계 (`MATCH`+`WITH` 반복) | O | X | O | 탈락 | Alice, Carol |
# | 서브질의 / `OPTIONAL MATCH` | O | X | O | O | Alice, Carol, Dave |
#
# - 쉼표로 나열한 두 경로는 공유 변수 `c` 기준 **inner join**이며 곱집합을 만든다.
# - `WITH`는 집계 경계를 만들고, 뒤따르는 `WHERE`는 `HAVING` 역할을 한다.
# - 정답을 원하면 경로별로 집계 경계를 따로 두거나 서브질의로 분리한다.
# - 한쪽 상품이 없는 고객까지 세분화하려면 `OPTIONAL MATCH`가 필요하다.
