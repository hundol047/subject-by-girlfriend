"""
8. Pilot 검증 (Pilot terminology mapping accuracy).

주의: 이것은 "의료 AI 정확도"가 아니라, 자동 SNOMED CT 후보 매핑 결과 중 일부를
사람이 직접 확인했을 때의 정확도(Pilot terminology mapping accuracy)이다.
"""

import random

import pandas as pd

import config


def create_pilot_sample(integrated_df, sample_size=None, seed=None):
    """빈도 상위 용어 위주로 Pilot 검증 대상 표본을 만든다 (사람이 직접 채점).

    human_judgment 열은 비워두며, 사용자가 Correct / Incorrect / Uncertain 중
    하나를 직접 입력한 뒤 compute_pilot_accuracy() 를 다시 실행하면 된다.
    """
    sample_size = sample_size or config.PILOT_SAMPLE_SIZE
    seed = config.RANDOM_SEED if seed is None else seed

    n = min(sample_size, len(integrated_df))
    top_n = max(1, n // 2)
    top_terms = integrated_df.head(top_n)

    remaining = integrated_df.iloc[top_n:]
    rng = random.Random(seed)
    extra_n = n - len(top_terms)
    if extra_n > 0 and len(remaining) > 0:
        extra_idx = rng.sample(range(len(remaining)), k=min(extra_n, len(remaining)))
        extra_terms = remaining.iloc[extra_idx]
    else:
        extra_terms = remaining.iloc[0:0]

    pilot_df = pd.concat([top_terms, extra_terms]).drop_duplicates(subset=["term"])
    pilot_df = pilot_df[["term", "snomed_concept", "snomed_concept_id",
                          "mapping_status", "total_frequency"]].copy()
    pilot_df["human_judgment"] = ""  # Correct / Incorrect / Uncertain (사람이 직접 입력)
    return pilot_df.reset_index(drop=True)


def compute_pilot_accuracy(pilot_csv_path=None):
    """Pilot terminology mapping accuracy = Correct / 전체 검증 대상 수 x 100.

    human_judgment 열이 비어 있으면 (아직 사람이 채점하지 않았으면) None 을 반환한다.
    """
    pilot_csv_path = pilot_csv_path or config.PILOT_VALIDATION_CSV
    df = pd.read_csv(pilot_csv_path)

    total = len(df)
    if total == 0:
        return None, 0, 0

    judgments = df["human_judgment"].fillna("").astype(str).str.strip().str.capitalize()
    judged = (judgments != "").sum()
    correct = (judgments == "Correct").sum()

    if judged == 0:
        return None, 0, total

    accuracy = correct / total * 100
    return accuracy, judged, total


def run(integrated_df):
    pilot_df = create_pilot_sample(integrated_df)
    pilot_df.to_csv(config.PILOT_VALIDATION_CSV, index=False, encoding="utf-8-sig")
    print(f"  - Pilot 검증용 표본 {len(pilot_df)}건 생성 -> {config.PILOT_VALIDATION_CSV}")
    print("    (human_judgment 열에 Correct/Incorrect/Uncertain 을 직접 입력한 뒤 "
          "다시 계산하세요)")

    accuracy, judged, total = compute_pilot_accuracy()
    if accuracy is None:
        print(f"    Pilot terminology mapping accuracy: 대기 중 (0/{total} 건 채점됨)")
    else:
        print(f"    Pilot terminology mapping accuracy: {accuracy:.2f}% "
              f"({judged}/{total} 건 채점됨)")
    return pilot_df


if __name__ == "__main__":
    df = pd.read_csv(config.INTEGRATED_MAPPING_CSV)
    run(df)
