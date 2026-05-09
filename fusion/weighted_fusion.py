import json
from pathlib import Path
from collections import defaultdict, Counter


BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(exist_ok=True)


WEIGHTS = {
    "fma": 0.4,
    "pvia": 0.3,
    "lvia": 0.3
}


def load_json(filename):
    """Load a JSON file from INPUT_DIR.

    Note: Since FMA/enron.py now outputs parameterized filenames
    (e.g. fma_candidates_nkw500_query5000_month6_del20.json),
    you may need to copy or symlink the desired parameter file
    to the default name expected here, or update the filename in main().
    """
    path = INPUT_DIR / filename
    if not path.exists():
        print(f"[Warning] Missing file: {path}")
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename, data):
    path = OUTPUT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_candidate_scores(candidate_scores):
    """
    把一个查询下的候选分数归一化到 0~1。

    注意：
    如果所有候选分数完全相同，不再强行变成 1.0，
    而是保留原始分数。
    这样可以避免 FMA 的等分候选被全部放大。
    """
    if not candidate_scores:
        return {}

    values = list(candidate_scores.values())
    min_value = min(values)
    max_value = max(values)

    if max_value == min_value:
        return {
            keyword: float(score)
            for keyword, score in candidate_scores.items()
        }

    return {
        keyword: (score - min_value) / (max_value - min_value)
        for keyword, score in candidate_scores.items()
    }



def weighted_fusion(module_results):
    """
    加权融合：
    final_score = 0.4 * FMA + 0.3 * PVIA + 0.3 * LVIA
    """
    fused_scores = defaultdict(lambda: defaultdict(float))

    for module_name, result in module_results.items():
        weight = WEIGHTS[module_name]

        for query_id, candidate_scores in result.items():
            normalized_scores = normalize_candidate_scores(candidate_scores)

            for keyword, score in normalized_scores.items():
                fused_scores[query_id][keyword] += weight * score

    sorted_fused_scores = {}

    for query_id, candidate_scores in fused_scores.items():
        sorted_fused_scores[query_id] = dict(
            sorted(
                candidate_scores.items(),
                key=lambda item: item[1],
                reverse=True
            )
        )

    return sorted_fused_scores


def naive_top1(fused_scores):
    """
    不做冲突仲裁时，直接给每个查询选分数最高的关键词。
    """
    mapping = {}

    for query_id, candidate_scores in fused_scores.items():
        if not candidate_scores:
            continue

        best_keyword, best_score = max(
            candidate_scores.items(),
            key=lambda item: item[1]
        )

        mapping[query_id] = {
            "keyword": best_keyword,
            "score": best_score
        }

    return mapping


def count_conflicts(mapping):
    """
    统计冲突数量：
    如果多个 query 都被映射到同一个 keyword，就算冲突。
    """
    keyword_counter = Counter(
        item["keyword"] for item in mapping.values()
    )

    conflict_count = 0

    for keyword, count in keyword_counter.items():
        if count > 1:
            conflict_count += count - 1

    return conflict_count


def greedy_arbitration(fused_scores):
    """
    贪心冲突仲裁：
    1. 把所有 query-keyword-score 组合放在一起。
    2. 按分数从高到低排序。
    3. 优先保留高分匹配。
    4. 一个 query 只能匹配一个 keyword。
    5. 一个 keyword 尽量只分配给一个 query。
    """
    all_pairs = []

    for query_id, candidate_scores in fused_scores.items():
        for keyword, score in candidate_scores.items():
            all_pairs.append((score, query_id, keyword))

    all_pairs.sort(reverse=True)

    assigned_queries = set()
    assigned_keywords = set()
    final_mapping = {}

    for score, query_id, keyword in all_pairs:
        if query_id in assigned_queries:
            continue

        if keyword in assigned_keywords:
            continue

        final_mapping[query_id] = {
            "keyword": keyword,
            "score": score
        }

        assigned_queries.add(query_id)
        assigned_keywords.add(keyword)

    return final_mapping


def evaluate(final_mapping, ground_truth):
    """
    计算融合后的恢复率。
    ground_truth 格式：
    {
      "query_1": "energy",
      "query_2": "report"
    }
    """
    if not ground_truth:
        return 0, 0, 0.0

    correct = 0
    total = len(ground_truth)

    for query_id, true_keyword in ground_truth.items():
        predicted = final_mapping.get(query_id)

        if predicted is None:
            continue

        if predicted["keyword"] == true_keyword:
            correct += 1

    accuracy = correct / total if total > 0 else 0.0
    return correct, total, accuracy


def main():
    # --- FMA/PVIA/LVIA input files ---
    # New FMA/enron.py outputs parameterized filenames, e.g.:
    #   fma_candidates_nkw500_query5000_month6_del20.json
    #   ground_truth_nkw500_query5000_month6_del20.json
    # To use them here, either copy/rename the desired file to
    # the default name below, or update the filename string.
    fma_result = load_json("fma_candidates.json")
    pvia_result = load_json("pvia_candidates.json")
    lvia_result = load_json("lvia_candidates.json")
    # ground_truth is also parameterized by new FMA/enron.py;
    # see comment above for fma_candidates.
    ground_truth = load_json("ground_truth.json")

    module_results = {
        "fma": fma_result,
        "pvia": pvia_result,
        "lvia": lvia_result
    }

    fused_scores = weighted_fusion(module_results)

    naive_mapping = naive_top1(fused_scores)
    final_mapping = greedy_arbitration(fused_scores)

    conflict_before = count_conflicts(naive_mapping)
    conflict_after = count_conflicts(final_mapping)

    correct, total, accuracy = evaluate(final_mapping, ground_truth)

    save_json("fused_scores.json", fused_scores)
    save_json("final_mapping.json", final_mapping)

    metrics_path = OUTPUT_DIR / "fusion_metrics.txt"

    with open(metrics_path, "w", encoding="utf-8") as f:
        f.write("Weighted Fusion and Conflict Arbitration Results\n")
        f.write("=" * 50 + "\n")
        f.write(f"Correct queries: {correct}\n")
        f.write(f"Total queries: {total}\n")
        f.write(f"Fusion accuracy: {accuracy:.4f}\n")
        f.write(f"Conflict count before arbitration: {conflict_before}\n")
        f.write(f"Conflict count after arbitration: {conflict_after}\n")

    print("Done.")
    print(f"Correct queries: {correct}")
    print(f"Total queries: {total}")
    print(f"Fusion accuracy: {accuracy:.4f}")
    print(f"Conflict count before arbitration: {conflict_before}")
    print(f"Conflict count after arbitration: {conflict_after}")
    print(f"Results saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
