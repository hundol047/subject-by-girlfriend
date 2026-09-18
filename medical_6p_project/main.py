"""
심혈관계 / 심부전(Heart Failure) 6P 프로젝트 - 전체 파이프라인 실행 스크립트.

실행: python main.py

단계:
  1. 가상 EMR 생성
  2. 임상 기사(공개 웹 문서) 수집
  3~4. 텍스트 전처리 + 키워드/TF-IDF 마이닝
  5. 카테고리별 의료 용어 추출 (질환/증상/약물/검사/검사결과/치료)
  6. SNOMED CT 후보 매핑
  7. EMR + 기사 통합 매핑
  8. Pilot 검증용 표본 생성 (Pilot terminology mapping accuracy)
  9. 시각화(PNG) 생성 + 결과 요약(summary.txt)
"""

import datetime
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "src"))

import config
from generate_emr import run as run_generate_emr
from crawler import run as run_crawler
from text_mining import run as run_text_mining
from snomed_mapper import run as run_snomed_mapper
from validate_mapping import run as run_validate_mapping
from visualize import run as run_visualize
from terminology import CLINICAL_CATEGORIES


def build_summary(emr_df, articles_df, mapping_df, pilot_df, pilot_stats):
    clinical_mapping = mapping_df[mapping_df["source_type"].isin(CLINICAL_CATEGORIES)]
    status_counts = mapping_df["mapping_status"].value_counts()

    if pilot_stats["accuracy"] is None:
        accuracy_line = "Manual validation pending"
    else:
        accuracy_line = (f"{pilot_stats['accuracy']:.2f}% "
                          f"(correct {pilot_stats['correct']} / reviewed "
                          f"{pilot_stats['total_reviewed']} / pilot total "
                          f"{pilot_stats['total_pilot']})")

    lines = [
        f"=== {config.SYSTEM_KO} / {config.DISEASE_KO} ({config.DISEASE_EN}) "
        f"6P 분석 결과 요약 ===",
        f"생성 일시: {datetime.datetime.now().isoformat(timespec='seconds')}",
        "",
        f"Synthetic EMR 환자 수: {len(emr_df)}",
        f"수집 기사 수: {len(articles_df)}",
        f"추출 의료용어 수 (질환/증상/약물/검사/검사결과/치료): {len(clinical_mapping)}",
        f"SNOMED 후보 매핑 수 (일반 키워드 포함 전체): {len(mapping_df)}",
        f"  - Exact: {int(status_counts.get('Exact', 0))}",
        f"  - Partial: {int(status_counts.get('Partial', 0))}",
        f"  - Unverified: {int(status_counts.get('Unverified', 0))}",
        f"  - No Match: {int(status_counts.get('No Match', 0))}",
        f"Pilot 검증 대상 개수: {len(pilot_df)}",
        f"Pilot terminology mapping accuracy: {accuracy_line}",
        "",
        "※ SNOMED CT 매핑은 후보(candidate) 수준이며, 최종 확인은 사람이 담당합니다.",
    ]
    return "\n".join(lines)


def main():
    print(f"=== {config.SYSTEM_KO} / {config.DISEASE_KO} ({config.DISEASE_EN}) "
          f"6P 분석 파이프라인 시작 ===\n")

    print("[1/7] 가상 EMR 생성 (synthetic data)")
    emr_df = run_generate_emr()

    print("\n[2/7] 임상 기사(공개 웹 문서) 수집")
    articles_df = run_crawler()

    print("\n[3/7] 텍스트 전처리 + 키워드/TF-IDF 마이닝")
    keyword_df, emr_term_counts, article_term_counts = run_text_mining(emr_df, articles_df)

    print("\n[4/7] SNOMED CT 후보 매핑 + EMR/기사 통합")
    top_general_keywords = keyword_df.sort_values(
        by=["emr_frequency", "article_frequency"], ascending=False
    ).head(15)["keyword"].tolist()
    keyword_freq_lookup = {
        row["keyword"]: (row["emr_frequency"], row["article_frequency"])
        for _, row in keyword_df.iterrows()
    }
    mapping_df, integrated_df = run_snomed_mapper(
        emr_term_counts, article_term_counts,
        extra_keywords=top_general_keywords,
        keyword_freq_lookup=keyword_freq_lookup,
    )

    print("\n[5/7] Pilot 검증용 표본 생성")
    pilot_df, pilot_stats = run_validate_mapping(mapping_df, integrated_df)

    print("\n[6/7] 시각화(PNG) 생성")
    run_visualize(keyword_df, mapping_df)

    print("\n[7/7] 결과 요약 생성")
    summary_text = build_summary(emr_df, articles_df, mapping_df, pilot_df, pilot_stats)
    config.SUMMARY_TXT.write_text(summary_text, encoding="utf-8")
    print(f"  - 결과 요약 저장 -> {config.SUMMARY_TXT}")
    print("\n" + summary_text)

    print("\n=== 파이프라인 완료 ===")
    print(f"data/    : {config.SYNTHETIC_EMR_CSV.name}, {config.ARTICLES_CSV.name}, "
          f"{config.SNOMED_MAPPING_CSV.name}")
    print(f"results/ : {config.KEYWORD_FREQUENCY_CSV.name}, "
          f"{config.INTEGRATED_MAPPING_CSV.name}, {config.PILOT_VALIDATION_CSV.name}, "
          f"{config.SUMMARY_TXT.name}, *.png")


if __name__ == "__main__":
    main()
