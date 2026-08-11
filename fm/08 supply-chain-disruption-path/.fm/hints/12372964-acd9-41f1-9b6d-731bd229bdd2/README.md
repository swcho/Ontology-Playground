# 관계 2: `Component used in ProductLine` (many-to-many)

## 질문

관계 2 `Component used in ProductLine`의 카디널리티와 중요성은?

## 답

**many-to-many (M:N)** 다. 중요성은 **단일 부품의 공급 실패가 여러 제품 라인을 동시에 멈출 수 있다**는 점이다.

```
Component "GPU Module"
  usedIn→ ProductLine "Gaming Laptop 2024"
       → ProductLine "Workstation Pro"
       → ProductLine "Tablet Plus"
```

원문의 카디널리티 표에도 그 이유가 한 줄로 압축돼 있다.

| Relationship | Cardinality | Why |
|---|---|---|
| Component → ProductLine | **M:N** | Components reused; products share components |

"Why"가 두 방향을 동시에 말하고 있다는 데 주목하자.

- **한 부품 → 여러 제품 라인** (components reused): GPU Module 하나가 3개 라인에 들어간다.
- **한 제품 라인 → 여러 부품** (products share components): Gaming Laptop 2024는 GPU Module, Memory Board, Power Supply를 모두 필요로 한다.

이 양방향성이 M:N의 정의이며, 뒤에 나올 "중복 계산" 문제의 원인이기도 하다.

---

## 1. M:N은 왜 리스크 증폭기(risk amplifier)인가

### 1:N 체인이라면 피해는 선형이다

만약 부품이 오직 하나의 제품 라인에만 쓰인다면(1:1 또는 1:N in the other direction), 부품 1개가 죽으면 라인 1개가 멈춘다. 피해 = 입력. 증폭 없음.

### M:N이면 팬아웃(fan-out)이 곱셈으로 커진다

실제 카스케이드는 두 개의 팬아웃이 직렬로 이어진 구조다.

```
DisruptionEvent  ──M:N──▶  Supplier  ──1:N──▶  Component  ──M:N──▶  ProductLine
   (지진 1건)              (3개 공급사)          (47개 부품)          (12개 라인)
```

원문 Phase 2의 수치를 그대로 옮기면:

```
"Which suppliers are affected by the Taiwan earthquake?"  → 3 critical suppliers
"For these 3 suppliers, show me all components"           → 47 components
"For these 47 components, which product lines use them?"  → 12 product lines exposed
```

여기서 **관계 2(M:N)가 마지막 홉을 담당한다**. 그리고 이 홉이 리스크 증폭의 성격을 결정한다.

- 관계 1(`Supplier supplies Component`, 1:N)은 **피해 범위를 넓히는** 홉이다. 공급사 3개 → 부품 47개. 트리 구조이므로 부품은 중복되지 않는다(한 부품이 한 공급사에서만 온다는 가정 하에).
- 관계 2(M:N)는 **피해를 수익으로 환산하는** 홉이다. 부품 47개 → 제품 라인 12개. 여기서는 그래프가 겹친다. 같은 라인에 여러 부품이 걸리고, 같은 부품이 여러 라인에 걸린다.

증폭의 본질은 이것이다: **M:N에서는 노드 1개 제거가 여러 개의 하위 노드를 동시에 무력화한다.** GPU Module 하나만 끊겨도 Gaming Laptop 2024, Workstation Pro, Tablet Plus가 함께 멈춘다. 즉 리스크가 부품 수에 비례하지 않고, 부품의 **연결 차수(degree)** 에 비례한다.

### 증폭 계수를 정의해 보면

부품 c의 팬아웃을 `fanout(c) = |{p : c usedIn p}|`이라 하면,

- `fanout(GPU Module) = 3`
- 이 부품이 끊길 때 위험에 노출되는 연매출 = `annualRevenue(Gaming Laptop) + annualRevenue(Workstation Pro) + annualRevenue(Tablet Plus)`

원문의 카스케이드 예시에서 GPU Module은 2개 라인($50M + $30M)만 명시되어 `revenueAtRisk=$80M`이 나온다. 부품 1개의 3일치 재고 문제가 $80M 노출로 번역되는 이유가 바로 이 M:N 팬아웃이다.

그래서 온톨로지 설계 관점에서 다음 쿼리가 곧 "리스크 증폭기 랭킹"이 된다.

```
"How many product lines depend on this component?"   ← 원문의 query example
```

`fanout`이 높은 부품 + `daysOfSupplyOnHand`가 낮은 부품 + `Supplier.singleSourced=true`인 부품, 이 세 조건의 교집합이 가장 위험한 지점이다. 원문 Fabric IQ 예시에서 에이전트가 "3 critical single-source suppliers, ~$180M in 4-9 days"를 답할 수 있는 것도 이 세 축을 조합하기 때문이다.

---

## 2. 부품 공유는 원가 절감 ↔ 리스크 집중의 트레이드오프

M:N은 데이터 모델링의 우연이 아니다. **엔지니어링과 조달 조직이 의도적으로 만든 구조**다.

### 공유(플랫폼 전략)를 하는 이유 — 원가와 속도

| 이점 | 설명 |
|---|---|
| 규모의 경제 | 3개 라인 물량을 한 부품으로 합쳐서 구매하면 단가가 내려간다 |
| 재고 풀링 | 공용 안전재고 하나로 3개 라인을 커버 → 총 재고 자본 감소 |
| 인증/검증 비용 절감 | 부품 하나만 qualify하면 여러 제품에 재사용 |
| 개발 속도 | 신제품이 기존 검증 부품을 그대로 재사용 → 출시 단축 |
| 협상력 | 대량 발주로 공급사 대상 레버리지 확보 |

이것이 `ProductLine`을 "a group of finished products **sharing common components**"로 정의한 이유다. 공유는 기능이지 결함이 아니다.

### 같은 구조가 만드는 비용 — 리스크 집중

문제는 **원가 절감과 리스크 집중이 같은 화살표에서 나온다**는 것이다. 공유도를 높이면 단가는 내려가지만, 동시에

- **상관된 실패(correlated failure)**: 독립적이라고 믿었던 3개 사업부가 실은 하나의 부품에, 나아가 하나의 공급사, 하나의 지역(Taiwan)에 동시 의존한다.
- **분산 효과 소멸**: 포트폴리오를 다양화해도 부품 계층에서 병목이 하나면 다양화 효과가 사라진다.
- **단일 실패점(SPOF) 심화**: `singleSourced=true` 공급사가 팬아웃 높은 부품을 공급하면, 부품 1개 = 사업 전체 리스크.

즉 **분모(단가)를 줄이려는 최적화가 분자(노출 매출)를 키운다.** 절감액은 매 분기 P&L에 확실하게 보이는 반면, 리스크 비용은 재해가 터진 분기에만 한꺼번에 보인다. 이 비대칭 때문에 조직은 구조적으로 과잉 공유 쪽으로 기운다.

### 온톨로지가 이 트레이드오프를 계산 가능하게 만든다

관계 2를 명시적 M:N으로 모델링하면 트레이드오프를 정성적 직관이 아니라 숫자로 다룰 수 있다.

- **절감 측**: 공유로 인한 단가 인하 + 재고 풀링 효과
- **리스크 측**: `SUM(노출 라인의 revenueAtRisk)` × 사건 확률
- **완화 비용**: `MitigationAction.estimatedCost`, `AlternativeSupplier.pricePremiumPercent`

원문에서 "Activate ChipX Europe: cost +$2M vs. $80M loss", "+12% price premium"이 나오는 이유가 이것이다. **부품 공유로 아낀 몇 %가, 대체 공급사 프리미엄 12%와 $80M 노출과 같은 저울 위에 올라간다.** 이 비교를 가능케 하는 것이 관계 2다.

완화 전략도 결국 M:N 구조를 건드리는 것으로 정리된다.

| 전략 | M:N 구조에 대한 효과 |
|---|---|
| `Activate Alternative Supplier` | 상위 홉(공급사)을 다중화 → 부품 팬아웃은 그대로 두고 실패 확률을 낮춤 |
| `Increase Safety Stock` | `daysOfSupplyOnHand`를 늘려 `timeToImpactDays` 확보 → 팬아웃의 시간적 완충 |
| `Redesign Component` | 팬아웃 자체를 쪼갬 → 리스크 구조 변경, 대신 가장 느리고 비싸다 |
| 이중 소싱(dual sourcing) 정책 | `singleSourced=false`로 만들어 증폭 경로를 사전에 차단 |

---

## 3. revenueAtRisk 집계에서 관계 2의 역할 (47 → 12 → $127M)

원문 Phase 3의 집계 로직을 그대로 보자.

```
Calculation Engine:
  For each exposed ProductLine:
    revenue_at_risk = annualRevenue / 365 * daysOfSupplyOnHand
    urgency = 100 - (daysOfSupplyOnHand * 10)

  Aggregate:
    total_revenue_at_risk = SUM(revenue_at_risk)
    critical_product_lines = WHERE urgency > 70

  Result:
    Total at risk: $127M
```

여기서 관계 2가 하는 일은 **정확히 두 가지**다.

### 역할 A — 집계 대상 집합을 만든다 (선택)

`revenueAtRisk`의 금액은 `Component`가 아니라 `ProductLine.annualRevenue`에서 나온다. 그런데 재해가 직접 때리는 것은 `Supplier`이고 그 다음이 `Component`다. 즉 **돈이 있는 곳과 사고가 나는 곳이 다르다.** 관계 2가 이 두 계층을 잇는 유일한 브릿지다.

```
사고 발생 계층 ── 관계 1(1:N) ──▶ 부품 계층 ── 관계 2(M:N) ──▶ 금액 계층
   Supplier                        Component                    ProductLine
                                                                (annualRevenue)
```

관계 2가 없으면 "47개 부품이 멈췄다"에서 멈추고, "그래서 얼마인가"에 답할 수 없다.

### 역할 B — 단위를 부품에서 제품 라인으로 전환한다 (집계 단위 결정)

집계 루프가 `For each exposed ProductLine`인 것이 핵심이다. **`For each Component`가 아니다.** M:N을 통과하면서 집계 단위가 47(부품)에서 12(제품 라인)로 바뀐다.

이것이 의도적인 설계다. 부품 단위로 더하면 같은 매출을 여러 번 세게 되기 때문이다(아래 4절).

### 47 → 12의 의미: 압축이지 축소가 아니다

47 → 12는 "리스크가 줄었다"는 뜻이 아니다. 47개 부품이 중복 포함 관계로 12개 라인에 매핑됐다는 뜻이며, 평균적으로 라인 하나가 여러 개의 끊긴 부품에 걸려 있다는 뜻이다. 오히려 **한 라인이 여러 부품 때문에 노출됐다는 것은 그 라인이 더 위험하다는 신호**다(복구해야 할 부품이 여러 개이므로).

---

## 4. 중복 계산(double counting) 주의점

M:N 그래프를 순회해서 금액을 더할 때 가장 흔한 버그가 중복 계산이다. 유형이 두 가지 있다.

### 유형 1 — 같은 제품 라인을 여러 부품 때문에 여러 번 계산

Gaming Laptop 2024가 GPU Module과 Memory Board 둘 다 때문에 노출됐다고 하자.

**틀린 집계 (부품 단위 순회, DISTINCT 없음)**

```
FOR each component c in 47:
  FOR each productLine p in c.usedIn:
    total += p.annualRevenue / 365 * ...
```

→ Gaming Laptop의 매출이 2번(부품 개수만큼) 더해진다. 47개 부품이 평균 3개 라인에 연결돼 있다면 순회 결과는 최대 141건이고, 실제 고유 라인은 12개다. 즉 **금액이 10배 이상 부풀 수 있다.**

이 오류는 조용하다. 결과가 커지기만 하고 어디서도 예외가 나지 않으며, "리스크가 크게 나왔다"는 결론은 심리적으로 그럴듯해 보인다. 그리고 그 부풀려진 숫자가 그대로 Phase 5의 자동화 임계값(`revenueAtRisk > $50M`)을 넘겨서 불필요한 발주와 임원 에스컬레이션을 트리거한다.

**올바른 집계 (제품 라인 단위로 dedupe 후 순회)**

```
exposedLines = DISTINCT( traverse(47 components → usedIn → ProductLine) )   -- 12개
FOR each p in exposedLines:                                                 -- 라인당 정확히 1회
  total += p.annualRevenue / 365 * daysOfSupply(p)
```

원칙: **금액 속성이 붙어 있는 엔티티(여기서는 `ProductLine.annualRevenue`)를 집계 단위로 삼고, 그 엔티티를 정확히 한 번만 방문한다.** 부품은 "노출 여부를 판정하는 근거"일 뿐, 더하기의 단위가 아니다.

원문의 47 → **12** 결과가 이미 DISTINCT를 적용한 숫자라는 점, 그리고 집계 루프가 `For each exposed ProductLine`이라는 점이 이 원칙을 반영한다.

### 유형 2 — 라인당 `daysOfSupplyOnHand`가 여러 개일 때 어느 값을 쓸 것인가

라인을 한 번만 세더라도, 그 라인에 걸린 여러 부품의 재고 일수가 다르면 `revenue_at_risk = annualRevenue / 365 * daysOfSupplyOnHand`의 `daysOfSupplyOnHand`가 모호해진다.

```
Gaming Laptop 2024
  ├─ GPU Module     daysOfSupplyOnHand = 3
  └─ Memory Board   daysOfSupplyOnHand = 10
```

라인이 멈추는 시점은 **가장 먼저 소진되는 부품**이 결정한다(부품은 AND 조건이다 — 하나만 없어도 조립이 안 된다). 따라서

```
daysOfSupply(p) = MIN( c.daysOfSupplyOnHand  for c in 끊긴 부품들 usedIn p )
```

가 맞다. `MIN`을 쓰지 않고 평균이나 첫 번째 값을 쓰면 노출 시점을 낙관적으로 오판한다. 위 예에서 3일이 아니라 6.5일로 계산하면, `timeToImpactDays < 5` 조건을 만족하지 못해 자동화가 아예 발동하지 않는다. 원문 카스케이드에서 `daysOfSupplyOnHand=3` → `timeToImpactDays=3`으로 이어지는 것도 최소값 기준이다.

`urgency = 100 - (daysOfSupplyOnHand * 10)`도 같은 값을 써야 일관된다. (MIN을 쓰면 urgency는 라인별 최대값이 된다.)

### 유형 3 — 반대 방향의 함정: 부품 단위 dedupe

부품이 여러 공급사에서 올 수 있게 모델링돼 있다면(원문 `Component` 정의는 "sourced from **one or more** suppliers"), 관계 1도 사실상 M:N에 가깝다. 그러면 3개 공급사 → 부품 순회에서도 같은 부품이 두 번 나올 수 있으므로 **47이라는 숫자 자체가 DISTINCT 결과여야 한다.** 즉 M:N 그래프에서는 홉마다 dedupe가 필요하다.

한편 여러 공급사에서 오는 부품은 한 공급사가 끊겨도 완전히 죽지 않는다. 엄밀하게 하려면 "노출"을 이진값이 아니라 부분 노출(해당 공급사의 물량 비중)로 다뤄야 한다. 원문 모델은 단순화를 위해 이진 노출을 쓰고, 그 오차를 `RiskAssessment.confidenceLevel`(High/Medium/Low)과 개선 지표 "Impact estimate accuracy ±10%"로 흡수한다.

### 반대편 오류 — 과소 계산

중복 계산을 두려워해서 지나치게 깎아내는 것도 문제다.

- 매출 전체를 세는 대신 "부품 원가 비중만큼만" 세면 안 된다. 부품 하나가 없으면 완제품을 못 팔기 때문에 노출 매출은 **라인 전체 매출**이다.
- 파생 손실(지연 배상금, 고객 이탈, 시장 점유율)은 이 공식에 없다. 원문의 "Affected customers: 450,000+"는 그래서 금액과 별도로 보고된다.

원문이 `$127M`을 "**exposure**"라고 부르고, 실제 결과를 "Revenue protected: ~$100M of $127M exposure"로 표현하는 것에 주의하자. `revenueAtRisk`는 확정 손실이 아니라 **완화 조치 전의 노출 상한**이며, 의사결정 우선순위를 정하기 위한 값이다.

---

## 5. 정리 및 검증 체크리스트

- 카디널리티: `Component used in ProductLine` = **many-to-many**
- 중요성 한 문장: **부품 하나의 공급 실패가 여러 제품 라인을 동시에 멈추므로, 이 관계가 리스크 증폭기이자 매출 환산 브릿지다.**
- 예시: GPU Module → Gaming Laptop 2024 / Workstation Pro / Tablet Plus
- 트레이드오프: 부품 공유 = 원가 절감(규모의 경제, 재고 풀링, 인증 재사용) ↔ 리스크 집중(상관된 실패, 분산 효과 소멸, SPOF)
- 집계에서의 역할: 부품 계층(사고)과 매출 계층(금액)을 잇는 유일한 홉. 47 부품 → **DISTINCT** 12 라인 → $127M
- 집계 규칙 3개
  1. 금액이 붙은 엔티티(`ProductLine`) 단위로 집계하고, 각 라인을 **정확히 한 번만** 센다.
  2. 라인의 `daysOfSupplyOnHand`는 걸린 부품들의 **MIN**을 쓴다.
  3. 홉마다 DISTINCT를 적용한다(부품 계층도 포함).

### 관련 학습 포인트

- 원문 "Cardinality and relationships" 절에서 M:N의 다른 예: `MitigationAction activates AlternativeSupplier`(관계 6). "One action activates multiple backups; backups handle multiple situations" — 여기서는 M:N이 리스크가 아니라 **복원력**을 만든다. 같은 카디널리티가 실패 경로에서는 증폭기, 복구 경로에서는 다중화 수단이 된다.
- 대비되는 카디널리티: `AlternativeSupplier canReplace Supplier`(관계 7, M:1) — 하나의 주 공급사에 여러 백업이 붙는다.
- 구현 관점: 관계형 DB에서 M:N은 조인 테이블(`ComponentProductLine`)로 구체화되고, 여기에 `quantityPerUnit` 같은 관계 속성을 붙일 수 있다. 그 속성이 있으면 "부품 1개당 몇 대를 못 만드는가"까지 계산해 노출 추정 정확도를 높일 수 있다.
