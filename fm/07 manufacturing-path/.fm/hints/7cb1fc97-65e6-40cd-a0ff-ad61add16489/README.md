# 하나의 Part가 여러 Quality-Check를 가질 수 있는 이유

## 질문과 답

**Q.** 하나의 Part가 여러 Quality-Check를 가질 수 있는 이유는?

**A.** 한 부품이 여러 번 검사될 수 있기 때문이다. 최초 검사와 재작업 후 재검사(re-check after rework)가 대표적이며, 그래서 `inspects`는 다대일이다.

---

## 1. `inspects`가 다대일(many-to-one)이라는 말의 의미

원문 자료의 관계 정의는 다음과 같다.

> **inspects** — `Quality-Check` → `Part` (many-to-one)
> Each quality check inspects a specific part. A part may undergo multiple inspections (initial check, re-check after rework).

방향과 카디널리티를 정확히 읽어야 한다.

| 관점 | 카디널리티 | 읽는 법 |
|---|---|---|
| Quality-Check 쪽에서 | 1 (many 쪽의 각 인스턴스) | 검사 1건은 **정확히 하나의** 부품만 검사한다 |
| Part 쪽에서 | N (one 쪽) | 부품 1개는 **여러 건의** 검사 기록을 가질 수 있다 |

즉 "many-to-one"의 **many가 Quality-Check**, **one이 Part**다. 화살표가 `Quality-Check → Part`로 향하는 이유도 여기에 있다 — 여러 개(many)인 쪽이 하나(one)인 쪽을 가리킨다. 같은 학습 경로의 `monitors` (`Sensor → Machine`, many-to-one), `assigned_to` (`Work-Order → Machine`, many-to-one)와 정확히 같은 패턴이다. 센서 여러 개가 기계 하나를 감시하듯, 검사 기록 여러 건이 부품 하나를 가리킨다.

만약 이 관계가 일대일(one-to-one)이었다면 부품당 검사는 평생 단 한 번만 가능해지고, 재검사 자체를 모델링할 수 없게 된다.

## 2. 재작업 루프(rework loop) — 여러 검사가 생기는 실제 경로

Quality-Check 엔티티의 속성 표를 보자.

| Property | Type | Identifier? |
|---|---|---|
| `checkId` | string | ✓ |
| `inspector` | string | |
| `checkDate` | date | |
| `passed` | boolean | |
| `defectCode` | string | |

원문의 설명대로 `passed`는 **"부품이 출하될지(ship) 재작업될지(rework)를 결정하는" 결정적 속성**이고, `defectCode`는 **근본 원인 분석(root cause analysis)을 위해 불량을 분류**한다.

실제 공정에서 일어나는 흐름은 이렇다.

```
Part(P-1001) 생산 완료
   │
   ├─ QC-001  checkDate=2026-03-01  inspector=김검사  passed=false  defectCode=DIM-OUT
   │             └─ 실패 → 재작업(rework)으로 반송
   │
   ├─ (재작업 수행: 재가공, 치수 보정 등)
   │
   └─ QC-014  checkDate=2026-03-03  inspector=박검사  passed=true   defectCode=null
                 └─ 합격 → 출하
```

한 부품에 대해 `QC-001`, `QC-014` 두 개의 Quality-Check 노드가 생기고, 둘 다 `inspects`로 같은 Part를 가리킨다. 이것이 원문이 말하는 "initial check, re-check after rework"다.

재검사 외에도 부품 하나가 복수 검사를 받는 경우는 많다. 공정 단계별 중간 검사, 샘플링 후 전수 재검, 고객 클레임에 따른 재검증 등이 모두 같은 구조로 표현된다. 모델은 "왜 여러 번인지"를 제한하지 않고, 단지 "여러 번일 수 있다"만 표현한다.

## 3. `checkDate` + `inspector` — 각 검사를 고유한 역사적 기록으로 만드는 장치

부품에 검사가 여러 번 붙을 수 있다면, 검사끼리 **구분**되어야 의미가 있다. 그 구분을 만드는 것이 `checkId`(식별자)와 함께 `checkDate`, `inspector`다.

- **`checkDate`** — 검사의 **시점**을 못 박는다. 이 덕분에 "최초 검사"와 "재검사"의 순서가 데이터 자체로 결정된다. 시간 순 정렬만으로 재작업 전/후를 판별할 수 있고, "지난주 실패한 검사"(시나리오 개요의 대표 질문)나 defect rate 추이 같은 시계열 분석이 가능해진다.
- **`inspector`** — 검사의 **주체**를 남긴다. 누가 통과시켰는지 추적할 수 있어 감사(audit) 요구를 충족하고, 검사자별 판정 편차 같은 품질 관리 이슈도 볼 수 있다.
- **`defectCode`** — 각 검사마다 다른 불량 유형이 나올 수 있다. 1차에서 치수 불량, 2차에서 표면 결함이 나왔다면 이는 서로 다른 두 사실이며, 각각의 Quality-Check 노드에 따로 기록되어야 한다.

핵심은 이것이다. Quality-Check는 **부품의 상태가 아니라 "검사라는 사건(event)"** 을 표현하는 엔티티다. 사건은 발생 시점과 행위자를 갖고, 발생한 뒤에는 덮어쓰이지 않는다. 그래서 `passed=false` 기록은 나중에 `passed=true` 검사가 추가되어도 사라지지 않고 **이력으로 누적**된다.

이는 이 학습 경로가 반복해 보여준 패턴과 같다. Work-Order가 Machine과 Part 사이의 "사건"을 표현하듯(원문: 헬스케어의 Appointment가 Patient와 Provider를 잇는 것과 유사), Quality-Check는 Part에 대한 "검사 사건"을 표현한다. 사건 엔티티는 본질적으로 여러 개가 쌓인다.

## 4. 이 구조가 가능하게 하는 질의 — "재검사가 필요한 부품"

원문의 질의 표를 보자.

| Question | Graph path |
|---|---|
| Which machines produce parts that fail inspection? | `Machine → Part ← Quality-Check (passed=false)` |
| Which sensors were abnormal when defective parts were produced? | `Sensor → Machine → Part ← Quality-Check (passed=false)` |
| What is the defect rate by work order priority? | `Work-Order (priority) → Part ← Quality-Check` |
| **Which parts need re-inspection?** | **`Part ← Quality-Check (passed=false, count > 1)`** |

마지막 행이 이 카드가 겨냥하는 지점이다. `count > 1`이라는 조건은 **한 Part에 검사 노드가 여러 개 매달릴 수 있어야만** 성립한다. 다대일 관계가 아니면 count는 언제나 1이고, 이 질의는 아예 작성 자체가 불가능하다.

의미를 풀면 이렇다.

- `Part ← Quality-Check`: 화살표가 Part로 들어온다 — 부품을 기준으로 그에 붙은 검사들을 역방향으로 모은다.
- `passed=false`: 그중 실패한 검사만 고른다.
- `count > 1`: 실패가 **두 번 이상** 누적된 부품 — 재작업했는데 또 떨어졌거나, 만성적으로 문제가 있는 부품이다. 단순 실패보다 훨씬 강한 신호이며, 폐기(scrap) 판정이나 공정 개선의 우선 대상이 된다.

여기서 `count`는 집계다. 집계할 대상이 존재하려면 개별 기록이 각각 살아 있어야 한다. 다대일 관계 + 사건 엔티티 설계가 곧 집계 가능성을 만들어 준다.

같은 데이터로 파생되는 질의도 많다.
- 부품별 검사 횟수 → 재작업 비용, 수율(yield) 산출
- 첫 검사 실패율 vs 최종 합격률 → 공정 능력 지표
- `defectCode` 분포 → 근본 원인 분석
- 원문의 GQL 예시처럼 센서 이상치와 불량을 상관 분석:

```gql
MATCH (s:Sensor)-[:monitors]->(m:Machine)-[:has_part]->(p:Part)<-[:inspects]-(qc:QualityCheck)
WHERE s.lastReading > s.threshold AND qc.passed = false
RETURN m.name, s.type, s.lastReading, p.name, qc.defectCode
```

여기서도 `<-[:inspects]-`는 Part 하나에 여러 QualityCheck가 매칭될 수 있음을 전제로 한다.

## 5. 만약 `passed`를 Part에 직접 저장했다면 — 무엇을 잃는가

가장 흔한 안티패턴은 Quality-Check 엔티티를 없애고 Part에 `passed: boolean` 같은 플래그 하나를 두는 것이다. 무엇이 사라지는지 항목별로 보자.

| 잃는 것 | 설명 |
|---|---|
| **검사 이력(inspection history)** | Part의 `passed`는 검사할 때마다 **덮어쓰기(overwrite)** 된다. 재작업 후 `true`로 바꾸는 순간, 최초에 실패했다는 사실 자체가 데이터에서 소멸한다. 겉보기에 "정상 부품"과 "한 번 떨어졌다 고쳐진 부품"이 구별되지 않는다. |
| **근본 원인 추적(root-cause trail)** | `defectCode`가 어느 시점의 어떤 불량이었는지 남지 않는다. 원문이 강조한 피드백 루프 `Quality-Check (passed=false) → Part → Work-Order → Machine`이 끊긴다 — 추적할 실패 기록 자체가 없기 때문이다. |
| **시점 정보** | `checkDate`가 없으니 "지난주 불량"처럼 기간을 자르는 질의가 불가능하다. 센서 이상치가 발생한 시각과 검사 결과를 시간축에서 맞춰 볼 수도 없다. |
| **검사 주체 / 감사 추적** | `inspector`가 사라져 누가 어떤 판정을 내렸는지 확인할 수 없다. 규제 산업에서는 이것만으로도 설계가 실격이다. |
| **`count > 1` 질의** | 플래그는 개수 개념이 없다. "재검사가 필요한 부품" 질의가 원천적으로 불가능해진다. |
| **다중 불량의 표현** | 한 부품에 서로 다른 불량 코드가 순차적으로 나온 상황을 단일 문자열 필드로는 담을 수 없다. |

정리하면, Part의 플래그는 **"지금 상태"** 만 말할 수 있고, Quality-Check 엔티티는 **"어떤 과정을 거쳐 그 상태에 도달했는가"** 를 말할 수 있다. 스마트 팩토리의 지속적 개선(continuous improvement)은 후자에서만 나온다. 원문의 핵심 정리 3번 "Quality feedback loops enable root cause analysis across the production chain"이 성립하려면 반드시 검사가 독립 엔티티여야 한다.

> 일반화하면: **시간에 따라 반복될 수 있고, 발생 시점·행위자·결과를 갖는 것은 속성이 아니라 엔티티로 모델링한다.** 부품의 검사, 환자의 진료, 계좌의 거래가 모두 같은 규칙을 따른다.

---

## 한 줄 요약

`inspects`가 `Quality-Check → Part` 다대일인 것은 한 부품이 최초 검사·재작업 후 재검사 등 **여러 번 검사될 수 있기 때문**이며, `checkDate`·`inspector`가 각 검사를 덮어쓰기 불가능한 고유 이력으로 만들어 주기에 `Part ← Quality-Check (passed=false, count > 1)` 같은 재검사 대상 조회와 근본 원인 추적이 가능해진다.
