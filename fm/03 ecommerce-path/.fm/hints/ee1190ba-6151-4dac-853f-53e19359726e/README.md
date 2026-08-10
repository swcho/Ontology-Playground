# Session entity란 무엇인가?

## 한 줄 정답

**장바구니(Shopping-Cart)처럼 진행 중이거나 일시적인 상태를 담는 임시 객체 엔티티**다. 확정된 거래 기록(Order)과 달리 가변적이며, 세션이 끝나면 사라지거나 다른 엔티티로 전환된다.

---

## 1. 왜 이런 엔티티가 필요한가

E-Commerce 온톨로지의 뼈대는 **구매 흐름(purchase flow)** 이다.

```
Buyer --places--> Order --includes--> Product
```

그런데 이 세 엔티티만으로는 **"결제 직전까지의 세계"** 를 전혀 표현하지 못한다. 모든 브라우징 세션이 구매로 이어지지는 않기 때문이다. 원문의 표현대로:

> Not every browsing session leads to a purchase. The **Shopping Cart** captures what a buyer is considering before checking out. It's a session entity — temporary and mutable.

즉 Session entity는 **"아직 확정되지 않았지만 지금 현재 진행 중인 상태"** 를 온톨로지 안에 1급 시민으로 올려놓기 위한 모델링 장치다.

---

## 2. 핵심 특성 3가지

| 특성 | 설명 |
|---|---|
| **Temporary (일시적)** | 세션 수명 동안만 존재한다. 세션 종료·체크아웃·만료 시 사라지거나 다른 엔티티로 전환된다. |
| **Mutable (가변적)** | 담긴 내용이 계속 바뀐다. 상품을 담고 빼고 수량을 바꾼다. |
| **Current-state (현재 상태)** | 누적 이력이 아니라 "지금 이 순간의 상태" 하나만 의미가 있다. |

이 세 특성이 곧 **Order와의 차이**를 만든다.

---

## 3. Session entity vs. Transaction record (Cart vs. Order)

이 카드의 핵심 대비 지점이다.

| 축 | **Shopping-Cart** (Session entity) | **Order** (확정된 거래 기록) |
|---|---|---|
| 성격 | 진행 중 / 임시 | 확정 / 영구 |
| 가변성 | 계속 변함 (mutable) | 사실상 불변 (immutable record) |
| 수명 | 세션과 함께 소멸 또는 전환 | 영구 보존 (감사·정산·배송 근거) |
| 개수 | 바이어당 **활성 카트 1개** | 바이어당 시간이 지나며 **누적 다수** |
| 관계 카디널리티 | `has_cart` → **one-to-one** | `places` → **one-to-many** |
| 대표 질의 | "이번 주 버려진 카트는 몇 개인가" | "이 주문의 총액과 배송 방법은" |

원문의 노트를 그대로 옮기면:

> **One-to-one pattern:** The `has_cart` relationship is one-to-one because each buyer has a single active shopping session. This is different from orders (one-to-many) because a buyer **accumulates orders over time but only has one cart at any moment**.

👉 암기 포인트: **Order는 쌓이고, Cart는 갱신된다.**

---

## 4. Shopping-Cart 엔티티 정의 (자료 기준)

| Property | Type | Identifier? |
|---|---|---|
| `cartId` | string | ✓ |
| `createdAt` | datetime | |
| `itemCount` | integer | |
| `subtotal` | decimal (USD) | |

- `createdAt`이 있다는 점이 session 성격을 드러낸다. **"언제 시작된 세션인가"** 가 곧 카트 만료·이탈 판정의 기준이 된다.
- `itemCount`, `subtotal`은 **비정규화(denormalized) 요약 속성**이다. 카트에 담긴 상품들로부터 계산할 수도 있지만, 직접 저장해두면 질의가 빨라진다. (저장 공간을 쓰고 질의 속도를 얻는 트레이드오프)

### 관계

- **has_cart** — `Buyer` → `Shopping-Cart` (**one-to-one**)
  각 바이어는 정확히 하나의 활성 카트를 가지고, 각 카트는 정확히 한 바이어에게 속한다.
- **contains** — `Shopping-Cart` → `Product` (**many-to-many**)
  카트는 여러 상품을 담을 수 있고, 상품은 여러 카트에 담길 수 있다.

---

## 5. Session entity를 모델링하면 무엇을 물을 수 있게 되는가

Cart가 없으면 아예 물어볼 수 없는 질문들이 열린다.

- "이번 주에 **버려진 카트(abandoned cart)** 는 몇 개인가?"
- "**평균 카트 금액 vs 평균 주문 금액**은 얼마나 차이 나는가?"
- "카트에는 자주 담기지만 **끝내 구매되지 않는 상품**은 무엇인가?"
- "카트는 채웠는데 주문은 없는 바이어는 누구인가?"
  → 그래프 경로: `Buyer → Cart (itemCount > 0)` 는 있는데 `Buyer → Order` 는 없는 노드

즉 Session entity는 **전환 퍼널(conversion funnel) 분석**의 전제 조건이다. 확정 기록만 저장하는 모델은 "성공한 거래"만 볼 수 있고, **실패·이탈·미결정**을 볼 수 없다.

### GQL 예시 (Cart를 경유하는 질의)

```gql
MATCH (b:Buyer)-[:has_cart]->(c:Cart)-[:contains]->(p:Product)<-[:reviews]-(r:Review)
WHERE r.verified = true
RETURN p.name, r.rating, r.title
```

---

## 6. 다른 Session entity 사례

Cart는 대표 사례일 뿐, 패턴 자체는 도메인 전반에 적용된다. 원문도 "carts, drafts, sessions"라고 묶어 표현한다.

| 도메인 | Session entity (임시) | 전환 후 확정 엔티티 |
|---|---|---|
| 이커머스 | Shopping-Cart | Order |
| 문서/CMS | Draft | Published Document |
| 예약 | Hold / Reservation-Hold | Booking |
| 인증 | Login Session | Audit Log |
| 결제 | Payment Intent | Payment / Transaction |

공통 구조는 **`임시 상태 → (확정 이벤트) → 불변 기록`** 이다. 체크아웃이 카트를 주문으로 바꾸는 것처럼, 확정 시점에 session entity의 내용이 영구 기록으로 **전환(materialize)** 된다.

---

## 7. 자주 하는 실수

- ❌ **"카트는 임시니까 온톨로지에 넣지 말자"**
  → 임시라는 것과 모델링 가치가 없다는 것은 다르다. 이탈 분석의 핵심 자산이다.
- ❌ **Cart와 Order를 하나의 엔티티로 합치고 `status`로 구분**
  → 카디널리티가 달라진다(활성 1개 vs 누적 다수). 불변성 요구도 달라진다. 분리가 맞다.
- ❌ **`has_cart`를 one-to-many로 설정**
  → "한 시점에 활성 카트는 하나"라는 도메인 제약을 잃는다. one-to-one이 이 규칙을 스키마 수준에서 강제한다.

---

## 8. 관련 퀴즈 (원문 수록)

> **Q. `has_cart` 관계가 왜 one-to-many가 아니라 one-to-one인가?**
> **A. 각 바이어는 어느 시점에나 정확히 하나의 활성 카트를 갖기 때문이다.**
>
> 바이어는 한 번에 하나의 활성 쇼핑 세션(카트)만 유지한다. 생애에 걸쳐 누적되는 주문과 달리, 카트는 **현재 상태(current-state) 엔티티** — 한 바이어에 하나의 활성 카트다.

---

## 요약 카드

| 질문 | 답 |
|---|---|
| Session entity란? | 진행 중·일시적 상태를 담는 임시 객체 엔티티 (예: Shopping-Cart) |
| 성격은? | temporary, mutable, current-state |
| Order와 차이는? | Order는 확정·불변·누적 / Cart는 미확정·가변·단일 활성 |
| 끝나면? | 소멸하거나 확정 엔티티(Order)로 전환 |
| 왜 필요? | 이탈·전환 퍼널 분석 (abandoned cart, cart-to-order 비율) |
