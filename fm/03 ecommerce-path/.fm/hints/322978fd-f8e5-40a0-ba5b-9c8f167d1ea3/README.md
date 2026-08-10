# 장바구니 속 상품의 verified 리뷰 찾기 — GQL 질의 해부

## 한 줄 답

```gql
MATCH (b:Buyer)-[:has_cart]->(c:Cart)-[:contains]->(p:Product)<-[:reviews]-(r:Review)
WHERE r.verified = true
RETURN p.name, r.rating, r.title
```

`Buyer → Cart → Product` 로 "지금 담겨 있는 상품"을 찾고, 그 상품에 **거꾸로 꽂히는** `Review`를 붙인 뒤(`<-[:reviews]-`), `verified = true`로 걸러 상품명·평점·리뷰 제목만 뽑는다.

이 한 줄에 온톨로지의 세 관계(`has_cart`, `contains`, `reviews`)가 그대로 들어가 있다는 것이 핵심이다. **온톨로지를 잘 설계했다면 질의는 그림을 그대로 베껴 쓴 것처럼 보인다.**

---

## 1. GQL은 어디에 서 있는 언어인가

| 항목 | 내용 |
|---|---|
| 정식 명칭 | **ISO/IEC 39075:2024** — Information technology — Database languages — **GQL** |
| 공표 시점 | 2024년 4월 |
| 역사적 의미 | ISO가 **SQL(1987) 이후 37년 만에** 새로 제정한 데이터베이스 질의 언어 표준 |
| 대상 데이터 모델 | **속성 그래프(property graph)** — 노드/엣지에 레이블과 속성(key-value)이 붙는 모델 |

### Cypher와의 관계

GQL은 무에서 나온 것이 아니라 **Neo4j의 Cypher(및 오픈 규격인 openCypher)** 를 뼈대로, PGQL·G-CORE 등의 아이디어와 SQL의 문법 관습을 흡수해 표준화한 것이다.

- **거의 같은 부분** — `MATCH … WHERE … RETURN`이라는 핵심 구조, 아스키 아트식 경로 패턴 `(a)-[:REL]->(b)`. 이 카드의 질의는 Cypher로 붙여넣어도 그대로 동작한다.
- **달라진 부분** — 쓰기 문법이 대표적이다. Cypher의 `CREATE` 대신 GQL은 **`INSERT`** 를 쓴다(SQL 관습 쪽으로 정렬).
- **더해진 부분** — 그래프 객체 카탈로그, 더 풍부한 타입 시스템, 표준 오류 처리, 그리고 Cypher의 약점으로 지적되던 **정규 경로 질의(RPQ, regular path query)** 에 대한 강화된 패턴 매칭.

> 참고로 **SQL/PGQ**(ISO/IEC 9075-16:2023)라는 사촌도 있다. 이쪽은 "관계형 테이블 위에 그래프 뷰를 씌워 SQL 안에서 `MATCH`를 쓰는" 접근이고, GQL은 "그래프가 1급 시민인 독립 언어"다.

학습 관점에서의 요점: **온톨로지는 "무엇이 존재하고 어떻게 연결되는가"를 정의하고, GQL은 그 정의 위를 걷는 발걸음이다.** 온톨로지에 없는 관계는 질의로도 걸을 수 없다.

---

## 2. 토큰 단위 해부

### 2.1 `MATCH` — 그래프에서 찾을 "모양"을 그린다

`MATCH`는 SQL의 `FROM` + `JOIN`을 합친 자리다. 다만 테이블을 나열하고 조인 조건을 따로 쓰는 대신, **찾고 싶은 부분 그래프(subgraph)의 모양 자체**를 한 줄로 그린다. 이 모양을 **경로 패턴(path pattern)** 이라 한다.

```
(b:Buyer)-[:has_cart]->(c:Cart)-[:contains]->(p:Product)<-[:reviews]-(r:Review)
   노드      엣지         노드      엣지        노드       역방향 엣지   노드
```

엔진은 그래프 전체를 훑으며 **이 모양에 정확히 맞아떨어지는 모든 조합**을 찾아 각각을 결과 1행으로 만든다.

### 2.2 `(변수:레이블)` — 노드 패턴

| 조각 | 의미 |
|---|---|
| `(b:Buyer)` | `Buyer` 레이블이 붙은 노드를 찾아 변수 `b`에 바인딩 |
| `(c:Cart)` | 장바구니 노드 → `c` |
| `(p:Product)` | 상품 노드 → `p` |
| `(r:Review)` | 리뷰 노드 → `r` |

- **콜론 앞은 변수, 뒤는 레이블.** 변수는 뒤에서 참조(`WHERE r.verified`, `RETURN p.name`)하기 위한 이름표일 뿐이다. 뒤에서 안 쓸 노드는 `()` 또는 `(:Cart)`처럼 변수를 생략해도 된다.
- 여기서 `c`는 사실 `RETURN`에도 `WHERE`에도 등장하지 않는다. **"경유지"** 로서만 존재한다. 엄밀히 하면 `(:Cart)`로 줄여도 결과는 같다.
- 레이블은 온톨로지의 **엔터티 타입**에 대응한다. 온톨로지 문서상 엔터티 이름은 `Shopping-Cart`이지만 질의에서는 `Cart`를 쓴다 — 하이픈은 식별자 문법과 충돌하기 쉬워서 실제 그래프에 실릴 때는 `Cart` / `ShoppingCart` 같은 형태로 정규화되는 것이 보통이다. **개념 이름과 물리 레이블은 다를 수 있다**는 점을 기억해 두면 좋다.

### 2.3 `-[:관계타입]->` — 방향 있는 엣지 패턴

| 조각 | 읽는 법 |
|---|---|
| `-[:has_cart]->` | 왼쪽(`b`)에서 오른쪽(`c`)으로 나가는 `has_cart` 엣지 |
| `-[:contains]->` | `c`에서 `p`로 나가는 `contains` 엣지 |

- 대괄호 안도 노드와 같은 `변수:타입` 문법이다. 엣지의 속성을 쓰고 싶다면 `-[e:contains]->` 처럼 변수를 붙인다(이 질의는 필요 없어 생략).
- **화살표는 장식이 아니다.** 속성 그래프의 엣지는 방향을 가지며, 온톨로지에서 정의한 방향과 어긋나게 쓰면 결과가 0행이 된다.
- 방향을 무시하고 싶으면 `-[:contains]-`(화살촉 없음)로 쓴다.

### 2.4 `<-[:reviews]-` — 역방향 엣지가 등장하는 이유

이 질의에서 **가장 자주 틀리는 지점**이다.

온톨로지의 정의는 다음과 같다.

> **reviews** — `Review` → `Product` (many-to-one)
> 리뷰 하나는 정확히 상품 하나에 대한 것이고, 상품 하나는 여러 리뷰를 가진다.

즉 화살표는 **Review에서 Product를 향한다**. 그런데 우리는 경로를 `Buyer`에서 출발해 `Product`까지 걸어온 상태다. 이어 붙일 `Review`는 Product의 **오른쪽에 쓰되 화살표는 왼쪽(Product)을 향해야** 한다. 그래서:

```
(p:Product)<-[:reviews]-(r:Review)
```

이것은 `(r:Review)-[:reviews]->(p:Product)`와 **완전히 같은 뜻**이다. 문장에서 어느 쪽을 먼저 쓰느냐가 다를 뿐이다. 실제로 이렇게 써도 동일하다.

```gql
MATCH (b:Buyer)-[:has_cart]->(:Cart)-[:contains]->(p:Product),
      (r:Review)-[:reviews]->(p)
WHERE r.verified = true
RETURN p.name, r.rating, r.title
```

(콤마로 여러 패턴을 나열하면 같은 변수 `p`를 통해 자동으로 이어 붙는다.)

**요령**: 한 줄짜리 체인으로 쓸 때, 각 화살표 방향은 "내가 지금 걷고 있는 방향"이 아니라 **"온톨로지에 정의된 관계의 방향"** 을 따라야 한다. 걷는 방향과 관계 방향이 반대면 `<-`가 나온다.

### 2.5 `WHERE r.verified = true` — 속성 필터

- `MATCH`가 **구조(어떻게 연결되어 있나)** 를 거른다면, `WHERE`는 **속성 값(어떤 값을 갖고 있나)** 을 거른다.
- `verified`는 Review 엔터티의 boolean 속성으로, **리뷰어가 실제로 그 상품을 구매했는지**를 나타내는 신뢰 신호다. 이 필터가 "그냥 리뷰"와 "믿을 만한 리뷰"를 가른다.
- boolean이므로 `WHERE r.verified` 만 써도 되지만, `= true`를 명시하면 의도가 분명해진다.
- 노드 패턴 안에 인라인으로 넣을 수도 있다: `(r:Review {verified: true})`. 동등 비교만 필요할 때 짧아지는 대신, 범위 비교(`>=`)나 복합 조건은 `WHERE`를 써야 한다.

### 2.6 `RETURN p.name, r.rating, r.title` — 프로젝션

- SQL의 `SELECT`에 해당한다. **바인딩된 노드 전체가 아니라 필요한 속성만** 골라 표 형태로 내보낸다.
- `RETURN p, r` 처럼 노드 자체를 반환하면 모든 속성이 딸려 나온다. 필요한 열만 뽑는 것이 전송량·가독성 모두에 유리하다.
- 별칭은 `AS`로: `RETURN p.name AS product, r.rating AS rating`.

---

## 3. 이 경로가 대응하는 온톨로지 정의

| 질의 조각 | 온톨로지 관계 정의 | 카디널리티 |
|---|---|---|
| `(b:Buyer)-[:has_cart]->(c:Cart)` | **has_cart** — `Buyer` → `Shopping-Cart` | **one-to-one** (구매자 1명 ↔ 활성 카트 1개) |
| `(c:Cart)-[:contains]->(p:Product)` | **contains** — `Shopping-Cart` → `Product` | **many-to-many** (카트에 여러 상품, 상품은 여러 카트에) |
| `(p:Product)<-[:reviews]-(r:Review)` | **reviews** — `Review` → `Product` | **many-to-one** (리뷰는 상품 하나, 상품은 리뷰 여럿) |

이 질의는 5개 엔터티(Buyer / Product / Order / Shopping-Cart / Review), 6개 관계(places / includes / has_cart / contains / writes / reviews) 중 **관계 3개만 걸어간다**. `places`, `includes`, `writes`는 이 질문에 필요 없다.

> 참고로 `writes`(Buyer → Review)를 쓰지 않았다는 점이 중요하다. 반환되는 리뷰는 **`b`가 쓴 리뷰가 아니라 남들이 쓴 리뷰**다. 의도가 바로 그것이다 — "내가 담아둔 상품에 대해 **다른 사람들이** 남긴, 실구매 인증된 평가"를 보여주는 것.

### 결과 행이 곱해지는 방식

경로 패턴 매칭은 **모든 가능한 조합을 하나씩 행으로 펼친다**. 카디널리티를 따라가면 행 수가 보인다.

```
Buyer 1명
  × has_cart (1:1)        → 카트 1개
  × contains (1:N)        → 카트 안 상품 N개
  × reviews 역방향 (1:M)  → 상품마다 verified 리뷰 M개
```

즉 **행 수 = Σ(카트 속 각 상품의 verified 리뷰 개수)** 다.

구체적인 예 — 카트에 상품 3개가 담겼고 각각 verified 리뷰가 4개 / 0개 / 12개라면:

| 상품 | verified 리뷰 수 | 생성 행 수 |
|---|---|---|
| 무선 이어폰 | 4 | 4 |
| USB 케이블 | 0 | **0** |
| 기계식 키보드 | 12 | 12 |
| **합계** | | **16행** |

여기서 두 가지 함정을 짚어야 한다.

1. **상품명이 중복된다.** "무선 이어폰"이 4번, "기계식 키보드"가 12번 나타난다. 상품 목록이 필요한 것이라면 `RETURN DISTINCT p.name`을 쓰거나 집계로 접어야 한다.
2. **리뷰가 0개인 상품은 아예 사라진다.** `MATCH`는 **inner join**처럼 동작한다 — 패턴 전체가 맞아야 행이 생긴다. USB 케이블은 카트에 분명히 담겨 있는데도 결과에 없다. "리뷰 없는 상품도 보고 싶다"면 선택적 매칭이 필요하다.

```gql
MATCH (b:Buyer)-[:has_cart]->(:Cart)-[:contains]->(p:Product)
OPTIONAL MATCH (p)<-[:reviews]-(r:Review WHERE r.verified = true)
RETURN p.name, r.rating, r.title
```

`OPTIONAL MATCH`는 SQL의 `LEFT JOIN`에 해당한다. 매칭이 없으면 `r` 관련 열이 `NULL`로 채워진 채 행이 유지된다.

또 하나 — 원본 질의에는 **특정 buyer를 지정하는 조건이 없다.** 따라서 "누군가의 장바구니"는 문자 그대로 **플랫폼의 모든 구매자의 모든 카트**를 훑는다. 위 계산의 Buyer 1명은 전체 구매자 수만큼 다시 곱해진다.

---

## 4. 실무로 가는 확장

### 4.1 특정 구매자로 한정

가장 먼저 붙여야 할 조건이다. 실제 서비스에서 "장바구니 페이지에 신뢰 리뷰 배지 붙이기" 같은 용도라면 반드시 필요하다.

```gql
MATCH (b:Buyer)-[:has_cart]->(:Cart)-[:contains]->(p:Product)<-[:reviews]-(r:Review)
WHERE b.buyerId = 'B-10293' AND r.verified = true
RETURN p.name, r.rating, r.title
```

`buyerId`는 Buyer의 **식별자(identifier)** 속성이므로 인덱스가 걸려 있을 가능성이 높다. 이 조건 하나로 스캔 범위가 전체 그래프 → 카트 1개로 줄어든다. **온톨로지에서 식별자를 지정하는 것이 성능과 직결되는 지점.**

노드 패턴 안에 인라인으로 써도 같다: `(b:Buyer {buyerId: 'B-10293'})`.

### 4.2 평점 필터 · 정렬 · 상한

"좋은 리뷰 몇 개만 보여줘"는 UI에서 거의 항상 필요하다.

```gql
MATCH (b:Buyer)-[:has_cart]->(:Cart)-[:contains]->(p:Product)<-[:reviews]-(r:Review)
WHERE b.buyerId = 'B-10293'
  AND r.verified = true
  AND r.rating >= 4
RETURN p.name, r.rating, r.title
ORDER BY r.rating DESC, p.name
LIMIT 10
```

| 절 | 역할 |
|---|---|
| `r.rating >= 4` | 4점 이상만 (Review의 `rating`은 integer) |
| `ORDER BY r.rating DESC` | 평점 내림차순, 동점이면 상품명 오름차순 |
| `LIMIT 10` | 상위 10행만 |
| (`SKIP 20`) | 페이지네이션용 오프셋. `SKIP 20 LIMIT 10` = 3페이지 |

절의 실행 순서는 `MATCH → WHERE → RETURN → ORDER BY → SKIP → LIMIT`이다. **`LIMIT`은 정렬 후에 적용**되므로 "상위 10개"가 제대로 나온다.

### 4.3 상품별 집계 — 평균 평점과 리뷰 수

행이 곱해지는 문제를 정면으로 해결하는 방법. 상품 1개당 1행으로 접는다.

```gql
MATCH (b:Buyer)-[:has_cart]->(:Cart)-[:contains]->(p:Product)<-[:reviews]-(r:Review)
WHERE b.buyerId = 'B-10293' AND r.verified = true
RETURN p.name,
       p.price,
       count(r)      AS verifiedReviewCount,
       avg(r.rating) AS avgRating
ORDER BY avgRating DESC
```

**GQL/Cypher 계열의 집계에는 `GROUP BY`가 없다.** `RETURN`에서 집계 함수(`count`, `avg`, `sum`, `min`, `max`, `collect`)가 아닌 표현식들 — 여기서는 `p.name`, `p.price` — 이 **암묵적으로 그룹 키가 된다.** SQL을 쓰던 사람이 가장 자주 놀라는 부분이다.

신뢰도가 낮은(리뷰 1~2개짜리) 상품을 걸러내려면 집계 후 필터가 필요하다.

```gql
MATCH (b:Buyer)-[:has_cart]->(:Cart)-[:contains]->(p:Product)<-[:reviews]-(r:Review)
WHERE r.verified = true
WITH p, count(r) AS cnt, avg(r.rating) AS avgRating
WHERE cnt >= 5
RETURN p.name, cnt, round(avgRating, 2) AS avgRating
ORDER BY avgRating DESC
LIMIT 20
```

`WITH`는 **중간 결과를 다음 단계로 넘기는 파이프**이며, `WITH` 뒤의 `WHERE`는 SQL의 **`HAVING`** 역할을 한다. 리뷰 제목 몇 개를 함께 보고 싶다면 `collect(r.title)[0..3] AS sampleTitles` 처럼 리스트로 접어 반환할 수도 있다.

### 4.4 같은 온톨로지로 답할 수 있는 다른 질문들

시나리오 문서가 예고했던 질문들도 결국 같은 문법의 조립이다.

```gql
-- 리뷰를 썼지만 구매하지 않은 사람 (verified 개념의 검증)
MATCH (b:Buyer)-[:writes]->(r:Review)-[:reviews]->(p:Product)
WHERE NOT EXISTS { (b)-[:places]->(:Order)-[:includes]->(p) }
RETURN b.buyerId, p.name, r.rating
```

```gql
-- 카트는 찼는데 주문은 한 번도 없는 구매자 (전환 퍼널 이탈)
MATCH (b:Buyer)-[:has_cart]->(c:Cart)
WHERE c.itemCount > 0
  AND NOT EXISTS { (b)-[:places]->(:Order) }
RETURN b.buyerId, b.email, c.subtotal
ORDER BY c.subtotal DESC
```

`NOT EXISTS { … }` 안에 패턴을 넣어 **"이런 경로가 없는 것"** 을 표현하는 것이 그래프 질의의 강력한 무기다. 관계형으로는 `NOT EXISTS (SELECT … )` 서브쿼리나 `LEFT JOIN … IS NULL` 관용구가 필요하다.

---

## 5. 관계형 SQL과의 대비 — 왜 그래프 패턴이 이득인가

같은 질문을 정규화된 관계형 스키마(`buyers`, `carts`, `cart_items`, `products`, `reviews`)로 쓰면 이렇게 된다.

```sql
SELECT p.name, r.rating, r.title
FROM   buyers      b
JOIN   carts       c  ON c.buyer_id  = b.buyer_id
JOIN   cart_items  ci ON ci.cart_id  = c.cart_id
JOIN   products    p  ON p.sku       = ci.sku
JOIN   reviews     r  ON r.sku       = p.sku
WHERE  r.verified = TRUE;
```

| 비교 축 | GQL | SQL |
|---|---|---|
| 연결 표현 | 화살표 방향으로 시각화 (`-[:contains]->`) | `ON` 절의 키 등식으로 서술 |
| 다대다 관계 | 엣지 그 자체 | **연결 테이블**(`cart_items`) 필요 — 개념에 없던 테이블이 등장 |
| 조인 조건 | 관계 타입 이름 하나 | 테이블마다 어느 컬럼이 어느 컬럼과 짝인지 매번 명시 |
| 방향/의미 | 관계 이름과 화살표에 내장 | 컬럼 이름 관례에 의존 (`r.sku`가 무엇을 뜻하는지 스키마를 봐야 함) |
| 줄 수 | 3줄 | 7줄 (+ 연결 테이블 정의) |

핵심 차이 세 가지.

1. **연결 테이블이 사라진다.** 관계형에서 many-to-many(`contains`)는 반드시 `cart_items` 같은 중간 테이블을 만들어야 하고, 질의를 쓸 때마다 그것을 기억해야 한다. 그래프에서 many-to-many는 **엣지를 여러 개 그으면 끝**이다. 개념 모델과 물리 모델의 거리가 짧다.

2. **조인 조건을 매번 다시 쓰지 않는다.** SQL의 `ON c.buyer_id = b.buyer_id`는 "이 두 테이블이 어떻게 연결되는가"를 **질의문마다 재선언**하는 행위다. 오타 하나면 조용히 카티션 곱이 난다. GQL은 `has_cart`라는 관계 이름 하나로 끝난다 — 연결 방식은 **그래프(온톨로지)가 알고 있다**.

3. **가변 길이·경로 탐색에서 격차가 벌어진다.** 위 예시는 홉이 4개로 고정이라 SQL도 감당할 만하다. 하지만 "3~5단계 안에 연결된 관련 상품", "추천의 추천의 추천"처럼 **깊이가 가변인 질문**이 오면 SQL은 재귀 CTE로 급격히 복잡해지는 반면, GQL은 `-[:contains*1..3]->` 한 조각으로 표현한다. GQL 표준이 정규 경로 질의(RPQ)를 강화한 이유가 여기 있다.

> 정리하면 — **관계형은 "테이블을 어떻게 붙일까"를 매번 설명해야 하고, 그래프는 "어떤 모양을 찾을까"만 말하면 된다.** 온톨로지가 연결 규칙을 이미 담고 있기 때문이다. 이것이 시나리오 문서가 "온톨로지 없이는 여러 시스템을 가로지르는 조인, 온톨로지가 있으면 하나의 그래프 패턴"이라고 말한 이유다.

---

## 암기 포인트

1. **`MATCH`는 찾을 부분 그래프의 모양, `WHERE`는 속성 값 필터, `RETURN`은 뽑을 열.**
2. **`<-[:reviews]-` 의 역방향 화살표는 온톨로지의 `Review → Product` 방향을 그대로 따른 결과**다. 걷는 방향이 아니라 정의된 방향이 화살표를 결정한다.
3. **결과 행 수 = 카트 속 상품 수 × 상품별 verified 리뷰 수**(정확히는 합). 상품명이 중복되고, 리뷰 0개인 상품은 사라진다(`MATCH`는 inner join).
4. `verified`는 **실구매 인증**을 뜻하는 boolean이며, 신뢰 기반 필터링의 축이다.
5. **GQL = ISO/IEC 39075:2024**, SQL 이후 37년 만의 새 ISO 질의 언어 표준, Cypher가 모태. `CREATE` 대신 `INSERT`.
6. **집계에 `GROUP BY`가 없다.** `RETURN`의 비집계 표현식이 곧 그룹 키, `HAVING`은 `WITH … WHERE`.

---

## 출처

- [ISO/IEC 39075:2024 — Information technology — Database languages — GQL](https://www.iso.org/standard/76120.html)
- [Graph Query Language — Wikipedia](https://en.wikipedia.org/wiki/Graph_Query_Language)
- [GQL: A New ISO Standard for Querying Graph Databases — The New Stack](https://thenewstack.io/gql-a-new-iso-standard-for-querying-graph-databases/)
- [GQL vs. Cypher: What the New ISO Standard Brings to the Table — NebulaGraph](https://nebula-graph.io/posts/gql-vs.-cypher-what-the-new-iso-standard-brings-to-the-table)
- [GQL Standards](https://www.gqlstandards.org/) / [openCypher](https://opencypher.org/)
