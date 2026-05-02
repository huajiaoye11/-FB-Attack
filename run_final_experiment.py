import os
import json
import numpy as np

from FVFA.fvfa_cr import FVFA_CR_Attack


def load_keyword_json(path, top_k=1000):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    sorted_items = sorted(
        data.items(),
        key=lambda x: x[1]["size"],
        reverse=True
    )

    return dict(sorted_items[:top_k])


def build_keyword_freq(keyword_data):
    total = sum(item["size"] for item in keyword_data.values())

    return {
        w: item["size"] / total
        for w, item in keyword_data.items()
    }


def build_keyword_volume(keyword_data):
    return {
        w: item["size"]
        for w, item in keyword_data.items()
    }


def build_query_data(keyword_freq, keyword_volume, noise=True):
    query_freq = {}
    query_volume = {}
    true_mapping = {}

    rng = np.random.default_rng(seed=42)

    for index, w in enumerate(keyword_freq.keys()):
        q = f"q{index}"

        if noise:
            freq_noise = rng.uniform(0.8, 1.2)
            volume_noise = rng.uniform(0.8, 1.2)

            query_freq[q] = keyword_freq[w] * freq_noise
            query_volume[q] = max(1, int(keyword_volume[w] * volume_noise))
        else:
            query_freq[q] = keyword_freq[w]
            query_volume[q] = keyword_volume[w]

        true_mapping[q] = w

    total = sum(query_freq.values())
    query_freq = {
        q: v / total
        for q, v in query_freq.items()
    }

    return query_freq, query_volume, true_mapping


def run_fvfa(alpha, query_freq, query_volume, keyword_freq, keyword_volume, true_mapping):
    attack = FVFA_CR_Attack(
        alpha=alpha,
        conflict_threshold=0.03
    )

    pred_map, score_map = attack.predict_all(
        query_freq,
        query_volume,
        keyword_freq,
        keyword_volume
    )

    top1 = FVFA_CR_Attack.accuracy(true_mapping, pred_map)
    top5 = FVFA_CR_Attack.top_k_accuracy(true_mapping, score_map, k=5)

    return top1, top5


def main():
    project_root = os.path.dirname(os.path.abspath(__file__))

    edb_path = os.path.join(
        project_root,
        "PVIA_Enron",
        "edb",
        "0.9.json"
    )

    top_k = 1000

    keyword_data = load_keyword_json(edb_path, top_k=top_k)

    keyword_freq = build_keyword_freq(keyword_data)
    keyword_volume = build_keyword_volume(keyword_data)

    query_freq, query_volume, true_mapping = build_query_data(
        keyword_freq,
        keyword_volume,
        noise=True
    )

    print("Final Experiment Results")
    print("=" * 50)
    print("Dataset: Enron")
    print("Top keywords:", top_k)
    print()

    print("Baseline Results")
    print("-" * 50)

    print("FMA baseline: use original FMA result")
    print("VIA baseline: use original VIA/PVIA result")
    print()

    print("FVFA-CR Results")
    print("-" * 50)

    result_table = []

    for alpha in [0.3, 0.5, 0.7]:
        top1, top5 = run_fvfa(
            alpha,
            query_freq,
            query_volume,
            keyword_freq,
            keyword_volume,
            true_mapping
        )

        result_table.append((alpha, top1, top5))

        print(
            f"alpha={alpha:.1f} | "
            f"Top-1 Accuracy={top1:.4f} | "
            f"Top-5 Accuracy={top5:.4f}"
        )

    print()
    print("Recommended Table for Thesis")
    print("-" * 50)
    print("Method\t\tConfig\t\tTop-1\t\tTop-5")

    print("FMA\t\tA\t\t填原FMA结果\t-")
    print("VIA\t\tB\t\t填原VIA结果\t-")

    for alpha, top1, top5 in result_table:
        print(
            f"FVFA-CR\t\talpha={alpha:.1f}\t{top1:.4f}\t\t{top5:.4f}"
        )


if __name__ == "__main__":
    main()
