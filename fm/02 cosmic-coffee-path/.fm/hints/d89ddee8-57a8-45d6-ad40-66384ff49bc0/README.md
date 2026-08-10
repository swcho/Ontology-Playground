# 왜 `<-[:sentBy]-` 처럼 화살표가 반대로 쓰였나?

**Q.** 예시 GQL 질의에서 `<-[:sentBy]-`처럼 화살표 방향이 반대로 쓰인 이유는?

**A.** `sentBy`는 `Shipment` → `Supplier` 방향으로 선언된 관계다. 그런데 질의 패턴을 `Supplier`에서 시작해서 쓰면 이 관계를 **역방향으로 순회**해야 한다. GQL은 패턴 안에서 관계의 방향을 화살표로 **명시적으로** 표기하기 때문에, 역방향 순회는 `<-[:sentBy]-`로 적힌다.

---

## 1. 문제의 질의

Fourth Coffee 온톨로지의 GQL 예시 — "Fair Trade 인증 공급자 중 캘리포니아 매장으로 배송하는 곳 찾기":

```gql
MATCH (sup:Supplier)<-[:sentBy]-(s:Shipment)-[:deliveredTo]->(st:Store)
WHERE sup.certification = 'Fair Trade' AND st.state = 'CA'
RETURN sup.name, st.name, s.status
```

한 줄에 화살표가 두 개 있는데 하나는 왼쪽(`<-`), 하나는 오른쪽(`->`)을 향한다. 처음 보면 "일관성이 없나?" 싶지만, 사실 **완벽하게 일관적**이다.

## 2. 온톨로지에 선언된 관계 방향

에셋의 "New relationships" 절에 나온 선언을 그대로 옮기면:

| 관계 | 선언된 방향 | 카디널리티 |
|---|---|---|
| `sourcedFrom` | `Product` → `Supplier` | many-to-one |
| **`sentBy`** | **`Shipment` → `Supplier`** | many-to-one |
| **`deliveredTo`** | **`Shipment` → `Store`** | many-to-one |
| `carries` | `Shipment` → `Product` | many-to-many |

핵심: `sentBy`와 `deliveredTo` **둘 다 Shipment에서 출발한다.** Shipment는 허브(hub) 엔티티이고, 화살표들이 허브에서 **바깥으로 뻗어나가는** 모양이다.

```
                 Supplier                    Store
                    ▲                          ▲
                    │ sentBy                   │ deliveredTo
                    │                          │
                    └────── Shipment ──────────┘
                          (허브 엔티티)
```

## 3. 토큰 단위로 읽어보기

패턴을 조각내서, 각 조각이 위 그림의 어느 부분인지 대응시켜 보자.

```
MATCH (sup:Supplier) <-[:sentBy]- (s:Shipment) -[:deliveredTo]-> (st:Store)
      └─── ① ─────┘  └── ② ───┘  └─── ③ ────┘ └───── ④ ─────┘ └── ⑤ ──┘
```

| # | 토큰 | 의미 |
|---|---|---|
| ① | `(sup:Supplier)` | `Supplier` 라벨의 노드를 `sup` 변수에 바인딩. **패턴의 시작점**이다. |
| ② | `<-[:sentBy]-` | 화살촉이 `sup` 쪽(왼쪽)을 향함 = "`sentBy` 간선이 **sup을 향해** 들어온다". 즉 간선의 꼬리는 오른쪽 노드(③)에 있다. |
| ③ | `(s:Shipment)` | 간선의 출발점. 여기가 **허브**이고 패턴의 중간에 앉아 있다. |
| ④ | `-[:deliveredTo]->` | 화살촉이 오른쪽을 향함 = "`deliveredTo` 간선이 `s`에서 **나가서** ⑤로 들어간다". |
| ⑤ | `(st:Store)` | 도착점. |

정리하면 이 패턴이 그려내는 그림은 정확히 다음과 같다.

```
Supplier  ◀────sentBy────  Shipment  ────deliveredTo────▶  Store
   ①                          ③                             ⑤
```

**두 간선 모두 물리적으로 Shipment에서 멀어지는 방향을 가리킨다.** 그런데 우리가 패턴을 **왼쪽 끝(Supplier)에서부터 텍스트로 써 내려가기** 때문에, 첫 번째 간선은 "거꾸로 그려야" 하고 두 번째 간선은 "그대로 그리면" 된다. 두 화살표는 모순이 아니라 **허브에서 만나는 것**이다.

> 만약 첫 번째 간선을 `-[:sentBy]->`로 썼다면 그건 `Supplier` → `Shipment`가 되어 온톨로지에 존재하지 않는 관계를 요구하는 셈이고, 결과는 0건이 된다.

## 4. GQL / Cypher 스타일 패턴 문법 3종

| 표기 | 뜻 | 언제 쓰나 |
|---|---|---|
| `(a)-[:REL]->(b)` | 선언된 방향을 **그대로** 따라간다. 간선은 `a` → `b`. | 패턴 작성 순서와 관계 선언 방향이 일치할 때 |
| `(a)<-[:REL]-(b)` | 선언된 방향을 **거슬러** 순회한다. 간선은 `b` → `a`. | 관계의 도착지 쪽에서 패턴을 시작할 때 (지금 케이스) |
| `(a)-[:REL]-(b)` | 방향 **무관**. `a`→`b`든 `b`→`a`든 매칭. | 방향을 모르거나 상관없을 때. 양방향을 다 탐색하므로 보통 더 느리다 |

가장 중요한 오해 포인트:

> **화살표는 "간선에 선언된 방향"을 서술한다. 질의를 읽는 순서나 데이터가 흐르는 순서를 서술하는 게 아니다.**

`<-`는 "거꾸로 읽으라"는 지시가 아니고, "이 위치에 있는 간선의 화살촉이 내 왼쪽 노드를 향해 있다"는 **사실 서술**이다. 패턴은 그림이고, 화살표는 그 그림에 그려진 화살촉이다.

## 5. 진짜 핵심: 모델링 결정 vs 질의 결정

여기서 사람들이 가장 많이 헷갈린다.

| | 관계 방향 (relationship direction) | 순회 방향 (traversal direction) |
|---|---|---|
| **누가 정하나** | 온톨로지 설계자 (모델링 시점) | 질의 작성자 (질의 시점) |
| **어디에 기록되나** | 온톨로지 스키마 (`sentBy: Shipment → Supplier`) | `MATCH` 패턴의 화살표 |
| **바꿀 수 있나** | 스키마 변경이 필요 (비용 큼) | 질의마다 자유롭게 (비용 없음) |

**관계 방향은 모델링 결정이고, 순회 방향은 질의 결정이다.**

같은 간선을 어느 쪽으로 순회해도 의미상 손실이나 추가 비용이 없다. 그래프 DB는 보통 간선을 양쪽 노드에 모두 인덱싱해 두므로 `Shipment → Supplier`와 `Supplier ← Shipment` 탐색은 실질적으로 대등하다.

그럼 방향은 왜 선언하는가? 방향은 **"어느 쪽이 one 쪽인가 / 어느 엔티티가 참조를 소유하는가"**를 인코딩한다. 데이터가 그 방향으로만 흐른다는 뜻이 아니다.

- `sentBy`는 many-to-one (`Shipment` → `Supplier`)이다. 많은 Shipment가 하나의 Supplier를 가리킨다. 화살표 꼬리(Shipment)가 many 쪽, 화살촉(Supplier)이 one 쪽.
- 관계형 스키마로 치면 `shipment` 테이블에 `supplier_id` 외래키가 있는 것과 같다. **참조를 들고 있는 쪽이 화살표의 출발점**이다.
- 이름도 이 방향을 따라 자연어처럼 읽힌다: "Shipment **is sent by** Supplier". 반대로 `Supplier -[:sends]-> Shipment`라고 모델링했다면 같은 사실을 표현하되 이름과 방향이 함께 뒤집혔을 것이다.

즉 방향은 **누가 누구를 참조하는가**에 대한 설계 서술이고, **어디서 출발해 어디로 갈 수 있는가**에 대한 제약이 아니다.

## 6. 정방향 화살표만으로 다시 쓰기 (동일한 결과)

`<-`가 불편하다면 **허브인 Shipment에서 패턴을 시작하면** 화살표를 모두 정방향으로 쓸 수 있다.

```gql
MATCH (s:Shipment)-[:sentBy]->(sup:Supplier),
      (s)-[:deliveredTo]->(st:Store)
WHERE sup.certification = 'Fair Trade' AND st.state = 'CA'
RETURN sup.name, st.name, s.status
```

- 쉼표로 두 패턴을 나열하고, 두 번째 패턴에서 이미 바인딩된 `s`를 재사용해 같은 Shipment임을 강제한다.
- 콤마 없이 한 줄로 쓸 수도 있다 — 방향만 유지하면 `MATCH (sup:Supplier)<-[:sentBy]-(s:Shipment)-[:deliveredTo]->(st:Store)`와 동형이다.

두 질의는 **정확히 같은 행 집합**을 반환한다. 원본이 Supplier에서 시작한 이유는 단지 질문의 관심사가 "어떤 공급자?"여서 읽는 흐름(`Supplier → Shipment → Store`, 에셋의 표에 나온 그래프 경로 그대로)과 패턴 순서를 맞추려 한 것뿐이다.

세 번째 변형 — 방향 무관 표기를 쓰면 이렇게도 된다(권장하지는 않음. 존재하지 않는 역방향까지 후보로 놓고 탐색하므로):

```gql
MATCH (sup:Supplier)-[:sentBy]-(s:Shipment)-[:deliveredTo]-(st:Store)
```

이 온톨로지에서는 `Supplier -sentBy-> Shipment` 간선이 애초에 존재하지 않으므로 결과는 같지만, 엔진은 양방향을 모두 확인해야 한다.

## 7. 요약

1. `sentBy`는 `Shipment` → `Supplier`로 **선언**되었다.
2. 패턴을 `Supplier`에서 시작했으므로 그 간선은 **역방향 순회**가 되고, GQL은 이를 `<-[:sentBy]-`로 명시한다.
3. `deliveredTo`(`Shipment` → `Store`)는 패턴 순서와 방향이 일치하므로 `-[:deliveredTo]->`.
4. 두 화살표가 서로 반대로 보이는 건 **허브 엔티티 Shipment가 패턴 중앙에 있고 두 간선이 거기서 바깥으로 뻗기** 때문이다 — 모순이 아니다.
5. **방향 = 모델링 결정, 순회 = 질의 결정.** 같은 간선을 어느 쪽으로든 공짜로 순회할 수 있다.
6. Shipment를 시작점으로 재작성하면 화살표를 전부 정방향으로 쓸 수 있고, 결과는 동일하다.
