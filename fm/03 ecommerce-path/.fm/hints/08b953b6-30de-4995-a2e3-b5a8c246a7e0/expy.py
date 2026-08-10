# %% [markdown]
# # 장바구니 분석 → 전환 퍼널(conversion funnel)
#
# 이 노트북은 E-Commerce 온톨로지(Buyer / Product / Shopping-Cart / Order / Review)에서
# **그래프 경로 존재 여부**만으로 전환 퍼널을 계산하는 과정을 단계별로 보여준다.
#
# 퍼널 단계와 온톨로지 경로 매핑:
#
# | 단계 | 의미 | 그래프 경로 |
# |---|---|---|
# | view | 상품을 봄 | (온톨로지 밖 · 분석 웨어하우스의 view 이벤트) |
# | cart | 장바구니에 담음 | `Buyer -has_cart-> Shopping-Cart -contains-> Product` |
# | order | 주문 완료 | `Buyer -places-> Order -includes-> Product` |
# | review | 후기 작성 | `Buyer -writes-> Review -reviews-> Product` |
#
# 핵심 수식:
#
# $$c_i = \frac{N_i}{N_{i-1}}, \qquad C_{\text{total}} = \frac{N_{\text{last}}}{N_0} = \prod_i c_i$$
#
# 장바구니 이탈률(abandonment rate):
#
# $$A = 1 - \frac{N_{\text{order}}}{N_{\text{cart}}} = 1 - c_{\text{cart}\to\text{order}}$$

# %%
# 필요 패키지: numpy, pandas, plotly, kaleido
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


RNG = np.random.default_rng(20260810)
HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()

print("setup ok", HERE.name)
# 출력: setup ok 08b953b6-30de-4995-a2e3-b5a8c246a7e0

# %% [markdown]
# ## 1단계 — 합성 Buyer / Product 노드 만들기
#
# 실제 온톨로지의 식별자 규칙을 그대로 따른다: `Buyer.buyerId`, `Product.sku`.

# %%
N_BUYERS = 2_000
N_PRODUCTS = 30

buyers = [f"B{i:04d}" for i in range(N_BUYERS)]
products = pd.DataFrame(
    {
        "sku": [f"SKU-{i:03d}" for i in range(N_PRODUCTS)],
        "category": RNG.choice(["Home", "Tech", "Apparel"], size=N_PRODUCTS),
        "price": np.round(RNG.uniform(9.0, 180.0, size=N_PRODUCTS), 2),
    }
)
price_of = dict(zip(products["sku"], products["price"]))

print(len(buyers), "buyers /", len(products), "products")
print(products.head(3).to_string(index=False))
# 출력: 2000 buyers / 30 products
# 출력:     sku category  price
# 출력: SKU-000  Apparel 177.83
# 출력: SKU-001     Home 148.03
# 출력: SKU-002     Home 168.54

# %% [markdown]
# ## 2단계 — 엣지(관계) 생성
#
# 각 관계를 `(buyerId, sku)` 페어 집합으로 저장한다. 페어가 존재한다는 것은
# 그 Buyer에서 그 Product로 가는 **경로가 그래프에 존재**한다는 뜻이다.
#
# - `viewed` : 분석 웨어하우스의 view 이벤트 (퍼널의 출발점)
# - `cart_contains` : `has_cart` + `contains` 경로
# - `order_includes` : `places` + `includes` 경로
# - `review_pairs` : `writes` + `reviews` 경로
#
# 실제 시장처럼 뒤로 갈수록 통과 확률이 낮아지도록 만든다.

# %%
P_CART = 0.45  # 본 상품을 담을 확률
P_ORDER = 0.18  # 담은 상품을 주문할 확률  ← 병목 후보
P_REVIEW = 0.40  # 주문한 상품에 후기를 쓸 확률

viewed, cart_contains, order_includes, review_pairs = set(), set(), set(), set()
carts, orders = [], []  # Shopping-Cart / Order 노드의 속성 기록용

for b in buyers:
    seen = RNG.choice(products["sku"], size=RNG.integers(1, 6), replace=False)
    for sku in seen:
        viewed.add((b, sku))

    in_cart = [s for s in seen if RNG.random() < P_CART]
    if not in_cart:
        continue
    # Buyer -has_cart-> Shopping-Cart (one-to-one)
    for sku in in_cart:
        cart_contains.add((b, sku))
    carts.append({"buyerId": b, "itemCount": len(in_cart), "subtotal": sum(price_of[s] for s in in_cart)})

    bought = [s for s in in_cart if RNG.random() < P_ORDER]
    if not bought:
        continue
    for sku in bought:
        order_includes.add((b, sku))
    orders.append({"buyerId": b, "total": sum(price_of[s] for s in bought)})

    for sku in bought:
        if RNG.random() < P_REVIEW:
            review_pairs.add((b, sku))

carts = pd.DataFrame(carts)
orders = pd.DataFrame(orders)
print(f"엣지 수 — viewed={len(viewed)} cart={len(cart_contains)} order={len(order_includes)} review={len(review_pairs)}")
# 출력: 엣지 수 — viewed=5881 cart=2610 order=459 review=172

# %% [markdown]
# ## 3단계 — 경로 존재 여부로 단계별 인원 세기
#
# 퍼널은 **Buyer 단위**로 센다. "한 번이라도 그 단계에 도달한 사람 수"이므로
# 각 페어 집합에서 `buyerId`만 뽑아 유일값 개수를 구하면 된다.

# %%
def reach(pairs: set) -> set:
    """해당 경로가 하나라도 존재하는 Buyer 집합."""
    return {b for b, _ in pairs}


stages = ["view", "cart", "order", "review"]
reached = {
    "view": reach(viewed),
    "cart": reach(cart_contains),
    "order": reach(order_includes),
    "review": reach(review_pairs),
}
counts = np.array([len(reached[s]) for s in stages], dtype=float)

funnel = pd.DataFrame({"stage": stages, "buyers": counts.astype(int)})
print(funnel.to_string(index=False))
# 출력:  stage  buyers
# 출력:   view    2000
# 출력:   cart    1518
# 출력:  order     416
# 출력: review     164

# %% [markdown]
# ## 4단계 — 단계 전환율 $c_i$, 전체 전환율 $C_{\text{total}}$, 이탈률 $A$
#
# $$c_i = \frac{N_i}{N_{i-1}}, \qquad C_{\text{total}} = \prod_i c_i = \frac{N_{\text{review}}}{N_{\text{view}}}$$
#
# 전체 전환율은 단계 전환율의 **곱**이므로, 어느 한 단계가 낮으면 나머지가 아무리 좋아도
# 전체가 그 단계에 끌려 내려간다.

# %%
step_rates = counts[1:] / counts[:-1]
step_names = [f"{a}→{b}" for a, b in zip(stages[:-1], stages[1:])]

total_by_product = float(np.prod(step_rates))
total_direct = counts[-1] / counts[0]

for name, r in zip(step_names, step_rates):
    print(f"{name:<14} c = {r:6.2%}")
print(f"\nC_total (곱)   = {total_by_product:.4%}")
print(f"C_total (직접) = {total_direct:.4%}   <- 동일해야 함")

abandonment = 1 - step_rates[1]
print(f"\n장바구니 이탈률 A = 1 - c(cart→order) = {abandonment:.2%}")
# 출력: view→cart      c = 75.90%
# 출력: cart→order     c = 27.40%
# 출력: order→review   c = 39.42%
# 출력:
# 출력: C_total (곱)   = 8.2000%
# 출력: C_total (직접) = 8.2000%   <- 동일해야 함
# 출력:
# 출력: 장바구니 이탈률 A = 1 - c(cart→order) = 72.60%

# %% [markdown]
# ## 5단계 — 평균 장바구니 금액(ACV) vs 평균 주문 금액(AOV)
#
# `Shopping-Cart.subtotal`과 `Order.total`의 평균을 비교하면 **금액 기준 이탈**이 보인다.
#
# $$\text{금액 전환율} = \frac{\sum \text{Order.total}}{\sum \text{Cart.subtotal}}$$
#
# 인원 전환율보다 금액 전환율이 더 낮으면 "비싼 장바구니가 더 많이 이탈한다"는 뜻이고,
# 배송비·결제 수단·할부 같은 결제 단계 마찰을 의심해야 한다.

# %%
acv = carts["subtotal"].mean()
aov = orders["total"].mean()
value_rate = orders["total"].sum() / carts["subtotal"].sum()

print(f"평균 장바구니 금액 ACV = ${acv:,.2f}  (n={len(carts)})")
print(f"평균 주문 금액   AOV = ${aov:,.2f}  (n={len(orders)})")
print(f"AOV / ACV            = {aov / acv:.2%}")
print(f"금액 기준 전환율      = {value_rate:.2%}  vs  인원 기준 {step_rates[1]:.2%}")
# 출력: 평균 장바구니 금액 ACV = $179.70  (n=1518)
# 출력: 평균 주문 금액   AOV = $116.39  (n=416)
# 출력: AOV / ACV            = 64.77%
# 출력: 금액 기준 전환율      = 17.75%  vs  인원 기준 27.40%

# %% [markdown]
# ## 6단계 — 병목 단계 찾기 & 개선 민감도
#
# 한 단계 $k$의 전환율을 $c_k \to c_k + \Delta$ 로 올리면
#
# $$C'_{\text{total}} = C_{\text{total}} \cdot \frac{c_k + \Delta}{c_k}
# \quad\Longrightarrow\quad
# \frac{\Delta C}{C} = \frac{\Delta}{c_k}$$
#
# **같은 절대 개선폭 $\Delta$라도 상대 효과는 $c_k$가 작은 단계(=병목)에서 가장 크다.**
# 이것이 개선 노력을 병목에 집중해야 하는 수학적 이유다.

# %%
DELTA = 0.05  # 모든 단계에 동일하게 +5%p

bottleneck = int(np.argmin(step_rates))
print(f"병목 단계: {step_names[bottleneck]} (c = {step_rates[bottleneck]:.2%})\n")

rows = []
for i, (name, c) in enumerate(zip(step_names, step_rates)):
    new_rates = step_rates.copy()
    new_rates[i] = c + DELTA
    new_total = float(np.prod(new_rates))
    rows.append(
        {
            "개선 단계": name,
            "c": c,
            "c+Δ": c + DELTA,
            "C_total'": new_total,
            "절대증가(pp)": (new_total - total_by_product) * 100,
            "상대증가": new_total / total_by_product - 1,
        }
    )
sens = pd.DataFrame(rows)
print(sens.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
print(f"\n기준 C_total = {total_by_product:.4%}")
print(f"이론값 Δ/c_k  = {[f'{DELTA / c:.1%}' for c in step_rates]}  <- '상대증가'와 일치")
# 출력: 병목 단계: cart→order (c = 27.40%)
# 출력:
# 출력:        개선 단계      c    c+Δ  C_total'  절대증가(pp)   상대증가
# 출력:    view→cart 0.7590 0.8090    0.0874    0.5402 0.0659
# 출력:   cart→order 0.2740 0.3240    0.0970    1.4961 0.1825
# 출력: order→review 0.3942 0.4442    0.0924    1.0400 0.1268
# 출력:
# 출력: 기준 C_total = 8.2000%
# 출력: 이론값 Δ/c_k  = ['6.6%', '18.2%', '12.7%']  <- '상대증가'와 일치

# %% [markdown]
# ## 7단계 — 시각화
#
# 왼쪽: 퍼널 차트(단계별 인원). 오른쪽: 같은 +5%p를 어느 단계에 쓰느냐에 따른
# 전체 전환율 증가폭 비교 — 막대가 가장 높은 곳이 병목이다.

# %%
INK = "#1f2933"
BASE = "#7b8794"
ACCENT = "#c2410c"
STEPS = ["#94a3b8", "#7c8da3", "#64748b", "#475569"]

fig = make_subplots(
    rows=1,
    cols=2,
    column_widths=[0.48, 0.52],
    subplot_titles=(
        f"전환 퍼널 (C_total = {total_by_product:.2%})",
        f"+{DELTA:.0%}p 투입 시 전체 전환율 증가",
    ),
    specs=[[{"type": "funnel"}, {"type": "xy"}]],
)

fig.add_trace(
    go.Funnel(
        y=stages,
        x=counts,
        textinfo="value+percent previous",
        marker=dict(color=STEPS),
        connector=dict(line=dict(color=BASE, width=1)),
        hovertemplate="%{y}: %{x:,.0f}명<extra></extra>",
        showlegend=False,
    ),
    row=1,
    col=1,
)

fig.add_trace(
    go.Bar(
        x=sens["개선 단계"],
        y=sens["절대증가(pp)"],
        marker_color=[ACCENT if i == bottleneck else BASE for i in range(len(sens))],
        text=[f"+{v:.2f}pp" for v in sens["절대증가(pp)"]],
        textposition="outside",
        hovertemplate="%{x}<br>전체 전환율 +%{y:.2f}pp<extra></extra>",
        showlegend=False,
    ),
    row=1,
    col=2,
)

fig.update_yaxes(title_text="C_total 증가 (%p)", row=1, col=2, gridcolor="#e5e7eb", zerolinecolor="#e5e7eb")
fig.update_xaxes(row=1, col=2, showgrid=False)
fig.update_layout(
    title=dict(text="장바구니 분석 → 전환 퍼널과 병목 민감도", font=dict(size=18, color=INK)),
    template="plotly_white",
    font=dict(color=INK, size=13),
    width=1100,
    height=520,
    margin=dict(t=100, b=60, l=90, r=40),
    annotations=list(fig.layout.annotations)
    + [
        dict(
            x=0.5,
            y=-0.16,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=12, color=BASE),
            # 주의: plotly는 텍스트의 '$...$'를 MathJax로 해석하므로 통화기호 대신 USD 표기를 쓴다
            text=(
                f"장바구니 이탈률 {abandonment:.1%} · ACV {acv:,.0f} USD → AOV {aov:,.0f} USD · "
                f"병목 = {step_names[bottleneck]} (c = {step_rates[bottleneck]:.1%})"
            ),
        )
    ],
)

_show(fig)

out = HERE / "expy.png"
fig.write_image(str(out), scale=2)  # kaleido 필요
print("saved:", out)
# 출력: saved: .../08b953b6-30de-4995-a2e3-b5a8c246a7e0/expy.png

# %% [markdown]
# ## 정리
#
# 1. 장바구니(Shopping-Cart)는 **주문 이전 상태를 붙잡아 두는 세션 엔티티**라서,
#    퍼널의 중간 지점을 관측 가능하게 만든다. 카트가 없으면 view와 order 사이가 블랙박스다.
# 2. 각 단계는 그래프 **경로 존재 여부**로 셀 수 있다 — 별도 ETL 없이
#    `has_cart→contains`, `places→includes`, `writes→reviews` 패턴만으로 계산된다.
# 3. $C_{\text{total}} = \prod_i c_i$ 이므로 전체 전환율은 곱셈. 상대 개선 효과는 $\Delta / c_k$,
#    즉 **가장 낮은 $c_k$(병목)에 투자할 때 가장 크다.**
# 4. 인원 전환율과 금액 전환율(ACV vs AOV)을 함께 보면 "누가" 이탈했는지에 더해
#    "얼마짜리 장바구니가" 이탈했는지까지 드러난다.
