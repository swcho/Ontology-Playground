# contains 관계는 왜 many-to-many인가

**Q.** `contains` relationship이 one-to-many가 아니라 many-to-many인 이유는?

**A.** 주문에는 보통 라떼·머핀·원두 봉지처럼 여러 제품이 함께 담기고, 동시에 각 제품은 수많은 서로 다른 주문에 등장한다. 이 양방향 다중성(bidirectional multiplicity) 때문에 many-to-many가 필요하다.

---

## 1. 카디널리티를 고르는 절차: "몇 개?"를 **양쪽 모두** 물어라

카디널리티는 관계의 성질이 아니라 **두 방향 질문의 답을 합친 결과**다. 그래서 한쪽만 보고 결정하면 반드시 틀린다. 절차는 항상 세 단계다.

1. 관계의 **출발 엔터티 → 도착 엔터티** 방향으로 "하나당 몇 개?"를 묻는다.
2. **반대 방향**으로도 똑같이 "하나당 몇 개?"를 묻는다.
3. 두 답(one / many)을 조합한다.

`contains` (`Order` → `Product`)에 적용하면:

| 방향 | 질문 | 답 |
|---|---|---|
| Order → Product | 한 Order가 담을 수 있는 Product 수는? | **여러 개** (라떼 + 머핀 + 원두) |
| Product → Order | 한 Product가 등장할 수 있는 Order 수는? | **여러 개** (라떼는 매일 수백 건의 주문에) |

두 방향이 모두 "many" → **many-to-many**. 이것이 답의 전부이며, 어느 한쪽만 many였다면 many-to-many가 아니다.

### 조합표 (Fourth Coffee 온톨로지 전체)

| Relationship | 정방향 질문 | 역방향 질문 | 결과 |
|---|---|---|---|
| `places` (Customer → Order) | 고객 1명이 낼 주문 수? **여러 개** | 주문 1건의 고객 수? **1명** | one-to-many |
| `contains` (Order → Product) | 주문 1건의 제품 수? **여러 개** | 제품 1개가 실린 주문 수? **여러 개** | **many-to-many** |
| `processedAt` (Order → Store) | 주문 1건이 처리되는 매장 수? **1곳** | 매장 1곳이 처리하는 주문 수? **여러 개** | many-to-one |
| `sourcedFrom` (Product → Supplier) | 제품 1개의 공급사 수? **1곳** | 공급사 1곳이 대는 제품 수? **여러 개** | many-to-one |
| `carries` (Shipment → Product) | 배송 1건의 제품 수? **여러 개** | 제품 1개가 실린 배송 수? **여러 개** | many-to-many |

`places`와 `contains`를 나란히 보면 차이가 선명하다. 둘 다 "정방향은 여러 개"지만, `places`는 **역방향이 1**이라서 one-to-many에서 멈춘다. 주문은 결제한 고객 한 명에게 귀속되기 때문이다. `contains`는 역방향도 열려 있어 한 칸 더 나아간다.

`processedAt`은 방향만 뒤집힌 같은 모양이다. 자료에서도 "Order 관점에서는 many-to-one"이라고 명시한다. 즉 **one-to-many와 many-to-one은 같은 구조를 어느 쪽에서 읽었는지의 차이**이고, many-to-many만이 방향을 바꿔도 구조가 바뀌지 않는 유일한 형태다.

## 2. 데이터로 확인하기 — 주장이 아니라 관찰

Fourth Coffee의 실제 주문 몇 건을 펼쳐 보면 양방향 다중성이 눈에 보인다.

| orderId | customerId | 담긴 Product |
|---|---|---|
| order-1001 | cust-01 | prod-latte, prod-muffin |
| order-1002 | cust-02 | prod-latte, prod-coldbrew |
| order-1003 | cust-01 | prod-beans-ethiopia, prod-muffin, prod-latte |

두 방향을 각각 읽어 보자.

- **행 방향(→)**: `order-1003` 한 줄에 제품이 3개 있다. Order 하나가 여러 Product를 가진다. ✅
- **열 방향(←)**: `prod-latte`를 세로로 따라가면 order-1001, order-1002, order-1003에 모두 등장한다. Product 하나가 여러 Order에 속한다. ✅

`prod-latte`가 세 주문에 반복 등장하는 이 그림이 바로 many-to-many의 증거다. 반대로 `customerId` 열을 보면 각 주문에 고객이 **정확히 하나씩만** 적혀 있다 — `places`가 one-to-many에 머무는 이유가 같은 표 안에서 대조된다. (`cust-01`이 order-1001과 order-1003 두 건을 가진 것은 "고객당 주문 여러 개" 쪽이다.)

## 3. 잘못 모델링하면 무슨 일이 생기는가

`contains`를 one-to-many로 강제하면 두 갈래로 깨진다. 어느 쪽으로 밀든 정보가 손상된다.

### (a) "Order 하나 : Product 여러 개, 단 Product는 Order 하나에만" 으로 밀면 → 제품 행 복제

Product가 단 하나의 Order에만 속할 수 있으므로, 같은 라떼를 세 주문에서 팔면 라떼 행을 주문마다 따로 만들어야 한다.

| productId | name | price | 소속 order |
|---|---|---|---|
| prod-latte-1001 | 라떼 | 5.50 | order-1001 |
| prod-latte-1002 | 라떼 | 5.50 | order-1002 |
| prod-latte-1003 | 라떼 | 5.50 | order-1003 |

이 순간 Product는 더 이상 **"카탈로그 상의 제품"이라는 엔터티가 아니라 주문 명세서 한 줄**로 격하된다. 부작용:

- `productId`가 식별자로서 의미를 잃는다. "라떼"라는 개념의 안정적 키가 사라진다.
- 라떼 가격을 5.50 → 5.80으로 올리려면 수천 개 복제 행을 모두 수정해야 하고, 일부만 고쳐지면 데이터가 불일치한다(갱신 이상, update anomaly).
- "라떼가 가장 많이 팔린 제품인가?"를 물으려면 이름 문자열로 묶어야 한다. 온톨로지가 없애려던 바로 그 종류의 문제로 되돌아간다.
- `sourcedFrom` (Product → Supplier)도 함께 오염된다. 하나의 공급사 관계가 주문 수만큼 중복 기록된다.

### (b) 반대로 "Order 하나에 Product 하나"로 밀면 → 라인 아이템 소실

Order에 `productId` 칼럼 하나만 두면 order-1003의 3개 품목 중 1개만 남는다. 나머지는 표현할 자리가 없어 **버려진다**. 그러면 `Order.total`이 실제 담긴 품목 합계와 맞지 않고, 장바구니 구성·함께 구매 분석·재고 차감이 모두 불가능해진다. 아니면 주문 하나를 품목마다 쪼개 order-1003a/b/c로 나눠야 하는데, 그러면 "한 번의 거래"라는 Order의 의미와 결제·상태(`status`) 관리가 무너진다.

정리하면, one-to-many는 **한쪽 엔터티의 정체성을 희생해서** 관계를 억지로 끼워 맞춘다. 양방향 다중성이 실재하는 도메인에서는 many-to-many가 유일하게 손실 없는 표현이다.

## 4. 물리 저장에서는 junction table로 구체화된다 — 그리고 그것이 hub entity의 씨앗

논리 모델의 many-to-many는 관계형 저장소에 그대로 담을 수 없다. 실제로는 **연결 테이블(junction table, 교차/브리지 테이블)** 로 풀린다. 즉 many-to-many 하나가 두 개의 many-to-one으로 분해된다.

```
Order 1---* OrderLine *---1 Product
```

| orderId | productId | quantity | unitPrice |
|---|---|---|---|
| order-1001 | prod-latte | 1 | 5.50 |
| order-1001 | prod-muffin | 2 | 3.25 |
| order-1003 | prod-latte | 1 | 5.50 |
| order-1003 | prod-beans-ethiopia | 1 | 18.00 |

여기서 결정적인 관찰이 하나 나온다. 이 테이블에는 `quantity`, `unitPrice`, 할인율, 옵션(샷 추가, 오트밀크) 같은 **관계 자체에 붙는 속성**이 생긴다. 이 속성들은 Order에도 Product에도 속하지 않는다. "이 주문에서 이 제품이 어떻게 팔렸는가"에만 속한다.

속성을 가진 연결 테이블은 사실상 **하나의 엔터티**다. 이름을 붙여 주면(`OrderLine`, `LineItem`) 온톨로지의 정식 시민이 되고, 두 개의 many-to-one 관계를 갖는다. 이것이 자료의 **Shipment** 와 정확히 같은 구조다.

- `Shipment` 는 `sentBy` (→ Supplier), `deliveredTo` (→ Store), `carries` (→ Product) 를 가지며 sourcing·logistics·retail 도메인을 잇는다.
- 그 자체의 속성(`dispatchDate`, `arrivalDate`, `status`, `weight`)을 가진다 — 어느 한쪽 엔터티에 귀속되지 않는 속성들.

즉 **many-to-many에 속성이 붙기 시작하면 그것은 hub entity가 되려는 신호**다. `contains`는 아직 이름 없는 관계로 남겨 두었지만, 같은 논리를 한 단계 더 밀면 `Shipment` 같은 독립 엔터티로 승격된다. Step 1의 `contains`와 Step 3의 `Shipment`는 서로 다른 개념이 아니라 **같은 패턴의 두 성숙 단계**다.

## 5. 한 줄 요약

- 카디널리티는 **양방향 "몇 개?" 질문**의 답을 조합한 결과다. 한쪽만 보면 틀린다.
- `contains`는 양쪽이 모두 many → many-to-many. `places`는 역방향이 1 → one-to-many. `processedAt`은 정방향이 1 → many-to-one.
- 잘못 one-to-many로 두면 제품 행이 복제되어 Product의 정체성이 깨지거나, 라인 아이템이 사라진다.
- 물리 저장에서는 `quantity`·`unitPrice`를 갖는 junction table로 구체화되고, 그것이 `Shipment` 같은 hub entity의 씨앗이다.
