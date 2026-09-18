"""
3. 텍스트 전처리 + 4. 텍스트 마이닝 + 5. 의료 용어(카테고리별) 추출.
"""

import re
from collections import Counter

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

import config
from terminology import CATEGORY_KEYWORDS

# 아주 흔한 영어 불용어 (nltk 다운로드 없이 오프라인에서도 동작하도록 직접 정의)
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "of", "to", "in", "on",
    "at", "by", "for", "with", "about", "against", "between", "into", "through", "during",
    "before", "after", "above", "below", "from", "up", "down", "out", "off", "over",
    "under", "again", "further", "once", "is", "am", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "having", "do", "does", "did", "doing", "will", "would",
    "should", "can", "could", "may", "might", "must", "shall", "this", "that", "these",
    "those", "it", "its", "as", "not", "no", "nor", "so", "than", "too", "very", "s", "t",
    "just", "also", "such", "each", "other", "some", "any", "all", "both", "more", "most",
    "which", "who", "whom", "what", "when", "where", "why", "how", "there", "here", "we",
    "you", "he", "she", "they", "his", "her", "their", "our", "your", "i", "my", "me",
    "him", "them", "us", "his", "one", "two", "three", "into",
}

# 키워드 빈도/TF-IDF 결과에서 제외할 "의미 없는 일반 단어" (질환명을 구성하는 단독
# 조각이나 서술용 상투어). "heart failure", "ejection fraction" 같은 복합 의료
# 용어 자체는 extract_medical_terms() 에서 별도로(구문 단위) 집계되므로 영향이 없다.
NOISE_WORDS = {
    "heart", "failure", "symptom", "symptoms", "patient", "patients", "presenting",
    "currently", "diagnosed", "medical", "history", "result", "results", "following",
    "include", "includes", "included", "associated", "note", "notes", "also", "using",
    "used", "well", "typically", "common", "commonly", "may", "often", "showing", "shows",
    "show", "ejection", "fraction", "level", "levels", "due", "present", "presents",
    "related", "based", "study", "studies", "review", "reviews", "article", "articles",
    "information", "data", "clinical", "adults", "population", "research", "known",
}

# 검사 단위처럼 그 자체로는 의미가 없는 토큰
UNIT_WORDS = {"mg", "ml", "mcg", "kg", "cm", "dl", "meq", "bpm", "mmhg", "ng"}
_UNIT_PATTERN = re.compile(r"^[a-z]{1,4}/[a-z0-9]{1,4}$")  # meq/l, mg/dl, pg/ml, ml/min 등
_NUMERIC_PATTERN = re.compile(r"^[\d.%\-]+$")  # 순수 숫자/퍼센트 토큰


def _is_noise_token(tok):
    if tok in NOISE_WORDS or tok in UNIT_WORDS:
        return True
    if _UNIT_PATTERN.match(tok) or _NUMERIC_PATTERN.match(tok):
        return True
    return False


def clean_text(text):
    """공백/특수문자 정리. 의료 수치·단위(%,/,-,.)는 보존한다."""
    if not isinstance(text, str):
        return ""
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9%./\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def remove_duplicate_texts(texts):
    """완전히 동일한 텍스트 중복을 제거하되 순서는 유지한다."""
    seen = set()
    unique = []
    for t in texts:
        key = t.strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(t)
    return unique


def tokenize(text):
    cleaned = clean_text(text).lower()
    tokens = cleaned.split(" ")
    result = []
    for tok in tokens:
        tok = tok.strip(".-")
        if not tok:
            continue
        if tok in STOPWORDS:
            continue
        if len(tok) < 3 and not any(ch.isdigit() for ch in tok):
            continue
        if _is_noise_token(tok):
            continue
        result.append(tok)
    return result


def word_frequency(token_lists, top_n=20):
    counter = Counter()
    for tokens in token_lists:
        counter.update(tokens)
    return counter.most_common(top_n)


def tfidf_scores(documents):
    """문서 리스트에 대해 평균 TF-IDF 점수를 단어별로 계산한다."""
    docs = [d for d in documents if d.strip()]
    if len(docs) < 2:
        return {}
    vectorizer = TfidfVectorizer(stop_words=list(STOPWORDS), min_df=1)
    matrix = vectorizer.fit_transform(docs)
    avg_scores = matrix.mean(axis=0).A1
    return dict(zip(vectorizer.get_feature_names_out(), avg_scores))


def extract_medical_terms(documents):
    """CATEGORY_KEYWORDS 사전을 이용해 카테고리별 후보 의료 용어 빈도를 센다.

    반환: {term: {"category": str, "count": int}}
    """
    joined = " ".join(clean_text(d).lower() for d in documents)
    results = {}
    for category, terms in CATEGORY_KEYWORDS.items():
        for term in terms:
            pattern = r"\b" + re.escape(term.lower()) + r"\b"
            count = len(re.findall(pattern, joined))
            if count > 0:
                results[term] = {"category": category, "count": count}
    return results


def build_emr_documents(emr_df):
    cols = ["chief_complaint", "diagnosis", "past_history", "medications",
            "symptoms", "lab_results", "clinical_note"]
    docs = []
    for _, row in emr_df.iterrows():
        docs.append(" ".join(str(row[c]) for c in cols if pd.notna(row[c])))
    return docs


def run_text_mining(emr_df, articles_df):
    """EMR/기사 텍스트를 분석하여 키워드 빈도 결과 DataFrame을 만들고 저장한다.

    반환: (keyword_df, emr_term_counts, article_term_counts)
    """
    emr_docs = remove_duplicate_texts(build_emr_documents(emr_df))
    article_docs = remove_duplicate_texts(articles_df["text"].dropna().tolist())

    emr_tokens = [tokenize(doc) for doc in emr_docs]
    article_tokens = [tokenize(doc) for doc in article_docs]

    emr_top20 = word_frequency(emr_tokens, 20)
    article_top20 = word_frequency(article_tokens, 20)

    emr_words = {w for w, _ in emr_top20}
    article_words = {w for w, _ in article_top20}
    common_words = emr_words & article_words

    emr_freq_map = dict(emr_top20)
    article_freq_map = dict(article_top20)

    tfidf_emr = tfidf_scores(emr_docs)
    tfidf_article = tfidf_scores(article_docs)

    all_keywords = sorted(emr_words | article_words)
    rows = []
    for kw in all_keywords:
        if kw in common_words:
            category = "common"
        elif kw in emr_words:
            category = "emr_only"
        else:
            category = "article_only"
        rows.append({
            "keyword": kw,
            "emr_frequency": emr_freq_map.get(kw, 0),
            "article_frequency": article_freq_map.get(kw, 0),
            "category": category,
            "tfidf_emr": round(tfidf_emr.get(kw, 0.0), 4),
            "tfidf_article": round(tfidf_article.get(kw, 0.0), 4),
        })
    keyword_df = pd.DataFrame(rows).sort_values(
        by=["emr_frequency", "article_frequency"], ascending=False
    ).reset_index(drop=True)

    emr_term_counts = extract_medical_terms(emr_docs)
    article_term_counts = extract_medical_terms(article_docs)

    return keyword_df, emr_term_counts, article_term_counts


def run(emr_df, articles_df):
    keyword_df, emr_term_counts, article_term_counts = run_text_mining(emr_df, articles_df)
    keyword_df.to_csv(config.KEYWORD_FREQUENCY_CSV, index=False, encoding="utf-8-sig")
    print(f"  - 키워드 빈도 분석 완료 ({len(keyword_df)}개 키워드) -> {config.KEYWORD_FREQUENCY_CSV}")
    return keyword_df, emr_term_counts, article_term_counts


if __name__ == "__main__":
    from generate_emr import generate_emr
    from crawler import collect_articles

    run(generate_emr(), collect_articles())
