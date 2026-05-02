import os
import json
import sys
import numpy as np

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

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
    total = sum(
        item["size"]
        for item in keyword_data.values()
    )

    return {
        w: item["size"] / total
        for w, item in keyword_data.items()
    }


def build_keyword_volume(keyword_data):
    return {
        w: item["size"]
        for w, item in keyword_data.items()
    }


def build_query_data_from_keyword(keyword_freq, keyword_volume):
    """
    快速实验版本：
    使用关键词集合构造查询 token q0, q1, q2...
    用于验证频率-体积融合攻击模型。
    """

    query_freq = {}
    query_volume = {}
    true_mapping = {}

    for index, w in enumerate(keyword_freq.keys()):
        q = f"q{index}"

        query_freq[q] = keyword_freq[w]
        query_volume[q] = keyword_volume[w]
        true_mapping[q] = w

    return query_freq, query_volume, true_mapping


def run_single_alpha(alpha, keyword_freq, keyword_volume):
    query_freq, query_volume, true_mapping = build_query_data_from_keyword(
        keyword_freq,
        keyword_volume
    )

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

    top1 = FVFA_CR_Attack.accuracy(
        true_mapping,
        pred_map
    )

    top5 = FVFA_CR_Attack.top_k_accuracy(
        true_mapping,
        score_map,
        k=5
    )

    return top1, top5, pred_map, true_mapping


def main():
    project_root = os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )

    edb_path = os.path.join(
        project_root,
        "PVIA_Enron",
        "edb",
        "0.9.json"
    )

    top_k = 1000

    keyword_data = load_keyword_json(
        edb_path,
        top_k=top_k
    )

    keyword_freq = build_keyword_freq(keyword_data)
    keyword_volume = build_keyword_volume(keyword_data)

    print("FVFA-CR Results")
    print("=" * 40)
    print("Dataset: Enron")
    print("Top keyword number:", top_k)

    best_alpha = None
    best_acc = -1

    print("\nAlpha Comparison:")
    print("-" * 40)

    for alpha in np.arange(0.1, 1.0, 0.1):
        alpha = round(float(alpha), 1)

        top1, top5, pred_map, true_mapping = run_single_alpha(
            alpha,
            keyword_freq,
            keyword_volume
        )

        print(
            f"alpha={alpha:.1f} | "
            f"Top-1 Accuracy={top1:.4f} | "
            f"Top-5 Accuracy={top5:.4f}"
        )

        if top1 > best_acc:
            best_acc = top1
            best_alpha = alpha

    print("\nBest Result")
    print("-" * 40)
    print("Best alpha:", best_alpha)
    print("Best Top-1 Accuracy:", round(best_acc, 4))

    top1, top5, pred_map, true_mapping = run_single_alpha(
        best_alpha,
        keyword_freq,
        keyword_volume
    )

    print("\nSample predictions:")
    print("-" * 40)

    for i, q in enumerate(pred_map.keys()):
        print(
            q,
            "->",
            pred_map[q],
            "| true:",
            true_mapping[q]
        )

        if i >= 10:
            break


if __name__ == "__main__":
    main()
