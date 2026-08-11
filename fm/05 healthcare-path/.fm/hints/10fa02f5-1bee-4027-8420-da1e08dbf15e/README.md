# Appointment은 왜 Patient와 Provider **둘 다**에 연결하는가

## 질문과 정답

**Q.** Appointment를 Patient와 Provider 중 한쪽만이 아니라 둘 다에 연결하는 이유는?

**A.** 예약은 본질적으로 환자와 provider가 함께 참여하는 **협업 이벤트(collaborative event)** 이기 때문이다. 두 관계를 모두 모델링하면 "환자의 다음 방문은 언제인가?"와 "이 provider는 하루에 몇 명을 보는가?" **양방향 쿼리**가 모두 가능해진다.

---

## 1. 원문에서의 위치 — 공유 엔티티(Shared Entity) 패턴

Healthcare System 온톨로지의 1단계(Care Delivery)는 세 개의 엔티티로 시작한다.

| 엔티티 | 대답하는 질문 | 주요 프로퍼티 |
|---|---|---|
| **Patient** | 누가 진료를 **받는가**? | `patientId`(식별자), `mrn`, `dateOfBirth`, `bloodType`, `allergies` |
| **Provider** | 누가 진료를 **제공하는가**? | `providerId`(식별자), `name`, `specialty`, `licenseNumber`, `department` |
| **Appointment** | 진료가 **언제·어떻게** 일어나는가? | `appointmentId`(식별자), `scheduledTime`, `duration`, `type`, `status` |

여기서 정의된 관계는 두 개다.

- **has_appointment** — `Patient` → `Appointment` (one-to-many)
  환자는 시간이 흐르며 여러 번의 예약을 갖는다.
- **sees** — `Provider` → `Appointment` (one-to-many)
  provider는 여러 예약을 처리한다.

> **Shared entity pattern:** Appointment connects to *both* Patient and Provider. It's the meeting point where two independent entities interact. This pattern is common whenever two actors participate in the same event.

즉 Appointment는 그 자체로 독립적인 주체가 아니라, **서로 독립적인 두 행위자(actor)가 만나는 접점(meeting point)** 을 실체화한 엔티티다. 원문이 이를 "**scheduling triangle** (Patient–Appointment–Provider)"이라 부르며 헬스케어 온톨로지의 토대로 규정한 이유가 여기에 있다.

```
        has_appointment              sees
Patient ────────────────► Appointment ◄──────────────── Provider
 (진료를 받는 쪽)          (만남의 접점)              (진료를 제공하는 쪽)
```

---

## 2. 원문 quiz 블록 — "왜 한쪽만이 아닌가"

원문의 퀴즈는 오답 보기를 통해 **틀린 이유들**을 명시적으로 배제한다. 이 오답들을 하나씩 짚는 것이 이 카드의 핵심이다.

| 보기 | 판정 | 왜 그런가 |
|---|---|---|
| 그래프를 더 완성돼 보이게 하려고 | ✗ | 관계는 장식이 아니다. 각 엣지는 **실제로 필요한 쿼리 경로**를 만들어야 존재 가치가 있다. |
| Appointment가 **shared entity** — 두 행위자 사이의 상호작용 지점을 표현하므로 | **✓ 정답** | 현실 세계의 예약이 두 주체의 공동 참여 이벤트라는 사실을 모델이 그대로 반영한 것이다. |
| 모든 엔티티는 최소 두 개의 관계를 가져야 하므로 | ✗ | 그런 규칙은 없다. 관계 개수는 규칙이 아니라 **도메인의 실제 구조**가 결정한다. |
| Patient와 Provider가 같은 프로퍼티를 갖기 때문에 | ✗ | 둘의 프로퍼티는 전혀 다르다(`mrn`/`bloodType` vs `specialty`/`licenseNumber`). 프로퍼티 유사성은 관계 설계의 근거가 아니다. |

원문 해설:

> An appointment is inherently a collaborative event involving both a patient and a provider. Modelling both relationships captures the full scheduling picture and enables queries from either perspective: "When is the patient's next visit?" or "How many patients does this provider see per day?"

여기서 놓치기 쉬운 포인트: 정답의 근거는 **"두 개가 더 많아서"가 아니라 "현실이 그렇게 생겼기 때문"** 이다. 온톨로지 설계에서 관계의 정당성은 언제나 (1) 도메인 현실의 반영과 (2) 그 관계가 열어 주는 쿼리, 이 두 가지에서 나온다.

---

## 3. 한쪽만 모델링하면 무엇이 불가능해지는가 (핵심 대비)

가장 설득력 있는 근거는 **잃어버리는 쿼리를 직접 대조**해 보는 것이다.

### 시나리오 A — `Patient → Appointment` 만 모델링한 경우

그래프: `Patient ──has_appointment──► Appointment` (Provider 연결 없음)

| 쿼리 | 가능? | 이유 |
|---|---|---|
| 이 환자의 다음 방문은 언제인가? | ✅ 가능 | `Patient → Appointment`에서 `scheduledTime` 정렬 |
| 이 환자의 예약 이력 전체 | ✅ 가능 | 같은 경로 |
| **이 provider는 하루에 몇 명을 보는가?** | ❌ 불가능 | 예약에서 provider로 되짚을 엣지가 없다 |
| **Cardiology 부서의 오늘 스케줄** | ❌ 불가능 | `Provider.department` → Appointment 경로 부재 |
| **provider별 진료 시간 활용률(utilization)** | ❌ 불가능 | `duration` 값을 provider 단위로 집계할 방법이 없다 |
| **환자 A를 특정 전문의에게 배정/리퍼럴** | ❌ 불가능 | "누가 본다"라는 정보 자체가 그래프에 없다 |
| **이중 예약(double-booking) 탐지** | ❌ 불가능 | 같은 provider의 동시간대 예약을 찾을 수 없다 |
| **provider 부재 시 예약 재배정 영향 범위** | ❌ 불가능 | 해당 provider의 예약 집합을 특정할 수 없다 |

즉 **환자 중심(patient-centric) 뷰만 남고, 운영·스케줄링 뷰 전체가 사라진다.** 병원 입장에서 가장 돈이 되는 질문들(부서별 캐파, 활용률, 대기 시간)이 통째로 답 불가가 된다.

### 시나리오 B — `Provider → Appointment` 만 모델링한 경우

그래프: `Provider ──sees──► Appointment` (Patient 연결 없음)

| 쿼리 | 가능? | 이유 |
|---|---|---|
| 이 provider의 오늘 스케줄 | ✅ 가능 | `Provider → Appointment` |
| provider별 일일 진료 건수 | ✅ 가능 | 같은 경로에 count |
| **이 환자의 다음 방문은 언제인가?** | ❌ 불가능 | 예약에 환자 연결이 없다 |
| **환자의 방문 이력 / 재방문(follow-up) 추적** | ❌ 불가능 | 환자 단위로 예약을 묶을 수 없다 |
| **노쇼(no-show)가 잦은 환자 식별** | ❌ 불가능 | `status='no-show'`를 환자에 귀속시킬 수 없다 |
| **환자에게 예약 리마인더 발송** | ❌ 불가능 | 예약 → 환자 방향을 찾을 수 없다 |
| **예약 → 진단 → 처방 케어 체인 연결** | ❌ 사실상 불가능 | 케어 체인의 주체가 환자인데 시작점이 끊긴다 |

즉 **provider 중심(provider-centric) 운영 뷰만 남고, 환자 여정(patient journey) 전체가 사라진다.**

### 시나리오 C — 둘 다 모델링 (원문의 선택)

```gql
-- 양방향 쿼리 1: 환자 관점 — "이 환자의 다음 방문은?"
MATCH (p:Patient)-[:has_appointment]->(a:Appointment)
WHERE p.patientId = 'P-001' AND a.scheduledTime > CURRENT_TIMESTAMP
     AND a.status = 'scheduled'
RETURN a.appointmentId, a.scheduledTime, a.type
ORDER BY a.scheduledTime
LIMIT 1
```

```gql
-- 양방향 쿼리 2: provider 관점 — "이 provider는 하루에 몇 명을 보는가?"
MATCH (pr:Provider)-[:sees]->(a:Appointment)
WHERE pr.providerId = 'PR-100' AND a.scheduledTime >= DATE '2026-08-11'
     AND a.scheduledTime < DATE '2026-08-12'
RETURN COUNT(a) AS dailyLoad, SUM(a.duration) AS bookedMinutes
```

```gql
-- 그리고 오직 "둘 다" 있을 때만 가능한 것: 삼각형을 관통하는 조인
-- "Cardiology provider와 예약된 환자 목록"
MATCH (p:Patient)-[:has_appointment]->(a:Appointment)<-[:sees]-(pr:Provider)
WHERE pr.specialty = 'Cardiology' AND a.status = 'scheduled'
RETURN pr.name, p.patientId, a.scheduledTime
```

세 번째 쿼리가 결정적이다. Appointment를 **중간 허브**로 삼아 Patient와 Provider를 **간접적으로 연결**할 수 있게 되는데, 이것은 두 엣지가 모두 있을 때만 성립한다. 한쪽 엣지가 없으면 이 조인은 아예 표현 자체가 불가능하다.

---

## 4. 왜 Patient → Provider 직접 관계로 대체할 수 없는가

"그러면 Appointment를 빼고 `Patient → Provider` 직접 관계만 두면 안 되나?"라는 반문이 자연스럽게 나온다. 안 되는 이유:

1. **이벤트의 속성을 담을 곳이 없다.** `scheduledTime`, `duration`, `type`, `status`는 환자의 속성도 provider의 속성도 아니다. **만남 그 자체의 속성**이다. 관계를 실체화한 엔티티(Appointment)만이 이를 보관할 수 있다.
2. **같은 쌍의 반복을 구별할 수 없다.** 환자 A가 같은 provider를 12번 만났다면, 직접 관계로는 12번을 하나로 뭉개 버린다. Appointment 엔티티가 있으면 각 방문이 별도의 노드로 식별된다(`appointmentId`).
3. **후속 임상 데이터의 앵커가 사라진다.** 원문이 명시하듯 "Every diagnosis and treatment flows from an appointment." 진단·처방은 특정 방문 사건에 걸려야 의미가 있다.
4. **취소/노쇼 같은 상태 전이를 표현할 수 없다.** `status`는 시간에 따라 변하는 이벤트의 라이프사이클인데, 직접 관계에는 라이프사이클이 없다.

관계형 DB에 익숙하다면 Appointment는 **속성을 가진 조인 테이블(associative entity)** 에 해당한다고 보면 정확하다. 다대다 관계를 그냥 잇는 대신, 관계를 1급 엔티티로 승격시켜 프로퍼티와 식별자를 부여한 것이다.

---

## 5. 같은 패턴의 반복 — 이 카드가 일반화되는 지점

이 패턴은 Appointment 하나에 국한되지 않는다. 원문 2단계에서 Diagnosis가 정확히 같은 구조를 반복한다.

> **Dual authorship:** Diagnosis connects to both Patient (who has the condition) and Provider (who identified it). This dual connection enables both patient-centric views ("all of my conditions") and provider-centric views ("all conditions I've identified").

| 공유 엔티티 | Patient 쪽 관계 | Provider 쪽 관계 | 열리는 양방향 뷰 |
|---|---|---|---|
| **Appointment** | `has_appointment` | `sees` | "내 다음 방문" ↔ "내 일일 진료 건수" |
| **Diagnosis** | `diagnosed_with` | `diagnoses` | "내 모든 질환" ↔ "내가 식별한 모든 질환" |
| **Prescription** | (Diagnosis 경유 `treated_by`) | `prescribes` | "내가 받은 처방" ↔ "내가 쓴 처방" |

그래서 원문의 최종 정리에서 Provider가 **가장 많이 연결된 엔티티**가 된다 — "Provider connects to Appointment, Diagnosis, and Prescription — reflecting their role at every stage of care." 현실의 임상 워크플로에서 provider가 모든 단계에 개입하기 때문이며, 만약 각 단계에서 Provider 연결을 하나씩 생략했다면 "이 의사의 진료 성과/부하/처방 패턴"에 관한 질문 전부가 답 불가가 된다.

---

## 6. 암기 포인트 정리

- **정답의 근거는 두 겹이다**: (1) 현실 반영 — 예약은 협업 이벤트다, (2) 쿼리 역량 — 양방향 조회가 열린다. 둘 중 하나만 말하면 절반만 답한 것이다.
- **핵심 용어**: shared entity(공유 엔티티), meeting point(접점), scheduling triangle(Patient–Appointment–Provider), 양방향(bidirectional) 쿼리.
- **판별 기준**: 관계를 추가할 근거는 "그래프가 예뻐진다"나 "관계 개수 규칙"이 아니라 **그 엣지가 없으면 못 하게 되는 쿼리가 있는가** 이다.
- **한 문장 요약**: 두 행위자가 함께 참여하는 이벤트는 공유 엔티티로 실체화하고 **양쪽 모두 연결**해야, 이벤트 고유 속성을 보관하면서 두 관점의 쿼리와 둘을 관통하는 조인이 모두 가능해진다.
