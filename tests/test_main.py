import time
import unittest
from unittest.mock import patch

from main import EXPECTED_ANSWER, extract_final_answer, run_models


class ExtractFinalAnswerTests(unittest.TestCase):
    def test_extracts_chinese_final_answer(self) -> None:
        reply = "先分析各种最坏情况。最终答案为 21 颗。"
        self.assertEqual(extract_final_answer(reply), EXPECTED_ANSWER)

    def test_uses_last_explicit_answer(self) -> None:
        reply = "一开始猜答案为 25。重新计算后，最终答案：21颗。"
        self.assertEqual(extract_final_answer(reply), EXPECTED_ANSWER)

    def test_extracts_boxed_answer(self) -> None:
        self.assertEqual(extract_final_answer(r"Therefore, \\boxed{21}"), EXPECTED_ANSWER)

    def test_returns_none_without_final_signal(self) -> None:
        self.assertIsNone(extract_final_answer("圆形有 7、9、8 颗，继续讨论。"))


class RunModelsTests(unittest.TestCase):
    def test_runs_models_and_reports_progress(self) -> None:
        progress = []

        def fake_call(base_url: str, api_key: str, model: str, temperature: float):
            time.sleep(0.001)
            return model, "ok", "答案为 21", 0.001

        with patch("main.call_and_capture", side_effect=fake_call):
            results = run_models(
                "https://example.com/v1",
                "secret",
                ["model-a", "model-b", "model-c"],
                0,
                2,
                lambda result, completed, total: progress.append((completed, total)),
            )

        self.assertEqual({result[0] for result in results}, {"model-a", "model-b", "model-c"})
        self.assertEqual(progress, [(1, 3), (2, 3), (3, 3)])


if __name__ == "__main__":
    unittest.main()
