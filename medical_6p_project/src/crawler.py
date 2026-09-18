"""
2. 임상 기사(공개 웹 문서) 수집.

- Wikipedia REST API, PubMed(NCBI) E-utilities, MedlinePlus 검색 API 등
  "공식적으로 공개된 API" 만 사용한다. robots.txt 를 우회하는 스크래핑은 하지 않는다.
- 특정 사이트 하나에만 의존하지 않도록 여러 소스에서 나눠 수집한다.
- 각 소스 요청은 개별적으로 예외처리하며, 실패해도 나머지 소스로 계속 진행한다.
- 실행 환경에 외부 네트워크가 차단되어 있어 목표 개수(ARTICLE_TARGET_COUNT)를
  채우지 못한 경우에만, 파이프라인이 끝까지 동작하도록 아주 소규모의
  오프라인 대체 텍스트(직접 작성한 일반 교육용 요약, source="Offline_Fallback")로
  부족분을 채운다. 실제 인터넷이 연결된 환경에서는 이 대체 데이터 없이도
  목표 개수를 채울 수 있다.
"""

import datetime
import xml.etree.ElementTree as ET

import pandas as pd
import requests

import config

HEADERS = {"User-Agent": "medical-6p-student-project/1.0 (educational use)"}
TIMEOUT = 10


def fetch_wikipedia_articles(topics):
    """Wikipedia 공식 REST API(extracts)로 문서 요약을 가져온다."""
    articles = []
    for topic in topics:
        try:
            url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "prop": "extracts",
                "explaintext": 1,
                "titles": topic,
                "format": "json",
                "redirects": 1,
            }
            resp = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
            pages = resp.json().get("query", {}).get("pages", {})
            for page in pages.values():
                text = page.get("extract", "").strip()
                if len(text) < 50:
                    continue
                articles.append({
                    "title": page.get("title", topic),
                    "source": "Wikipedia",
                    "date": "",
                    "url": f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}",
                    "text": text,
                })
        except Exception as exc:
            print(f"    [경고] Wikipedia 수집 실패 ({topic}): {exc}")
    return articles


def fetch_pubmed_articles(query, retmax):
    """NCBI E-utilities(esearch + efetch)로 PubMed 초록을 가져온다."""
    articles = []
    try:
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        search_params = {"db": "pubmed", "term": query, "retmax": retmax, "retmode": "json"}
        resp = requests.get(search_url, params=search_params, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        pmids = resp.json().get("esearchresult", {}).get("idlist", [])
    except Exception as exc:
        print(f"    [경고] PubMed 검색 실패 ({query}): {exc}")
        return articles

    if not pmids:
        return articles

    try:
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        fetch_params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml", "rettype": "abstract"}
        resp = requests.get(fetch_url, params=fetch_params, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        for article in root.findall(".//PubmedArticle"):
            try:
                pmid = article.findtext(".//PMID", default="")
                title = article.findtext(".//ArticleTitle", default="").strip()
                abstract_parts = [
                    (node.text or "") for node in article.findall(".//AbstractText")
                ]
                text = " ".join(part.strip() for part in abstract_parts if part).strip()
                if not text:
                    continue
                year = article.findtext(".//PubDate/Year", default="")
                articles.append({
                    "title": title or f"PubMed article {pmid}",
                    "source": "PubMed",
                    "date": year,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    "text": text,
                })
            except Exception as exc:
                print(f"    [경고] PubMed 개별 레코드 파싱 실패: {exc}")
    except Exception as exc:
        print(f"    [경고] PubMed 본문 조회 실패 ({query}): {exc}")

    return articles


def fetch_medlineplus_articles(query, retmax):
    """MedlinePlus 공식 검색 웹서비스에서 건강 정보 topic 을 가져온다."""
    articles = []
    try:
        url = "https://wsearch.nlm.nih.gov/ws/query"
        params = {"db": "healthTopics", "term": query, "retmax": retmax}
        resp = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        for doc in root.findall(".//document"):
            title, url_, snippet = "", doc.get("url", ""), ""
            for content in doc.findall("content"):
                name = content.get("name", "")
                text = "".join(content.itertext()).strip()
                if name == "title":
                    title = text
                elif name in ("snippet", "FullSummary", "full-summary"):
                    snippet = snippet + " " + text if snippet else text
            if title and snippet and len(snippet) > 30:
                articles.append({
                    "title": title,
                    "source": "MedlinePlus",
                    "date": "",
                    "url": url_,
                    "text": snippet.strip(),
                })
    except Exception as exc:
        print(f"    [경고] MedlinePlus 수집 실패 ({query}): {exc}")
    return articles


# 네트워크가 차단된 환경에서 파이프라인을 끝까지 실행해보기 위한 최소한의
# 오프라인 대체 텍스트. 실제 웹에서 스크랩한 것이 아니라 직접 작성한
# 일반적인 심부전 교육 요약이며, source 를 "Offline_Fallback" 으로 명확히 구분한다.
OFFLINE_FALLBACK_TEXTS = [
    ("Heart failure overview",
     "Heart failure is a chronic condition in which the heart cannot pump enough blood "
     "to meet the body's needs. It is commonly classified as heart failure with reduced "
     "ejection fraction (HFrEF) or heart failure with preserved ejection fraction (HFpEF)."),
    ("Common symptoms of heart failure",
     "Typical symptoms of heart failure include dyspnea on exertion, orthopnea, "
     "paroxysmal nocturnal dyspnea, fatigue, leg edema, and rapid weight gain due to "
     "fluid retention."),
    ("Diagnostic workup",
     "Diagnostic evaluation of suspected heart failure usually includes echocardiography "
     "to measure ejection fraction, electrocardiogram, chest x-ray, and BNP or NT-proBNP "
     "blood testing."),
    ("Natriuretic peptide biomarkers",
     "BNP and NT-proBNP are natriuretic peptides released by the heart under wall stress "
     "and are used as blood biomarkers to support or exclude a diagnosis of heart failure."),
    ("Pharmacologic therapy classes",
     "Guideline-directed medical therapy for heart failure with reduced ejection fraction "
     "includes ACE inhibitors or ARNI, beta blockers, mineralocorticoid receptor "
     "antagonists such as spironolactone, and SGLT2 inhibitors."),
    ("Diuretics in heart failure",
     "Loop diuretics such as furosemide and torsemide are used to relieve congestion and "
     "reduce fluid overload symptoms such as leg edema and shortness of breath."),
    ("Beta blockers",
     "Beta blockers including carvedilol, metoprolol succinate, and bisoprolol reduce "
     "heart rate and myocardial oxygen demand and are part of standard heart failure "
     "therapy."),
    ("Digoxin use",
     "Digoxin may be used in selected patients with heart failure and atrial fibrillation "
     "to control heart rate and reduce hospitalization for symptomatic heart failure."),
    ("Device therapy",
     "Selected patients with heart failure with reduced ejection fraction may benefit "
     "from an implantable cardioverter defibrillator or cardiac resynchronization "
     "therapy to reduce arrhythmic risk and improve symptoms."),
    ("Comorbidities",
     "Hypertension, diabetes mellitus, coronary artery disease, atrial fibrillation, and "
     "chronic kidney disease are common comorbidities that both contribute to and "
     "complicate the management of heart failure."),
    ("Acute decompensated heart failure",
     "Acute decompensated heart failure presents with worsening dyspnea, orthopnea, and "
     "peripheral edema, and is typically managed with intravenous diuretics and "
     "close monitoring of renal function and electrolytes."),
    ("Lifestyle management",
     "Non-pharmacologic management of heart failure includes sodium restriction, fluid "
     "restriction in selected patients, daily weight monitoring, and cardiac "
     "rehabilitation."),
    ("Prognosis",
     "Heart failure is associated with significant morbidity and mortality, and "
     "prognosis is influenced by ejection fraction, comorbidities, and adherence to "
     "guideline-directed medical therapy."),
    ("NYHA functional classification",
     "The New York Heart Association functional classification grades heart failure "
     "symptom severity from class I (no limitation) to class IV (symptoms at rest), and "
     "is widely used to describe disease severity."),
    ("Coronary artery disease and heart failure",
     "Coronary artery disease and prior myocardial infarction are leading causes of "
     "heart failure with reduced ejection fraction due to loss of contractile "
     "myocardium."),
    ("Renal function monitoring",
     "Renal function and electrolytes, including creatinine, sodium, and potassium, "
     "are monitored closely in heart failure patients because diuretics and "
     "ACE inhibitors can affect kidney function."),
    ("Atrial fibrillation and heart failure",
     "Atrial fibrillation frequently coexists with heart failure, and rate or rhythm "
     "control strategies are chosen based on symptoms and left ventricular function."),
    ("SGLT2 inhibitors",
     "SGLT2 inhibitors such as empagliflozin and dapagliflozin have been shown to reduce "
     "hospitalization for heart failure across the spectrum of ejection fraction."),
    ("Chest x-ray findings",
     "Chest x-ray in heart failure may show cardiomegaly, pulmonary vascular congestion, "
     "and pleural effusion, supporting a clinical diagnosis of decompensated heart "
     "failure."),
    ("Echocardiography role",
     "Echocardiography is the primary imaging test used to estimate ejection fraction, "
     "assess valvular function, and classify heart failure as reduced or preserved "
     "ejection fraction."),
    ("Follow-up care",
     "Patients with heart failure require regular outpatient follow-up including weight "
     "monitoring, medication titration, and education about symptoms of "
     "decompensation such as increasing dyspnea or edema."),
    ("Epidemiology",
     "Heart failure prevalence increases with age and is a leading cause of "
     "hospitalization among older adults, often complicated by multiple chronic "
     "comorbidities."),
]


def build_offline_fallback(n_needed):
    today = datetime.date.today().isoformat()
    fallback = []
    for title, text in OFFLINE_FALLBACK_TEXTS[:n_needed]:
        fallback.append({
            "title": title,
            "source": "Offline_Fallback",
            "date": today,
            "url": "offline://no-network-fallback",
            "text": text,
        })
    return fallback


def collect_articles():
    """여러 공개 소스에서 기사를 모으고, 부족하면 오프라인 대체 텍스트로 채운다."""
    articles = []

    print("  - Wikipedia 수집 시도...")
    articles += fetch_wikipedia_articles(config.WIKIPEDIA_TOPICS)

    print("  - PubMed 수집 시도...")
    for term in config.DISEASE_SEARCH_TERMS:
        articles += fetch_pubmed_articles(term, config.PUBMED_RETMAX)

    print("  - MedlinePlus 수집 시도...")
    for term in config.DISEASE_SEARCH_TERMS:
        articles += fetch_medlineplus_articles(term, config.MEDLINEPLUS_RETMAX)

    df = pd.DataFrame(articles, columns=["title", "source", "date", "url", "text"])
    if not df.empty:
        df = df.drop_duplicates(subset=["text"]).reset_index(drop=True)

    n_collected = len(df)
    n_needed = max(0, config.ARTICLE_TARGET_COUNT - n_collected)

    if n_needed > 0:
        print(f"  - 실시간 수집 {n_collected}건 (목표 {config.ARTICLE_TARGET_COUNT}건). "
              f"부족분 {n_needed}건은 오프라인 대체 텍스트로 채웁니다 "
              f"(네트워크 차단 환경 대비).")
        fallback_df = pd.DataFrame(build_offline_fallback(n_needed))
        df = pd.concat([df, fallback_df], ignore_index=True)

    return df


def run():
    df = collect_articles()
    df.to_csv(config.ARTICLES_CSV, index=False, encoding="utf-8-sig")
    print(f"  - 기사 {len(df)}건 저장 완료 -> {config.ARTICLES_CSV}")
    print(f"    (소스 구성: {df['source'].value_counts().to_dict()})")
    return df


if __name__ == "__main__":
    run()
