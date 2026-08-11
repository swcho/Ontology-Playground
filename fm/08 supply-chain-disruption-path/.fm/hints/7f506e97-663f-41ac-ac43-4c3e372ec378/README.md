# Component의 `criticalityLevel`과 `daysOfSupplyOnHand`

## 질문

Component의 `criticalityLevel` enum 값과 `daysOfSupplyOnHand`의 역할은?

## 답

- `criticalityLevel`은 **Critical / High / Medium / Low** 4단계 enum이다.
- `daysOfSupplyOnHand`는 **남은 재고로 며칠을 버틸 수 있는지**를 나타내는 정수 값으로, 어떤 부품이 공급 중단을 견딜 수 있는지 판단하는 기준이 된다.

---

## 1. Component 엔티티에서의 위치

Component는 Supply Chain Disruption 온톨로지의 Tier 1(the network) 엔티티로, 공급업체에서 조달해 제품군에 투입되는 부품·자재·서브어셈블리를 표현한다.

| 속성 | 타입 | 값/의미 |
|---|---|---|
| `componentId` | string(식별자) | `COMP-SEM-0821` 형태의 유일 키 |
| `name` | string | 부품명 (예: "GPU Module") |
| `category` | enum | Electronic / Mechanical / Chemical / Packaging / Raw Material |
| `daysOfSupplyOnHand` | integer | 현재 재고로 버틸 수 있는 일수 (안전재고 잔량) |
| `criticalityLevel` | enum | Critical / High / Medium / Low |

Component의 use case는 문서에 이렇게 정의되어 있다: *"안전재고를 기준으로 어떤 부품이 공급업체 중단을 견딜 수 있는지 추적한다."* 즉 이 엔티티의 존재 이유 자체가 `daysOfSupplyOnHand`에 걸려 있다.

두 속성의 타입 차이도 의도적이다. 온톨로지의 속성 타입 표에 따르면

- `integer`(= `daysOfSupplyOnHand`)는 **임계값 기반 경보(threshold-based alerts)** 에 쓰이고,
- `enum`(= `criticalityLevel`)은 **분류와 의사결정 트리(classification, decision trees)** 에 쓰인다.

하나는 "연속적인 시간 여유"를 재는 계량 축, 다른 하나는 "얼마나 대체 불가한 부품인가"를 나누는 범주 축이다.

---

## 2. `criticalityLevel` — 4단계 enum의 역할

`criticalityLevel`은 부품이 대체 불가능한 정도, 즉 그 부품이 끊겼을 때의 파급력을 사람이 읽을 수 있는 라벨로 고정한다.

- **Critical** — 대체품이 없고 끊기면 생산이 즉시 정지. 예시 시나리오의 "GPU Module"처럼 단일 소싱(`Supplier.singleSourced = true`) 공급업체에 묶인 부품이 전형적이다.
- **High** — 대체 가능하지만 재인증/재설계 리드타임이 길다.
- **Medium** — 승인된 대체 공급처가 있어 전환 비용이 감당 가능하다.
- **Low** — 범용품(commodity)으로 시장에서 즉시 조달 가능.

enum이라서 얻는 이점이 세 가지 있다.

1. **에스컬레이션 규칙을 코드로 쓸 수 있다.** `DisruptionEvent.severity`(Critical/High/Medium/Low)와 값 도메인이 동일해서 "Critical 이벤트 × Critical 부품"처럼 두 축을 그대로 결합한 결정 트리를 만들 수 있다.
2. **자연어 에이전트가 근거로 삼을 수 있다.** Fabric IQ 데이터 에이전트는 "Critical 부품만 보여줘" 같은 질문을 자유 텍스트 해석 없이 정확한 필터로 변환한다.
3. **자유 입력 오염을 막는다.** "매우 중요", "critical!!", "핵심" 같은 표기 편차가 없으므로 집계와 대시보드가 깨지지 않는다.

반대로 한계도 분명하다. `criticalityLevel`은 **시간 정보를 전혀 담지 않는다.** Critical 부품이라도 재고가 90일치라면 지금 당장 대응할 필요는 없다. 그래서 `daysOfSupplyOnHand`가 필요하다.

---

## 3. `daysOfSupplyOnHand` — 완충 구간(runway)의 길이

`daysOfSupplyOnHand`는 "공급이 오늘 끊겨도 기존 재고로 생산을 며칠 더 돌릴 수 있는가"이다. 시나리오의 대만 정전 사례에서 `Component "GPU Module"`은 `daysOfSupplyOnHand = 3`이고, 이 값이 그대로 `RiskAssessment.timeToImpactDays = 3`으로 이어진다.

이 값이 실질적으로 하는 일은 **중단(disruption)의 발생 시점과 생산 정지 시점 사이의 간격**, 즉 대응에 쓸 수 있는 시간을 정의하는 것이다.

$$\text{생산 정지 시점} = \text{중단 발생일} + \text{daysOfSupplyOnHand}$$

그리고 완화 조치(MitigationAction)가 성립하는지는 다음 비교로 결정된다.

$$\text{daysOfSupplyOnHand} + \text{leadTimeSavedDays} \;\gtrless\; \text{estimatedDurationDays}$$

시나리오에서 대만 정전의 `estimatedDurationDays = 7`, 재고는 3일치라 4일이 비는데, ChipX Europe 대체 공급처 활성화로 `leadTimeSavedDays = 2`를 확보해 생산 영향을 7일 → 3일로 줄인다. 재고 일수는 이런 판단의 출발점이 되는 기준선이다.

---

## 4. 두 계산식에서 `daysOfSupplyOnHand`의 두 얼굴

Phase 3(Quantify impact, 중단 감지 후 15분)에서 노출된 각 ProductLine에 대해 두 값을 계산한다.

$$\text{revenue\_at\_risk} = \frac{\text{annualRevenue}}{365} \times \text{daysOfSupplyOnHand}$$

$$\text{urgency} = 100 - (\text{daysOfSupplyOnHand} \times 10)$$

같은 속성이 두 식에서 **정반대 방향**으로 작용한다는 점이 핵심이다.

### (a) 금액 축 — 완충 구간을 금액으로 환산

$\dfrac{\text{annualRevenue}}{365}$는 해당 제품군의 **일 매출**이다. 여기에 `daysOfSupplyOnHand`를 곱하면 "완충 구간 동안 이 제품군이 만들어내는 매출", 즉 이 부품 하나에 얹혀 있는 매출 규모가 나온다. 여기서 `daysOfSupplyOnHand`는 **곱셈 계수(측정 창의 길이)** 다.

예: `annualRevenue = $50M`, `daysOfSupplyOnHand = 3`

$$\frac{50{,}000{,}000}{365} \times 3 \approx 136{,}986 \times 3 \approx \$411\text{K}$$

이 값들을 노출된 제품군 전체에 대해 합산해 총 노출액을 만든다.

$$\text{total\_revenue\_at\_risk} = \sum \text{revenue\_at\_risk}$$

문서의 워크플로에서 이 합계가 $127M로 보고된다. (참고: cascade 예시의 `revenueAtRisk = $80M`는 두 제품군의 연 매출 $50M + $30M을 그대로 더한 값이라 Phase 3 공식과 스케일이 다르다. 실제 구현에서는 "완충 구간 매출"이냐 "연 매출 전액 노출"이냐를 조직이 하나로 정해야 하며, 위 공식은 전자에 해당한다.)

### (b) 시간 축 — 완충 구간을 긴급도로 반전

`urgency`에서는 `daysOfSupplyOnHand`가 **음의 기울기로 들어간다.** 재고가 많을수록 급하지 않다는 상식을 그대로 수식화한 것이다.

| daysOfSupplyOnHand | urgency | 해석 |
|---|---|---|
| 0 | 100 | 이미 정지 상태 |
| 1 | 90 | 초긴급 |
| 2 | 80 | 임계 (필터 통과) |
| 3 | 70 | 경계선 — `urgency > 70` 조건을 통과하지 못함 |
| 5 | 50 | 계획 대응 가능 |
| 10 이상 | 0 이하 | 즉시 대응 불필요 |

기울기 $-10$은 **10일을 만점 스케일의 한계**로 잡은 설계다. 10일 이상 버티는 부품은 긴급도 0으로 수렴하므로, 이 지표는 "열흘 안에 터질 일"에만 해상도를 준다. 필터는 다음과 같다.

$$\text{critical\_product\_lines} = \{\, p \mid \text{urgency}(p) > 70 \,\} \iff \text{daysOfSupplyOnHand} < 3$$

즉 `urgency > 70`은 사실상 **재고 3일 미만**이라는 조건과 동일하다. 예시의 GPU Module(3일)은 정확히 경계선에 놓여 있고, 이는 임계값 설계가 시나리오 특성에 맞춰 조정될 여지가 있음을 보여준다.

### 두 식을 함께 보면

- `revenue_at_risk` → **얼마나 큰가**(금액, 경영진 보고용)
- `urgency` → **얼마나 급한가**(시간, 실행 순서 결정용)

`daysOfSupplyOnHand` 하나가 이 두 축을 동시에 만들어낸다. 그래서 이 속성은 단순 재고 필드가 아니라 **위험 정량화의 축(pivot)** 이다.

---

## 5. `criticalityLevel` × `daysOfSupplyOnHand` = 우선순위

두 속성은 독립적인 축이고, 조합했을 때 비로소 실행 가능한 우선순위가 나온다.

|  | 재고 0~2일 (urgency > 70) | 재고 3~9일 | 재고 10일 이상 (urgency ≤ 0) |
|---|---|---|---|
| **Critical** | **P0 — 즉시 대체 공급처 활성화 / 자동 발주** | P1 — 대체 공급처 사전 확보 및 리드타임 확인 | P2 — 모니터링, 단일 소싱 해소 계획 |
| **High** | P1 — 긴급 조달·특송(Expedite Shipment) | P2 — 안전재고 증량 검토 | P3 — 정기 검토 |
| **Medium** | P2 — 대체품 전환 준비 | P3 | P3 |
| **Low** | P3 — 시장 조달로 흡수 | P3 | 조치 불필요 |

읽는 방식은 이렇게 정리된다.

- `criticalityLevel`이 **영향의 크기(어떤 조치가 필요한가)** 를 정하고,
- `daysOfSupplyOnHand`가 **시급성(언제까지 해야 하는가)** 을 정한다.

한쪽만으로는 오판이 발생한다. Critical 라벨만 보면 재고 90일치 부품에 인력을 낭비하고, 재고 일수만 보면 어차피 시장에서 살 수 있는 Low 부품의 재고 부족에 경보가 울린다. 두 축을 함께 봐야 "Critical이면서 재고가 3일치인 GPU Module"이 최우선으로 튀어나온다.

여기에 `Supplier.singleSourced`(boolean)와 `DisruptionEvent.severity`를 더하면 위험 증폭 조건이 완성된다. 시나리오의 최악 조합은 **Critical 부품 + 단일 소싱 공급업체 + 재고 3일 + Critical severity 이벤트**이며, 이것이 $80M~$127M 규모 노출로 이어진다.

---

## 6. 자동화로 이어지는 경로

두 속성이 만든 값은 Phase 5에서 실제 실행 조건으로 소비된다.

```
IF RiskAssessment.revenueAtRisk > $50M AND
   RiskAssessment.timeToImpactDays < 5:
   THEN 대체 공급처 발주 생성 + 생산 일정 갱신 + 이해관계자 알림 + Activator 경보
```

- `revenueAtRisk` ← `revenue_at_risk` 합계 ← `daysOfSupplyOnHand` × 일 매출
- `timeToImpactDays` ← `daysOfSupplyOnHand` (예시의 GPU Module: 3일)

두 조건이 모두 **`daysOfSupplyOnHand`에서 파생**된다. 즉 이 단일 정수 속성이 금액 임계값과 시간 임계값 양쪽에 동시에 개입해 자동 실행 여부를 결정한다. 그리고 이 값은 Day 2~4의 "4시간마다 최신 재고 데이터로 RiskAssessment 재계산" 루프에서 계속 갱신되는 살아있는 값이다.

---

## 7. 한 줄 요약

`criticalityLevel`(Critical/High/Medium/Low)은 부품 중단의 **파급력**을 4단계로 분류하는 enum이고, `daysOfSupplyOnHand`는 재고로 버틸 수 있는 **일수**로서 $\text{revenue\_at\_risk} = \frac{\text{annualRevenue}}{365} \times \text{daysOfSupplyOnHand}$에서는 노출 금액의 곱셈 계수로, $\text{urgency} = 100 - \text{daysOfSupplyOnHand} \times 10$에서는 긴급도를 깎는 음의 항으로 작용한다. 전자가 "무엇을 해야 하는가", 후자가 "언제까지 해야 하는가"를 정하며, 둘을 교차시켜 P0~P3 대응 우선순위가 결정된다.
