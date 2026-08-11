# `patientId` vs `mrn` — 식별자 두 겹으로 두는 설계

## 카드 요약

**Q.** `patientId`와 `mrn`을 구분해서 두는 설계의 의미는 무엇인가?

**A.** 온톨로지 식별자(`patientId`)와 도메인 고유 식별자(`mrn`)가 공존할 수 있음을 보여준다. 온톨로지는 자체 식별 체계를 유지하면서 외부 시스템(EHR)의 식별자를 속성으로 보존한다.

---

## 1. 원문에서의 근거

Healthcare 학습 경로의 Patient 엔티티 정의는 이렇게 되어 있다.

| Property | Type | Identifier? |
|---|---|---|
| `patientId` | string | ✓ |
| `mrn` | string | |
| `dateOfBirth` | date | |
| `bloodType` | string | |
| `allergies` | string | |

> The `mrn` (Medical Record Number) is the hospital's internal identifier. The `patientId` is used as the ontology identifier, while `mrn` is a domain-specific property that maps to the EHR system.

그리고 해당 단계의 정리(What we learned)에 이 문장이 못 박혀 있다.

> **Domain-specific identifiers** (MRN) coexist with ontology identifiers (patientId)

즉 "둘 중 하나를 고른다"가 아니라 **역할이 다른 두 식별자를 동시에 유지한다**는 것이 이 카드의 핵심이다.

- `patientId` → 온톨로지 내부에서 노드를 지목하고 관계(`has_appointment`, `diagnosed_with`)를 걸 때 쓰는 **유일한 공식 키**
- `mrn` → 원천 시스템(EHR)에 되돌아가 조회·조인할 때 쓰는 **보존된 외부 키**

---

## 2. 키의 종류로 보는 구도 (surrogate vs natural/business key)

데이터 모델링에서 오래된 구분을 그대로 대응시킬 수 있다.

| 구분 | Surrogate key (대리 키) | Natural / Business key (자연 키·업무 키) |
|---|---|---|
| 정의 | 시스템이 발급한, 업무 의미가 없는 식별자 | 업무 세계에 이미 존재하는 의미 있는 식별자 |
| 이 카드의 예 | `patientId` | `mrn` |
| 값의 출처 | 온톨로지/플랫폼이 스스로 생성 | 병원 EHR이 생성 |
| 의미 | 없음(불투명, opaque) | 있음(의무기록 번호) |
| 변경 가능성 | 원칙적으로 불변(immutable) | 업무 사정에 따라 바뀔 수 있음 |
| 유일성 범위 | 온톨로지 전체 | 발급 기관(병원/네트워크) 안에서만 |

핵심은 **"의미 있는 식별자는 언젠가 변한다"**는 경험 법칙이다. 의미가 담긴 키는 그 의미가 바뀔 때 값도 바뀌어야 하고, 그 값이 그래프 전역의 참조 키였다면 변경 비용이 폭발한다.

### `mrn`을 그대로 primary identifier로 쓰면 생기는 문제

1. **유일성 보장 범위가 좁다** — MRN은 보통 한 병원(또는 한 EHR 인스턴스) 안에서만 유일하다. 병원 네트워크가 여러 기관을 통합하면 서로 다른 환자가 같은 MRN을 갖는 충돌이 발생한다.
2. **한 환자가 MRN을 여러 개 가진다** — A병원 MRN, B병원 MRN, 과거 등록 착오로 생긴 중복 MRN 등. 1:1을 전제로 한 키가 사실은 1:N이다.
3. **값이 변한다** — 중복 등록 병합(merge), EHR 교체·마이그레이션, 번호 체계 개편 시 MRN이 재발급된다. 이때 MRN이 참조 키라면 이 환자를 가리키던 모든 Appointment·Diagnosis·Prescription 참조를 함께 갱신해야 한다.
4. **원천 시스템에 종속된다** — 내일 EHR을 다른 벤더 제품으로 바꾸면 온톨로지의 정체성 체계가 함께 흔들린다.
5. **민감정보 노출 면적이 커진다** — MRN은 사실상 환자를 지목하는 식별정보(PHI)에 가깝다. 그것이 모든 관계·URI·로그·API 응답에 박히는 것은 프라이버시 관점에서 불리하다. 불투명한 `patientId`는 그 노출을 줄인다.

`patientId`를 별도로 두면 위 문제 전부가 **속성 값 하나를 고치는 문제**로 축소된다. 두 MRN이 같은 사람으로 판명되면 `patientId` 노드 하나로 병합하고 `mrn` 값들만 정리하면 되며, 그 환자를 가리키던 6개 관계는 손대지 않아도 된다.

---

## 3. 시스템 간 매핑 관점: 그래도 `mrn`을 버리지 않는 이유

`patientId`가 있으니 `mrn`은 버려도 될까? 아니다. 원문 시나리오는 데이터가 **EHR, 스케줄링 시스템, 약국 DB, 청구 플랫폼**에 흩어져 있다고 명시한다. 온톨로지는 이들을 잇는 층이므로, 각 원천으로 되돌아갈 **왕복 티켓**이 반드시 필요하다.

```
   [ EHR ]        [ Scheduling ]      [ Pharmacy ]      [ Billing ]
      | MRN            | apptRef          | rxNumber        | memberNo
      v                v                  v                v
 ┌──────────────────────────────────────────────────────────────┐
 │                      Ontology (Patient)                      │
 │   patientId (identifier, 불변·내부 발급)                      │
 │   mrn        ← EHR로 되돌아가는 외부 키(속성으로 보존)         │
 │   dateOfBirth / bloodType / allergies                        │
 └──────────────────────────────────────────────────────────────┘
```

`mrn`이 속성으로 남아 있어서 가능한 일들:

- **파이프라인 조인 키** — EHR에서 새 임상 데이터를 적재할 때, 들어온 레코드의 MRN으로 기존 Patient 노드를 찾아 붙인다(upsert 시 lookup key).
- **역추적(traceability)** — 온톨로지 질의 결과에서 "이 환자의 원본 차트를 열어라"로 이어질 수 있다. 감사·임상 검증에서 필수.
- **엔티티 해석(identity resolution)** — MRN + 생년월일 + 이름 등을 매칭 근거로 삼아 여러 원천의 레코드를 하나의 `patientId`로 수렴시킨다. 실제 병원 네트워크에서 이 역할을 하는 것이 EMPI(Enterprise Master Patient Index)이며, 온톨로지의 `patientId`는 그 마스터 ID와 같은 위치에 있다.
- **상호운용성** — 외부 기관과 데이터를 주고받을 때 그쪽이 아는 언어(MRN)로 말할 수 있다.

정리하면 역할 분담은 이렇다.

| 용도 | 사용하는 키 |
|---|---|
| 그래프 내부 참조·관계 연결 | `patientId` |
| 질의 결과에서 환자 지목 (`RETURN p.patientId`) | `patientId` |
| 원천 시스템 조인·적재 매칭 | `mrn` |
| 외부 기관/사람과의 커뮤니케이션 | `mrn` |

---

## 4. 같은 온톨로지 안의 대조 사례: `rxNumber`

흥미로운 점은 이 온톨로지가 **모든 엔티티에 대리 키를 강제하지는 않는다**는 것이다.

| 엔티티 | Identifier | 성격 |
|---|---|---|
| Patient | `patientId` | 온톨로지 발급 대리 키 (`mrn`은 속성) |
| Provider | `providerId` | 온톨로지 발급 대리 키 (`licenseNumber`는 속성) |
| Appointment | `appointmentId` | 온톨로지 발급 대리 키 |
| Diagnosis | `diagnosisId` | 온톨로지 발급 대리 키 (`icdCode`는 분류 코드 속성) |
| Prescription | `rxNumber` | **약국 표준 식별자를 그대로 identifier로 채택** |

원문도 `rxNumber`를 "a pharmacy-standard identifier"라고 설명한다. 여기서 얻을 수 있는 판단 기준:

- 도메인 식별자가 **전역적으로 유일하고, 안정적이며, 발급 주체가 신뢰할 수 있고, 재사용/변경되지 않는다면** 그것을 그대로 온톨로지 식별자로 써도 된다(`rxNumber`).
- 반대로 **기관 지역적이고, 한 대상이 여러 개를 가질 수 있고, 병합·재발급 가능성이 있다면** 별도의 대리 키를 세우고 도메인 식별자는 속성으로 내린다(`mrn`).

또한 `icdCode`와의 구분도 같은 계열의 교훈이다. ICD 코드는 **개체(instance) 식별자가 아니라 분류(classification) 코드**다. 같은 `icdCode`를 가진 Diagnosis 인스턴스는 수천 건 존재할 수 있으므로 identifier가 될 수 없고, 상호운용을 위한 속성으로만 존재한다. "표준 코드가 붙어 있다 ≠ 식별자다"를 구분하는 감각이 필요하다.

---

## 5. 실무에서 따라오는 설계 디테일

- **`mrn`에 유일성 제약을 걸 것인가** — 걸고 싶은 마음이 들지만, 다기관 환경에서는 `(발급기관, mrn)` 조합이어야 유일해진다. 값 하나만으로 unique 제약을 걸면 통합 시점에 데이터 적재가 깨진다. 필요하면 `mrn`을 다중 값(또는 `MedicalRecordNumber` 별도 엔티티)으로 승격시키는 것이 정직한 모델링이다.
- **`mrn`이 optional인 이유** — 위 표에서 `mrn`은 identifier 표시가 없고 필수도 아니다. 신규 등록 환자나 EHR 미연동 원천에서 들어온 환자는 MRN이 아직 없을 수 있다. 필수 키였다면 그런 레코드를 아예 표현할 수 없다.
- **`patientId`는 절대 재사용하지 않는다** — 삭제된 환자의 ID를 새 환자에게 다시 부여하면, 과거 참조가 조용히 다른 사람을 가리키게 되어 가장 찾기 어려운 종류의 오류가 된다.
- **`patientId`에 의미를 심지 말 것** — `2024-CARDIO-0032`처럼 연도나 진료과를 인코딩하면 결국 "그 환자가 다른 과로 옮기면?"이라는 변경 압력이 다시 생긴다. 대리 키의 가치는 의미가 없다는 데서 나온다.

---

## 6. 한 문장 정리

`patientId`는 **온톨로지가 스스로 세계를 지목하는 방식**이고, `mrn`은 **다른 시스템이 같은 환자를 지목하던 방식을 잊지 않기 위한 기록**이다. 온톨로지는 자기 식별 체계의 안정성을 지키면서(대리 키), 외부와의 연결 통로를 속성으로 남긴다(자연 키 보존). 이것이 여러 원천 시스템 위에 놓이는 통합 층의 표준적인 식별자 설계다.

## 기억을 위한 연결고리

- "MRN은 병원이 준 번호, patientId는 온톨로지가 준 번호" — 발급 주체가 다르다.
- "관계를 걸 때는 patientId, EHR을 찾아갈 때는 mrn" — 쓰임새가 다르다.
- "mrn은 바뀔 수 있고 patientId는 안 바뀐다" — 안정성이 다르다.
- 대조 암기: **Patient는 대리 키(mrn을 속성으로 내림), Prescription은 자연 키(rxNumber를 그대로 씀).**
