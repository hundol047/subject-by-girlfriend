"""
프로젝트 설정값.
다른 질환/계통으로 바꾸고 싶으면 이 파일의 값만 수정하면 된다.
(단, 기사 검색 키워드나 SNOMED 매핑용 용어 사전(src/terminology.py)도 함께 바꿔야
 실제 분석 결과가 새 질환에 맞게 나온다.)
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# 6P - Placement (대상 계통 / 질환)
# ---------------------------------------------------------------------------
SYSTEM_KO = "심혈관계"
DISEASE_KO = "심부전"
DISEASE_EN = "Heart Failure"

# 기사 검색에 사용할 키워드 (필요 시 추가)
DISEASE_SEARCH_TERMS = ["heart failure", "congestive heart failure"]

# ---------------------------------------------------------------------------
# 1. 가상 EMR 생성
# ---------------------------------------------------------------------------
N_PATIENTS = 40
RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# 2. 임상 기사 수집
# ---------------------------------------------------------------------------
ARTICLE_TARGET_COUNT = 20
PUBMED_RETMAX = 12
MEDLINEPLUS_RETMAX = 8
WIKIPEDIA_TOPICS = [
    "Heart failure",
    "Congestive heart failure",
    "Cardiomyopathy",
    "Ejection fraction",
    "Natriuretic peptide",
    "Diuretic",
    "Beta blocker",
    "ACE inhibitor",
]

# ---------------------------------------------------------------------------
# 8. Pilot 검증
# ---------------------------------------------------------------------------
PILOT_SAMPLE_SIZE = 25

# ---------------------------------------------------------------------------
# 경로
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"

DATA_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

SYNTHETIC_EMR_CSV = DATA_DIR / "synthetic_emr.csv"
ARTICLES_CSV = DATA_DIR / "articles.csv"
SNOMED_MAPPING_CSV = DATA_DIR / "snomed_mapping.csv"

KEYWORD_FREQUENCY_CSV = RESULTS_DIR / "keyword_frequency.csv"
INTEGRATED_MAPPING_CSV = RESULTS_DIR / "integrated_mapping.csv"
PILOT_VALIDATION_CSV = RESULTS_DIR / "pilot_validation.csv"
