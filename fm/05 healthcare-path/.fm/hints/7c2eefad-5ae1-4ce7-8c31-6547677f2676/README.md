# care chain(진료 체인)이란?

## 한 줄 정답

Healthcare 온톨로지에서 **`Patient → Diagnosis → Prescription`으로 이어지는 경로**를 가리킨다.
환자가 진단을 받고, 그 진단에 대한 치료(처방)를 받는 **실제 임상 흐름을 그래프 경로로 표현한 것**이다.

원문에서는 다음과 같이 정의한다:

> **Care chain:** The complete path is now `Patient → Diagnosis → Prescription`, with `Provider` connecting at every stage (sees appointments, makes diagnoses, writes prescriptions). This reflects the real clinical workflow.

---

## 왜 "체인(chain)"인가

care chain은 특정 엔티티나 관계 하나의 이름이 아니다. **여러 관계를 이어 붙여 만들어지는 다중 홉(multi-hop) 경로**의 이름이다.

| 구간 | 관계 이름 | 방향 / 카디널리티 | 의미 |
|---|---|---|---|
| 1번째 홉 | `diagnosed_with` | `Patient` → `Diagnosis` (1:N) | 환자가 여러 진단을 받는다 |
| 2번째 홉 | `treated_by` | `Diagnosis` → `Prescription` (1:N) | 한 진단이 여러 처방으로 이어진다 |

두 관계를 연결하면 `Patient → Diagnosis → Prescription`이 되고, 이것이 곧 care chain이다.

```
                 diagnosed_with          treated_by
   ┌─────────┐ ─────────────────► ┌───────────┐ ─────────────► ┌──────────────┐
   │ Patient │                    │ Diagnosis │                │ Prescription │
   └─────────┘                    └───────────┘                └──────────────┘
        │                               ▲                             ▲
        │ has_appointment               │ diagnoses                   │ prescribes
        ▼                               │                             │
   ┌─────────────┐   sees        ┌────────────┐                       │
   │ Appointment │ ◄──────────── │  Provider  │ ──────────────────────┘
   └─────────────┘               └────────────┘
```

즉 care chain은 **"진료 예약 → 진단 → 치료"라는 임상 워크플로**를 그래프 위에 그대로 얹은 구조다.
원문 표현으로는 이것이 **care cycle을 닫는(closing the care cycle)** 마지막 조각이며, `Prescription`을 추가한 3단계에서 완성된다.

---

## 각 엔티티가 체인에서 맡는 역할

### Patient (체인의 시작점)

| Property | Type | 식별자 |
|---|---|---|
| `patientId` | string | ✓ |
| `mrn` | string | |
| `dateOfBirth` | date | |
| `bloodType` | string | |
| `allergies` | string | |

- 체인의 출발점. "누가 진료를 받는가"
- `mrn`(Medical Record Number)은 병원 내부 식별자, `patientId`는 온톨로지 식별자로 **두 종류의 ID가 공존**한다.

### Diagnosis (체인의 허리)

| Property | Type | 식별자 |
|---|---|---|
| `diagnosisId` | string | ✓ |
| `icdCode` | string | |
| `description` | string | |
| `severity` | string | |
| `diagnosedDate` | date | |

- 체인의 중간 연결점. **진단 없이는 Patient와 Prescription이 직접 연결되지 않는다.**
- `icdCode`는 ICD(International Classification of Diseases) 표준 코드 → 보험/청구/연구 시스템과의 상호운용성 확보
- `severity`는 위험 계층화(risk stratification)와 임상 우선순위 판단에 사용

### Prescription (체인의 끝점)

| Property | Type | 식별자 |
|---|---|---|
| `rxNumber` | string | ✓ |
| `medication` | string | |
| `dosage` | string | |
| `frequency` | string | |
| `refillsRemaining` | integer | |

- 진단에 대한 **치료 반응(treatment response)**. 체인의 종착점.
- `rxNumber`는 약국 표준 식별자
- `refillsRemaining`(integer)은 리필 추적과 복약 순응도(medication adherence) 모니터링을 가능하게 한다.

---

## Provider는 체인의 "모든 단계"에 붙는다

care chain 정의에서 빠지기 쉬운 포인트가 바로 이 부분이다.
`Provider`는 체인 경로 자체에는 포함되지 않지만, **체인의 각 단계마다 옆에서 연결된다.**

| 관계 | 경로 | 대응하는 체인 단계 |
|---|---|---|
| `sees` | `Provider` → `Appointment` | 진료(만남) |
| `diagnoses` | `Provider` → `Diagnosis` | 진단 |
| `prescribes` | `Provider` → `Prescription` | 처방 |

그래서 `Provider`는 이 온톨로지에서 **가장 많이 연결된 엔티티**다. 이는 "의료진이 진료 전달의 모든 단계에 관여한다"는 현실을 그대로 반영한다.

---

## care chain이 왜 유용한가 (질의 관점)

care chain을 모델링해 두면, 여러 시스템(EHR / 스케줄링 / 약국 DB / 청구)에 흩어진 데이터를 **하나의 그래프 경로 순회**로 답할 수 있다.

| 임상 질문 | 그래프 경로 |
|---|---|
| 리필이 필요한 환자는? | `Patient → Diagnosis → Prescription (refillsRemaining=0)` |
| 약을 가장 많이 처방하는 의료진은? | `Provider → Prescription` (count) |
| 아직 치료가 없는 중증 진단은? | `Diagnosis (severity=severe)` 중 `→ Prescription`이 없는 것 |
| 자신이 진단한 병을 직접 처방까지 하는 전문의는? | `Provider → Diagnosis` AND `Provider → Prescription` |

세 번째 행이 특히 중요하다. **care chain이 끊긴 지점(진단은 있는데 처방이 없음)을 찾는 것**은 미치료 환자 발견이라는 실무적 가치를 갖는다. 경로를 모델링해 두면 "경로의 부재"도 질의할 수 있게 된다.

### GQL 예시

중증 진단을 받았고 처방 리필이 소진되어 가는 환자 찾기 — care chain을 그대로 따라간다.

```gql
MATCH (p:Patient)-[:diagnosed_with]->(d:Diagnosis)-[:treated_by]->(rx:Prescription)
WHERE d.severity = 'severe' AND rx.refillsRemaining <= 1
RETURN p.patientId, d.description, rx.medication, rx.refillsRemaining
```

`MATCH` 절의 패턴 `(p)-[:diagnosed_with]->(d)-[:treated_by]->(rx)`가 바로 care chain의 문법적 표현이다.

---

## 헷갈리기 쉬운 포인트

- **`Patient → Prescription` 직접 관계는 없다.** 처방은 반드시 진단을 경유한다. 이는 "근거 없는 처방은 없다"는 임상 원칙을 스키마 수준에서 강제하는 효과가 있다.
- **`Appointment`는 care chain 경로에 들어가지 않는다.** 원문은 서술적으로 `appointment → diagnosis → treatment`라는 care cycle을 언급하지만, care chain으로 명시된 **경로 정의는 `Patient → Diagnosis → Prescription`** 이다. `Appointment`는 Patient와 Provider가 만나는 공유 엔티티(shared entity)로서 별도 축을 이룬다.
- **1:N이 연쇄된다.** 환자 1명 → 진단 N개 → 각 진단당 처방 M개. 따라서 체인을 끝까지 순회하면 결과가 곱셈으로 늘어난다(한 조건에 여러 약을 처방하는 경우 등).

---

## 핵심 정리

1. care chain = **`Patient → Diagnosis → Prescription`** 경로 (관계: `diagnosed_with` + `treated_by`)
2. 실제 임상 흐름(진단 → 치료)을 그래프 경로로 옮긴 것
3. `Prescription` 추가로 care cycle이 닫히며 5 엔티티 / 6 관계 온톨로지가 완성된다
4. `Provider`는 체인 경로 밖에서 **모든 단계에 연결**된다
5. 체인이 있으면 다중 홉 임상 질의와 **"체인이 끊긴 지점" 탐색**이 모두 가능해진다
