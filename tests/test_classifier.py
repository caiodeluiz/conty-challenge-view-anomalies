import json
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import HTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from api import Handler
from classifier import classify
from dataset import check_readme, evaluate, generate


ROOT = Path(__file__).resolve().parents[1]


class ClassifierTests(unittest.TestCase):
    def test_gradual_organic_viral_is_not_a_bought_spike(self):
        data = generate()
        organic = next(case for case in data["cases"] if case["id"] == "organic-viral-00")
        bought = next(case for case in data["cases"] if case["id"] == "suspicious-isolated-00")
        self.assertEqual(classify(organic["views"])["classification"], "legitimate")
        result = classify(bought["views"])
        self.assertEqual(result["classification"], "suspicious")
        self.assertTrue(result["signals"]["isolated_peak_followed_by_drop"])
        self.assertIn("hora seguinte", result["reason"])

    def test_mechanical_repetition_and_low_volume_differ(self):
        self.assertEqual(classify([900] * 24)["classification"], "suspicious")
        self.assertEqual(classify([9] * 24)["classification"], "legitimate")

    def test_plateau_drop_with_small_jitter(self):
        result = classify([12] * 6 + [2000, 2002, 1998, 2003, 2001, 1999] + [2] * 12)
        self.assertEqual(result["classification"], "suspicious")
        self.assertTrue(result["signals"]["near_constant_plateau_followed_by_drop"])

    def test_plateau_requires_minimum_volume_in_every_hour(self):
        for first in (490, 499):
            with self.subTest(first_hour=first):
                result = classify([10] * 6 + [first, 500, 500, 500, 500, 500] + [10] * 12)
                self.assertEqual(result["classification"], "legitimate")
                self.assertFalse(result["signals"]["near_constant_plateau_followed_by_drop"])
                self.assertEqual(result["signals"]["longest_identical_high_run"], 5)

    def test_plateau_each_hour_at_or_above_exact_minimum_still_matches(self):
        result = classify([10] * 6 + [500, 500, 501, 501, 500, 500] + [50] + [10] * 11)
        self.assertEqual(result["classification"], "suspicious")
        self.assertTrue(result["signals"]["near_constant_plateau_followed_by_drop"])
        self.assertIn("500 views em cada hora", result["reason"])

    def test_prefers_not_to_accuse_when_information_is_sparse(self):
        for views in ([0] * 23 + [9000], [1000] * 5, [0] * 24):
            with self.subTest(views=views):
                self.assertEqual(classify(views)["classification"], "inconclusive")

    def test_peak_at_last_hour_does_not_invent_a_future_drop(self):
        result = classify([30] * 23 + [9000])
        self.assertFalse(result["signals"]["isolated_peak_followed_by_drop"])
        self.assertNotEqual(result["classification"], "suspicious")

    def test_peak_at_either_edge_prefers_inconclusive_with_faithful_reason(self):
        for views in ([9000] + [30] * 23, [30] * 23 + [9000]):
            result = classify(views)
            self.assertEqual(result["classification"], "inconclusive")
            self.assertIn("extremidade", result["reason"])
            self.assertNotIn("pico gradual", result["reason"])

    def test_invalid_series_rejected(self):
        for views in (None, [], "100", [True], [-1], [1.5], [float("nan")], [2**53], [0] * 8761):
            with self.subTest(value=str(views)[:50]):
                with self.assertRaises(ValueError):
                    classify(views)

    def test_dataset_is_reproducible_and_labels_do_not_depend_on_predictions(self):
        self.assertEqual(generate(), generate())
        data = generate()
        self.assertEqual(len(data["cases"]), 60)
        counterexample = next(case for case in data["cases"] if case["id"] == "organic-live-counterexample")
        self.assertEqual(counterexample["label"], "legitimate")
        self.assertEqual(classify(counterexample["views"])["classification"], "suspicious")

    def test_readme_false_positive_number_matches_measured(self):
        metrics = evaluate(generate())
        check_readme(ROOT / "README.md", metrics)
        self.assertEqual(metrics["legitimate_cases"], 40)
        self.assertEqual(metrics["false_positives"], 1)
        self.assertEqual(metrics["false_negatives"], 0)

    def test_readme_drift_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            readme = Path(directory) / "README.md"
            readme.write_text("Falso positivo no dataset: **0.00% (0/40)**")
            with self.assertRaisesRegex(ValueError, "diverge"):
                check_readme(readme, evaluate(generate()))

    def test_generation_command_recreates_committed_data_and_measures(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "data.json"
            metrics = Path(directory) / "metrics.json"
            result = subprocess.run(
                [sys.executable, str(ROOT / "dataset.py"), "--output", str(output), "--metrics", str(metrics), "--check-readme", str(ROOT / "README.md")],
                check=True, capture_output=True, text=True, cwd=ROOT,
            )
            self.assertEqual(json.loads(result.stdout)["false_positive_percent"], 2.5)
            self.assertEqual(output.read_bytes(), (ROOT / "data/synthetic.json").read_bytes())
            self.assertEqual(json.loads(metrics.read_text()), evaluate(generate()))


class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def post(self, raw, path="/classify"):
        request = Request(self.url + path, data=raw, headers={"Content-Type": "application/json"})
        try:
            response = urlopen(request, timeout=3)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.loads(response.read())

    def test_api_response_contains_explanation_and_signals(self):
        status, body = self.post(json.dumps({"views": [900] * 24}).encode())
        self.assertEqual(status, 200)
        self.assertEqual(body["classification"], "suspicious")
        self.assertTrue(body["reason"])
        self.assertEqual(body["signals"]["hours"], 24)

    def test_bad_json_nan_and_invalid_counts_are_400(self):
        for raw in (b"{", b'{"views":[NaN]}', b'{"views":[true]}', b"[]", b"{}"):
            with self.subTest(raw=raw):
                status, body = self.post(raw)
                self.assertEqual(status, 400)
                self.assertIn("error", body)

    def test_unknown_route(self):
        self.assertEqual(self.post(b"{}", "/unknown")[0], 404)


if __name__ == "__main__":
    unittest.main()
