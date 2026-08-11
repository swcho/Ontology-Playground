# Machine + Sensor = 텔레메트리 백본(telemetry backbone)

> **Q.** Machine과 Sensor가 함께 형성하는 것을 무엇이라 부르는가?
> **A.** **텔레메트리 백본(telemetry backbone)**. 이후 추가되는 생산·품질 엔티티들이 올라앉는 IoT 기반 층 역할을 한다.

---

## 1. "백본"이라는 표현이 나온 자리

Smart Manufacturing 학습 경로의 2번째 글 **Factory Floor**는 모든 스마트 팩토리가 두 개의 개념에서 출발한다고 말한다.

- **Machine** — 공장 바닥에 어떤 장비가 있는가?
- **Sensor** — 그 장비가 어떤 데이터를 만들어내고 있는가?

> Machines and sensors form the **telemetry backbone**. Before tracking production or quality, you need to know what's running and what it's reporting.

즉 *생산(production)*이나 *품질(quality)*을 추적하기 **전에**, "무엇이 돌아가고 있고(what's running) 무엇을 보고하고 있는가(what it's reporting)"가 먼저 확정되어야 한다는 뜻이다. 백본(등뼈)이라는 비유가 쓰인 이유는 이 두 엔티티가 화려한 기능을 담당해서가 아니라, **나머지 모든 것이 여기에 붙어서 지탱된다**는 구조적 위치 때문이다.

같은 글의 마무리에서도 이를 다시 못 박는다.

> Even two entities can form a useful **telemetry backbone**.

엔티티가 단 2개뿐이어도 의미 있는 층이 만들어진다는 것 — 온톨로지 설계에서 "작게 시작해서 층을 쌓는다"는 원칙의 예시다.

---

## 2. 두 엔티티의 속성 테이블이 말해주는 것

### Machine

| Property | Type | Identifier? |
|---|---|---|
| `machineId` | string | ✓ |
| `name` | string | |
| `type` | string | |
| `status` | string | |
| `installDate` | date | |

- `status`는 **운영 상태(operational state)**를 추적한다 — `running`, `idle`, `maintenance`, `offline`.
- 이 하나의 속성이 실시간 대시보드와 유지보수 스케줄링을 가능하게 한다. 즉 Machine은 단순한 "장비 명부"가 아니라 **현재 상태를 들고 있는 살아있는 노드**다.

### Sensor

| Property | Type | Identifier? |
|---|---|---|
| `sensorId` | string | ✓ |
| `type` | string | |
| `unit` | string | |
| `lastReading` | float | |
| `threshold` | float | |

- `lastReading`은 **현재 값**, `threshold`는 **경보 경계선**이다.
- `lastReading > threshold`가 되면 알람이 발생한다. 이 패턴이 곧 **예지보전(predictive maintenance)**의 기본형이다.
- `unit`이 따로 있는 이유는 센서 종류마다 단위가 다르기 때문(°C, mm/s, kPa …). 값과 단위를 분리해 두어야 이종 센서를 한 스키마로 다룰 수 있다.

두 테이블을 나란히 보면 역할 분담이 분명하다. **Machine은 "무엇이 존재하고 어떤 상태인가"를, Sensor는 "그것이 지금 무엇을 보고하는가"를 담당한다.** 이 둘이 합쳐져야 비로소 "공장 바닥의 현재"가 데이터로 표현된다.

---

## 3. `monitors` 관계와 소유 계층(ownership hierarchy)

이 층을 실제로 "백본"으로 만들어 주는 것은 속성이 아니라 **관계 하나**다.

- **monitors** — `Sensor` → `Machine` (many-to-one)
  하나의 기계를 여러 센서가 감시한다 — 온도용 하나, 진동용 하나 등.

원문의 강조 박스가 이 관계의 핵심을 설명한다.

> **Ownership hierarchy:** In IoT ontologies, sensors belong to machines. **The direction matters**: sensors monitor machines, not the other way around. This parent-child hierarchy is how IoT platforms organize telemetry data.

여기서 놓치기 쉬운 세 가지 포인트.

**(1) 방향이 중요하다.**
`Sensor → Machine`이지 `Machine → Sensor`가 아니다. 카디널리티가 **many-to-one**이라는 사실이 방향을 결정한다. 많은 쪽(Sensor)이 하나의 쪽(Machine)을 가리켜야 각 센서 인스턴스가 자기 부모를 유일하게 지목할 수 있다. 반대 방향으로 잡으면 Machine 하나가 여러 Sensor를 가리키는 다중 참조가 되어 그래프 순회와 조인이 지저분해진다.

**(2) 이것은 "소유"의 계층이다.**
센서는 기계에 **속한다(belong to)**. 센서는 독립적으로 존재하는 관측 대상이 아니라, 어떤 장비에 부착되어 그 장비를 대신해 말해주는 부속물이다. 그래서 부모-자식(parent-child) 구조가 된다.

**(3) 이 계층이 곧 텔레메트리 집계(telemetry aggregation)의 축이다.**
경로의 마지막 글 **Key takeaways** 1번이 이를 정확히 요약한다.

> **IoT hierarchies** organize sensors under machines for **telemetry aggregation**.

### 텔레메트리 집계란 무엇인가

IoT 플랫폼에서 원시 데이터는 **개별 센서 단위**로 초 단위·밀리초 단위로 쏟아진다. 하지만 사람이 묻고 싶은 질문은 센서 단위가 아니라 **장비 단위**다.

- "CNC-01호기 상태가 이상한가?" (← 사람의 질문)
- "sensor-7742의 lastReading이 82.3인가?" (← 센서가 보고하는 것)

이 간극을 메우는 것이 소유 계층이다. 시나리오 개요의 **Key concepts**에 나온 표현대로 *"machines own sensors, **readings flow upward**"* — 판독값이 **위로 흘러올라간다**. 즉 `monitors` 엣지를 역방향으로 타고 올라가면 개별 센서의 값들이 하나의 기계라는 집계 지점(rollup point)으로 모인다.

```
  [temp sensor]  ─┐
  [vib sensor]   ─┼─ monitors ─▶ [Machine CNC-01]  ← 여기서 집계된다
  [press sensor] ─┘
```

이 축이 있기 때문에 다음이 가능해진다.

- **롤업(roll-up)**: 기계 하나에 달린 모든 센서 판독값을 묶어 "이 기계의 건강 상태"를 산출.
- **알람 귀속(alarm attribution)**: 임계치를 넘은 센서 알람을 자동으로 특정 기계에 귀속. 알람이 어느 장비의 문제인지 사람이 매핑표를 뒤질 필요가 없다.
- **탐색 경로의 단일화**: 어떤 질문이든 "센서 → 기계"라는 단 하나의 홉으로 정규화된다.

**Machine이 곧 집계 지점(aggregation point)**이라는 점이 백본 비유의 실체다. 등뼈에 갈비뼈가 붙듯, 센서들이 기계에 붙어 하나의 구조를 이룬다.

---

## 4. 왜 "기반 층(foundation layer)"인가 — 위에 무엇이 올라앉는가

답변의 뒷부분, "이후 추가되는 생산·품질 엔티티들이 올라앉는 IoT 기반 층"이 이 카드의 진짜 요점이다. 학습 경로 자체가 층을 쌓는 순서로 설계되어 있다.

| Step | Entities added | Cumulative | Key concept |
|---|---|---|---|
| 1 | **Machine, Sensor** | 2 | IoT hierarchy, telemetry |
| 2 | + Work-Order, Part | 4 | Production chains, tolerances |
| 3 | + Quality-Check | 5 | Feedback loops, inspection |

### Step 2 — 생산 층이 Machine 위에 붙는다

Work-Order와 Part가 추가될 때 새로 생기는 관계 세 개를 보자.

- **assigned_to** — `Work-Order` → `Machine` (many-to-one)
- **produces** — `Work-Order` → `Part` (one-to-many)
- **has_part** — `Machine` → `Part` (one-to-many)

세 개 중 **두 개가 Machine에 직접 연결된다.** 새 엔티티들이 허공에 뜨는 것이 아니라 이미 존재하는 백본 노드에 접합되는 것이다. 원문의 표현대로 *"Work-Order and Part join the graph, adding production tracking **to the IoT foundation**."*

여기서 Machine의 역할이 확장된다. Step 1에서 Machine은 "센서가 감시하는 대상"이었지만, Step 2에서는 동시에 "작업 지시가 할당되는 대상"이자 "부품을 생산하는 주체"가 된다. **하나의 노드가 모니터링 축과 생산 축을 동시에 물고 있다** — 이것이 백본이 백본인 이유다.

> **Production chain:** The chain `Machine ← Work-Order → Part` connects equipment to output through a scheduling entity.

### Step 3 — 품질 층이 Part 위에 붙는다

- **inspects** — `Quality-Check` → `Part` (many-to-one)

Quality-Check는 Machine에 직접 붙지 않는다. Part를 거쳐 간접적으로 연결된다. 그런데도 원문은 피드백 루프가 **Machine까지 도달한다**고 말한다.

> **Feedback loop:** When a quality check fails, the production chain reverses: `Quality-Check (passed=false) → Part → Work-Order → Machine`.

즉 품질 실패의 원인 추적이 **끝내 백본 노드로 수렴한다**. 층이 몇 겹 올라가든 최종 착지점은 Step 1에서 정의한 Machine이다.

### 결정적 증거 — 두 축이 만나는 GQL 질의

경로 전체를 관통하는 질문은 이것이었다.

> "Which machines with abnormal sensor readings produced parts that failed quality checks last week?"
> (비정상 센서 판독값을 보인 기계가 생산한, 품질 검사에 실패한 부품은?)

이것이 GQL로는 다음과 같이 표현된다.

```gql
MATCH (s:Sensor)-[:monitors]->(m:Machine)-[:has_part]->(p:Part)<-[:inspects]-(qc:QualityCheck)
WHERE s.lastReading > s.threshold AND qc.passed = false
RETURN m.name, s.type, s.lastReading, p.name, qc.defectCode
```

이 한 줄이 백본 개념의 완결된 증명이다. 패턴의 **한가운데에 `(m:Machine)`이 있고**, 왼쪽에서 텔레메트리 축(`Sensor -[:monitors]-> Machine`)이, 오른쪽에서 생산·품질 축(`Machine -[:has_part]-> Part <-[:inspects]- QualityCheck`)이 들어와 **Machine에서 만난다.**

Step 1의 두 엔티티와 `monitors` 관계가 없었다면 이 질의의 왼쪽 절반은 아예 존재할 수 없다. 센서 이상과 품질 불량을 상관분석하는 것 — 스마트 팩토리 온톨로지의 최종 목표 — 이 정확히 백본 위에서 성립한다.

---

## 5. 정리 — 시험에 나올 만한 포인트

- **명칭**: Machine + Sensor = **텔레메트리 백본(telemetry backbone)**. "IoT foundation"이라고도 불린다.
- **왜 백본인가**: 생산·품질을 추적하기 전에 "무엇이 돌아가고 무엇을 보고하는가"가 먼저 확정되어야 하므로, 나머지 층이 모두 이 위에 얹힌다.
- **핵심 관계**: `monitors` — **Sensor → Machine, many-to-one**. 방향이 중요하다(센서가 기계를 감시하지, 그 반대가 아니다).
- **소유 계층**: 센서는 기계에 속한다. parent-child 구조이며, IoT 플랫폼이 텔레메트리 데이터를 조직하는 방식이다.
- **텔레메트리 집계**: 판독값이 `monitors`를 따라 위로 흘러 Machine이라는 집계 지점으로 모인다 → 롤업, 알람 귀속이 가능해진다.
- **위에 얹히는 것들**: Work-Order(`assigned_to`), Part(`has_part`)가 Machine에 직접 붙고, Quality-Check는 Part를 거쳐 붙어 결국 `QC → Part → Work-Order → Machine` 피드백 루프로 백본에 수렴한다.
- **최종 형태**: 5 entities, 5 relationships (`monitors`, `assigned_to`, `produces`, `has_part`, `inspects`).
- **암기 문장**: *"Even two entities can form a useful telemetry backbone."*

### 헷갈리기 쉬운 것

- 백본을 형성하는 것은 **Machine과 Sensor 둘 다**다. Sensor 하나만으로는 부착 지점이 없고, Machine 하나만으로는 보고할 데이터가 없다. 두 엔티티와 그 사이의 `monitors` 관계가 세트로 백본이다.
- `monitors`의 방향을 `Machine → Sensor`로 착각하지 말 것. many-to-one이므로 **많은 쪽인 Sensor가 출발점**이다.
- Quality-Check는 Machine에 **직접** 연결되지 않는다. Part를 경유한다.
