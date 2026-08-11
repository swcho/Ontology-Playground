# Prescription — 진단에 대한 "치료 반응"

## 한 줄 정리

Healthcare 온톨로지의 마지막 조각인 **Prescription(처방)** 은 **진단에 대한 치료 반응(treatment response to a diagnosis)** 을 표현한다.
Prescription이 추가되면서 **예약(appointment) → 진단(diagnosis) → 치료(treatment)** 로 이어지는 **진료 사이클이 닫힌다**.

원문 표현 그대로:

> The final piece of the healthcare puzzle is **Prescription** — the treatment response to a diagnosis. This closes the care cycle: appointment → diagnosis → treatment.

---

## 1. Prescription 엔티티 속성

| Property | Type | Identifier? | 의미 |
|---|---|---|---|
| `rxNumber` | string | ✓ | 처방 번호. 약국 표준(pharmacy-standard) 식별자 |
| `medication` | string | | 약품명 |
| `dosage` | string | | 1회 투여량 (예: 500mg) |
| `frequency` | string | | 투여 빈도 (예: 1일 2회) |
| `refillsRemaining` | integer | | 남은 재처방(리필) 횟수 |

### 속성 설계에서 짚어둘 점

- **`rxNumber`를 식별자로 쓴다** — Patient의 `mrn`(Medical Record Number), Diagnosis의 `icdCode`와 같은 결. 이 온톨로지는 도메인에서 이미 통용되는 **표준 식별자/코드**를 그대로 속성으로 끌어와서 EHR·보험·청구·약국 시스템과의 **상호운용성(interoperability)** 을 확보한다. 학습 경로의 핵심 takeaway 중 하나가 "Standardized codes (ICD, Rx) enable cross-system interoperability"다.
- **`refillsRemaining`이 integer인 이유** — 문자열이 아니라 정수여야 `<= 1`, `= 0` 같은 **비교 연산이 가능한 운영 질의**를 할 수 있다. 이 하나의 정수 속성이 "리필 추적(refill tracking)"과 "복약 순응도 모니터링(medication adherence monitoring)"을 가능하게 한다. Appointment의 `duration`(분 단위 integer)과 같은 패턴이다.
- `dosage`/`frequency`는 문자열로 둔다 — 임상 표기가 자유 형식("500mg, twice daily")에 가깝기 때문. 이 둘은 필터링보다 **표시/전달용 속성**에 가깝다.

---

## 2. 새로 추가되는 두 관계

### treated_by — `Diagnosis` → `Prescription` (one-to-many)

하나의 진단이 **여러 처방**으로 이어질 수 있다. 예: 같은 고혈압 진단에 대해 복합 약제 2~3종을 동시에 처방.
이름이 `treated_by`인 것에 주목 — 주체가 Diagnosis이고, "이 진단은 (이 처방으로) 치료된다"라는 방향이다. 즉 **처방의 존재 이유를 진단에 묶어둔** 관계다.

### prescribes — `Provider` → `Prescription` (one-to-many)

한 의료진이 여러 처방을 발행한다. Provider는 이제 **세 지점 모두**에 연결된다.

| Provider의 관계 | 대상 | 역할 |
|---|---|---|
| `sees` | Appointment | 진료를 본다 |
| `diagnoses` | Diagnosis | 진단을 내린다 |
| `prescribes` | Prescription | 처방을 쓴다 |

이 온톨로지에서 **Provider가 가장 많이 연결된 엔티티**가 되는데, 이는 실제 임상 워크플로에서 의료진이 진료 전달 체인의 **모든 단계에 관여**한다는 사실을 그대로 반영한 것이다. (이 경로의 마지막 퀴즈 정답이 바로 이 항목이다.)

---

## 3. 완성된 그래프: 5 엔티티 / 6 관계

```
                  has_appointment            diagnosed_with
        Patient ───────────────► Appointment       │
           │                          ▲            │
           └──────────────────────────┼────────────┘
                                      │            ▼
                             sees     │        Diagnosis ──treated_by──► Prescription
        Provider ─────────────────────┘            ▲                          ▲
           ├──────────── diagnoses ────────────────┘                          │
           └──────────── prescribes ──────────────────────────────────────────┘
```

| # | 관계 | From → To |
|---|---|---|
| 1 | `has_appointment` | Patient → Appointment |
| 2 | `sees` | Provider → Appointment |
| 3 | `diagnosed_with` | Patient → Diagnosis |
| 4 | `diagnoses` | Provider → Diagnosis |
| 5 | `treated_by` | Diagnosis → Prescription |
| 6 | `prescribes` | Provider → Prescription |

빌드 순서 요약:

| Step | 추가 엔티티 | 누적 | 핵심 개념 |
|---|---|---|---|
| 1 | Patient, Provider, Appointment | 3 | 공유 엔티티, 스케줄링 |
| 2 | + Diagnosis | 4 | 표준 코드, 이중 연결 |
| 3 | **+ Prescription** | **5** | **케어 체인, 치료 추적** |

---

## 4. "진료 사이클이 닫힌다"는 말의 의미

핵심은 **그래프상에 진료의 모든 단계가 노드로 존재하고, 그 사이가 관계로 이어져 있어서 한 번의 탐색(single traversal)으로 질의할 수 있게 된다**는 것이다.

- **예약 단계** → `Appointment` 노드 (언제/어디서 진료가 일어났나)
- **진단 단계** → `Diagnosis` 노드 (무슨 상태인가, ICD 코드·severity)
- **치료 단계** → `Prescription` 노드 (무엇으로 대응했나, 약·용량·리필)

Prescription이 없던 Step 2까지의 그래프는 "무슨 병인지"까지만 알 수 있고 **"그래서 어떻게 조치했는지"에 답할 수 없는 열린 사이클**이었다. Prescription을 붙이면 `Patient → Diagnosis → Prescription`이라는 **케어 체인(care chain)** 이 완성되어, 원래는 EHR·스케줄링·약국·청구 시스템에 흩어져 있던 정보를 **하나의 경로 패턴 질의**로 답할 수 있다.

### 완성 모델이 답할 수 있게 되는 질문들

| 질문 | 그래프 경로 |
|---|---|
| 처방 리필이 필요한 환자는? | Patient → Diagnosis → Prescription (refillsRemaining = 0) |
| 약을 가장 많이 처방하는 의료진은? | Provider → Prescription (count) |
| 아직 치료가 시작되지 않은 중증 진단은? | Diagnosis (severity = severe) 중 → Prescription 이 **없는** 것 |
| 자기가 진단한 질환을 직접 처방까지 하는 전문의는? | Provider → Diagnosis AND Provider → Prescription |

세 번째 항목이 특히 중요하다. **관계의 부재(absence)** 자체가 의미 있는 신호가 된다 — "중증인데 처방이 없다"는 임상적 누락 탐지가 되고, 이는 Prescription 노드가 그래프에 들어와 있을 때만 표현 가능한 질의다.

### GQL 예시

시나리오 도입부의 질문 — "심장내과 의료진에게 중증으로 진단받았고, 처방 리필이 0인 환자는?" — 이 그대로 한 패턴으로 떨어진다.

```gql
MATCH (p:Patient)-[:diagnosed_with]->(d:Diagnosis)-[:treated_by]->(rx:Prescription)
WHERE d.severity = 'severe' AND rx.refillsRemaining <= 1
RETURN p.patientId, d.description, rx.medication, rx.refillsRemaining
```

`MATCH` 절 한 줄이 곧 "환자 → 진단 → 처방"이라는 임상 워크플로 그 자체다. 온톨로지가 없으면 이 질문은 여러 시스템에 걸친 조인/ETL 작업이 된다.

---

## 5. 왜 Prescription은 Patient에 직접 연결되지 않고 Diagnosis를 경유하는가

이 카드에서 가장 헷갈리기 쉬운 지점이다. 직관적으로는 "처방은 환자가 받는 것"이니 `Patient → Prescription`을 만들고 싶어진다. 그런데 이 온톨로지는 의도적으로 **Diagnosis를 경유**하게 설계했다.

**1) 처방은 "임상적 근거(clinical indication)"를 가져야 한다.**
`Prescription`은 정의상 **"진단에 대한 치료 반응"** 이다. 어떤 진단 때문에 이 약을 쓰는지가 처방의 존재 이유(적응증)다. `Diagnosis`를 경유시키면 **모든 처방이 근거가 되는 진단을 반드시 갖게 되는 구조**가 된다. Patient에 직접 붙이면 "환자가 이 약을 먹는다"는 사실만 남고 **왜 먹는지가 그래프에서 사라진다.**

**2) 환자 정보는 여전히 도달 가능하다 — 중복 없이.**
`Patient -[:diagnosed_with]-> Diagnosis -[:treated_by]-> Prescription` 경로로 환자에서 처방까지 얼마든지 갈 수 있다. `Patient → Prescription` 간선을 추가하면 같은 사실을 두 경로로 표현하게 되어 **중복 표현(redundancy)** 이 생기고, 두 경로가 서로 어긋나는 **불일치 상태**(진단 없이 환자에게만 매달린 처방 등)가 가능해진다. 경로가 하나뿐이면 그런 모순이 원천적으로 발생하지 않는다.

**3) 임상 워크플로의 인과 순서를 보존한다.**
실제 진료는 예약 → 평가 → 진단 → 처방 순으로 흐른다. 그래프의 간선 방향이 이 인과 사슬을 그대로 담고 있어야 "진단 후 며칠 만에 처방이 나갔나", "이 진단 코드에는 어떤 약이 주로 쓰이나" 같은 **단계 간 분석**이 가능하다. 지름길 간선은 이 사슬의 중간 단계를 건너뛰게 만들어 단계 간 분석을 망가뜨린다.

**4) 대조: Provider는 왜 직접 연결되는가?**
`prescribes`(Provider → Prescription)는 경유 없이 직접 간선이다. 이유가 다르다 — Provider는 처방의 **임상적 근거**가 아니라 **발행 주체(authorship/책임)** 다. 누가 서명했는지는 진단과 독립적인 사실이고, 처방 권한·법적 책임·감사(audit) 관점에서 직접 확인해야 하는 정보다. 그래서 "왜(근거)"는 Diagnosis를 통해, "누가(책임)"는 Provider에서 직접 온다. 앞서 Diagnosis가 Patient(질환을 가진 사람)와 Provider(찾아낸 사람) 양쪽에 연결됐던 **이중 저작(dual authorship)** 패턴과 같은 사고방식이다.

---

## 6. 헷갈리기 쉬운 오답들

| 오답 | 왜 틀렸나 |
|---|---|
| "Prescription은 환자의 복약 목록이다" | 목록이 아니라 **진단에 대한 치료 반응**. 근거 진단과 짝을 이루는 개체다 |
| "Prescription은 Appointment에 연결된다" | 예약이 아니라 **Diagnosis**에 `treated_by`로 연결된다. 예약은 진단을 낳고, 진단이 처방을 낳는다 |
| "Prescription은 Patient → Prescription으로 직접 연결된다" | Diagnosis를 경유한다. 직접 간선을 두면 처방의 임상적 근거가 사라진다 |
| "진단 1건에는 처방 1건" | `treated_by`는 **one-to-many**. 한 진단에 복수 약제 처방이 가능하다 |
| "식별자는 medication" | 식별자는 **`rxNumber`** (약국 표준 처방 번호) |

---

## 7. 이 경로의 Key takeaways (원문)

1. **공유 엔티티**(Appointment, Diagnosis)는 여러 행위자를 연결한다
2. **표준 코드**(ICD, Rx)는 시스템 간 상호운용성을 가능하게 한다
3. **케어 체인**(Patient → Diagnosis → Prescription)은 임상 워크플로를 모델링한다
4. **Provider는 모든 단계에 연결된다** — 의료 전달 체계에서의 중심 역할을 반영
5. **정수 속성**(refillsRemaining, duration)은 운영 질의를 가능하게 한다

---

### 암기 포인트

> Prescription = **진단에 대한 치료 반응**.
> `rxNumber`(식별자) / medication / dosage / frequency / **refillsRemaining(integer)**.
> `Diagnosis --treated_by--> Prescription`, `Provider --prescribes--> Prescription`.
> 예약 → 진단 → **치료**가 모두 그래프에 있으니 **한 번의 탐색으로 진료 사이클 전체를 질의**할 수 있다 = 사이클이 닫혔다.
