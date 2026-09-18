"""
6. SNOMED CT 후보 매핑 + 7. EMR/기사 통합.

원칙: SNOMED CT concept id 는 절대 임의로 만들지 않는다.
terminology.SNOMED_REFERENCE 에 있는, 공개적으로 널리 확인된 code 만 사용하며
그 외의 경우 snomed_concept_id 는 항상 "UNVERIFIED" 로 남긴다.

mapping_status
    Exact      : 정규화된 문자열이 참조표와 완전히 동일
    Partial    : 동의어/유사어를 통해 참조표의 개념과 연결됨 (후보 수준)
    Unverified : 우리 카테고리 사전에는 있는 의료 용어이지만 참조표에 없음
    No Match   : 의료 용어 사전에서도 확인되지 않음
"""

import difflib
import re

import pandas as pd

import config
from terminology import SNOMED_REFERENCE, SYNONYM_MAP, CATEGORY_KEYWORDS

UNVERIFIED = "UNVERIFIED"

_REF_BY_TERM = {ref["term"]: ref for ref in SNOMED_REFERENCE}
_REF_TERMS = list(_REF_BY_TERM.keys())

_ALL_CATEGORY_TERMS = {
    term for terms in CATEGORY_KEYWORDS.values() for term in terms
}


def normalize_term(term):
    term = term.lower().strip()
    term = re.sub(r"\s+", " ", term)
    term = term.strip(".,;:")
    return term


def map_term(term, category):
    """단일 용어를 SNOMED 참조표와 대조하여 후보 매핑 1건을 만든다."""
    normalized = normalize_term(term)

    # 1) Exact: 정규화 문자열이 참조표와 동일
    if normalized in _REF_BY_TERM:
        ref = _REF_BY_TERM[normalized]
        return {
            "snomed_concept": ref["snomed_concept"],
            "snomed_concept_id": ref["snomed_concept_id"],
            "mapping_status": "Exact",
        }

    # 2) Partial: 동의어 사전을 통해 참조표 개념과 연결
    synonym_target = SYNONYM_MAP.get(normalized)
    if synonym_target and synonym_target in _REF_BY_TERM:
        ref = _REF_BY_TERM[synonym_target]
        return {
            "snomed_concept": ref["snomed_concept"],
            "snomed_concept_id": ref["snomed_concept_id"],
            "mapping_status": "Partial",
        }

    # 2-2) Partial: 문자열 유사도가 높은 참조 용어가 있는 경우
    close = difflib.get_close_matches(normalized, _REF_TERMS, n=1, cutoff=0.84)
    if close:
        ref = _REF_BY_TERM[close[0]]
        return {
            "snomed_concept": ref["snomed_concept"],
            "snomed_concept_id": ref["snomed_concept_id"],
            "mapping_status": "Partial",
        }

    # 3) Unverified: 우리 카테고리 사전에는 존재하는 의료 용어
    if normalized in _ALL_CATEGORY_TERMS:
        return {
            "snomed_concept": "",
            "snomed_concept_id": UNVERIFIED,
            "mapping_status": "Unverified",
        }

    # 4) No Match
    return {
        "snomed_concept": "",
        "snomed_concept_id": UNVERIFIED,
        "mapping_status": "No Match",
    }


def build_snomed_mapping(term_category_pairs):
    """(term, category) 목록을 받아 SNOMED 후보 매핑 DataFrame을 만든다."""
    rows = []
    seen = set()
    for term, category in term_category_pairs:
        normalized = normalize_term(term)
        if normalized in seen:
            continue
        seen.add(normalized)

        mapping = map_term(term, category)
        rows.append({
            "original_term": term,
            "normalized_term": normalized,
            "english_term": normalized,
            "snomed_concept": mapping["snomed_concept"],
            "snomed_concept_id": mapping["snomed_concept_id"],
            "source_type": category,
            "mapping_status": mapping["mapping_status"],
        })

    columns = ["original_term", "normalized_term", "english_term", "snomed_concept",
               "snomed_concept_id", "source_type", "mapping_status"]
    return pd.DataFrame(rows, columns=columns)


def integrate_with_frequency(mapping_df, emr_term_counts, article_term_counts,
                              keyword_freq_lookup=None):
    """SNOMED 매핑 결과에 EMR/기사 빈도를 합쳐 통합 매핑 테이블을 만든다.

    keyword_freq_lookup: {normalized_word: (emr_freq, article_freq)} 형태의 보조 사전.
    general_keyword(카테고리 사전 밖의 상위 키워드)처럼 emr_term_counts /
    article_term_counts 에 없는 용어의 빈도를 찾을 때 사용한다.
    """
    keyword_freq_lookup = keyword_freq_lookup or {}
    rows = []
    for _, r in mapping_df.iterrows():
        term = r["normalized_term"]
        if term in emr_term_counts or term in article_term_counts:
            emr_freq = emr_term_counts.get(term, {}).get("count", 0)
            article_freq = article_term_counts.get(term, {}).get("count", 0)
        else:
            emr_freq, article_freq = keyword_freq_lookup.get(term, (0, 0))
        rows.append({
            "term": term,
            "emr_frequency": emr_freq,
            "article_frequency": article_freq,
            "total_frequency": emr_freq + article_freq,
            "snomed_concept": r["snomed_concept"],
            "snomed_concept_id": r["snomed_concept_id"],
            "mapping_status": r["mapping_status"],
        })
    df = pd.DataFrame(rows)
    df = df.sort_values(by="total_frequency", ascending=False).reset_index(drop=True)
    return df


def run(emr_term_counts, article_term_counts, extra_keywords=None, keyword_freq_lookup=None):
    """extra_keywords: 카테고리 사전과 무관하게 매핑을 시도해볼 일반 상위 키워드 목록.
    (의료 용어가 아닌 경우가 섞여 있어, mapping_status = "No Match" 사례를 보여준다.)
    """
    all_terms = set(emr_term_counts) | set(article_term_counts)
    term_category_pairs = []
    for term in all_terms:
        category = emr_term_counts.get(term, article_term_counts.get(term))["category"]
        term_category_pairs.append((term, category))

    for term in (extra_keywords or []):
        normalized = normalize_term(term)
        if normalized not in {normalize_term(t) for t, _ in term_category_pairs}:
            term_category_pairs.append((term, "general_keyword"))

    mapping_df = build_snomed_mapping(term_category_pairs)
    mapping_df.to_csv(config.SNOMED_MAPPING_CSV, index=False, encoding="utf-8-sig")
    print(f"  - SNOMED CT 후보 매핑 {len(mapping_df)}건 생성 -> {config.SNOMED_MAPPING_CSV}")
    print(f"    (상태 분포: {mapping_df['mapping_status'].value_counts().to_dict()})")

    integrated_df = integrate_with_frequency(
        mapping_df, emr_term_counts, article_term_counts, keyword_freq_lookup
    )
    integrated_df.to_csv(config.INTEGRATED_MAPPING_CSV, index=False, encoding="utf-8-sig")
    print(f"  - EMR+기사 통합 매핑 {len(integrated_df)}건 생성 -> {config.INTEGRATED_MAPPING_CSV}")

    return mapping_df, integrated_df


if __name__ == "__main__":
    from generate_emr import generate_emr
    from crawler import collect_articles
    from text_mining import run_text_mining

    _, emr_terms, article_terms = run_text_mining(generate_emr(), collect_articles())
    run(emr_terms, article_terms)
