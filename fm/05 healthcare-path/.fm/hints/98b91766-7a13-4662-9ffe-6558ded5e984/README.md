# Diagnosis의 `severity` 속성이 가능하게 하는 임상 활용

## 질문

Diagnosis의 `severity` 속성이 가능하게 하는 임상 활용은?

## 답

**리스크 층화(risk stratification)와 임상 우선순위 결정(clinical prioritization)**이다.
`severity`로 필터링하면 중증 환자를 선별해 우선 대응할 수 있다.

원문의 "What we learned"에 그대로 한 줄로 못 박혀 있다.

> **Severity properties** enable risk stratification and clinical prioritization

---

## 1. Diagnosis 엔티티에서 `severity`의 위치

| Property | Type | Identifier? |
|---|---|---|
| `diagnosisId` | string | ✓ |
| `icdCode` | string | |
| `description` | string | |
| **`severity`** | **string** | |
| `diagnosedDate` | date | |

Diagnosis의 5개 속성은 각자 역할이 다르다. 이 역할 분담을 이해하면 왜 `severity`가 "임상 우선순위"를 담당하는지가 자연히 보인다.

| 속성 | 담당하는 질문 | 담당하는 기능 |
|---|---|---|
| `diagnosisId` | "어느 진단?" | 식별(identity) |
| `icdCode` | "무슨 병?" | **표준화·상호운용성** (보험·청구·연구 시스템 연동) |
| `description` | "사람이 읽으면?" | 가독성 |
| **`severity`** | **"얼마나 심각한가?"** | **리스크 층화·우선순위** |
| `diagnosedDate` | "언제?" | 시계열·기간 질의 (예: "지난 분기") |

핵심 대비: `icdCode`는 **어떤 종류**의 문제인지(what)를 말하고, `severity`는 **얼마나 급한** 문제인지(how bad)를 말한다. 둘은 직교(orthogonal)한다. 같은 ICD 코드라도 severity가 다르면 대응 순서가 완전히 달라진다 — 경증 천식과 중증 천식은 같은 병명이지만 다른 트리아지 대상이다.

> 시험 함정: "severity가 진단을 표준 코드체계와 연결한다"는 `icdCode`의 역할이다. 두 속성의 역할을 섞지 말 것.

---

## 2. 원문에서 `severity`가 실제로 쓰이는 세 곳

`severity`가 왜 중요한지는 추상적 설명보다 **원문에 등장하는 실제 질의 3개**를 보면 즉시 납득된다. 세 질의 모두 `severity`를 **필터 축(filter axis)** 또는 **정렬 축(ranking axis)**으로 쓴다.

### (A) 중증 진단 + 리필 소진 임박 → 치료 중단 위험 (Care gap)

시나리오 개요에 나온 대표 임상 질문이자, 마지막 단계의 GQL 예제다.

> "Which patients diagnosed with severe conditions by cardiology providers still have prescriptions with zero refills remaining?"

그래프 경로:

```
Patient → Diagnosis (severity=severe) ← Provider (specialty=Cardiology)
Diagnosis → Prescription (refillsRemaining=0)
```

```gql
MATCH (p:Patient)-[:diagnosed_with]->(d:Diagnosis)-[:treated_by]->(rx:Prescription)
WHERE d.severity = 'severe' AND rx.refillsRemaining <= 1
RETURN p.patientId, d.description, rx.medication, rx.refillsRemaining
```

여기서 벌어지는 일:

- `severity = 'severe'` → **리스크 층화**. 전체 환자 모집단에서 고위험군만 남긴다.
- `refillsRemaining <= 1` → **운영 신호**. 약이 곧 끊긴다.
- 두 조건의 **교집합** = "중증인데 곧 약이 끊기는 환자" = 지금 당장 전화를 걸어야 하는 사람.

`severity`가 없다면 이 질의는 "리필이 임박한 모든 환자"가 되어 수천 명이 쏟아진다. 그 목록은 실행 불가능하다(actionable하지 않다). `severity`는 그 목록을 **개입 가능한 크기로 압축하는 축**이다. 이것이 "우선순위 결정"의 실질적 의미다.

또한 이 질의는 `severity`(Diagnosis) + `refillsRemaining`(Prescription) + `specialty`(Provider)처럼 **서로 다른 엔티티의 속성을 조합**한다는 점이 중요하다. 케어 체인 `Patient → Diagnosis → Prescription`이 연결되어 있기 때문에, `severity`라는 단일 속성이 체인 전체를 관통하는 필터로 작동한다.

### (B) 치료가 아직 없는 중증 진단 → 누락 탐지 (Negative pattern)

완성 모델이 가능하게 하는 질문 표에 있다.

| Question | Graph path |
|---|---|
| Which severe diagnoses have no treatment yet? | `Diagnosis (severity=severe)` with no → `Prescription` |

이건 (A)와 성격이 다르다. **관계의 부재(absence)를 찾는 질의**다.

```gql
MATCH (d:Diagnosis)
WHERE d.severity = 'severe'
  AND NOT EXISTS { MATCH (d)-[:treated_by]->(:Prescription) }
RETURN d.diagnosisId, d.description, d.diagnosedDate
```

- 중증 진단이 내려졌는데 `treated_by` 엣지가 없다 = **미치료 중증 환자**.
- 이것은 환자 안전(patient safety) 이슈이며, 임상 품질 지표(quality measure)로 직결된다.
- 여기서도 `severity`가 없으면 "처방이 없는 모든 진단"이 되어 의미가 사라진다. 감기 진단에 처방이 없는 건 정상이다. **중증**에 처방이 없는 것이 비정상이다. 즉 `severity`가 **정상/비정상을 가르는 기준선**을 제공한다.

> 온톨로지 관점 포인트: 관계가 **없는 것**을 질의하려면 그 관계가 스키마에 정의되어 있어야 한다. `treated_by`가 모델에 있기 때문에 "없음"을 물을 수 있다. `severity` + 관계 부재의 조합이 "치료 공백(treatment gap)"이라는 임상 개념을 그래프 패턴으로 표현해준다.

### (C) 가장 심각한 상태를 가장 많이 식별한 provider → 순위·집계

Diagnosis 도입 단계에서 새로 가능해진 질문 중 하나다.

> "Which provider identified the most severe conditions last quarter?"

그래프 경로: `Provider → Diagnosis (severity=severe)`, `diagnosedDate`로 기간 제한, provider별 count.

```gql
MATCH (pr:Provider)-[:diagnoses]->(d:Diagnosis)
WHERE d.severity = 'severe'
  AND d.diagnosedDate >= DATE '2026-04-01'
  AND d.diagnosedDate <  DATE '2026-07-01'
RETURN pr.providerId, COUNT(d) AS severeCount
ORDER BY severeCount DESC
```

이 질의가 성립하는 데 필요한 모델 요소 3개:

1. **`diagnoses` 관계** (`Provider → Diagnosis`) — 원문이 강조하는 **dual authorship**. Diagnosis는 Patient(누가 앓는가)와 Provider(누가 식별했는가) 양쪽에 연결되어 있어서, 환자 중심 뷰와 **제공자 중심 뷰**를 모두 지원한다. 이 질의는 제공자 중심 뷰다.
2. **`severity`** — 집계 대상을 중증으로 한정.
3. **`diagnosedDate`** — "지난 분기"라는 기간 창.

`severity`가 여기서 담당하는 건 필터를 넘어 **워크로드·케이스믹스(case mix) 측정**이다. 어느 의사가 고난도 케이스를 많이 보는지 알면 인력 배치, 성과 평가, 보상 조정에 쓸 수 있다.

> 주의: 이 지표는 해석에 조심해야 한다. severe 건수가 많다는 건 (a) 실제로 중증 환자를 많이 본다, (b) severity를 후하게 매기는 코딩 습관이 있다, 두 가지로 다 읽힐 수 있다. `severity`가 **자유 문자열**이면 (b)의 위험이 커진다 — 이것이 바로 다음 절의 문제로 이어진다.

### 세 질의의 공통 구조

| 질의 | severity의 역할 | 결합되는 요소 | 산출물 |
|---|---|---|---|
| (A) severe + 리필 임박 | 고위험군 선별 | `refillsRemaining`, `specialty` | 개입 대상 환자 명단 |
| (B) severe인데 처방 없음 | 정상/비정상 기준선 | 관계 **부재**(`treated_by`) | 치료 공백 알림 |
| (C) severe 최다 식별 provider | 집계 대상 한정 | `diagnoses` 관계, `diagnosedDate` | 제공자 순위·케이스믹스 |

패턴: `severity`는 혼자서는 아무것도 안 한다. **다른 축(운영 지표 / 관계 부재 / 시간·집계)과 결합될 때 리스크 층화와 우선순위가 나온다.** 이것이 온톨로지의 가치이기도 하다 — 속성 하나가 그래프 전체를 가로지르는 렌즈가 된다.

---

## 3. `severity`가 `string`인 것의 장단점

원문 표는 `severity`를 명시적으로 `string`으로 둔다. 이건 학습용으로는 자연스럽지만, 실무 모델링에서는 **트레이드오프가 뚜렷한 선택**이다.

### 장점

| 장점 | 설명 |
|---|---|
| **소스 다양성 수용** | EHR, 스케줄링, 약국, 청구 시스템이 각각 다른 표현을 쓴다. `string`은 있는 그대로 받아들여 통합 초기에 데이터 손실이 없다. |
| **스키마 변경 없이 확장** | 새 등급(`critical`, `life-threatening`)이 생겨도 스키마를 안 고친다. enum이면 마이그레이션이 필요하다. |
| **가독성** | `'severe'`는 사람이 보면 바로 안다. `4`는 코드북을 봐야 한다. |
| **프로토타이핑 속도** | 도메인 등급 체계가 아직 확정 안 된 초기 모델링 단계에 적합. 학습 경로가 `string`을 쓴 이유. |

### 단점

#### (1) 순서 비교가 불가능하다 — 가장 치명적

`severity`는 본질적으로 **서수형(ordinal)** 데이터다. mild < moderate < severe라는 **순서가 의미를 갖는다**. 그런데 `string`은 그 순서를 모델이 알지 못한다.

- `WHERE d.severity >= 'moderate'` ("중등도 이상 전부") 같은 자연스러운 질의를 쓸 수 없다.
- 쓸 수 있는 건 `IN ('moderate', 'severe')` 같은 **열거**뿐이다. 등급이 추가될 때마다 모든 질의를 찾아 고쳐야 한다.
- `MAX(d.severity)` ("이 환자의 가장 심한 진단")가 의미 없는 값을 낸다.
- **사전순 함정**: 우연히 `'mild' < 'moderate' < 'severe'`는 알파벳순과 임상적 순서가 일치한다. 그래서 문자열 비교가 "되는 것처럼" 보인다. 하지만 `'critical'`을 추가하는 순간 무너진다 — 알파벳순으로 `'critical'`은 `'mild'`보다 **앞**이라서, 가장 위중한 등급이 가장 경한 등급으로 정렬된다. 조용히 틀리는(silently wrong) 종류의 버그라 더 위험하다.

#### (2) 값 통제가 없다 (제약 부재)

`string`은 어떤 값이든 받는다. 실제 통합 데이터에서 벌어지는 일:

```
severe / Severe / SEVERE / sev / s / 3 / High / severe   / 중증 / null / "" / unknown / N/A
```

결과:

- `WHERE severity = 'severe'`가 **조용히 환자를 놓친다**. `'Severe'`로 들어간 레코드는 매칭되지 않는다. (A)·(B) 질의가 중증 환자를 빠뜨리면 그건 안전 사고다.
- `GROUP BY severity` 집계가 같은 등급을 여러 버킷으로 쪼갠다 → (C)의 provider 순위가 왜곡된다.
- 오타·동의어를 잡아줄 스키마 레벨 검증이 없어서, 문제는 런타임 질의 결과에서야 드러난다.

#### (3) 그 외

- **국제화/다국어**: `'중증'`과 `'severe'`가 같은 개념인데 다른 값이 된다.
- **외부 표준과 단절**: SNOMED·FHIR의 severity 개념 코드에 자동 매핑되지 않는다. `icdCode`로 상호운용성을 확보한 모델이 `severity`에서는 그것을 놓치는 셈이라 다소 비일관적이다.
- **계산 불가**: 리스크 점수 산출처럼 severity를 수치로 가중합해야 하는 계산에 바로 쓸 수 없다.

### 대안 설계

#### 대안 1 — Enum / 통제 어휘(controlled vocabulary)

`severity`를 허용값이 고정된 열거형으로 선언한다.

```
severity: enum { mild, moderate, severe, critical }
```

- 얻는 것: 값 검증, 오타 차단, 일관된 집계, UI 드롭다운 자동 생성.
- 여전히 아쉬운 것: 많은 시스템에서 enum 자체는 순서 비교를 보장하지 않는다(선언 순서를 서열로 쓰는 구현도 있지만 의존하기 위험하다).
- 비용: 등급 추가 시 스키마 변경·마이그레이션.

#### 대안 2 — 서수 인코딩(ordinal encoding)

등급을 정수로 표현한다.

```
severityLevel: integer   // 1=mild, 2=moderate, 3=severe, 4=critical
```

- 얻는 것: **`WHERE severityLevel >= 2`가 그대로 동작한다.** `ORDER BY`, `MAX()`, 평균·가중합 모두 자연스럽다.
- 원문의 마지막 takeaway와 정확히 같은 논리다 — *"**Integer properties** (refillsRemaining, duration) enable operational queries."* `refillsRemaining`이 정수라서 `<= 1` 비교가 가능했던 것처럼, severity도 정수라면 `>=` 비교가 가능해진다. 실제로 GQL 예제에서 두 조건은 `d.severity = 'severe'`(등호만 가능)와 `rx.refillsRemaining <= 1`(부등호 가능)로 **표현력이 비대칭**인데, 그 원인이 바로 타입 차이다.
- 잃는 것: 가독성. `3`만 보고는 뜻을 모른다. 또 정수는 **등간(interval)** 처럼 보이게 만드는 함정이 있다 — "severe(3)는 mild(1)의 3배 심각"은 임상적으로 무의미하다. 평균 severity 같은 지표를 만들 때 조심해야 한다.

#### 대안 3 — 라벨 + 서열을 둘 다 (실무 권장)

```
severity:      string   // 'severe'  — 표시·보고용
severityRank:  integer  // 3         — 비교·정렬·집계용
```

중복이지만 의도적인 중복이다. 사람이 읽는 값과 기계가 비교하는 값을 분리한다. 둘의 동기화는 파이프라인이나 파생 속성으로 보장한다.

#### 대안 4 — Severity를 별도 엔티티/참조 데이터로 승격

```
Diagnosis --[has_severity]--> SeverityLevel { code, label, rank, description, scale }
```

- 등급 체계 자체에 메타데이터를 붙일 수 있다: 어떤 척도(ESI인지 CTAS인지)에 속하는가, 표시 라벨, 다국어 이름, 순위, 정의.
- 여러 척도를 동시에 지원할 수 있다. 응급실은 ESI 1–5, 외래는 mild/moderate/severe를 쓸 수 있다.
- 온톨로지답게 **어휘를 데이터로 다루는** 방식이다. 대가는 조인 하나가 늘어나고 모델이 무거워지는 것.

#### 대안 5 — 표준 코드체계 참조

`icdCode`가 ICD를 참조하는 것과 같은 논리를 severity에도 적용한다. SNOMED CT의 severity qualifier를 값으로 쓴다.

| 개념 | SNOMED CT 코드 |
|---|---|
| Mild (qualifier value) | `255604002` |
| Moderate (severity modifier) | `6736007` |
| Severe (severity modifier) | `24484000` |

HL7 FHIR의 `Condition.severity`가 정확히 이 세 코드를 기본 밸류셋으로 쓴다. 즉 이 모델의 Diagnosis는 FHIR `Condition` 리소스에 대응하며, `severity`를 코드화하면 EHR 간 교환이 가능해진다. SNOMED에서는 "severe headache"처럼 단일 코드가 없을 때 두 코드(질환 + 심각도 수식어)를 **후조합(post-coordination)** 해서 표현한다.

### 정리

| 설계 | 순서 비교 | 값 검증 | 가독성 | 확장 비용 | 상호운용성 |
|---|---|---|---|---|---|
| `string` (원문) | ✗ | ✗ | ◎ | 낮음 | ✗ |
| enum | △ | ◎ | ◎ | 중간 | △ |
| integer rank | ◎ | △ | ✗ | 낮음 | ✗ |
| 라벨 + rank | ◎ | ○ | ◎ | 낮음 | △ |
| 별도 엔티티 | ◎ | ◎ | ◎ | 높음 | ◎ |
| 표준 코드(SNOMED/FHIR) | △ | ◎ | △ | 중간 | ◎ |

**학습 경로가 `string`을 고른 것은 틀린 게 아니라, 단계에 맞는 선택이다.** 목적은 "severity라는 축이 리스크 층화를 가능하게 한다"는 개념을 전달하는 것이고, 타입 정교화는 다음 문제다. 다만 실제 시스템을 만든다면 최소한 **통제 어휘 + 서수 인코딩**은 갖추는 것이 맞다.

---

## 4. 실무의 리스크 층화·트리아지 관행

원문의 "risk stratification"과 "clinical prioritization"은 추상 용어가 아니라, 현실 의료에 대응물이 있다.

### 응급실 트리아지 — ESI (Emergency Severity Index)

미국 응급실 표준. AHRQ가 배포하며 현재 5판(ESI v5)까지 나왔다. 환자를 **1(가장 위급) ~ 5(가장 덜 위급)** 다섯 단계로 층화한다.

| 레벨 | 구분 | 기준 |
|---|---|---|
| 1 | Emergent | 즉각적 생명 구조 개입 필요 (지연 시 사망·비가역적 손상) |
| 2 | Emergent | 기다리게 하면 안 되는 환자 — 급성도(acuity)와 악화 위험으로 판정 |
| 3 | Urgent | 잠시 안전하게 대기 가능 — 여기부터는 **예상 자원 소요량**으로 판정 |
| 4 | Non-urgent | 오래 안전하게 대기 가능 |
| 5 | Non-urgent | 최소 자원 |

주목할 점 두 가지:

1. **정수 척도다.** 1~5의 순서가 의미를 가지며 비교·정렬이 필수다. 실무 표준이 서수형을 쓰는 이유가 위 절의 "string은 순서 비교 불가"와 정확히 맞물린다.
2. **레벨의 판정 기준이 구간마다 다르다.** 1–2는 급성도, 3–5는 자원 소요량. 즉 severity는 단순한 "심함의 정도"가 아니라 **운영 결정을 내리기 위한 파생 지표**다. ESI v5는 이전 판보다 낮은 등급으로 분류된 환자의 **비정상 활력징후 포착**을 강화했다 — 잘못된 층화(under-triage)의 위험을 줄이려는 방향이다.

유사 척도로 캐나다의 CTAS, 영국의 Manchester Triage System이 있다. 모두 순서 있는 등급 체계다.

### 그 밖의 층화 도구

- **조기경고점수(NEWS2, MEWS)**: 활력징후를 합산해 악화 위험을 점수화. 임계값 초과 시 신속대응팀 호출 — 자동 우선순위 결정.
- **동반질환 지수(Charlson Comorbidity Index)**: 진단 목록을 가중합해 사망 위험을 추정. 진단(diagnosis) 집합 → 단일 리스크 점수. 이 모델의 `Patient → Diagnosis` 일대다 관계가 바로 이런 계산의 입력이 된다.
- **리스크 조정 / HCC 코딩**: 진단 코드와 중증도로 환자 모집단의 예상 비용을 조정. `icdCode` + `severity`가 청구·보험과 만나는 지점.
- **케어 매니지먼트 대상 선정**: 고위험 환자를 골라 집중 관리. 원문 질의 (A)가 정확히 이 작업의 축소판이다.

이 관행들의 공통점: **모두 순서 있는 수치 척도로 표현되고, 그 값에 따라 다른 행동이 트리거된다.** severity를 잘 모델링해야 하는 실질적 이유다.

---

## 5. 오답 노트

| 헷갈리는 답 | 왜 틀렸나 |
|---|---|
| "진단을 표준 코드체계와 연결해 상호운용성을 준다" | `icdCode`의 역할. severity는 심각도 축. |
| "중복 진단 기록을 막는다" | 중복 방지는 식별자(`diagnosisId`)의 역할. |
| "진단 시점을 추적한다" | `diagnosedDate`의 역할. |
| "환자와 제공자 양쪽 관점을 가능하게 한다" | dual authorship, 즉 `diagnosed_with` / `diagnoses` **관계**의 역할. 속성이 아니다. |
| "리필 추적과 복약 순응도 모니터링" | `refillsRemaining`(Prescription)의 역할. 단 severity와 **조합**하면 (A) 질의가 된다. |

---

## 6. 암기 훅

- **`icdCode` = 무슨 병 (what)** / **`severity` = 얼마나 급한가 (how bad)** → **급한 것부터(prioritization)**, **급한 사람 골라내기(stratification)**
- 세 질의로 기억: **중증+리필임박**(개입 대상) / **중증인데 처방없음**(치료 공백) / **중증 최다 식별 provider**(케이스믹스)
- 타입 교훈: **severity는 서수인데 string으로 쓰면 `>` 를 못 쓴다.** `refillsRemaining`은 integer라서 `<= 1`이 되고, `severity`는 string이라서 `= 'severe'`밖에 안 된다 — 이 비대칭이 힌트다.

---

## Sources

- [Emergency Severity Index (ESI): A Triage Tool for Emergency Departments — AHRQ](https://www.ahrq.gov/patient-safety/settings/emergency-dept/esi.html)
- [Emergency Severity Index Handbook, Fifth Edition](https://media.emscimprovement.center/documents/Emergency_Severity_Index_Handbook.pdf)
- [The Emergency Severity Index (ESI) Version 5: Simulation of Predictive Validity and Triage Level Distribution — Journal of Emergency Medicine](https://www.jem-journal.com/article/S0736-4679(25)00288-4/fulltext)
- [Severe (severity modifier) (qualifier value) — SNOMED CT 24484000](https://snomedbrowser.com/Codes/Details/24484000)
- [Qualifying Characteristics — SNOMED CT Editorial Guide](https://docs.snomed.org/snomed-ct-specifications/snomed-ct-editorial-guide/readme/concept-model-overview/qualifying-characteristics)
- [2.3 Clinical Assessment — SNOMED CT Guide for COVID-19 (severity post-coordination)](https://docs.snomed.org/implementation-guides/snomed-ct-guide-for-covid-19/2-coding-covid-19-related-data/2.3-clinical-assessment)
- [ValueSet condition-severity — HL7 FHIR v5.0.0](https://www.hl7.org/fhir/valueset-condition-severity.xml.html)
