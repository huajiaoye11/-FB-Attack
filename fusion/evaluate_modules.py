import json
from pathlib import Path
from collections import Counter


BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(exist_ok=True)


def load_json(path):
    if not path.exists():
        print("Missing:", path)
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def top1_mapping(candidate_data):
    mapping = {}

    for query_id, candidates in candidate_data.items():
        if not candidates:
            continue

        best_keyword, best_score = max(
            candidates.items(),
            key=lambda item: item[1]
        )

        mapping[query_id] = {
            "keyword": best_keyword,
            "score": best_score
        }

    return mapping


def count_conflicts(mapping):
    keyword_counter = Counter(
        item["keyword"] for item in mapping.values()
    )

    conflict_count = 0

    for keyword, count in keyword_counter.items():
        if count > 1:
            conflict_count += count - 1

    return conflict_count


def evaluate_candidate_file(name, candidate_data, ground_truth):
    total_truth = len(ground_truth)
    covered_queries = 0
    top1_correct = 0
    contains_true = 0
    candidate_size_sum = 0

    mapping = top1_mapping(candidate_data)

    for query_id, true_keyword in ground_truth.items():
        candidates = candidate_data.get(query_id)

        if not candidates:
            continue

        covered_queries += 1
        candidate_size_sum += len(candidates)

        if true_keyword in candidates:
            contains_true += 1

        predicted = mapping.get(query_id)

        if predicted and predicted["keyword"] == true_keyword:
            top1_correct += 1

    top1_accuracy_total = top1_correct / total_truth if total_truth else 0.0
    top1_accuracy_covered = top1_correct / covered_queries if covered_queries else 0.0
    contains_true_rate = contains_true / covered_queries if covered_queries else 0.0
    average_candidate_size = candidate_size_sum / covered_queries if covered_queries else 0.0
    conflict_count = count_conflicts(mapping)

    return {
        "name": name,
        "total_truth": total_truth,
        "covered_queries": covered_queries,
        "top1_correct": top1_correct,
        "top1_accuracy_total": top1_accuracy_total,
        "top1_accuracy_covered": top1_accuracy_covered,
        "contains_true": contains_true,
        "contains_true_rate": contains_true_rate,
        "average_candidate_size": average_candidate_size,
        "conflict_count": conflict_count
    }


def evaluate_fusion(final_mapping, ground_truth):
    total_truth = len(ground_truth)
    correct = 0
    covered_truth_queries = 0

    filtered_mapping = {}

    for query_id, true_keyword in ground_truth.items():
        predicted = final_mapping.get(query_id)

        if predicted is None:
            continue

        covered_truth_queries += 1
        filtered_mapping[query_id] = predicted

        if predicted["keyword"] == true_keyword:
            correct += 1

    accuracy_total = correct / total_truth if total_truth else 0.0
    accuracy_covered = correct / covered_truth_queries if covered_truth_queries else 0.0
    conflict_count = count_conflicts(filtered_mapping)

    return {
        "name": "Fusion",
        "total_truth": total_truth,
        "covered_queries": covered_truth_queries,
        "top1_correct": correct,
        "top1_accuracy_total": accuracy_total,
        "top1_accuracy_covered": accuracy_covered,
        "contains_true": "-",
        "contains_true_rate": "-",
        "average_candidate_size": "-",
        "conflict_count": conflict_count
    }


def format_percent(value):
    if isinstance(value, str):
        return value

    return f"{value * 100:.2f}%"


def format_number(value):
    if isinstance(value, str):
        return value

    return f"{value:.2f}"


def main():
    ground_truth = load_json(INPUT_DIR / "ground_truth.json")

    fma = load_json(INPUT_DIR / "fma_candidates.json")
    pvia = load_json(INPUT_DIR / "pvia_candidates.json")
    lvia = load_json(INPUT_DIR / "lvia_candidates.json")
    fusion = load_json(OUTPUT_DIR / "final_mapping.json")

    results = []

    results.append(evaluate_candidate_file("FMA", fma, ground_truth))
    results.append(evaluate_candidate_file("PVIA", pvia, ground_truth))
    results.append(evaluate_candidate_file("LVIA", lvia, ground_truth))
    results.append(evaluate_fusion(fusion, ground_truth))

    output_path = OUTPUT_DIR / "module_comparison_metrics.txt"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("Module Comparison Results\n")
        f.write("=" * 100 + "\n")
        f.write(
            "Method\t"
            "Covered\t"
            "Top1 Correct\t"
            "Top1 Accuracy Total\t"
            "Top1 Accuracy Covered\t"
            "Contains True\t"
            "Contains True Rate\t"
            "Avg Candidate Size\t"
            "Conflict Count\n"
        )

        for item in results:
            avg_candidate_size_text = format_number(item["average_candidate_size"])

            f.write(
                f"{item['name']}\t"
                f"{item['covered_queries']}\t"
                f"{item['top1_correct']}\t"
                f"{format_percent(item['top1_accuracy_total'])}\t"
                f"{format_percent(item['top1_accuracy_covered'])}\t"
                f"{item['contains_true']}\t"
                f"{format_percent(item['contains_true_rate'])}\t"
                f"{avg_candidate_size_text}\t"
                f"{item['conflict_count']}\n"
            )

    print("Module Comparison Results")
    print("=" * 80)

    for item in results:
        print()
        print("Method:", item["name"])
        print("Covered queries:", item["covered_queries"])
        print("Top1 correct:", item["top1_correct"])
        print("Top1 accuracy total:", format_percent(item["top1_accuracy_total"]))
        print("Top1 accuracy covered:", format_percent(item["top1_accuracy_covered"]))
        print("Contains true:", item["contains_true"])
        print("Contains true rate:", format_percent(item["contains_true_rate"]))
        print("Average candidate size:", format_number(item["average_candidate_size"]))
        print("Conflict count:", item["conflict_count"])

    print()
    print("Saved to:", output_path)


if __name__ == "__main__":
    main()
