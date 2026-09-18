"""
심부전(Heart Failure) 도메인 용어 사전.

CATEGORY_KEYWORDS
    텍스트(EMR/기사)에서 "이 카테고리의 의료 용어로 볼 수 있다"고 판단할 후보 목록.
    질환 / 증상 / 약물 / 검사 / 검사결과 / 치료 6개 카테고리로 구성.

SNOMED_REFERENCE
    실제로 공개적으로 널리 검증된(교과서/공식 예제 등에 반복적으로 등장하는)
    SNOMED CT concept id 만 모아둔 소규모 참조 테이블.
    -> 이 표에 없는 용어는 절대 임의의 concept id 를 만들어 붙이지 않는다.

SYNONYM_MAP
    표기가 다르지만 같은 개념을 가리키는 표현들을 SNOMED_REFERENCE 의 표준 용어로
    연결해주는 보조 사전 (완전히 같은 문자열은 아니므로 Partial 매핑에 사용).
"""

# mapping_status 와 무관하게, "실제 임상 개념" 카테고리 목록 (일반 상위 키워드는 제외).
CLINICAL_CATEGORIES = ["disease", "symptom", "medication", "test", "test_result", "treatment"]

CATEGORY_KEYWORDS = {
    "disease": [
        "heart failure",
        "congestive heart failure",
        "heart failure with reduced ejection fraction",
        "heart failure with preserved ejection fraction",
        "hypertension",
        "diabetes mellitus",
        "atrial fibrillation",
        "myocardial infarction",
        "coronary artery disease",
        "chronic kidney disease",
        "cardiomyopathy",
    ],
    "symptom": [
        "dyspnea",
        "shortness of breath",
        "orthopnea",
        "paroxysmal nocturnal dyspnea",
        "fatigue",
        "chest pain",
        "chest discomfort",
        "palpitations",
        "cough",
        "edema",
        "leg edema",
        "leg swelling",
        "peripheral edema",
        "weight gain",
        "decreased appetite",
    ],
    "medication": [
        "furosemide",
        "lisinopril",
        "carvedilol",
        "spironolactone",
        "digoxin",
        "metoprolol",
        "sacubitril",
        "valsartan",
        "sacubitril/valsartan",
        "enalapril",
        "losartan",
        "bisoprolol",
        "empagliflozin",
        "dapagliflozin",
        "torsemide",
        "hydrochlorothiazide",
    ],
    "test": [
        "echocardiography",
        "echocardiogram",
        "electrocardiogram",
        "ecg",
        "ekg",
        "chest x-ray",
        "chest radiograph",
        "cardiac catheterization",
        "stress test",
    ],
    "test_result": [
        "ejection fraction",
        "bnp",
        "nt-probnp",
        "b-type natriuretic peptide",
        "creatinine",
        "sodium",
        "potassium",
        "troponin",
        "glomerular filtration rate",
        "gfr",
    ],
    "treatment": [
        "ace inhibitor",
        "angiotensin receptor blocker",
        "arb",
        "arni",
        "beta blocker",
        "beta-blocker",
        "mineralocorticoid receptor antagonist",
        "diuretic therapy",
        "diuretic",
        "sglt2 inhibitor",
        "cardiac resynchronization therapy",
        "implantable cardioverter defibrillator",
        "lifestyle modification",
        "sodium restriction",
        "fluid restriction",
        "cardiac rehabilitation",
    ],
}

# 공개적으로 널리 인용되는 SNOMED CT concept id 만 포함 (자체 생성 금지 원칙 준수).
# term 은 소문자 정규화된 표준 표기.
SNOMED_REFERENCE = [
    {"term": "heart failure", "category": "disease",
     "snomed_concept": "Heart failure (disorder)", "snomed_concept_id": "84114007"},
    {"term": "congestive heart failure", "category": "disease",
     "snomed_concept": "Congestive heart failure (disorder)", "snomed_concept_id": "42343007"},
    {"term": "hypertension", "category": "disease",
     "snomed_concept": "Hypertension (disorder)", "snomed_concept_id": "38341003"},
    {"term": "diabetes mellitus", "category": "disease",
     "snomed_concept": "Diabetes mellitus (disorder)", "snomed_concept_id": "73211009"},
    {"term": "atrial fibrillation", "category": "disease",
     "snomed_concept": "Atrial fibrillation (disorder)", "snomed_concept_id": "49436004"},
    {"term": "myocardial infarction", "category": "disease",
     "snomed_concept": "Myocardial infarction (disorder)", "snomed_concept_id": "22298006"},
    {"term": "coronary artery disease", "category": "disease",
     "snomed_concept": "Coronary arteriosclerosis (disorder)", "snomed_concept_id": "53741008"},
    {"term": "chronic kidney disease", "category": "disease",
     "snomed_concept": "Chronic kidney disease (disorder)", "snomed_concept_id": "709044004"},

    {"term": "dyspnea", "category": "symptom",
     "snomed_concept": "Dyspnea (finding)", "snomed_concept_id": "267036007"},
    {"term": "orthopnea", "category": "symptom",
     "snomed_concept": "Orthopnea (finding)", "snomed_concept_id": "86290005"},
    {"term": "fatigue", "category": "symptom",
     "snomed_concept": "Fatigue (finding)", "snomed_concept_id": "84229001"},
    {"term": "chest pain", "category": "symptom",
     "snomed_concept": "Chest pain (finding)", "snomed_concept_id": "29857009"},
    {"term": "palpitations", "category": "symptom",
     "snomed_concept": "Palpitations (finding)", "snomed_concept_id": "80313002"},
    {"term": "cough", "category": "symptom",
     "snomed_concept": "Cough (finding)", "snomed_concept_id": "49727002"},
    {"term": "edema", "category": "symptom",
     "snomed_concept": "Edema (finding)", "snomed_concept_id": "267038008"},

    {"term": "furosemide", "category": "medication",
     "snomed_concept": "Furosemide (substance)", "snomed_concept_id": "387475002"},
    {"term": "lisinopril", "category": "medication",
     "snomed_concept": "Lisinopril (substance)", "snomed_concept_id": "386872008"},
    {"term": "carvedilol", "category": "medication",
     "snomed_concept": "Carvedilol (substance)", "snomed_concept_id": "386836001"},
    {"term": "spironolactone", "category": "medication",
     "snomed_concept": "Spironolactone (substance)", "snomed_concept_id": "387078006"},
    {"term": "digoxin", "category": "medication",
     "snomed_concept": "Digoxin (substance)", "snomed_concept_id": "387106007"},
    {"term": "metoprolol", "category": "medication",
     "snomed_concept": "Metoprolol (substance)", "snomed_concept_id": "373492002"},

    {"term": "echocardiography", "category": "test",
     "snomed_concept": "Echocardiography (procedure)", "snomed_concept_id": "40701008"},
    {"term": "electrocardiogram", "category": "test",
     "snomed_concept": "Electrocardiographic procedure (procedure)", "snomed_concept_id": "29303009"},
    {"term": "chest x-ray", "category": "test",
     "snomed_concept": "Plain chest X-ray (procedure)", "snomed_concept_id": "399208008"},

    {"term": "ejection fraction", "category": "test_result",
     "snomed_concept": "Ejection fraction (observable entity)", "snomed_concept_id": "250908004"},
]

# 완전히 같은 문자열은 아니지만 같은 개념으로 볼 수 있는 표현 -> Partial 매핑 후보
SYNONYM_MAP = {
    "shortness of breath": "dyspnea",
    "sob": "dyspnea",
    "leg edema": "edema",
    "leg swelling": "edema",
    "peripheral edema": "edema",
    "swelling": "edema",
    "ecg": "electrocardiogram",
    "ekg": "electrocardiogram",
    "chest radiograph": "chest x-ray",
    "chf": "congestive heart failure",
    "heart failure with reduced ejection fraction": "heart failure",
    "heart failure with preserved ejection fraction": "heart failure",
    "cardiomyopathy": "heart failure",
}
