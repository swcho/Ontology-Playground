# "리필이 필요한 환자는 누구인가?" — 2-hop 그래프 경로

## 정답 요약

```
Patient --diagnosed_with--> Diagnosis --treated_by--> Prescription (refillsRemaining = 0)
```

Patient에서 출발해 **Diagnosis를 경유**하여 Prescription까지 내려간 뒤, `refillsRemaining`이 0인 처방만 남긴다. 관계를 두 번 타므로 **2-hop 경로**다.

원문 Complete Care Model의 "What the complete model enables" 표에 그대로 적혀 있다.

| Question | Graph path |
|---|---|
| Which patients need prescription refills? | `Patient → Diagnosis → Prescription (refillsRemaining=0)` |

---

## 왜 직결 경로가 없는가

Healthcare 온톨로지는 5 엔티티 / 6 관계로 구성되는데, 그 중 `Patient`와 `Prescription`을 직접 잇는 관계는 **존재하지 않는다**.

| 관계 이름 | 방향 | 카디널리티 |
|---|---|---|
| `has_appointment` | Patient → Appointment | one-to-many |
| `sees` | Provider → Appointment | one-to-many |
| `diagnosed_with` | Patient → Diagnosis | one-to-many |
| `diagnoses` | Provider → Diagnosis | one-to-many |
| `treated_by` | Diagnosis → Prescription | one-to-many |
| `prescribes` | Provider → Prescription | one-to-many |

`Patient → Prescription`이라는 엣지가 없으므로, 환자와 처방을 연결하려면 **반드시 Diagnosis를 중간 노드로 거쳐야** 한다. 이것이 원문에서 말하는 **care chain**(진료 사슬)이다: `appointment → diagnosis → treatment`. 처방은 "환자에게 그냥 붙는 것"이 아니라 **진단에 대한 치료 반응**이므로, 모델링 상으로도 Diagnosis를 경유하는 것이 임상 현실과 일치한다.

---

## 단계별 분해 (hop by hop)

### Hop 0 — 시작 노드: `Patient`

질문이 "누구인가?"이므로 **최종 반환 대상이 Patient**다. 즉 앵커(anchor)는 Patient이고, 조건은 경로 끝단(Prescription)에 걸린다. 이 비대칭(반환은 앞, 필터는 뒤)이 그래프 질의의 핵심 감각이다.

- 식별자: `patientId` (온톨로지 식별자)
- `mrn`은 병원 내부 식별자로 EHR 시스템에 매핑되는 도메인 속성

### Hop 1 — `diagnosed_with`: Patient → Diagnosis

- one-to-many: 한 환자는 병력에 걸쳐 여러 진단을 가질 수 있다.
- 따라서 이 hop을 지나면 행(row) 수가 **환자 수 → 진단 수**로 늘어난다.
- Diagnosis는 `diagnosisId`(식별자), `icdCode`, `description`, `severity`, `diagnosedDate`를 갖는다.
- Diagnosis는 Patient(질환을 가진 사람)와 Provider(그것을 식별한 사람) 양쪽에 연결된 **dual-connected 엔티티**다. 이 카드의 질문은 그 중 **환자 쪽 진입점**만 사용한다.

### Hop 2 — `treated_by`: Diagnosis → Prescription

- one-to-many: 한 진단이 여러 처방으로 이어질 수 있다(같은 질환에 복수 약제).
- 행 수가 다시 **진단 수 → 처방 수**로 늘어난다.
- Prescription은 `rxNumber`(약국 표준 식별자), `medication`, `dosage`, `frequency`, `refillsRemaining`을 갖는다.

### Hop 2의 필터 — `refillsRemaining = 0`

- `refillsRemaining`은 **integer** 속성이다. 정수형이기 때문에 `= 0`, `<= 1`, `> 3` 같은 **비교 연산 기반 운영 질의(operational query)** 가 가능해진다. 원문 key takeaway의 "Integer properties (refillsRemaining, duration) enable operational queries"가 바로 이 지점이다.
- 만약 리필 여부를 `"없음"` 같은 문자열로 저장했다면 이런 임계값 질의가 불가능하다.

### 마지막 단계 — Patient로 되돌아와 집계

경로를 끝까지 탄 뒤 다시 앞쪽 변수(`p`)를 반환해야 "환자 목록"이 된다. 한 환자가 여러 진단·여러 처방을 가질 수 있으므로 결과에 **환자 중복이 발생**한다. 실무에서는 `DISTINCT` 또는 환자 단위 집계가 필요하다.

---

## 원문 GQL 예시와 이 카드 조건의 차이

원문 Complete Care Model에 실린 GQL은 다음과 같다.

```gql
MATCH (p:Patient)-[:diagnosed_with]->(d:Diagnosis)-[:treated_by]->(rx:Prescription)
WHERE d.severity = 'severe' AND rx.refillsRemaining <= 1
RETURN p.patientId, d.description, rx.medication, rx.refillsRemaining
```

**경로(MATCH 절)는 이 카드의 답과 완전히 동일하다.** 차이는 `WHERE` 절, 즉 필터 조건뿐이다.

| 구분 | 원문 GQL | 이 카드 |
|---|---|---|
| 경로 | `Patient -diagnosed_with-> Diagnosis -treated_by-> Prescription` | 동일 |
| 리필 조건 | `refillsRemaining <= 1` | `refillsRemaining = 0` |
| 의미 | 리필 **임박** (곧 소진, 1회 남음 포함) | 리필 **소진** (이미 0) |
| 추가 조건 | `d.severity = 'severe'` (중증만) | 없음 (전체 진단) |
| 운영 성격 | 사전 예방적(proactive) — 끊기기 전에 개입 | 사후 대응적(reactive) — 이미 끊긴 환자 처리 |
| 결과 집합 | 더 넓음 (`0`과 `1` 모두 포함) | 더 좁음 (`= 0`은 `<= 1`의 부분집합) |

### 임박(`<= 1`) vs 소진(`= 0`)을 구분하는 이유

- **`= 0` (소진)**: 지금 당장 약이 없다. 복약 중단(medication non-adherence)이 **이미 발생 중일 수 있는** 상태. 즉시 처방 갱신 콜이 필요한 긴급 워크리스트.
- **`<= 1` (임박)**: 아직 1회분 리필 여유가 있다. 다음 방문 예약이나 갱신 안내를 **미리** 걸어둘 수 있는 예방 워크리스트. 약국 재고·진료 예약 리드타임을 흡수할 버퍼가 있다.

같은 그래프 경로에 임계값만 바꿔 끼워 서로 다른 운영 프로세스를 뽑아내는 것이 포인트다. 카드가 묻는 "리필이 **필요한** 환자"는 원문 표 그대로 `= 0`으로 정의되어 있고, 원문 GQL 예시는 "running out"(소진 임박)이라는 더 느슨한 정의를 쓴 것이다. **경로는 재사용, 임계값은 목적에 맞춰 조정**.

> 참고로 시나리오 개요의 대표 질문 — "Which patients diagnosed with severe conditions by cardiology providers still have prescriptions with zero refills remaining?" — 은 여기에 `Provider (specialty=Cardiology)`까지 얹은 확장형이다. 원문은 이를 `Patient → Diagnosis (severity=severe) ← Provider (specialty=Cardiology)` + `Diagnosis → Prescription (refillsRemaining=0)`로 분해한다. Diagnosis가 두 경로의 **교차점(join point)** 역할을 한다는 점을 확인하라.

---

## Provider → Prescription 경로로는 같은 답을 얻을 수 없는 이유

`prescribes` 관계(`Provider → Prescription`)를 타면 다음이 된다.

```
Provider --prescribes--> Prescription (refillsRemaining = 0)
```

이 경로도 "리필 잔량 0인 처방"을 정확히 찾아낸다. 그런데 **답이 되지 못한다.** 이유는 반환할 수 있는 것이 잘못됐기 때문이다.

### 1. 환자 정보에 도달하지 못한다

Prescription 엔티티의 속성은 `rxNumber`, `medication`, `dosage`, `frequency`, `refillsRemaining`뿐이다. **환자를 가리키는 속성이 없다.** 그리고 `Prescription → Patient` 방향의 관계도 온톨로지에 정의되어 있지 않다. 즉 이 경로를 끝까지 타도 손에 남는 것은 "누가 처방했는가(Provider)"와 "어떤 약인가(Prescription)"이며, **"누가 그 약을 먹어야 하는가(Patient)"는 어디에도 없다.**

질문은 "환자는 **누구인가**"다. 반환 대상이 Patient여야 하는데, 이 경로에는 Patient 노드가 아예 등장하지 않는다. → 질문에 답할 수 없다.

### 2. 답하는 질문이 다르다

`Provider → Prescription`이 답하는 질문은 원문 표에 따로 실려 있다.

| Question | Graph path |
|---|---|
| Which providers prescribe the most medications? | `Provider → Prescription (count)` |

즉 이 경로는 **처방자(provider) 관점**의 질의다. "어느 의사가 약을 많이 쓰는가", "어느 의사의 처방에 리필 소진이 많은가" 같은 질문에 맞다. 환자 관점의 질문과는 앵커가 다르다.

### 3. 우회 연결도 성립하지 않는다

"Provider에서 Patient로 갈 수는 없나?"를 따져봐도 막힌다.

- `Provider → Appointment (sees)` ← `Patient → Appointment (has_appointment)`: Appointment를 공유 엔티티로 삼아 Provider와 Patient를 이을 수는 있다. 하지만 이렇게 얻는 것은 "그 의사를 만난 적 있는 모든 환자"이며, **리필 0인 그 처방을 실제로 받은 환자**와는 무관하다. 예약을 잡았을 뿐 해당 처방의 대상이 아닌 환자가 대량으로 섞인다(false positive).
- `Provider → Diagnosis (diagnoses)` ← `Patient → Diagnosis (diagnosed_with)`: 마찬가지로 Diagnosis를 공유해 Patient에 도달할 수 있다. 하지만 이때도 그 Diagnosis가 리필 0인 처방과 실제로 `treated_by`로 이어져 있는지는 별도로 확인해야 한다. 결국 **`Diagnosis → Prescription` 엣지를 다시 타야** 하므로, 정답 경로를 우회해서 재발명하는 셈이 된다.

핵심: 처방을 환자에게 귀속시키는 **유일한 정합 경로는 Diagnosis를 통과하는 것**이다. Provider는 진료 사슬의 모든 단계에 연결된 가장 연결도 높은 엔티티(appointment를 보고, diagnosis를 내리고, prescription을 쓴다)이지만, **"환자 소유권(patient attribution)"의 축은 아니다.**

---

## 흔한 오답 패턴

| 오답 | 무엇이 틀렸나 |
|---|---|
| `Patient → Prescription (refillsRemaining=0)` | 그런 직접 관계가 온톨로지에 없다. Diagnosis 경유가 누락됐다. |
| `Provider → Prescription (refillsRemaining=0)` | 리필 0 처방은 찾지만 환자에 도달하지 못한다. 이건 처방자 랭킹 질의다. |
| `Patient → Appointment → Prescription` | `Appointment → Prescription` 관계가 존재하지 않는다. 처방은 Appointment가 아니라 Diagnosis에 매달린다. |
| `Patient → Diagnosis → Prescription (severity='severe')` | 필터를 잘못된 노드에 걸었다. 리필 조건은 Prescription의 `refillsRemaining`이다. |
| 방향을 뒤집어 `Prescription → Diagnosis → Patient` | 관계 방향은 `diagnosed_with`, `treated_by` 모두 아래로 향한다. 질의 엔진 구현에 따라 역방향 순회가 가능하더라도, 온톨로지 정의상 방향은 Patient에서 시작한다. |

---

## 기억할 한 문장

**"환자에게서 처방까지 가려면 항상 진단을 거친다 — Diagnosis가 care chain의 허리이고, `refillsRemaining`은 그 끝에 걸리는 정수 필터다."**
