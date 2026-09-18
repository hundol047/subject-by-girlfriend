# 심혈관계(심부전) 6P 의료데이터 분석 프로젝트

대학 과제용 프로젝트입니다. **가상(synthetic) EMR 생성 → 임상 기사 수집 → 텍스트
마이닝 → SNOMED CT 후보 매핑 → Pilot 검증**까지 이어지는 간단한 파이프라인을
`python main.py` 한 번으로 실행합니다.

- 웹앱/React/FastAPI/DB 없음 (순수 Python 스크립트)
- **실제 환자 데이터는 전혀 사용하지 않으며, 모든 EMR은 코드로 생성한 가상 데이터입니다.**

## 1. 프로젝트 목적

심혈관계 질환 중 **심부전(Heart Failure)** 을 대상으로, (1) 가상 EMR과 (2) 공개
임상 문서에서 각각 등장하는 의료 용어를 비교 분석하고, (3) 이를 SNOMED CT
개념과 후보 매핑한 뒤, (4) 일부 매핑 결과를 사람이 직접 검증하는 과정을
학생이 이해하기 쉬운 수준으로 구현한 것입니다.

## 2. 설치 방법 (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. 실행 방법

```powershell
python main.py
```

한 번 실행하면 `data/`, `results/` 폴더에 아래 산출물이 모두 생성됩니다.

## 4. 파일 구조

```
medical_6p_project/
  data/
    synthetic_emr.csv       # 가상 EMR (30~50명)
    articles.csv            # 수집된 임상 기사/문서
    snomed_mapping.csv       # 용어 -> SNOMED CT 후보 매핑
  src/
    generate_emr.py          # 1. 가상 EMR 생성
    crawler.py                # 2. 임상 기사 수집 (+오프라인 대체)
    text_mining.py             # 3~5. 전처리 + 키워드/TF-IDF + 용어 추출
    snomed_mapper.py            # 6~7. SNOMED 후보 매핑 + EMR/기사 통합
    validate_mapping.py          # 8. Pilot 검증 표본/정확도 계산
    visualize.py                  # 9. 시각화 PNG 생성
    terminology.py                 # 용어 사전 + SNOMED 참조표 (공용)
  results/
    keyword_frequency.csv          # EMR/기사 Top20 키워드 + 공통/전용 + TF-IDF
    integrated_mapping.csv          # 용어별 EMR/기사 빈도 + SNOMED 매핑 통합
    pilot_validation.csv             # Pilot 검증용 표본 (사람이 채점)
    summary.txt                       # 발표용 결과 요약 (자동 생성)
    *.png                              # 키워드/매핑 상태 시각화
  config.py                           # 질환/계통 등 설정값 (여기만 바꾸면 됨)
  main.py                              # 전체 파이프라인 실행 진입점
  requirements.txt
  README.md
```

## 5. 분석 흐름

1. **가상 EMR 생성** (`generate_emr.py`): `random` 모듈로 40명의 가상 환자
   레코드를 생성합니다. 심부전에 맞는 진단명(HFrEF/HFpEF/CHF/급성 대상부전),
   증상(호흡곤란, 부종, 피로 등), 검사수치(EF, BNP, Creatinine 등), 약물
   (Furosemide, Carvedilol 등)을 사용합니다.
2. **임상 기사 수집** (`crawler.py`): Wikipedia REST API, PubMed(NCBI)
   E-utilities, MedlinePlus 검색 API 등 **공식 공개 API만** 사용해 심부전
   관련 문서를 모읍니다. 사이트 하나에 의존하지 않도록 여러 소스를 나눠
   호출하며, 각 요청은 개별적으로 예외처리합니다. 네트워크가 막혀 있거나
   목표 개수(기본 20건)를 채우지 못하면, 직접 작성한 소규모 오프라인
   교육용 요약(`source = Offline_Fallback`)으로 부족분만 채워 파이프라인이
   끝까지 실행되도록 합니다.
3. **텍스트 전처리 + 마이닝** (`text_mining.py`): 공백/특수문자 정리, 중복
   텍스트 제거, 불용어 제거를 하되 `%`, `/`, `-`, 숫자 등 의료 수치·단위는
   보존합니다. EMR/기사 각각 Top20 키워드, 공통/EMR전용/기사전용 키워드,
   TF-IDF 점수를 계산해 `keyword_frequency.csv`로 저장합니다. 동시에
   질환/증상/약물/검사/검사결과/치료 6개 카테고리 사전으로 후보 의료 용어를
   추출합니다.
4. **SNOMED CT 후보 매핑** (`snomed_mapper.py`): 추출된 용어를 소규모 SNOMED
   참조표(`terminology.py`)와 대조합니다. 이 자동 매핑은 어디까지나
   **candidate mapping(후보 매핑)** 수준이며, concept id를 추측하거나 임의로
   만들지 않습니다. **실제로 공개적으로 검증되지 않은 concept id는 항상
   `UNVERIFIED`로 남기고, 최종 확인은 사람(Pilot 검증)이 담당합니다.**
   - `Exact`: 표준 표기와 완전히 동일
   - `Partial`: 동의어/유사 문자열로 연결된 후보
   - `Unverified`: 의료 용어 사전에는 있지만 참조표에 없음
   - `No Match`: 의료 용어로도 인식되지 않음 (일반 상위 키워드 등)
5. **EMR + 기사 통합** (`snomed_mapper.py`): 용어별 EMR/기사 빈도와 SNOMED
   매핑 결과를 합쳐 `integrated_mapping.csv`를 만듭니다.
6. **Pilot 검증** (`validate_mapping.py`): **일반 단어가 아닌 실제 임상 개념
   (질환/증상/약물/검사/검사결과/치료)만** 대상으로, 빈도 상위 절반 + 무작위
   절반을 합쳐 20~25개 표본을 뽑아 `pilot_validation.csv`를 생성합니다.
   컬럼은 `original_term, normalized_term, snomed_concept, snomed_concept_id,
   mapping_status, human_judgment, review_note`이며 `human_judgment`,
   `review_note`는 비워둡니다. 사람이 각 행의 `human_judgment`에
   `Correct`/`Incorrect`/`Uncertain`을 입력한 뒤 `pilot_validation_stats()`를
   다시 실행하면 `total_reviewed`, `correct`, `incorrect`, `uncertain`과 함께
   **Pilot terminology mapping accuracy** (= correct / total_reviewed × 100)를
   계산합니다. 아무도 채점하지 않았으면 정확도를 임의로 계산하지 않고
   `Manual validation pending`을 출력합니다.
   ※ 이는 "의료 AI 정확도"가 아니라 사람이 표본을 검토한 결과입니다.
7. **시각화 + 요약** (`visualize.py`, `main.py`): EMR/기사 키워드 Top15,
   EMR-기사 공통 키워드 비교, SNOMED 매핑 상태 분포를 PNG로 저장하고,
   환자 수/기사 수/추출 용어 수/매핑 상태 분포/Pilot 결과를 모아
   `results/summary.txt`에 발표용 요약으로 저장합니다.

## 6. 결과 파일 설명

| 파일 | 설명 |
|---|---|
| `data/synthetic_emr.csv` | 가상 환자 레코드 (patient_id, age, sex, chief_complaint, diagnosis, past_history, medications, allergy, symptoms, lab_results, clinical_note) |
| `data/articles.csv` | 수집된 임상 문서 (title, source, date, url, text) |
| `data/snomed_mapping.csv` | 용어별 SNOMED CT 후보 매핑 (original_term, normalized_term, english_term, snomed_concept, snomed_concept_id, source_type, mapping_status) |
| `results/keyword_frequency.csv` | EMR/기사 키워드 빈도, 공통/전용 구분, TF-IDF 점수 |
| `results/integrated_mapping.csv` | 용어별 EMR/기사/전체 빈도 + SNOMED 매핑 결과 |
| `results/pilot_validation.csv` | Pilot 검증 표본 (original_term, normalized_term, snomed_concept, snomed_concept_id, mapping_status, human_judgment, review_note). 실제 임상 개념만 포함하며 human_judgment는 사람이 채움 |
| `results/summary.txt` | 발표용 결과 요약 (환자 수, 기사 수, 추출 용어 수, 매핑 상태 분포, Pilot 결과) |
| `results/*.png` | 키워드 Top15, 공통 키워드, SNOMED 매핑 상태 분포 그래프 |

## 7. 질환/계통 변경 방법

`config.py`의 `SYSTEM_KO`, `DISEASE_KO`, `DISEASE_EN`, `DISEASE_SEARCH_TERMS`,
`WIKIPEDIA_TOPICS`만 바꾸면 됩니다. 단, 실제 분석 결과가 새 질환에 맞게
나오려면 `src/terminology.py`의 `CATEGORY_KEYWORDS`(증상/약물/검사 등 후보
용어)와 `SNOMED_REFERENCE`(검증된 SNOMED 코드)도 새 질환에 맞게 채워야
합니다.

## 8. 한계 (Limitations)

- **완전한 SNOMED CT 매핑이 아닙니다.** `SNOMED_REFERENCE`는 공개적으로 널리
  확인 가능한 극소수(약 24개) 코드만 담은 참조표이며, 실제 UMLS/SNOMED
  terminology 서버 조회가 아닙니다. 표에 없는 용어는 모두 `UNVERIFIED`로
  남기며, 이는 "확인 안 됨"을 뜻하지 "없음"을 뜻하지 않습니다.
- **의료 용어 추출은 NLP 모델이 아니라 사전(키워드) 기반**입니다. 사전에
  없는 표현(오탈자, 축약어 등)은 놓칠 수 있습니다.
- **임상 기사 수집은 네트워크 환경에 의존**합니다. 인터넷이 차단된
  환경(예: 일부 샌드박스)에서는 Wikipedia/PubMed/MedlinePlus 호출이 모두
  실패하고, 직접 작성한 오프라인 대체 텍스트로 대체되어 실행됩니다.
  (`data/articles.csv`의 `source` 열이 `Offline_Fallback`이면 실시간 수집이
  아니라 대체 텍스트임을 뜻합니다.) 인터넷이 연결된 일반 PC에서 실행하면
  실제 공개 문서가 수집됩니다.
- **자동 SNOMED 매핑은 candidate mapping(후보 매핑)일 뿐입니다.** 사람이
  Pilot 검증으로 확인하기 전까지는 최종 정답으로 취급하지 않습니다.
- **Pilot 검증은 사람이 직접 채점해야 의미가 있습니다.** `human_judgment`
  열을 비워둔 채로는 정확도가 계산되지 않으며(`Manual validation pending`으로
  표시), 임의로 자동 채점하지 않습니다.
- 데이터 규모(환자 40명, 기사 20여 건)가 작아 통계적으로 일반화할 수 있는
  결과가 아니라, 파이프라인 자체를 보여주기 위한 교육용 예시입니다.

## 6P 요약

| 항목 | 내용 |
|---|---|
| **Placement** | 심혈관계 |
| **Problem** | 심부전 환자의 주요 임상정보가 EMR과 공개 임상정보에서 어떻게 표현되는지 분석하고 의료용어 표준화 가능성을 확인 |
| **Project** | Synthetic EMR + 공개 임상기사 + 텍스트 마이닝 + SNOMED CT 후보 매핑 |
| **Place** | 가상 EMR 및 공개 의료정보 |
| **Pilot** | 주요 의료용어 20~25개를 사람이 직접 검증 |
| **Performance** | 키워드 빈도, EMR/기사 공통 개념, SNOMED 매핑 상태, Pilot terminology mapping accuracy |
