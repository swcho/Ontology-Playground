# 품질 피드백 루프와 지속적 개선

## 핵심 답

실패한 검사(`Quality-Check.passed = false`)를 `Quality-Check → Part → Work-Order → Machine` 경로로 되짚으면, 그 불량이 **어느 기계·어느 작업 지시·어떤 조건에서** 나왔는지가 특정된다. 개별 불량 하나를 추적하는 데서 끝나지 않고, 이렇게 얻은 발생원 정보를 **집계**해 패턴을 찾고, 그 패턴에 대응하는 조치를 취한 뒤, 다시 측정해 효과를 확인한다. 이 순환이 스마트 팩토리의 지속적 개선(continuous improvement)이다.

> 이 카드는 "경로를 어떻게 거슬러 올라가는가"(추적 메커니즘)가 아니라, **그 추적 결과로 무엇을 하는가**(개선 실무)에 관한 것이다.

---

## 1. 개별 불량 → 집계된 신호

한 건의 불합격은 "그 부품은 폐기하거나 재작업한다"는 정보밖에 주지 못한다. 개선은 **여러 건을 묶었을 때** 시작된다. 완성된 온톨로지는 묶는 축(axis)을 세 개 제공한다.

| 집계 축 | 사용 속성 | 드러나는 것 |
|---|---|---|
| **defectCode별** | `Quality-Check.defectCode` | 불량의 **유형**. 치수 초과인가, 표면 결함인가, 재료 문제인가 |
| **Machine별** | `Machine.machineId` / `name` | 불량의 **발생원**. 특정 장비가 유독 불량을 많이 내는가 |
| **Work-Order 속성별** | `Work-Order.priority`, `startDate`/`dueDate` | 불량의 **조건**. 급하게 밀어 넣은 작업일수록 불량이 나는가 |

`defectCode`가 존재하는 이유가 바로 이것이다. 원문은 이 속성을 "실패를 유형화해 근본 원인 분석(root cause analysis)을 가능하게 한다"고 설명한다. 자유 텍스트 메모가 아니라 **코드화된 범주**여야 `GROUP BY`가 성립하고, `GROUP BY`가 성립해야 파레토 분석(상위 몇 개 불량 코드가 전체의 대부분을 차지하는지)이 가능하다.

세 축을 교차하면 진단이 구체화된다.

- `defectCode = DIM-OVER`가 **CNC-03에만** 몰려 있다 → 장비 정밀도/마모 문제
- 같은 코드가 **모든 기계에 고르게** 퍼져 있다 → 장비가 아니라 재료 로트나 도면 사양 문제
- `priority = urgent`인 작업 지시에서만 튄다 → 장비가 아니라 **일정 압박**이 원인

마지막 경우가 중요하다. 온톨로지가 없으면 "급한 일이라 대충 했다"는 현장의 심증에 머물지만, `Work-Order.priority`와 `Quality-Check.passed`가 그래프로 연결되어 있으면 이것은 **측정 가능한 수치**가 된다.

---

## 2. 집계 쿼리 스케치

원문의 "이 모델이 가능하게 하는 질문" 표에 대응하는 두 가지 집계다.

### (a) 기계별 불량률 — `Machine → Part ← Quality-Check`

```gql
MATCH (m:Machine)-[:has_part]->(p:Part)<-[:inspects]-(qc:QualityCheck)
RETURN m.machineId,
       m.name,
       count(qc)                                   AS totalChecks,
       count(CASE WHEN qc.passed = false THEN 1 END) AS failures,
       count(CASE WHEN qc.passed = false THEN 1 END) * 1.0 / count(qc) AS defectRate
ORDER BY defectRate DESC
```

불량 **건수**가 아니라 **비율**로 봐야 한다는 점이 실무의 핵심이다. 가장 바쁜 기계는 불량 절대 건수도 당연히 많다. 분모(`totalChecks`)로 나누어야 "많이 만들어서 많이 틀린 기계"와 "적게 만드는데도 자주 틀리는 기계"가 구분된다.

여기에 `defectCode`를 한 축 더 얹으면 조치 대상이 바로 정해진다.

```gql
MATCH (m:Machine)-[:has_part]->(p:Part)<-[:inspects]-(qc:QualityCheck)
WHERE qc.passed = false
RETURN m.name, qc.defectCode, count(*) AS failures
ORDER BY failures DESC
```

### (b) 작업 지시 우선순위별 불량률 — `Work-Order (priority) → Part ← Quality-Check`

```gql
MATCH (wo:WorkOrder)-[:produces]->(p:Part)<-[:inspects]-(qc:QualityCheck)
RETURN wo.priority,
       count(qc)                                   AS totalChecks,
       count(CASE WHEN qc.passed = false THEN 1 END) * 1.0 / count(qc) AS defectRate
ORDER BY defectRate DESC
```

`urgent` 우선순위의 불량률이 `normal`보다 유의미하게 높게 나온다면, 이는 장비 문제가 아니라 **생산 계획 정책**의 문제다. 고칠 대상이 기계가 아니라 스케줄링 규칙이라는 것 — 온톨로지 없이는 나오기 어려운 결론이다.

> 원문의 GQL 예시는 여기서 한 걸음 더 나아가 센서까지 끌어온다: `(s:Sensor)-[:monitors]->(m:Machine)-[:has_part]->(p:Part)<-[:inspects]-(qc:QualityCheck)` with `s.lastReading > s.threshold AND qc.passed = false`. 즉 "불량이 났을 때 그 기계의 센서는 정상 범위였는가"를 함께 묻는다.

---

## 3. 닫힌 루프: 측정 → 추적 → 조치 → 재측정

피드백 "루프"라고 부르는 이유는 분석이 끝이 아니라 생산 쪽으로 되돌아가기 때문이다.

```
      [측정]  Quality-Check 기록 (passed, defectCode)
         ↓
      [추적]  Quality-Check → Part → Work-Order → Machine
         ↓
      [분석]  기계별 / 코드별 / 우선순위별 집계
         ↓
      [조치]  Machine.status, Sensor.threshold, 작업 배정 변경
         ↓
      [재측정] 조치 후 같은 쿼리를 다시 돌려 불량률 비교
         └────────────────── 반복 ──────────────────┘
```

품질 관리에서 익숙한 **PDCA**(Plan-Do-Check-Act)나 식스시그마의 **DMAIC**(Define-Measure-Analyze-Improve-Control)와 같은 골격이다. 온톨로지가 기여하는 부분은 그중 Measure와 Analyze — 데이터를 사람이 엑셀로 모으는 대신 그래프 순회 한 번으로 얻게 만드는 것이다. 그리고 마지막 Control/Act 단계, 즉 **조치 후 같은 쿼리를 재실행해 개선을 검증하는 단계**가 있어야 비로소 "루프"가 닫힌다. 분석만 하고 되돌아가지 않으면 그것은 리포트지 개선이 아니다.

---

## 4. 루프가 실제로 촉발하는 조치

분석 결과가 온톨로지의 어느 속성을 바꾸는지로 보면 구체적이다.

### `Machine.status` — 정비 스케줄링

특정 기계의 불량률이 임계선을 넘으면 `status`를 `running`에서 `maintenance`로 전환해 라인에서 빼고 점검한다. `status`가 `running` / `idle` / `maintenance` / `offline`을 갖는 것은 대시보드 표시용만이 아니라, **품질 데이터가 정비 결정을 구동할 수 있게 하는 연결점**이기 때문이다. 고장 나서 멈추는 사후 정비가 아니라, 불량률이 오르는 신호를 보고 미리 세우는 예방 정비로 옮겨간다.

### `Sensor.threshold` — 임계값 재조정

불량이 났는데 `lastReading`이 `threshold`를 넘지 않았다면, 알람이 울리지 않았다는 뜻이다. 이는 곧 **임계값이 너무 느슨하다**는 증거다. 불량 발생 시점의 실제 센서 값 분포를 보고 `threshold`를 낮춰 잡으면, 다음부터는 같은 상황에서 불량이 나기 **전에** 알람이 뜬다. 반대로 알람은 계속 울리는데 불량은 없다면 임계값이 과하게 빡빡한 것이고, 이 경우 잦은 헛경보가 현장의 알람 무시(alarm fatigue)를 부른다. 품질 결과가 예지 정비의 감도를 교정해 주는 셈이다.

### 작업 배정 — 공차 기반 재할당

`Part.tolerance`는 허용 제조 편차다. 원문이 짚듯 **공차가 빡빡한 부품은 더 정밀한 기계를 필요로 한다**. 피드백 루프가 "타이트한 공차 부품이 특정 기계에서만 불합격한다"를 밝혀내면, 조치는 그 기계를 고치는 것이 아니라 **`Work-Order`의 `assigned_to`를 더 정밀한 기계로 바꾸는 것**일 수 있다. 즉 장비를 등급에 맞게 쓰는 배정 규칙이 생긴다 — 정밀 장비는 타이트한 공차 전용, 여유 공차 부품은 일반 장비로.

### 그 밖의 후속 조치

- **재검사 대상 선별** — `Part ← Quality-Check (passed = false, count > 1)`로 반복 불합격 부품을 잡아낸다. 재작업 후에도 또 떨어지는 부품은 공정 자체가 잘못된 신호다.
- **생산 계획 규칙 수정** — `priority = urgent`의 불량률이 높으면 긴급 작업에 최소 리드타임을 강제하거나 검사 강도를 높인다.
- **범위 격리(containment)** — 불량 기계가 특정되면 그 기계가 같은 기간에 만든 다른 부품들을 `Machine → has_part → Part`로 한 번에 뽑아 선제 검사한다.

---

## 5. 왜 온톨로지가 이 루프를 싸게 만드는가

원문이 밝히듯 이 공장의 데이터는 **IoT 센서, MES, ERP, 품질관리 DB**라는 서로 다른 시스템에서 흘러 들어온다. 사일로 상태에서 위 루프를 돌리려면:

- QMS에서 불합격 목록을 뽑고
- MES에서 부품별 작업 지시 번호를 찾아 붙이고
- ERP/MES에서 작업 지시별 배정 장비를 또 붙이고
- IoT 히스토리언에서 그 시각의 센서 값을 시간 범위로 맞춰 조인한다

시스템마다 부품 식별자 체계가 다르면 조인 자체가 수작업이 된다. 결과적으로 근본 원인 분석이 **분기에 한 번, 엔지니어 며칠짜리 특별 프로젝트**가 되어 버린다. 비용이 비싸면 루프는 자주 돌지 않고, 자주 돌지 않으면 개선도 느리다.

온톨로지는 이 조인을 **모델 안에 미리 박아 둔다**.

| 사일로 방식 | 온톨로지 방식 |
|---|---|
| 시스템 4개에서 추출 후 수작업 조인 | 관계 순회 한 번 (`inspects` → `produces` → `assigned_to`) |
| 시스템마다 다른 식별자 매핑 | `partId`, `workOrderId`, `machineId` 식별자로 이미 연결 |
| 질문 하나마다 새 ETL | 새 질문 = 새 쿼리 (모델 변경 불필요) |
| 분기 단위 특별 분석 | 상시 대시보드 / 자동 알림 |

핵심은 **분석 비용이 내려가면 루프의 회전 주기가 짧아진다**는 것이다. 근본 원인 분석이 몇 초짜리 쿼리가 되면 매일, 매 교대(shift)마다 돌릴 수 있고, 조치의 효과 검증도 즉시 가능해진다. 지속적 개선에서 "지속적"이라는 말이 실제 의미를 갖는 지점이 여기다.

---

## 한 줄 요약

**불량을 코드·기계·작업 지시 조건별로 집계해 발생원을 특정하고 → 정비 스케줄, 센서 임계값, 작업 배정을 바꾸고 → 같은 쿼리로 다시 측정한다. 온톨로지는 이 루프의 추적 비용을 거의 0으로 만들어, 개선을 특별 프로젝트가 아닌 일상 운영으로 바꾼다.**
