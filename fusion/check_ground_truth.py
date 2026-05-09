import json
from pathlib import Path


INPUT_DIR = Path(__file__).resolve().parent / "input"


def load_json(filename):
    path = INPUT_DIR / filename

    if not path.exists():
        print("Missing:", filename)
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    fma = load_json("fma_candidates.json")
    pvia = load_json("pvia_candidates.json")
    lvia = load_json("lvia_candidates.json")
    truth = load_json("ground_truth.json")

    print("FMA query count:", len(fma))
    print("PVIA query count:", len(pvia))
    print("LVIA query count:", len(lvia))
    print("Ground truth count:", len(truth))
    print()

    truth_keys = set(truth.keys())
    fma_keys = set(fma.keys())
    pvia_keys = set(pvia.keys())
    lvia_keys = set(lvia.keys())

    print("Ground truth keys in FMA:", len(truth_keys & fma_keys))
    print("Ground truth keys in PVIA:", len(truth_keys & pvia_keys))
    print("Ground truth keys in LVIA:", len(truth_keys & lvia_keys))
    print()

    print("Example ground truth:")
    for index, item in enumerate(truth.items()):
        print(item)
        if index >= 4:
            break

    print()
    print("Example FMA:")
    for index, item in enumerate(fma.items()):
        print(item)
        if index >= 1:
            break


if __name__ == "__main__":
    main()
