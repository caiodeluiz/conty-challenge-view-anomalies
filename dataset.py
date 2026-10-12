"""Generate labelled synthetic examples independently of classifier decisions."""

import argparse
import json
import math
import random
import re
from pathlib import Path

from classifier import classify


SEED = 20261011


def generate():
    rng = random.Random(SEED)
    cases = []

    def add(identifier, label, scenario, views):
        cases.append({"id": identifier, "label": label, "scenario": scenario, "views": views})

    for index in range(20):
        add(f"organic-regular-{index:02d}", "legitimate", "variação orgânica moderada",
            [45 + rng.randint(-14, 14) for _ in range(24)])
    for index in range(10):
        add(f"organic-viral-{index:02d}", "legitimate", "crescimento e queda graduais de um viral",
            [max(0, 20 + round(950 * math.exp(-((hour - 12) / 3.3) ** 2)) + rng.randint(-8, 8)) for hour in range(24)])
    for index in range(9):
        views = [5 + index] * 24 if index < 8 else [0] * 23 + [900]
        add(f"organic-low-information-{index:02d}", "legitimate", "pouco volume ou pouca evidência para acusação", views)
    add("organic-live-counterexample", "legitimate", "evento ao vivo legítimo com contagem horária constante: falso positivo conhecido", [900] * 24)
    for index in range(10):
        views = [30 + rng.randint(-5, 5) for _ in range(24)]
        views[12] = 9000 + index * 100
        add(f"suspicious-isolated-{index:02d}", "suspicious", "pico isolado comprado no cenário sintético", views)
    for index in range(5):
        add(f"suspicious-mechanical-{index:02d}", "suspicious", "contagem mecânica repetida", [600 + index] * 24)
    for index in range(5):
        views = [10 + rng.randint(-2, 2) for _ in range(24)]
        views[5:11] = [2000 + rng.randint(-8, 8) for _ in range(6)]
        views[11] = 2
        add(f"suspicious-plateau-drop-{index:02d}", "suspicious", "plateau artificial com queda abrupta", views)
    return {"seed": SEED, "units": "views por hora; horas consecutivas", "cases": cases}


def evaluate(dataset):
    legitimate = false_positives = suspicious = true_positives = abstentions = 0
    results = []
    for case in dataset["cases"]:
        result = classify(case["views"])
        predicted = result["classification"]
        if case["label"] == "legitimate":
            legitimate += 1
            false_positives += predicted == "suspicious"
        elif case["label"] == "suspicious":
            suspicious += 1
            true_positives += predicted == "suspicious"
        else:
            raise ValueError("rótulo sintético inválido")
        abstentions += predicted == "inconclusive"
        results.append({"id": case["id"], "expected": case["label"], "predicted": predicted})
    return {
        "seed": dataset["seed"], "cases": len(results), "legitimate_cases": legitimate,
        "suspicious_cases": suspicious, "false_positives": false_positives,
        "false_positive_rate": false_positives / legitimate if legitimate else 0,
        "false_positive_percent": 100 * false_positives / legitimate if legitimate else 0,
        "true_positives": true_positives, "false_negatives": suspicious - true_positives,
        "abstentions": abstentions, "results": results,
    }


def check_readme(path, metrics):
    match = re.search(r"Falso positivo no dataset: \*\*([0-9]+\.[0-9]{2})% \(([0-9]+)/([0-9]+)\)\*\*", Path(path).read_text())
    expected = (f"{metrics['false_positive_percent']:.2f}", str(metrics["false_positives"]), str(metrics["legitimate_cases"]))
    if not match or match.groups() != expected:
        raise ValueError(f"README diverge da medição: esperado {expected[0]}% ({expected[1]}/{expected[2]})")


def write_json(path, value):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="data/synthetic.json")
    parser.add_argument("--metrics", default="evidence/metrics.json")
    parser.add_argument("--check-readme")
    args = parser.parse_args()
    data = generate()
    metrics = evaluate(data)
    write_json(args.output, data)
    write_json(args.metrics, metrics)
    if args.check_readme:
        check_readme(args.check_readme, metrics)
    print(json.dumps({key: value for key, value in metrics.items() if key != "results"}, ensure_ascii=False))
