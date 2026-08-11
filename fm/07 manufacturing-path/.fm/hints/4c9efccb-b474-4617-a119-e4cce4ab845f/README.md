# Machine.status — 네 가지 운영 상태

## 카드 요약

**Q.** Machine의 `status` 속성이 가질 수 있는 값과 그 용도는?

**A.** `running`, `idle`, `maintenance`, `offline` 네 가지 운영 상태를 추적한다. 실시간 대시보드와 유지보수 일정 수립을 가능하게 한다.

---

## 1. 원문 근거 — Machine 속성 표

Smart Manufacturing 경로의 "Factory Floor" 단계에서 Machine 엔티티는 다음과 같이 정의된다.

| Property | Type | Identifier? |
|---|---|---|
| `machineId` | string | ✓ |
| `name` | string | |
| `type` | string | |
| `status` | string | |
| `installDate` | date | |

원문 설명:

> The `status` property tracks operational state — `running`, `idle`, `maintenance`, or `offline`. This enables real-time dashboards and maintenance scheduling.

즉 `status`는 **장비(설비) 그 자체의 현재 운영 상태**를 나타내는 속성이며, 이 값이 실시간 모니터링 대시보드와 예방 정비 스케줄링의 입력이 된다. 같은 단계의 "What we learned"에서도 **"Status properties enable real-time operational tracking"** 을 핵심 학습 포인트로 못 박고 있다.

한편 시나리오 개요의 Key concepts에는 이렇게 적혀 있다.

> **Operational status** — real-time state tracking (running, idle, maintenance)

개요에서는 세 개만 예시로 들었지만, 실제 정의 문단에서는 `offline`을 포함한 **네 개**가 정식 값 집합이다. 카드 답안이 네 가지인 이유가 여기에 있다.

---

## 2. 왜 자유 텍스트가 아니라 통제된 열거값(controlled enum)인가

타입은 `string`이지만, 아무 문자열이나 들어가도 되는 필드가 아니다. 실질적으로는 **네 개의 값만 허용되는 열거형(enumeration)** 으로 취급해야 한다. 이유는 다음과 같다.

### 2.1 집계·필터링이 성립하려면 값이 유한해야 한다

"현재 가동 중인 설비 비율은?" 같은 질문은 `status = 'running'` 인 Machine을 세는 것으로 답한다. 만약 값이 자유 텍스트라면 소스마다 `Running`, `RUNNING`, `가동중`, `in operation`, `run` 처럼 제각각 들어와 같은 상태가 여러 버킷으로 쪼개진다. 그러면 카운트가 틀리고, 대시보드 숫자가 소스 시스템마다 달라진다.

### 2.2 온톨로지는 여러 소스를 통합하는 계층이다

시나리오 개요에 따르면 데이터는 **IoT 센서, MES(Manufacturing Execution System), ERP, 품질관리 DB** 등 서로 다른 시스템에서 흘러 들어온다. MES는 상태를 코드값(`ST01`)으로, PLC/SCADA는 비트 플래그로, ERP는 또 다른 라벨로 관리하는 것이 보통이다. 온톨로지의 `status`는 이 이질적인 표현들을 **하나의 공통 어휘로 정규화한 결과물**이다. 통제된 값 집합이 없으면 통합의 의미가 사라진다.

### 2.3 상태 전이 규칙과 알림 로직을 코드로 쓸 수 있다

값이 유한해야 "`running` → `maintenance` 로 바뀌면 생산계획 재배치", "`offline` 이 N분 이상 지속되면 알람" 같은 규칙을 안정적으로 작성할 수 있다. 자유 텍스트에는 이런 규칙을 걸 수 없다.

### 2.4 배타적이고 완결적(mutually exclusive & exhaustive)이다

네 값은 서로 겹치지 않으면서 설비가 취할 수 있는 상태를 모두 덮는다.

| 값 | 의미 | 생산 기여 | 계획된 상태인가 |
|---|---|---|---|
| `running` | 실제로 가동하며 생산 중 | 있음 | 정상 |
| `idle` | 전원은 살아 있으나 작업이 없어 대기 | 없음 | 대체로 계획됨(작업 대기, 셋업, 교대) |
| `maintenance` | 정비/점검 중이라 의도적으로 정지 | 없음 | 계획된 정지(또는 사후 정비) |
| `offline` | 전원 차단·통신 두절·고장으로 사용 불가 | 없음 | 대체로 비계획(이상 상황) |

특히 `idle`과 `offline`을 구분하는 것이 중요하다. 둘 다 "생산하지 않음"이지만, `idle`은 **일감이 없는 것**(스케줄링 문제)이고 `offline`은 **설비를 쓸 수 없는 것**(가용성 문제)이다. 원인이 다르므로 개선 액션도 다르다. `maintenance`를 `offline`과 합치지 않는 이유도 같다 — 계획 정비는 가용성 손실로 계산하되 고장과는 별도로 관리해야 한다.

---

## 3. 상태 전이(state transition)

네 값은 독립적인 라벨이 아니라 서로 오가는 **상태 기계(state machine)** 로 보는 것이 맞다.

```
                 작업 배정(Work-Order assigned_to Machine)
        ┌──────────────────────────────────────────┐
        │                                          ▼
   ┌─────────┐                                ┌─────────┐
   │  idle   │◀───────────────────────────────│ running │
   └─────────┘        작업 완료 / 작업 대기      └─────────┘
      │   ▲                                     │      │
      │   │ 정비 완료                    고장 정지 │      │ 예방 정비 시점 도래
      │   │                                     │      │  (센서 임계값 초과 등)
      ▼   │                                     ▼      ▼
 ┌──────────────┐    긴급 정비 필요        ┌─────────┐
 │ maintenance  │◀───────────────────────│ offline │
 └──────────────┘                        └─────────┘
        │              정비 후 복구 실패 / 전원 차단
        └────────────────────────────────────────▶
```

대표 전이 시나리오:

- **`idle` → `running`** : Work-Order가 해당 설비에 `assigned_to` 되어 실제 가공이 시작됨.
- **`running` → `idle`** : 작업이 끝났고 다음 Work-Order가 아직 배정되지 않음. 이 구간이 길면 스케줄링/부하 분배 문제.
- **`running` → `maintenance`** : 예방 정비 주기 도래, 또는 Sensor의 `lastReading`이 `threshold`를 넘어 예지 정비(predictive maintenance) 트리거 발생.
- **`running` → `offline`** : 예기치 못한 고장, 정전, 통신 두절. 계획되지 않은 다운타임.
- **`offline` → `maintenance`** : 고장 원인 파악 후 사후 정비(corrective maintenance)에 착수.
- **`maintenance` → `idle`** : 정비 완료 후 복구. 보통 곧바로 `running`이 아니라 대기 상태를 거친 뒤 작업이 배정된다.

전이가 언제 일어났는지를 남기려면 `status` 단일 필드만으로는 부족하다. 실무에서는 상태 변경 이력을 별도 이벤트(타임스탬프 + 이전 상태 + 새 상태 + 사유 코드)로 적재하고, Machine의 `status`는 **가장 최근 상태의 스냅샷** 역할을 한다. 이 학습 경로의 모델은 스냅샷만 담는 최소 형태다.

---

## 4. OEE / 가동률 대시보드와의 연결

`status`가 왜 "실시간 대시보드"를 가능하게 하는지는 제조 현장의 표준 지표인 **OEE(Overall Equipment Effectiveness, 종합설비효율)** 로 설명하면 명확해진다. OEE는 세 요소의 곱이다.

```
OEE = 가용성(Availability) × 성능(Performance) × 품질(Quality)
```

- **가용성(Availability)** — 계획된 생산 시간 중 실제로 돌 수 있었던 시간의 비율. 여기서 `status`가 직접 쓰인다.
  - `running` 시간 → 실가동 시간
  - `idle` 시간 → 대기 손실(작업 대기, 셋업, 교대)
  - `maintenance` 시간 → 계획 정지 손실
  - `offline` 시간 → 비계획 다운타임 손실
  - 대략 `Availability ≈ running / (running + idle + maintenance + offline)`. 어떤 상태를 분모의 "계획 생산 시간"에서 제외할지는 조직 정책에 따라 다르지만, **상태 값이 구분되어 있어야 그 정책을 적용할 수 있다**는 점이 핵심이다.
- **품질(Quality)** — 이 온톨로지에서는 Quality-Check의 `passed` 불리언에서 계산된다 (`Machine → Part ← Quality-Check`).
- **성능(Performance)** — Work-Order의 `startDate`/`dueDate`, 산출 Part 수량과 결합해 계산한다.

즉 `status`는 OEE 삼요소 중 **가용성 축을 담당하는 원천 데이터**다. 값이 통제되지 않으면 가용성 계산 자체가 무너진다.

대시보드에서 곧바로 나오는 질의 예:

| 질문 | `status` 활용 |
|---|---|
| 지금 가동 중인 설비는 몇 대인가 | `count(Machine where status='running')` |
| 라인별 가동률 | 라인별 `running` 비율 |
| 지금 멈춰 있는데 원인이 뭔가 | `idle`(일감 없음) / `maintenance`(정비) / `offline`(고장) 로 분해 |
| 비계획 다운타임이 늘고 있는가 | `offline` 누적 시간 추세 |

---

## 5. 유지보수 일정 수립과의 연결

`status`는 정비 계획에서 두 방향으로 쓰인다.

**(1) 정비 대상 선정 — 언제 `maintenance`로 보낼지**

Sensor 엔티티의 `threshold` 패턴이 여기에 물린다. 원문 설명:

> When `lastReading` exceeds `threshold`, the system triggers an alarm. This pattern is fundamental to predictive maintenance.

경로: `Sensor -[:monitors]-> Machine`. 어떤 설비의 진동 센서가 임계값을 계속 넘으면 → 예지 정비 후보 → 정비 창(maintenance window)을 잡아 `status`를 `maintenance`로 전이. Machine의 `installDate`와 결합하면 설비 노후도(경과 연수)까지 고려한 우선순위 산정이 가능하다.

**(2) 정비 창 배치 — 언제 세울지**

정비는 생산을 멈추므로 아무 때나 할 수 없다. `status`가 `idle`인 구간, 즉 배정된 Work-Order가 없는 시간대가 정비를 끼워 넣기 가장 좋은 창이다. 반대로 `dueDate`가 임박한 고우선순위 Work-Order가 붙어 있는 설비는 정비를 미루거나 다른 설비로 작업을 재배정해야 한다. 여기서 `Work-Order -[:assigned_to]-> Machine` 관계와 Work-Order의 `priority`, `dueDate`가 함께 쓰인다.

**(3) 사후 분석 — 상태와 품질의 상관**

완성 모델의 대표 질의는 센서 이상과 품질 불량의 상관을 본다.

```gql
MATCH (s:Sensor)-[:monitors]->(m:Machine)-[:has_part]->(p:Part)<-[:inspects]-(qc:QualityCheck)
WHERE s.lastReading > s.threshold AND qc.passed = false
RETURN m.name, s.type, s.lastReading, p.name, qc.defectCode
```

여기에 `m.status`를 조건이나 반환값으로 얹으면 "정비 직전 상태(`running`이지만 센서 이상)에서 만든 부품의 불량률"처럼, 정비 주기를 앞당길 근거를 뽑아낼 수 있다. 이것이 원문이 말하는 품질 피드백 루프(`Quality-Check → Part → Work-Order → Machine`)와 상태 추적이 만나는 지점이다.

---

## 6. Machine.status vs Work-Order.status — 헷갈리기 쉬운 지점

이 온톨로지에는 `status`라는 이름의 속성이 **두 개** 있다. 이름은 같지만 완전히 다른 것을 추적한다.

| | `Machine.status` | `Work-Order.status` |
|---|---|---|
| 대상 | **설비(자원, resource)** | **작업 지시(작업, job)** |
| 답하는 질문 | "이 기계는 지금 어떤 상태인가" | "이 생산 작업은 어디까지 진행됐나" |
| 값 성격 | `running`/`idle`/`maintenance`/`offline` — **순환하는 상태**. 설비는 계속 살아 있으면서 상태를 오간다 | `open`/`in_progress`/`completed`/`cancelled` 류 — **수명주기(lifecycle) 상태**. 완료되면 끝나고 되돌아가지 않는 것이 원칙 |
| 종료 개념 | 없음. 설비가 폐기될 때까지 계속 상태를 가짐 | 있음. 작업은 완료/취소로 종결됨 |
| 함께 쓰이는 속성 | `installDate`(노후도), Sensor의 `threshold` | `startDate`, `dueDate`, `priority` |
| 주 소비처 | 실시간 가동 대시보드, OEE 가용성, 정비 스케줄링 | 생산 계획, 납기 준수율(schedule adherence), 지연 작업 목록 |
| 카디널리티 관점 | 한 설비는 여러 Work-Order를 순차 처리 | 한 Work-Order는 한 설비에 배정 (`assigned_to`, many-to-one) |

**둘의 관계.** `Work-Order -[:assigned_to]-> Machine` 이므로 두 상태는 상관은 있지만 종속되지는 않는다.

- Work-Order가 `in_progress`인데 Machine이 `offline`이면 → **모순이 아니라 경보 신호**다. 작업 도중 설비가 고장 난 상태이며, 그 작업은 지연되거나 다른 설비로 재배정되어야 한다.
- Machine이 `idle`인데 배정된 미완료 Work-Order가 있으면 → 착수가 안 된 것. 스케줄링 병목.
- Work-Order가 모두 `completed`인데 Machine이 `running`이면 → 데이터 정합성 점검 대상.

이런 교차 점검이 가능하다는 것 자체가, 두 상태를 **각각 별도의 엔티티에 두는 설계가 옳다**는 근거다. 설비 상태를 작업에 우겨넣거나 그 반대로 하면 이 질문들을 던질 수 없다.

> 참고로 Quality-Check에는 `status`가 없고 `passed` 불리언이 있다. 검사 결과는 오가는 상태가 아니라 한 번 내려지는 판정이기 때문이다. 원문의 정리대로 **"Boolean properties (passed) create clear decision points in the workflow"**. 상태 값의 개수와 성격은 "그 대상이 실제로 어떻게 변하는가"를 따라간다는 점을 보여주는 대비 사례다.

---

## 7. 한 줄 정리

`Machine.status`는 `running` / `idle` / `maintenance` / `offline` 네 값으로 **설비 자체의 실시간 운영 상태**를 통제된 어휘로 정규화한 속성이며, 이 값이 있어야 OEE 가용성 계산과 실시간 대시보드가 성립하고, 센서 임계값 초과 및 Work-Order 배정 현황과 결합해 정비 창을 언제 잡을지 결정할 수 있다. 같은 이름의 `Work-Order.status`가 **작업의 수명주기**를 추적하는 것과 명확히 구분해야 한다.
