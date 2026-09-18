"""
9. 시각화 (matplotlib PNG 저장).
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config


def _bar_chart(labels, values, title, xlabel, filename, color="#4C72B0"):
    plt.figure(figsize=(9, 6))
    plt.barh(labels[::-1], values[::-1], color=color)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.tight_layout()
    path = config.RESULTS_DIR / filename
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def plot_emr_top_keywords(keyword_df, top_n=15):
    df = keyword_df.sort_values("emr_frequency", ascending=False).head(top_n)
    return _bar_chart(
        df["keyword"].tolist(), df["emr_frequency"].tolist(),
        "EMR Keyword Frequency (Top 15)", "Frequency",
        "emr_keywords_top15.png", color="#4C72B0",
    )


def plot_article_top_keywords(keyword_df, top_n=15):
    df = keyword_df.sort_values("article_frequency", ascending=False).head(top_n)
    return _bar_chart(
        df["keyword"].tolist(), df["article_frequency"].tolist(),
        "Article Keyword Frequency (Top 15)", "Frequency",
        "article_keywords_top15.png", color="#DD8452",
    )


def plot_common_keywords(keyword_df, top_n=15):
    df = keyword_df[keyword_df["category"] == "common"].copy()
    df["combined"] = df["emr_frequency"] + df["article_frequency"]
    df = df.sort_values("combined", ascending=False).head(top_n)

    labels = df["keyword"].tolist()[::-1]
    emr_vals = df["emr_frequency"].tolist()[::-1]
    article_vals = df["article_frequency"].tolist()[::-1]

    y = range(len(labels))
    plt.figure(figsize=(9, 6))
    plt.barh([i + 0.2 for i in y], emr_vals, height=0.4, label="EMR", color="#4C72B0")
    plt.barh([i - 0.2 for i in y], article_vals, height=0.4, label="Article", color="#DD8452")
    plt.yticks(list(y), labels)
    plt.title("EMR vs Article Common Keywords")
    plt.xlabel("Frequency")
    plt.legend()
    plt.tight_layout()
    path = config.RESULTS_DIR / "common_keywords.png"
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def plot_snomed_status_distribution(mapping_df):
    counts = mapping_df["mapping_status"].value_counts()
    order = ["Exact", "Partial", "Unverified", "No Match"]
    counts = counts.reindex(order).fillna(0)

    plt.figure(figsize=(7, 6))
    colors = ["#55A868", "#4C72B0", "#DD8452", "#C44E52"]
    plt.bar(counts.index, counts.values, color=colors)
    plt.title("SNOMED CT Candidate Mapping Status Distribution")
    plt.ylabel("Number of terms")
    plt.tight_layout()
    path = config.RESULTS_DIR / "snomed_mapping_status.png"
    plt.savefig(path, dpi=150)
    plt.close()
    return path


def run(keyword_df, mapping_df):
    paths = [
        plot_emr_top_keywords(keyword_df),
        plot_article_top_keywords(keyword_df),
        plot_common_keywords(keyword_df),
        plot_snomed_status_distribution(mapping_df),
    ]
    for p in paths:
        print(f"  - 그래프 저장 -> {p}")
    return paths


if __name__ == "__main__":
    import pandas as pd
    run(pd.read_csv(config.KEYWORD_FREQUENCY_CSV), pd.read_csv(config.SNOMED_MAPPING_CSV))
