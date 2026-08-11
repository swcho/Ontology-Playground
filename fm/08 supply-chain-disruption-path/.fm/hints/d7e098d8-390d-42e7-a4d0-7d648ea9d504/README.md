# DisruptionEvent의 `severity`와 분류(type)가 중요한 이유

## 한 줄 요약

`severity`는 **Critical / High / Medium / Low** 4단계 enum이고, `type`은 7종 enum이다.
이 둘의 **조합이 "누구에게 얼마나 빨리 알릴지(에스컬레이션 수준)"와 "언제까지 대응을 끝낼지(대응 타임라인)"를 결정**하기 때문에,
DisruptionEvent에서 가장 중요한 두 속성이다. 사람이 판단하지 않아도 자동화 엔진이 분기(decision tree)를 태울 수 있는 근거가 된다.

---

## 1. DisruptionEvent 속성 복습

```
DisruptionEvent
├─ eventId                (예: "DISR-202405-TAIWAN-001")
├─ type                   enum, 7종
├─ severity               enum, 4단계 (Critical/High/Medium/Low)
├─ startDate              date
├─ estimatedDurationDays  integer
└─ region                 string
```

원문의 Use case 문장이 핵심이다.

> **Classification and severity determine escalation level and response timeline.**
> (분류와 심각도가 에스컬레이션 수준과 대응 타임라인을 결정한다.)

즉 `severity`/`type`은 단순 라벨이 아니라 **워크플로 라우팅 키**다.

---

## 2. `type` 7종 — 무엇이 끊겼는지를 규정한다

| # | type | 성격 | 전형적 대응 축 |
|---|---|---|---|
| 1 | Natural Disaster | 지진·홍수·정전 등 물리적 파괴 | region 기반 광역 조회 → 대체 공급사 활성화 |
| 2 | Geopolitical | 제재·수출 규제·분쟁 | 국가(country) 단위 배제, 장기 소싱 재설계 |
| 3 | Financial | 공급사 부도·유동성 위기 | reliabilityScore 재평가, 선결제/자산 확보 |
| 4 | Logistics | 항만 적체·운송 지연 | Expedite Shipment, 경로 변경 |
| 5 | Quality Recall | 불량·리콜 | 이미 투입된 재고까지 소급, Redesign Component |
| 6 | Pandemic | 감염병으로 인한 가동 저하 | 장기 감산(Reduce Production), 안전재고 확대 |
| 7 | Cyber Attack | 랜섬웨어 등 공급사 IT 마비 | 보안 팀 동반 에스컬레이션, 수동 발주 전환 |

`type`이 **"어떤 종류의 MitigationAction이 유효한가"**를 좁혀 준다.
예를 들어 Logistics 지연에는 `Expedite Shipment`가 잘 먹히지만, Quality Recall에는 무의미하고
`Redesign Component`나 `Customer Communication`이 필요하다.

또한 `type`은 **탐지(Phase 1) 단계의 매칭 조건**에 직접 들어간다.

```
Matches: Supplier.country="Taiwan"
       + DisruptionEvent.region="Taiwan"
       + DisruptionEvent.type="Natural Disaster"
→ 3 critical suppliers identified
```

`type` 없이 region만으로 매칭하면 "대만에 있는 모든 공급사"가 잡히지만,
`type=Natural Disaster`가 붙으면 "물리적 생산 중단이므로 재고 소진 속도로 계산해야 한다"는
계산 모델까지 함께 선택된다.

---

## 3. `severity` 4단계 — 얼마나 급한지를 규정한다

`severity`는 `type`이 알려주지 않는 **강도**를 담는다. 같은 Natural Disaster라도
진도 4.0 지진(Low)과 진도 6.8 지진(Critical)은 전혀 다른 대응이 필요하다.

| severity | 의미 | 에스컬레이션 수준(관례적 해석) | 대응 타임라인 |
|---|---|---|---|
| Critical | 생산 정지가 임박/확정 | CEO·Board까지 즉시 통보, Activator 실시간 알림 | 분 단위 (원문 사례: 10:30 발생 → 10:50 경영진 통보) |
| High | 다수 제품군 노출, 완충 있음 | 조달·운영 리더십 | 시간 단위 (< 2h to mitigation) |
| Medium | 단일 부품/제품군 영향 | 담당 조달 매니저 | 일 단위 |
| Low | 모니터링 대상 | 대시보드 기록만 | 주기 점검(4시간 주기 재평가에 포함) |

원문의 "Continuous improvement" 표에 나오는 목표치(Detection speed < 1 hour,
Time to mitigation < 2 hours)는 사실상 **높은 severity 이벤트를 기준으로 잡은 SLA**다.
severity가 없으면 모든 이벤트에 같은 SLA를 적용하게 되고, 알림 피로(alert fatigue)로
정작 Critical 이벤트가 묻힌다.

---

## 4. type × severity 조합이 Phase 5 자동 실행으로 이어지는 경로

Phase 5의 자동 실행 조건은 **DisruptionEvent가 아니라 RiskAssessment의 수치**로 걸려 있다.

```
IF RiskAssessment.revenueAtRisk > $50M AND
   RiskAssessment.timeToImpactDays < 5:
   THEN:
     1. Create PurchaseOrder for recommended AlternativeSupplier
     2. Update ProductionSchedule with new timeline
     3. Send email to Procurement / Operations / Finance / CEO·Board
     4. Create Activator alerts with escalation policy
     5. Start monitoring MitigationAction.status
```

여기서 중요한 포인트는 **type/severity가 이 두 수치를 만들어내는 입력**이라는 것이다.
관계 4번 `DisruptionEvent triggers RiskAssessment`(1:N)를 타고 값이 흘러간다.

```
DisruptionEvent
├─ type      → 어떤 계산 모델/후보 액션 집합을 쓸지 선택
├─ severity  → 공급 중단 비율(전면 정지 vs 부분 감산) 가정
├─ region    → affects 관계로 몇 개 Supplier가 잡히는지 결정
└─ estimatedDurationDays → 중단 기간 가정
        ↓ (affects → supplies → usedIn 캐스케이드)
RiskAssessment
├─ revenueAtRisk      ← 노출 ProductLine.annualRevenue 합
└─ timeToImpactDays   ← Component.daysOfSupplyOnHand 최솟값
        ↓
Phase 5 자동 실행 게이트 (> $50M AND < 5일)
```

원문 사례를 숫자로 따라가면 이렇다.

```
10:45  DisruptionEvent 생성
       type = "Natural Disaster"      → 물리 중단, 대체 공급사 탐색 모드
       severity = "Critical"          → 전면 중단 가정 + 최고 에스컬레이션
       region = "Taiwan"              → 대만 소재 3개 critical supplier 매칭
       estimatedDurationDays = 7      → 7일 공백 vs 재고 3일 → 4일 결손

10:46  캐스케이드: 3 suppliers → 47 components → 12 product lines
       revenueAtRisk    = $127M   (> $50M ✅)
       timeToImpactDays = 3       (< 5   ✅)

10:48  두 조건 모두 충족 → MitigationAction 자동 생성 (PO 발행, 안전재고 발주)
10:50  Activator 트리거 → 에스컬레이션 정책이 리더십에 통보
```

만약 같은 지진이 `severity = "Low"`, `estimatedDurationDays = 1`로 기록됐다면
재고 3일 안에 복구되므로 결손이 없고, revenueAtRisk가 임계치 아래로 떨어져
**자동 실행이 발동하지 않고 모니터링 큐에만 남는다.**
즉 severity는 "$50M / 5일" 게이트를 넘길지 말지를 사실상 좌우하는 상류 변수다.

### 조합별 시나리오 예시

| type | severity | estimatedDurationDays | 예상 귀결 |
|---|---|---|---|
| Natural Disaster | Critical | 7 | 재고(3일) < 기간(7일) → 게이트 통과, PO 자동 발행 + 경영진 통보 |
| Cyber Attack | Critical | 2 | 기간 짧지만 전면 정지 → 통과 가능, 보안 팀 동반 에스컬레이션 |
| Logistics | High | 10 | 장기지만 부분 지연 → Expedite Shipment 권고, 승인 게이트 유지 |
| Geopolitical | Medium | 90 | 즉각 결손 없음(timeToImpactDays 큼) → 자동 실행 미발동, 장기 소싱 재설계 과제로 전환 |
| Quality Recall | High | 5 | 기존 재고까지 무효화 → daysOfSupplyOnHand가 0으로 재계산되어 급격히 통과 |
| Pandemic | Medium | 120 | 초장기 저강도 → 안전재고 증대 등 완만한 액션 |
| Natural Disaster | Low | 1 | 게이트 미달 → 대시보드 기록, 4시간 주기 재평가 대상 |

---

## 5. `estimatedDurationDays`와의 상호작용 — severity의 "짝" 변수

`severity`는 **강도(얼마나 심한가)**, `estimatedDurationDays`는 **지속(얼마나 오래)**을 담는다.
둘은 서로를 대체하지 못하고, 곱해져야 실제 결손이 나온다.

```
공백일수 = estimatedDurationDays - Component.daysOfSupplyOnHand
       (severity가 공급 중단 비율을 결정 → 부분 중단이면 실효 공백일수 감소)
```

- **높은 severity + 짧은 duration**: 급하지만 재고로 흡수 가능 → 알림은 강하게, 액션은 최소로.
- **낮은 severity + 긴 duration**: 서서히 재고를 잠식 → 즉시 알림은 불필요하나 반드시 안전재고/대체 소싱을 계획해야 함. severity만 보면 놓치는 유형이다.
- **높은 severity + 긴 duration**: Phase 5 자동 실행의 정석 케이스.

또 `estimatedDurationDays`는 **정적이지 않다.** Day 2-4 모니터링 루프가 4시간마다 이 값을 갱신한다.

```
Every 4 hours:
  - Check DisruptionEvent.estimatedDurationDays (update if recovery changes)
  - Recalculate RiskAssessment with latest inventory data
  - Alert if leadTimeSavedDays slips
```

즉 duration이 7일 → 10일로 늘어나면 revenueAtRisk가 재계산되어
그동안 게이트 아래에 있던 이벤트가 새로 자동 실행에 걸릴 수 있다.
반대로 복구가 빨라지면 에스컬레이션이 완화된다. **severity/duration은 이벤트의 상태를 추적하는 살아있는 값이다.**

---

## 6. `region`과의 상호작용 — 폭(breadth)을 결정한다

`region`은 `DisruptionEvent affects Supplier`(M:N) 관계의 **매칭 범위**를 정한다.

- `region`이 `Supplier.country`와 매칭되어 **몇 개 공급사가 걸리는가**를 결정한다.
- 걸린 공급사 수가 `supplies → usedIn` 캐스케이드의 팬아웃을 결정하고,
  결국 revenueAtRisk 총액을 좌우한다. (3 suppliers → 47 components → 12 product lines → $127M)
- 따라서 **severity가 같아도 region이 넓으면 게이트를 통과**한다.
  같은 High severity 정전이 단일 공단에 국한되면 $20M, 국가 단위면 $127M이 될 수 있다.

`region`은 대체 공급사 선정에도 다시 쓰인다. Phase 4의 필터에 배제 조건으로 등장한다.

```
Find AlternativeSupplier WHERE
  qualificationStatus = "Approved"
  AND capacityAvailable >= demand
  AND country NOT IN earthquake_region     ← region 재사용
```

즉 `region`은 (1) 피해 범위 산정 (2) 백업 후보에서 동일 위험 지역 제외라는
**두 방향으로 작동**한다. `region`을 무시하면 대만 지진에 대해 대만의 다른 공급사를
대체안으로 추천하는 치명적 오류가 난다.

### 세 속성의 역할 분담

| 속성 | 답하는 질문 | 캐스케이드에서의 역할 |
|---|---|---|
| `type` | 무엇이 끊겼나 | 계산 모델·유효 액션 집합 선택 |
| `severity` | 얼마나 심한가 | 에스컬레이션 수준, 중단 비율 가정 |
| `estimatedDurationDays` | 얼마나 오래 | 재고 소진 대비 공백일수 계산 |
| `region` | 어디까지 | affects 팬아웃 폭, 대체 공급사 배제 조건 |

네 개가 모여야 `revenueAtRisk`와 `timeToImpactDays`가 나오고, 그 두 수치가 Phase 5 게이트를 통과한다.

---

## 7. Activator 에스컬레이션 정책과의 연결

Phase 5의 4번 항목이 `Create Activator alerts with escalation policy`다.
Activator는 Microsoft Fabric의 실시간 이벤트-액션 도구로, "조건 충족 시 누구에게 어떻게 알릴지"를
정책으로 관리한다. 여기서 **severity가 정책 티어의 키**가 된다.

```
Day 1  10:50 AM: Activator triggered
       ├─ Real-time dashboard shows impact + actions
       ├─ Escalation policy notifies leadership       ← severity=Critical이므로 리더십까지
       └─ Procurement team acknowledges + confirms receipt
```

전형적인 매핑은 이렇다.

| severity | 수신자 | 채널 | 확인(ack) 요구 |
|---|---|---|---|
| Critical | 조달 + 운영 + 재무 + CEO/Board | 대시보드 + 이메일 + 즉시 호출 | 필수, 미확인 시 상위 재호출 |
| High | 조달·운영 리더십 | 이메일 + 대시보드 | 필수 |
| Medium | 담당 조달 매니저 | 이메일 | 선택 |
| Low | 대시보드 기록 | — | 불필요 |

`type`은 여기서 **수신자 목록을 조정**한다. 예를 들어 `Cyber Attack`이면 보안/IT 팀이,
`Quality Recall`이면 품질보증과 고객대응 팀이, `Geopolitical`이면 법무/통상 팀이
같은 severity에서도 추가로 붙는다. 즉 **severity가 "티어"를, type이 "부서 라우팅"을 담당**한다.

---

## 8. 왜 enum이어야 하나

원문의 속성 타입 표는 `enum`의 용도를 이렇게 적는다.

| Type | Example | Use in agents |
|---|---|---|
| `enum` | Supplier tier, disruption type, severity | **Classification, decision trees** |

자유 텍스트("꽤 심각함", "매우 나쁨")로 두면 위의 모든 자동 분기가 불가능하다.
enum으로 고정하면,

1. **결정론적 분기** — `IF severity = "Critical" THEN notify(board)`가 코드로 작성 가능.
2. **집계·정렬** — "Critical 이벤트 상위 N개" 같은 랭킹이 가능.
3. **Fabric IQ 데이터 에이전트 그라운딩** — 자연어 질문("지금 심각한 리스크 뭐야?")을
   `severity IN ("Critical","High")`로 정확히 번역할 수 있다.
4. **학습 루프** — "Critical로 분류한 이벤트의 실제 결손이 추정치와 얼마나 맞았나"를
   범주별로 집계해 추정 모델을 보정할 수 있다 (Impact estimate accuracy ±10% 목표).

요약 절의 `✅ Automation-ready with enum classifications and timestamps`가 바로 이 얘기다.
**enum 분류가 자동화의 전제조건**이다.

---

## 암기 포인트

- `severity` = **Critical / High / Medium / Low** 4단계 (Component의 `criticalityLevel`과 같은 4단계 값이라 혼동 주의).
- `type` = 7종: **Natural Disaster / Geopolitical / Financial / Logistics / Quality Recall / Pandemic / Cyber Attack**.
- 중요한 이유 한 문장: **"분류와 심각도가 에스컬레이션 수준과 대응 타임라인을 결정한다."**
- Phase 5 자동 실행 게이트: **revenueAtRisk > $50M AND timeToImpactDays < 5** (두 조건 AND).
- type/severity는 게이트에 직접 등장하지 않지만, region·estimatedDurationDays와 함께
  게이트 입력값(revenueAtRisk, timeToImpactDays)을 만들어내는 **상류 변수**다.
- 역할 분담: type=무엇/부서 라우팅, severity=얼마나 심함/알림 티어,
  estimatedDurationDays=얼마나 오래, region=어디까지(+백업 후보 배제).
