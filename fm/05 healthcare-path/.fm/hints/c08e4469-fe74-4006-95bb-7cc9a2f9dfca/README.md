# Diagnosis의 `icdCode` 속성이 중요한 이유

## 한 줄 정답

`icdCode`는 **전 세계적으로 표준화된 코딩 체계(ICD)** 를 온톨로지 안으로 끌어들인다. 덕분에 이 온톨로지는 보험, 청구(billing), 연구 시스템과 **상호운용(interoperability)** 이 가능해진다. 같은 코드가 EHR·보험 청구·임상시험·공중보건 통계에서 **동일한 상태를 의미**하게 된다.

---

## 1. 원문에서의 근거

학습 경로 `Diagnoses` 단계의 Diagnosis 엔티티 정의는 이렇다.

| Property | Type | Identifier? |
|---|---|---|
| `diagnosisId` | string | ✓ |
| `icdCode` | string | |
| `description` | string | |
| `severity` | string | |
| `diagnosedDate` | date | |

원문 설명:

> The `icdCode` property holds the standardized ICD (International Classification of Diseases) code — a globally recognized coding system. This makes the ontology interoperable with insurance, billing, and research systems.

그리고 `What we learned` 및 전체 경로 요약에서도 같은 메시지가 반복된다.

> - **Standardized codes** (ICD) make ontologies interoperable with external systems
> - 2. **Standardized codes** (ICD, Rx) enable cross-system interoperability

즉 이 카드는 "속성 하나 추가"의 문제가 아니라, **온톨로지가 외부 세계와 어떻게 접속하는가**에 관한 설계 원리를 묻고 있다.

여기서 중요한 대비 지점이 하나 있다. Diagnosis에는 이미 식별자 `diagnosisId`가 있다.

- `diagnosisId` — **내부(local) 식별자**. "이 병원 시스템의 이 진단 레코드" 하나를 가리킨다. 같은 당뇨 진단이 100명에게 내려지면 `diagnosisId`는 100개다.
- `icdCode` — **외부(global) 분류 코드**. "이 진단이 어떤 종류의 상태인가"를 전 세계 공통 어휘로 말한다. 당뇨 100건 모두 같은 ICD 코드를 갖는다.

이 둘은 경쟁 관계가 아니라 **역할이 다른 두 개의 키**다. 내부 키는 레코드를 유일하게 만들고, 외부 코드는 레코드를 **집계·비교·교환 가능**하게 만든다.

---

## 2. ICD란 무엇인가 — WHO 관리 체계

**ICD = International Classification of Diseases** (국제질병분류).

- **관리 주체**: WHO(세계보건기구). 회원국이 세계보건총회(World Health Assembly)에서 개정안을 승인한다. 즉 ICD는 어느 벤더의 사유 코드가 아니라 **국제 조약 수준의 공적 표준**이다.
- **법적 위상**: WHO 헌장에 따라 회원국은 사망·질병 통계를 ICD로 보고할 의무를 진다. 그래서 각국 사망원인 통계, 감염병 통계, 국제 질병 부담(Global Burden of Disease) 연구가 서로 비교 가능하다.
- **개정 이력**: ICD-9 → **ICD-10**(1990년 승인, 1994년부터 사용) → **ICD-11**(2019년 WHA 승인, **2022년 1월 1일 발효**).
- **지역 변형(modification)**: 국가별 임상 확장판이 존재한다.
  - 미국: **ICD-10-CM**(진단, 최대 7자리, 약 7만여 코드) + **ICD-10-PCS**(시술). WHO 원본 ICD-10의 3~4자리 약 1.4만 코드보다 훨씬 세분화되어 있다.
  - 한국: **KCD**(한국표준질병·사인분류). ICD-10을 기반으로 통계청이 고시하며 KCD-8(2021년 시행)이 사용된다. 건강보험 청구가 이 코드로 이루어진다.
  - 이 "국제 원본 + 국가별 확장" 구조 자체가, 온톨로지에서 코드 속성을 다룰 때 **어떤 코드 체계(system)의 코드인지**를 함께 관리해야 하는 이유다(→ 6장).

### ICD-10 코드 구조

형식: **영문자 1자 + 숫자 2자**(3자 카테고리) → 소수점 이하로 세분.

```
E   11        .9
│   │          └─ 세부 분류 (합병증 유무, 부위, 급성/만성 등)
│   └─ 카테고리 (질환군)
└─ 챕터 (E00–E89 = 내분비·영양·대사 질환)
```

실제 예시:

| 코드 | 의미 |
|---|---|
| `E11` | 2형 당뇨병 (Type 2 diabetes mellitus) |
| `E11.9` | 2형 당뇨병, 합병증 없음 |
| `E11.21` | 2형 당뇨병, 당뇨병성 신병증 동반 (ICD-10-CM) |
| `E10` | 1형 당뇨병 |
| `I10` | 본태성(원발성) 고혈압 |
| `I21.9` | 급성 심근경색, 상세불명 |
| `J45.909` | 천식, 합병증 없음, 상세불명 (ICD-10-CM) |
| `F32.1` | 중등도 우울 에피소드 |

원문 예제 질의가 "Which patients have been diagnosed with diabetes?"였다는 점을 떠올려 보자. `description` 문자열에 `"Diabetes"`, `"DM type II"`, `"T2DM"`, `"당뇨"` 가 섞여 들어오면 이 질의는 신뢰할 수 없다. 반면 `icdCode LIKE 'E11%'` 는 **표기 변형과 무관하게** 정확히 동작한다. 게다가 `E10`(1형)까지 포함하고 싶다면 `E10–E14` 범위로 확장하면 된다 — **코드의 계층 구조가 질의의 계층 구조가 된다.**

### ICD-11의 달라진 점 (온톨로지 학습자에게 특히 흥미로운 부분)

ICD-11은 사실상 **온톨로지로 재설계된 ICD**다.

- **Foundation Component**: 다중 부모(multi-parent)를 허용하는 개념 네트워크. 하나의 개념이 "감염성 질환"이면서 동시에 "호흡기 질환"일 수 있다. 여기서 특정 목적용 **linearization**(예: 통계용 MMS)을 뽑아낸다. 온톨로지의 "그래프 → 뷰" 구조와 정확히 같은 아이디어다.
- **URI 기반 식별자**: 각 개체가 `http://id.who.int/icd/entity/...` 형태의 영속 식별자를 가진다. RDF/OWL 온톨로지에서 바로 참조할 수 있다.
- **Stem code + Extension code (postcoordination)**: 미리 조합된 거대 코드 목록 대신, 기본 코드에 확장 코드를 조합해 표현한다.
  - 2형 당뇨병 = **`5A11`** (챕터 5 = 내분비·영양·대사). ICD-10의 `E11`에 대응.
  - 합병증 등은 하위/확장으로 표현: `5A11.1`(신병증 동반), `5A11.3`(망막병증 동반) 등.
  - 참고: ICD-11은 숫자 `1`/`0`과 혼동을 막기 위해 코드에 문자 `I`, `O`를 쓰지 않는다.
- **API 제공**: WHO가 공식 ICD API를 제공하므로, 온톨로지의 `icdCode` 값을 런타임에 검증하거나 사람이 읽을 라벨로 확장할 수 있다.

---

## 3. "상호운용성"이 구체적으로 무엇을 벌어주는가

원문이 말한 "insurance, billing, research systems"를 실제 시나리오로 풀면 이렇다. 이 학습 경로의 데이터가 "EHR, scheduling systems, pharmacy databases, and billing platforms"에 흩어져 있다는 설정을 기억하자.

| 수요자 | `icdCode` 없이는 | `icdCode` 있으면 |
|---|---|---|
| **보험/청구** | 청구서에 코드가 없어 심사 불가 → 지급 거절. 청구 코드를 사람이 다시 붙여야 함 | 진단 코드가 그대로 청구 코드가 되어 자동 청구·심사 |
| **EHR 간 전송(의뢰/회송)** | 상대 병원이 자유 텍스트를 재해석해야 함 | 코드가 그대로 의미를 전달. FHIR `Condition.code`에 매핑 |
| **임상시험 대상자 선별** | "당뇨 환자 찾기"를 텍스트 매칭으로 시도 → 누락/오포함 | `E11%` 코드 범위로 코호트 정의. 다기관 시험에서도 동일 기준 |
| **공중보건·역학** | 병원마다 집계 기준이 달라 합산 불가 | 국가/WHO 통계에 그대로 롤업. 국제 비교 가능 |
| **품질지표·수가 산정** | 위험도 보정(risk adjustment) 불가 | 코드 기반 중증도·동반질환 보정(Charlson 등) 가능 |
| **의사결정 지원** | 규칙을 텍스트로 작성 → 취약 | 코드 기반 알림/금기 규칙 |

핵심 통찰: **`icdCode`는 온톨로지의 조인 키(join key)를 조직 경계 밖으로 확장한다.** 내부 ID는 우리 시스템 안에서만 유효하지만, ICD 코드는 우리가 통제하지 않는 시스템과도 조인할 수 있는 키다. 온톨로지의 가치는 "흩어진 데이터를 연결하는 것"인데, `icdCode`는 그 연결 범위를 **회사 밖까지** 넓혀준다.

부수 효과로 원문의 다른 요소들과도 맞물린다. `severity` 속성은 위험 계층화(risk stratification)에 쓰이는데, ICD 코드와 결합되면 "심장내과 의사가 내린 중증 진단" 같은 질의가 표준 코드 기반으로 재현 가능해진다. Prescription 단계에서 등장하는 Rx 번호도 같은 원리다 — 표준 코드가 각 도메인의 접속 단자 역할을 한다.

---

## 4. SNOMED CT와의 차이 — "분류(classification)" vs "용어체계(terminology)"

`icdCode`를 이해하려면 ICD가 **무엇을 위한 도구가 아닌지**도 알아야 한다.

| 축 | **ICD-10/11** | **SNOMED CT** |
|---|---|---|
| 성격 | **분류(classification)** — 모든 사례를 상호배타적 범주에 배정 | **참조 용어체계(reference terminology)** — 임상 개념 그 자체를 표현 |
| 관리 주체 | WHO | SNOMED International (구 IHTSDO) |
| 규모 | ICD-10 약 1.4만(WHO), ICD-10-CM 약 7만 | 활성 개념 약 35만 이상 |
| 계층 | 단일 계층(mono-hierarchy)이 기본 | **다중 계층(poly-hierarchy)**, 기술논리(DL) 기반 정의 |
| 목적 | 통계, 역학, **청구·수가**, 사망원인 보고 | **EHR 진료 기록**, 임상 의사결정 지원, 상세 표현 |
| 표현력 | 범주로 뭉갠다("기타/상세불명"이 많음) | 속성 조합으로 정밀 표현(부위·시기·중증도 등) |
| 전형적 사용 지점 | 진료 후 코딩·청구·보고 | 진료 시점(point of care) 입력 |

한 문장 요약: **SNOMED CT는 "무엇을 관찰했는가"를 정밀하게 적기 위한 것이고, ICD는 "그것을 어떻게 세고 청구할 것인가"를 위한 것이다.**

그래서 현실 시스템은 보통 **둘 다** 쓴다. 진료 기록은 SNOMED CT로 남기고, 청구·통계로 나갈 때 ICD로 **매핑**한다(SNOMED International이 공식 ICD-10 매핑 셋을 배포한다). 이 매핑은 대체로 **다대일(many-to-1)** 이라 정보가 줄어드는 방향이며, 역방향(ICD → SNOMED)은 손실 때문에 일반적으로 무손실 복원이 불가능하다.

이 학습 경로가 `icdCode` 하나만 둔 것은 입문용 단순화다. 실무 온톨로지라면 Diagnosis에 `snomedCode`, `icdCode`, (미국이면) 시술용 `cptCode`를 **함께** 두거나, 아예 코드를 별도 엔티티로 승격시킨다(→ 6장).

### 함께 알아두면 좋은 이웃 표준

| 표준 | 대상 도메인 | 이 학습 경로와의 연결 |
|---|---|---|
| **ICD** | 진단·질병 | `Diagnosis.icdCode` |
| **SNOMED CT** | 임상 개념 전반 | 진단의 정밀 표현 |
| **LOINC** | 검사·측정 항목 | (이 경로엔 없음) Observation류 엔티티 |
| **RxNorm / ATC** | 의약품 | `Prescription` 단계의 약품 식별 |
| **CPT / HCPCS** | 시술·행위(미국 청구) | Procedure 엔티티 |
| **NPI / 면허번호** | 의료 제공자 | `Provider.licenseNumber` |
| **MRN** | 환자 (기관 내부 키) | `Patient` 식별자 — 단, 이건 **기관 로컬**이라 전역 표준이 아니다 |

MRN과 ICD의 대비가 이 카드의 요점을 잘 보여준다. 둘 다 "표준화된 식별자"로 원문에 나열되지만, MRN은 **한 기관 안에서만** 유효한 로컬 키이고 ICD는 **전 세계에서** 유효한 전역 어휘다. 상호운용성을 만들어주는 것은 후자다.

---

## 5. 원문 quiz 오답 선택지 분석

원문 퀴즈:

> **Q: Why is the ICD code property important for the Diagnosis entity?**

### ❌ "It makes the diagnosis identifier shorter" (진단 식별자를 더 짧게 만든다)

**틀린 이유**: 목적을 문자열 길이 최적화로 오독했다. 세 가지가 잘못됐다.

1. `icdCode`는 식별자가 아니다. Diagnosis의 식별자는 `diagnosisId`이고 표에 `Identifier? ✓`가 붙어 있다. `icdCode`에는 체크가 없다.
2. `icdCode`는 **식별자를 대체하지 않는다.** 같은 `E11`을 가진 진단 레코드가 수천 개 존재할 수 있으므로 `icdCode`만으로는 레코드를 유일하게 지목할 수 없다. 오히려 이것이 ICD 코드의 **본질적 성질**이다 — 여러 사례가 같은 코드를 공유해야 집계와 코호트 정의가 가능하다.
3. 짧다는 것은 코드 체계의 **부수적 특징**이지 존재 이유가 아니다. `Z98.890`처럼 길어질 수도 있고, ICD-11은 postcoordination으로 오히려 표현이 길어진다.

### ❌ "ICD codes are required by all ontology formats" (모든 온톨로지 포맷이 ICD 코드를 요구한다)

**틀린 이유**: 사실 자체가 거짓이다. OWL, RDF, 속성 그래프, Palantir Foundry의 객체 타입 등 어떤 온톨로지 포맷도 ICD 코드를 요구하지 않는다. 애초에 ICD는 **의료 도메인 전용 어휘**다. 커피 원두나 전자상거래 주문을 모델링하는 온톨로지에 ICD 코드가 있을 이유가 없다.

이 선택지가 놓친 구분: **포맷의 요구사항(formal requirement)** 과 **도메인 모델링의 좋은 관행(domain best practice)** 은 다른 층위다. `icdCode`가 중요한 것은 문법이 강제해서가 아니라, **의료 도메인의 데이터가 실제로 그 코드로 교환되기 때문**이다. 상호운용성은 스펙이 주는 게 아니라 **생태계 합의**가 주는 것이다.

### ❌ "It prevents duplicate diagnoses from being recorded" (중복 진단 기록을 방지한다)

**틀린 이유**: 정반대에 가깝다. ICD 코드는 **의도적으로 중복 공유되는 값**이다. 한 환자에게 `E11`이 여러 시점에 기록될 수도 있고(원문: "A patient can have multiple diagnoses over their medical history"), 서로 다른 환자 수만 명이 같은 `E11`을 갖는다. 중복 방지는 유일성 제약(uniqueness constraint)이나 식별자의 역할이며, 분류 코드의 역할이 아니다.

이 선택지는 "표준화 = 정규화 = 중복 제거"라는 직관에서 나온 함정이다. 표준화는 **의미를 일치시키는 것**이고, 중복 제거는 **레코드 수를 줄이는 것**이다. `icdCode` 덕분에 "이 두 레코드가 같은 상태를 말한다"는 사실을 *알 수는* 있지만, 그것이 곧 "하나를 지워야 한다"는 뜻은 아니다.

### ✅ 정답 "It provides a globally standardized coding system that enables interoperability with insurance, billing, and research systems"

원문 해설:

> ICD (International Classification of Diseases) codes are the universal standard for classifying medical conditions. Including them in the ontology enables interoperability — the same code means the same condition across EHRs, insurance claims, clinical trials, and public health systems.

**정답의 핵심 구조**: `globally standardized`(전역 표준) → `interoperability`(상호운용성) → 구체적 수요자 3종(보험/청구/연구). 오답 3개는 모두 **온톨로지 내부의 기술적 효용**(짧음, 포맷 요구, 중복 방지)을 말하고, 정답만이 **온톨로지 외부와의 접속**을 말한다. 이 카드에서 기억할 판별 기준이다.

---

## 6. 일반화: 온톨로지에서 통제 어휘(controlled vocabulary)를 참조하는 패턴

`icdCode`는 특정 사례가 아니라 **반복되는 설계 패턴**의 한 인스턴스다. 어떤 도메인이든 "외부에 이미 합의된 어휘가 있다면, 엔티티에 그 어휘의 코드를 참조하는 속성을 둔다."

- 전자상거래 → `Product.gtin` / `upc`, `Category.googleProductCategory`
- 금융 → `Security.isin` / `cusip`, `Institution.lei`, `Currency.iso4217`
- 물류 → `Port.unLocode`, `HsCode`
- 지리 → `Country.iso3166Alpha2`, `Place.geonamesId`
- 학술 → `Paper.doi`, `Person.orcid`
- 커피(이 저장소의 다른 경로) → 원산지 국가 코드, 품종 분류

### 구현 층위 3단계

**(1) 문자열 속성** — 이 학습 경로의 방식. `icdCode: string`.
- 장점: 가장 단순. 즉시 도입 가능.
- 단점: 코드 체계 버전, 사람이 읽을 라벨, 코드의 계층 구조를 담지 못한다. 유효하지 않은 코드가 들어와도 막을 수 없다.
- 입문 단계에서는 **옳은 선택**이다. 표준 코드를 붙인다는 행위 자체가 이미 대부분의 가치를 준다.

**(2) 코드 + 체계(system) 쌍** — 실무 최소 요건. `codeSystem: "ICD-10-CM"`, `codeSystemVersion: "2024"`, `code: "E11.9"`.
- ICD-10인지 ICD-10-CM인지 KCD-8인지 ICD-11인지에 따라 **같은 문자열이 다른 의미**가 될 수 있으므로 필요하다.
- HL7 **FHIR**의 `CodeableConcept`가 정확히 이 모양이다: `{ system, version, code, display }` + 원본 자유 텍스트 `text`. FHIR의 `Condition.code`가 이 학습 경로 `Diagnosis`의 실무 대응물이다.
- 여러 체계의 코드를 동시에 붙일 수 있다는 점도 중요하다(SNOMED + ICD 동시 기재).

**(3) 코드를 1급 엔티티로 승격** — 가장 표현력 높은 방식.
- `Diagnosis` --(classified_as)--> `DiagnosisCode` 관계를 만들고, `DiagnosisCode`에 `code`, `label`, `system`, `version`, 그리고 `broader`/`narrower` 자기참조 관계로 계층을 담는다.
- 그러면 "당뇨 계열 전체"를 코드 계층 순회로 질의할 수 있고, 라벨을 한 곳에서 관리하며, 코드 체계 개정도 버전 노드로 다룰 수 있다.
- RDF/OWL 세계에서는 **SKOS**가 이 패턴의 표준이다: `skos:Concept`, `skos:ConceptScheme`, `skos:prefLabel`, `skos:broader`, 그리고 체계 간 매핑용 `skos:exactMatch` / `closeMatch` / `broadMatch`. ICD ↔ SNOMED 매핑을 표현할 때 정확히 이 술어들을 쓴다.
- 트레이드오프: 엔티티 하나와 관계 하나가 늘어난다. 코드 계층 질의가 필요 없다면 과한 설계다.

### 이 패턴을 쓸 때 흔한 함정

- **버전 드리프트**: 코드 체계는 매년 개정된다. 코드가 삭제·분할·재정의되면 과거 데이터의 의미가 바뀐다. 그래서 `codeSystemVersion`과 `diagnosedDate`를 함께 보관하는 게 중요하다(원문의 `diagnosedDate`가 여기서 두 번째 역할을 한다).
- **원본 텍스트 폐기**: 코드는 손실 압축이다. 코딩 원본이 된 임상 서술(`description`)을 함께 남겨야 나중에 재코딩이 가능하다. 원문이 `icdCode`와 `description`을 **둘 다** 둔 이유가 이것이다.
- **청구 편향(billing bias)**: ICD 코드는 상당 부분 청구 목적으로 부여된다. 그래서 코드 분포가 임상 현실보다 **수가 구조**를 반영할 수 있다. 연구에 쓸 때 반드시 감안해야 하는 한계다.
- **"상세불명(unspecified)" 코드 남용**: `J45.909`처럼 `.9`로 끝나는 코드가 데이터의 큰 비중을 차지하는 경우가 흔하다. 코드가 있다고 해서 정보가 있다는 뜻은 아니다.
- **로컬 코드와의 혼용**: 병원 자체 코드를 `icdCode` 필드에 넣어버리면 상호운용성이라는 목적 자체가 무너진다. 표준 코드 필드와 로컬 코드 필드는 분리해야 한다.

---

## 7. 이 카드를 제대로 이해했는지 자문해 볼 질문

1. `diagnosisId`와 `icdCode`는 각각 어떤 질문에 답하는가? 왜 `icdCode`는 식별자가 아닌가?
2. `description`만 있고 `icdCode`가 없다면 "당뇨 환자 코호트 추출"은 왜 신뢰할 수 없게 되는가?
3. SNOMED CT가 ICD보다 표현력이 높은데, 왜 청구는 여전히 ICD로 하는가?
4. `icdCode: "E11.9"`라는 값 하나만 보고 그 의미를 확정할 수 없는 이유는? (힌트: ICD-10 vs ICD-10-CM vs KCD, 그리고 연도)
5. 이 저장소의 다른 학습 경로(전자상거래, 금융)에서 `icdCode`에 대응하는 속성은 무엇이겠는가?
6. 코드를 문자열 속성으로 두는 대신 별도 엔티티로 승격시키면 어떤 질의가 새로 가능해지는가?

---

## 참고 자료

- [WHO ICD-11 공식 브라우저](https://icd.who.int/browse11)
- [5A11 Type 2 diabetes mellitus — ICD-11 MMS](https://www.findacode.com/icd-11/code-119724091.html)
- [ICD-11: The future of diagnosis coding (Solventum/3M)](https://www.solventum.com/en-us/home/health-information-technology/resources-education/blog/2023/7/icd-11-the-future-of-diagnosis-coding/)
- [SNOMED International: 분류(ICD-10/ICPC)와 용어체계(SNOMED CT)의 차이](https://ihtsdo.freshdesk.com/support/solutions/articles/4000144252-what-is-the-difference-between-a-classification-such-as-icd-10-or-icpc-and-a-terminology-like-snomed-)
- [AHIMA: What's the Difference? SNOMED CT and ICD Systems are Suited for Different Purposes (PDF)](https://journal.ahima.org/Portals/0/archives/AHIMA%20files/What%E2%80%99s%20the%20Difference_%20SNOMED%20CT%20and%20ICD%20Systems%20are%20Suited%20for%20Different%20Purposes.pdf)
- [Medical coding systems explained: ICD-10-CM, CPT, SNOMED, and others (IMO Health)](https://www.imohealth.com/resources/medical-coding-systems-explained-icd-10-cm-cpt-snomed-and-others/)
- [ICD-11 Codes for Diabetes: Complete Guide with Examples (AMBCI)](https://ambci.org/medical-billing-and-coding-certification-blog/icd-11-codes-for-diabetes-mellitus-complete-guide-with-examples)
