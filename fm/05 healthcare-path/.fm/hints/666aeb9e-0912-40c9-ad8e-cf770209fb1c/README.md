# Healthcare 도메인에서 온톨로지가 필요한 이유를 보여주는 임상 질문 예시

## 카드 요지

원문(`Scenario Overview` → `Why an ontology?`)에 등장하는 대표 질문은 다음과 같다.

> **"Which patients diagnosed with severe conditions by cardiology providers still have prescriptions with zero refills remaining?"**
>
> "cardiology provider가 severe로 진단한 환자 중 refillsRemaining이 0인 처방을 가진 사람은 누구인가?"

이 한 문장이 온톨로지의 필요성을 증명하는 장치로 쓰인다. 이유는 답을 만들기 위해 **서로 다른 시스템에 흩어진 4가지 데이터**를 동시에 교차해야 하기 때문이다.

| 질문에 담긴 조건 | 필요한 데이터 | 실제 원천 시스템 |
|---|---|---|
| "환자는 누구인가" | 환자 기록 (patientId, mrn) | EHR (전자의무기록) |
| "severe로 진단된" | 진단 이력 (severity, icdCode) | EHR / 임상 문서 |
| "cardiology provider가" | provider 전문 분야 (specialty, department) | 인사·자격(라이선스) 시스템 |
| "refillsRemaining이 0인 처방" | 약국 데이터 (rxNumber, refillsRemaining) | 약국(pharmacy) DB |

원문 23번째 줄에서 명시하듯 데이터는 "electronic health records (EHR), scheduling systems, pharmacy databases, and billing platforms"에 분산되어 있다. 즉 질문 하나가 조직 경계와 시스템 경계를 동시에 넘는다.

## 온톨로지가 이 질문을 어떻게 해결하는가

온톨로지는 이 질문을 **그래프 경로(path)** 로 번역한다. 원문이 제시한 매핑은 두 조각이다.

```
Patient → Diagnosis (severity=severe) ← Provider (specialty=Cardiology)
Diagnosis → Prescription (refillsRemaining=0)
```

- 첫 줄은 **dual authorship(이중 저작권)** 패턴이다. `Diagnosis`는 조건을 가진 Patient와 그것을 식별한 Provider 양쪽에 연결된다(`diagnosed_with`, `diagnoses`). 그래서 "환자 관점"과 "진단한 의사 관점"을 같은 노드에서 동시에 걸 수 있다.
- 둘째 줄은 **care chain(진료 사슬)** 이다. `treated_by` 관계로 진단이 처방으로 이어지므로, 진단의 severity 조건과 처방의 refillsRemaining 조건을 한 경로에서 결합할 수 있다.

두 조각을 합치면 전체 경로는 `Provider → Diagnosis ← Patient`, `Diagnosis → Prescription`이 되고, 이것이 곧 5-entity / 6-relationship 온톨로지의 존재 이유가 된다.

## 온톨로지 없이 하면 왜 어려운가

- **조인 키가 서로 다르다.** 환자는 `patientId`(온톨로지 식별자)와 `mrn`(병원 내부 식별자)을 함께 갖고, 처방은 약국 표준인 `rxNumber`를 식별자로 쓴다. 시스템별 식별자 체계를 사람이 매번 손으로 맞춰야 한다.
- **의미가 코드에 숨는다.** "cardiology"는 Provider의 `specialty` 값, "severe"는 Diagnosis의 `severity` 값, "0 refills"는 Prescription의 `refillsRemaining` 정수 값이다. 온톨로지가 없으면 이 semantics가 각 팀의 SQL 안에 흩어져 재사용되지 않는다.
- **질문이 바뀌면 처음부터 다시 짠다.** 온톨로지가 있으면 같은 그래프에서 조건만 바꿔 새 질문을 즉시 표현할 수 있다(예: severity=severe인데 Prescription이 아예 없는 진단 찾기).

## 실제 쿼리로 본 모습

원문 `Complete Care Model` 단계의 GQL 예시가 이 질문을 거의 그대로 코드화한다(임계값만 `<= 1`로 완화된 버전).

```gql
MATCH (p:Patient)-[:diagnosed_with]->(d:Diagnosis)-[:treated_by]->(rx:Prescription)
WHERE d.severity = 'severe' AND rx.refillsRemaining <= 1
RETURN p.patientId, d.description, rx.medication, rx.refillsRemaining
```

카드의 질문을 완전히 재현하려면 provider 전문 분야 조건을 한 홉 더 붙이면 된다.

```gql
MATCH (prov:Provider)-[:diagnoses]->(d:Diagnosis)<-[:diagnosed_with]-(p:Patient),
      (d)-[:treated_by]->(rx:Prescription)
WHERE prov.specialty = 'Cardiology'
  AND d.severity = 'severe'
  AND rx.refillsRemaining = 0
RETURN p.patientId, p.mrn, d.icdCode, rx.medication
```

관계 이름(`diagnoses`, `diagnosed_with`, `treated_by`)이 그대로 문장의 동사가 되는 것이 핵심이다. 자연어 임상 질문 → 그래프 경로 → 쿼리로 매끄럽게 내려온다.

## 임상적 의미 (왜 이 질문이 실제로 중요한가)

이 질문은 단순한 데모가 아니라 실제 병원의 **medication adherence(복약 순응도) / 재처방 관리** 업무다.

- severe로 분류된 심장질환(예: 심부전, 부정맥, 관상동맥 질환) 환자에게 약이 끊기면 재입원·응급실 방문 위험이 급증한다.
- `refillsRemaining = 0`은 "다음 처방을 받지 못하면 곧 복약이 중단된다"는 조기 경보 신호다.
- 따라서 이 쿼리 결과는 곧 **선제적으로 연락해야 할 고위험 환자 리스트(care gap / outreach list)** 가 된다. severity 속성이 risk stratification(위험 계층화)에 쓰인다는 원문 설명이 여기서 실체를 갖는다.

## 함께 기억할 관련 질문들

원문은 완성된 모델이 답할 수 있는 질문을 표로 제시한다. 카드의 질문은 그 첫 행의 강화판이다.

| 질문 | 그래프 경로 |
|---|---|
| 재처방이 필요한 환자는? | Patient → Diagnosis → Prescription (refillsRemaining=0) |
| 약을 가장 많이 처방하는 provider는? | Provider → Prescription (count) |
| 아직 치료가 없는 severe 진단은? | Diagnosis (severity=severe) with no → Prescription |
| 자신이 진단한 질환을 직접 처방까지 하는 전문의는? | Provider → Diagnosis AND Provider → Prescription |

## 암기 포인트

1. 질문 문장을 기억하라: **cardiology provider + severe 진단 + refillsRemaining 0**.
2. 교차해야 하는 4가지: **환자 기록 / 진단 이력 / provider 전문 분야 / 약국 데이터**.
3. 매핑 형태를 기억하라: `Patient → Diagnosis ← Provider`(dual authorship) + `Diagnosis → Prescription`(care chain).
4. 온톨로지의 가치 = 흩어진 시스템의 데이터를 **하나의 탐색 가능한 경로**로 통합해, 자연어 질문을 그대로 쿼리로 바꿀 수 있게 하는 것.
