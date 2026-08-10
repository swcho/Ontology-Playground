# processedAt는 왜 many-to-one인가

**Q.** `processedAt` relationship의 cardinality가 many-to-one인 이유는?

**A.** 각 주문은 정확히 한 매장에서만 처리되지만, 한 매장은 하루 동안 많은 주문을 처리한다. Order 관점에서 보면 many-to-one이다.

---

## 1. 원문이 말하는 것

Fourth Coffee 온톨로지 Step 2에서 Store 엔티티가 추가되며 생기는 관계는 하나다.

> **processedAt** — `Order` → `Store` (many-to-one)
> Each order is processed at exactly one store, but a store processes many orders.
>
> **Design note:** This is a many-to-one relationship. Many orders map to one store. This is the most common cardinality pattern for "belongs to" or "happens at" relationships.

즉 근거는 두 문장으로 쪼개진다.

| 쪽 | 비즈니스 사실 | 다중성 |
|---|---|---|
| Order → Store | 주문 하나는 **정확히 한** 매장에서 처리된다 | **one** |
| Store → Order | 매장 하나는 하루에 **수많은** 주문을 처리한다 | **many** |

이 두 사실을 합치면 "many orders map to one store"가 되고, 이것이 many-to-one이다.

---

## 2. 핵심 함정: 관점(perspective)

이 카드를 틀리는 대부분의 이유는 개념을 몰라서가 아니다. **어느 쪽 끝에서 읽었는지**가 달랐기 때문이다.

```
        processedAt (many-to-one)
  Order ─────────────────────────▶ Store
  (many)                           (one)

        ◀───────────────────────── 같은 관계를 Store에서 읽으면
             (one-to-many)
```

- `Order → Store`를 many-to-one으로 선언한 것과
- `Store → Order`를 one-to-many로 선언한 것은

**내용상 완전히 동일한 하나의 관계**다. 데이터 제약도, 저장 방식도, 답할 수 있는 질문도 같다. 서로 다른 두 종류의 관계가 아니라, **같은 관계를 반대 방향에서 읽은 두 개의 이름**일 뿐이다.

학습자가 이 문제를 틀리는 전형적인 경로는 이렇다.

> "매장 하나가 주문 여러 개를 처리하니까 one-to-many 아닌가?"

이 문장 자체는 **틀리지 않았다**. 다만 그것은 `Store → Order` 방향의 서술이다. 문제가 묻는 것은 `processedAt`, 즉 **Order에서 출발해 Store로 향하는** 관계의 cardinality다. 방향이 반대이므로 라벨도 뒤집힌다.

### 모호함을 없애는 표기 규칙

> **Cardinality는 항상 그 관계가 선언된 방향(source → target)을 기준으로 읽는다.**

`processedAt`의 경우:

- source = `Order` → 여기가 **many** 쪽
- target = `Store` → 여기가 **one** 쪽
- 따라서 **many(Order)-to-one(Store)**

`Customer → Order`의 `places`가 one-to-many인 것도 같은 규칙 때문이다. source가 Customer(one), target이 Order(many)이므로 one-to-many. `places`와 `processedAt`은 "1쪽 하나에 N개가 달린다"는 구조가 사실상 같은데 라벨이 반대인데, 이는 **선언 방향이 반대**이기 때문이다.

| 관계 | source (앞) | target (뒤) | 라벨 |
|---|---|---|---|
| `places` | Customer (one) | Order (many) | one-to-many |
| `processedAt` | Order (many) | Store (one) | many-to-one |

암기 팁: 라벨의 **첫 단어는 언제나 source의 다중성**, **두 번째 단어는 target의 다중성**이다. 화살표를 그려놓고 앞뒤를 그대로 읽으면 절대 헷갈리지 않는다.

---

## 3. 오답 선택지 검증

원 퀴즈의 다른 선택지들이 왜 실패하는지 비즈니스 현실에 대입해 보자.

### ✗ one-to-one — "각 매장에 주문 하나"

one-to-one이려면 **양쪽 모두 최대 1개**여야 한다. 즉 매장 하나가 평생 주문 하나만 처리해야 한다. 커피 체인점의 현실과 정면으로 충돌한다. 매장은 하루에 수백 건을 처리하므로 Store 쪽 다중성은 many여야 한다. one-to-one으로 선언하면 두 번째 주문을 받는 순간 모델 제약을 위반한다. one-to-one은 `Order ↔ Receipt`(주문 하나에 영수증 하나)처럼 **실제로 1:1인 짝**에만 써야 한다.

### ✗ many-to-many — "주문이 여러 매장에서 동시 처리"

many-to-many이려면 Order 쪽도 many여야 한다. 즉 **하나의 주문이 여러 매장에서 동시에 처리**되어야 한다. 라떼 한 잔이 서울점과 부산점에서 동시에 만들어지는 상황인데, 매장에서 제조·픽업하는 주문 모델에서는 성립하지 않는다.

또한 many-to-many는 공짜가 아니다. 필요 없는 many-to-many를 쓰면 "이 주문의 매장은 어디?"라는 질문의 답이 **집합**이 되어, 매장별 매출·주문량 집계가 즉시 애매해진다(중복 집계 위험). 모델이 표현력을 얻는 대신 **정확히 한 곳**이라는 중요한 사실을 잃는다.

비교: 같은 온톨로지에서 `contains`(Order → Product)는 진짜 many-to-many다. 주문 하나에 여러 상품이 담기고, 상품 하나가 여러 주문에 등장한다. **양방향 모두 many**일 때만 many-to-many를 쓴다.

---

## 4. many-to-one은 "belongs to / happens at"의 기본 패턴

원문은 many-to-one을 "belongs to", "happens at", "located at" 패턴의 **가장 흔한** cardinality로 못박는다. 어떤 개체가 **어디에 속하는지 / 어디서 일어났는지 / 누구에게서 왔는지**를 표현하면 거의 항상 many-to-one이다.

Fourth Coffee 온톨로지의 7개 관계 중 **4개가 many-to-one**이다.

| 관계 | 방향 | 읽는 문장 |
|---|---|---|
| `processedAt` | Order → Store | 주문은 한 매장에서 처리된다 (happens at) |
| `sourcedFrom` | Product → Supplier | 상품은 한 공급사에서 조달된다 (comes from) |
| `sentBy` | Shipment → Supplier | 배송은 한 공급사가 발송한다 (sent by) |
| `deliveredTo` | Shipment → Store | 배송은 한 매장에 도착한다 (delivered to) |

나머지 3개: `places`(Customer → Order, one-to-many), `contains`(Order → Product, many-to-many), `carries`(Shipment → Product, many-to-many).

관계 이름이 과거분사/전치사구(`processedAt`, `sourcedFrom`, `sentBy`, `deliveredTo`)라는 점도 신호다. 이런 이름은 **many 쪽에서 one 쪽을 가리키는** 방향으로 자연스럽게 읽히며, 그래서 many-to-one으로 선언된다.

---

## 5. 물리 저장으로의 매핑

cardinality는 추상적 선언이 아니라 실제 저장 구조를 결정한다.

**many-to-one → many 쪽 테이블에 FK 컬럼 하나. junction table 불필요.**

```
Order 테이블
┌──────────┬───────────┬─────────┬──────────────────┐
│ orderId  │ timestamp │ total   │ storeId  (FK) ◀── │ one 쪽을 가리키는 단일 컬럼
├──────────┼───────────┼─────────┼──────────────────┤
│ ORD-001  │ 09:12     │ 12.50   │ STORE-SEA-01     │
│ ORD-002  │ 09:14     │  6.75   │ STORE-SEA-01     │  ← 같은 매장 값 반복 = many
│ ORD-003  │ 09:15     │ 21.00   │ STORE-POR-02     │
└──────────┴───────────┴─────────┴──────────────────┘
```

- 한 행에 `storeId` 컬럼이 **하나**뿐이므로, "주문은 매장 하나"라는 제약이 스키마 수준에서 자동으로 강제된다.
- 값이 여러 행에 반복될 수 있으므로 "매장은 주문 여러 개"가 자연히 표현된다.
- 이것이 many-to-one을 반대 방향(`Store → Order` one-to-many)으로 선언해도 저장 구조가 **똑같아지는** 이유다. FK는 언제나 many 쪽에 놓인다. → 두 라벨이 같은 관계라는 §2의 주장에 대한 물리적 증거.

반면 **many-to-many(`contains`, `carries`)는 FK 컬럼으로 표현할 수 없다.** Order 행에 productId를 몇 개 넣어야 할지 정할 수 없기 때문이다. 그래서 별도의 junction(연결) 테이블이 필요하다.

```
OrderProduct 테이블 (junction)
┌──────────┬────────────┬──────┐
│ orderId  │ productId  │ qty  │
├──────────┼────────────┼──────┤
│ ORD-001  │ PRD-LATTE  │ 2    │
│ ORD-001  │ PRD-MUFFIN │ 1    │
│ ORD-002  │ PRD-LATTE  │ 1    │
└──────────┴────────────┴──────┘
```

정리하면 cardinality 선택은 **테이블 개수를 바꾼다**. 불필요한 many-to-many는 조인 하나와 테이블 하나를 공짜로 늘리고, 집계 시 중복 계산 위험까지 얹는다. many-to-one이 가능한 자리에는 many-to-one을 쓰는 것이 정답이다.

---

## 6. 한 줄 요약

`processedAt`은 `Order`(source) → `Store`(target) 방향으로 선언되어 있고, source 쪽 주문은 여럿, target 쪽 매장은 하나이므로 **many-to-one**이다. "매장이 주문 여러 개를 처리한다"는 서술도 옳지만 그것은 **반대 방향의 이름(one-to-many)**이며, 동일한 관계를 가리킨다. 헷갈릴 때는 화살표를 그리고 **앞→뒤 순서대로** 다중성을 읽으면 된다.
