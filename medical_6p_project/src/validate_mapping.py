"""
8. Pilot 검증 (Pilot terminology mapping accuracy).

이것은 "의료 AI 정확도"가 아니라, 자동 SNOMED CT 후보 매핑(candidate mapping)
결과 중 일부를 사람이 직접 확인했을 때의 정확도(Pilot terminology mapping
accuracy)이다. 자동 매핑은 어디까지나 후보 수준이며 최종 확인은 사람이 한다.
"""

import random

import pandas as pd

import config
from terminology import CLINICAL_CATEGORIES

PILOT_COLUMNS = ["original_term", "normalized_term", "snomed_concept",
                  "snomed_concept_id", "mapping_status", "human_judgment", "review_note"]


def create_pilot_sample(mapping_df, integrated_df, sample_size=None, seed=None):
    """실제 임상 개념(질환/증상/약물/검사/검사결과/치료) 위주로 Pilot 표본을 만든다.

    일반 상위 키워드("general_keyword")나 불완전한 토큰은 애초에 대상에서 제외한다.
    빈도 상위 절반 + 무작위 절반으로 구성해 사람이 직접 채점(Correct/Incorrect/
    Uncertain)할 수 있는 표를 만든다. human_judgment, review_note 는 비워둔다.
    """
    sample_size = sample_size or config.PILOT_SAMPLE_SIZE
    seed = config.RANDOM_SEED if seed is None else seed

    clinical_mapping = mapping_df[mapping_df["source_type"].isin(CLINICAL_CATEGORIES)].copy()

    freq_lookup = integrated_df.set_index("term")["total_frequency"].to_dict()
    clinical_mapping["total_frequency"] = clinical_mapping["normalized_term"].map(freq_lookup).fillna(0)
    clinical_mapping = clinical_mapping.sort_values("total_frequency", ascending=False)

    n = min(sample_size, len(clinical_mapping))
    top_n = max(1, n // 2)
    top_terms = clinical_mapping.head(top_n)

    remaining = clinical_mapping.iloc[top_n:]
    rng = random.Random(seed)
    extra_n = n - len(top_terms)
    if extra_n > 0 and len(remaining) > 0:
        extra_idx = rng.sample(range(len(remaining)), k=min(extra_n, len(remaining)))
        extra_terms = remaining.iloc[extra_idx]
    else:
        extra_terms = remaining.iloc[0:0]

    pilot_df = pd.concat([top_terms, extra_terms]).drop_duplicates(subset=["normalized_term"])
    pilot_df = pilot_df[["original_term", "normalized_term", "snomed_concept",
                          "snomed_concept_id", "mapping_status"]].copy()
    pilot_df["human_judgment"] = ""   # Correct / Incorrect / Uncertain (사람이 직접 입력)
    pilot_df["review_note"] = ""      # 검토자 메모 (선택)
    return pilot_df.reset_index(drop=True)


def pilot_validation_stats(pilot_csv_path=None):
    """Pilot 표에 대한 집계.

    accuracy = correct / total_reviewed x 100  (human_judgment 를 채운 항목 기준)
    아직 아무도 채점하지 않았으면 accuracy=None 이고, 호출부에서
    "Manual validation pending" 을 출력해야 한다.
    """
    pilot_csv_path = pilot_csv_path or config.PILOT_VALIDATION_CSV
    df = pd.read_csv(pilot_csv_path)

    total_pilot = len(df)
    judgments = df["human_judgment"].fillna("").astype(str).str.strip().str.capitalize()

    total_reviewed = int((judgments != "").sum())
    correct = int((judgments == "Correct").sum())
    incorrect = int((judgments == "Incorrect").sum())
    uncertain = int((judgments == "Uncertain").sum())

    accuracy = (correct / total_reviewed * 100) if total_reviewed > 0 else None

    return {
        "total_pilot": total_pilot,
        "total_reviewed": total_reviewed,
        "correct": correct,
        "incorrect": incorrect,
        "uncertain": uncertain,
        "accuracy": accuracy,
    }


def run(mapping_df, integrated_df):
    pilot_df = create_pilot_sample(mapping_df, integrated_df)
    pilot_df.to_csv(config.PILOT_VALIDATION_CSV, index=False, encoding="utf-8-sig")
    print(f"  - Pilot 검증용 표본 {len(pilot_df)}건 생성 -> {config.PILOT_VALIDATION_CSV}")
    print("    (human_judgment 열에 Correct/Incorrect/Uncertain 을 직접 입력한 뒤 "
          "다시 계산하세요)")

    stats = pilot_validation_stats()
    if stats["accuracy"] is None:
        print("    Pilot terminology mapping accuracy: Manual validation pending")
    else:
        print(f"    Pilot terminology mapping accuracy: {stats['accuracy']:.2f}% "
              f"(correct {stats['correct']} / reviewed {stats['total_reviewed']} "
              f"/ pilot total {stats['total_pilot']})")
    return pilot_df, stats


if __name__ == "__main__":
    mapping = pd.read_csv(config.SNOMED_MAPPING_CSV)
    integrated = pd.read_csv(config.INTEGRATED_MAPPING_CSV)
    run(mapping, integrated)
