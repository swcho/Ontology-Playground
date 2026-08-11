# Quality-Check의 `passed`가 가장 중요한 이유

## 핵심 답

`passed` boolean이 **부품이 출하될지, 재작업(rework)될지**를 결정하기 때문이다.

자료의 표현 그대로: *"The `passed` boolean is the critical property — it determines whether a part ships or gets reworked."* 그리고 마지막 핵심 정리에서도 *"**Boolean properties** (passed) create clear decision points in the workflow"* 라고 못 박는다.

즉 `passed`는 단순한 기록용 필드가 아니라, **워크플로가 두 갈래로 갈라지는 분기점(decision point)** 그 자체다.

---

## Quality-Check 엔티티 전체 맥락

| Property | Type | Identifier? | 역할 |
|---|---|---|---|
| `checkId` | string | ✓ | 검사 건의 식별자 |
| `inspector` | string | | 누가 검사했는가 (책임 추적) |
| `checkDate` | date | | 언제 검사했는가 (기간 필터) |
| `passed` | boolean | | **합격/불합격 — 분기점** |
| `defectCode` | string | | 실패 유형 분류 (근본 원인 분석) |

관계는 하나뿐이다.

- **inspects** — `Quality-Check` → `Part` (다대일)
  각 검사는 특정 부품 하나를 검사한다. 한 부품은 여러 번 검사받을 수 있다 — 최초 검사, 재작업 후 재검사.

`checkId`, `inspector`, `checkDate`는 "이 검사가 무엇이었는지"를 서술하는 메타데이터다. 반면 `passed`만이 **다음에 무슨 일이 일어날지**를 바꾼다. 이것이 "가장 중요한 속성"인 이유다.

---

## 왜 자유 텍스트 판정이 아니라 boolean인가

만약 검사 결과를 `result: string`으로 두고 검사원이 `"통과"`, `"OK"`, `"pass"`, `"이상 없음"`, `"합격 (경미한 흠집 있음)"` 같은 값을 적는다면 어떻게 될까?

| 문제 | 결과 |
|---|---|
| 표기 흔들림 | `"pass"` / `"Pass"` / `"OK"` / `"통과"`가 전부 다른 값으로 취급된다 |
| 쿼리 불가 | `WHERE result = ?` 에 넣을 정답 문자열이 없다. 매번 문자열 매칭 규칙을 만들어야 한다 |
| 집계 불가 | 불량률을 세려면 먼저 문자열을 정규화하는 전처리가 필요하다 |
| 시스템 간 불일치 | MES와 QMS가 서로 다른 어휘를 쓰면 통합 시점에 깨진다 |

boolean은 이 모든 걸 없앤다. 값의 도메인이 `true` / `false` 두 개로 닫혀 있으므로, **모든 다운스트림 쿼리가 똑같은 방식으로 필터링**할 수 있다.

### 쿼리 표가 이를 증명한다

완성 모델이 답하는 질문 4개 중 **3개가 `passed=false`를 필터 조건으로 쓴다**.

| 질문 | 그래프 경로 | `passed` 사용 |
|---|---|---|
| 검사 실패 부품을 만든 기계는? | Machine → Part ← Quality-Check (passed=false) | ✓ |
| 불량 생산 시점에 이상했던 센서는? | Sensor → Machine → Part ← Quality-Check (passed=false) | ✓ |
| 작업지시 우선순위별 불량률은? | Work-Order (priority) → Part ← Quality-Check | 분모/분자 계산에 필요 |
| 재검사가 필요한 부품은? | Part ← Quality-Check (passed=false, count > 1) | ✓ |

GQL 예제에서도 `passed`가 WHERE 절의 절반을 차지한다.

```gql
MATCH (s:Sensor)-[:monitors]->(m:Machine)-[:has_part]->(p:Part)<-[:inspects]-(qc:QualityCheck)
WHERE s.lastReading > s.threshold AND qc.passed = false
RETURN m.name, s.type, s.lastReading, p.name, qc.defectCode
```

`s.lastReading > s.threshold`(센서 이상)와 `qc.passed = false`(품질 실패)가 AND로 묶여 있다. 두 조건 모두 **단순한 비교 연산**이라 이 상관 분석이 한 줄로 표현된다. 만약 `passed`가 자유 텍스트였다면 이 WHERE 절 자체가 성립하지 않는다.

---

## `passed`와 `defectCode`의 짝

두 속성은 함께 움직인다. 하나가 분기를 만들고, 다른 하나가 분기의 이유를 설명한다.

| `passed` | `defectCode` | 워크플로 |
|---|---|---|
| `true` | null / 빈 값 | 부품 **출하(ship)** |
| `false` | 유형 코드 (예: `SURFACE-01`, `DIM-OOT`) | 부품 **재작업(rework)** → 재검사 |

- `passed`는 **"무엇을 할 것인가"** 를 결정한다 → 출하 vs 재작업
- `defectCode`는 **"왜 실패했는가"** 를 분류한다 → 근본 원인 분석(root cause analysis)

자료의 표현대로 *"The `defectCode` property categorizes failures for root cause analysis."* `defectCode`는 `passed = false`인 경우에만 의미가 있는 종속 속성이다. 그래서 위 GQL도 `qc.passed = false`로 먼저 거른 뒤에 `qc.defectCode`를 RETURN한다 — 통과한 검사의 defectCode를 뽑아봐야 전부 빈 값이기 때문이다.

> 온톨로지 설계 관점: boolean이 **게이트(gate)** 역할을, 코드 문자열이 **라벨(label)** 역할을 한다. 게이트를 문자열로 만들면 게이트와 라벨이 뒤섞여 둘 다 못 쓰게 된다.

---

## 집계: 불량률(defect rate)

boolean이기 때문에 불량률이 산술 한 줄로 나온다.

```
불량률 = COUNT(passed = false) / COUNT(*)
```

`true`/`false`는 `1`/`0`으로 그대로 환산되므로, 평균을 내면 그것이 곧 합격률이다. 쿼리 표의 세 번째 질문 **"작업지시 우선순위별 불량률은?"** 이 정확히 이 계산이다.

- 경로: `Work-Order (priority) → Part ← Quality-Check`
- Work-Order의 `priority`로 그룹핑하고, 각 그룹에서 `passed = false` 비율을 센다
- 결과: "긴급(urgent) 작업지시의 불량률이 일반 작업지시의 3배" 같은 결론

같은 방식으로 기계별 · 검사원별(`inspector`) · 기간별(`checkDate`) 불량률도 전부 같은 필터 하나로 뽑힌다. **집계 축만 바뀌고 필터 조건은 항상 `passed = false`로 고정**된다는 점이 boolean의 힘이다.

---

## 피드백 루프: Machine으로 되돌아가기

`passed = false`는 단순히 그 부품 하나를 멈추는 데서 끝나지 않는다. 생산 체인을 **역방향으로 추적**하는 출발점이 된다.

```
Quality-Check (passed=false) → Part → Work-Order → Machine
```

- **inspects** 관계를 거꾸로 타면 문제의 Part에 도달한다
- **produces** / **has_part**를 거꾸로 타면 그 Part를 만든 Work-Order와 Machine에 도달한다
- 거기서 **monitors**를 타고 내려가면 그 시점 Machine의 Sensor 값까지 도달한다

자료의 표현: *"When a quality check fails, the production chain reverses ... This feedback loop is how smart factories identify problematic machines and improve production quality over time."*

즉 `passed = false`는 **루프의 트리거**다. 이 값이 boolean이라 "실패한 검사 전부"를 정확히 한 번에 집어낼 수 있고, 거기서 역추적이 시작된다. 스마트 팩토리의 지속적 개선(continuous improvement)이 이 한 비트 위에서 돌아간다.

---

## 설계상의 주의: 2값 속성의 한계

`passed`가 boolean이라는 것은 **상태가 딱 두 개뿐**이라는 뜻이다. 이는 장점이자 제약이다.

| 표현할 수 없는 상태 | 상황 |
|---|---|
| `pending` / `in-progress` | 검사가 시작되었지만 아직 결과가 안 나옴 |
| `waived` | 예외 승인으로 검사를 면제함 |
| `conditional pass` | 조건부 합격 (경미한 결함, 등급 하향 출하) |
| `not applicable` | 해당 부품에 적용되지 않는 검사 항목 |

boolean에서는 이런 상태를 `null`로 뭉개거나 별도 플래그를 덧붙이는 수밖에 없고, 그러면 `WHERE passed = false`가 조용히 틀린 답을 준다 — "아직 검사 중"인 건이 "합격"으로 세어지거나 아예 누락된다.

### 대안: status enum

검사가 **진행 중일 수 있다면** boolean 대신 상태 enum이 맞는 선택이다.

```
status: enum { pending, passed, failed, waived }
```

이렇게 하면 진행 중 상태를 1급 시민으로 표현하면서도 값 도메인이 여전히 닫혀 있어 쿼리·집계의 장점을 유지한다. Machine의 `status`(`running` / `idle` / `maintenance` / `offline`)나 Work-Order의 `status`가 정확히 이 패턴을 쓰고 있다는 점에 주목하자 — **같은 온톨로지 안에 두 방식이 공존**한다.

> 판단 기준: 값이 **오직 최종 결과**만 담고 중간 상태가 없다면 boolean. 시간에 따라 전이(transition)하는 라이프사이클이 있다면 enum. 이 학습 경로의 Quality-Check는 "검사가 끝난 뒤 기록되는 결과"로 단순화했기 때문에 boolean이 성립한다.

---

## 암기 팁

- **한 문장**: `passed`는 *출하냐 재작업이냐*를 가르는 스위치다.
- **짝으로 기억**: `passed` = 무엇을 할까(분기), `defectCode` = 왜 그런가(분류).
- **숫자로 기억**: 쿼리 표 4개 중 **3개**가 `passed=false`로 필터링한다.
- **루프 방향**: 실패하면 화살표를 거꾸로 — `Quality-Check → Part → Work-Order → Machine`.
- **한계 한 줄**: 2값이라 `pending`이 없다. 검사가 진행 중일 수 있으면 enum으로.
