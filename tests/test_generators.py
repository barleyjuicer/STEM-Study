import os
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC))

os.environ["STEM_STUDY_PORTABLE_DIR"] = str(PROJECT_ROOT / "work" / "test_runtime")

from stem_study_generator import app  # noqa: E402


class GeneratorTests(unittest.TestCase):
    def test_required_generators_grade_correct_answers(self):
        checks = [
            ("Physics II", "Coulomb's Law", "Easy"),
            ("Physics II", "Ohm's Law", "Easy"),
            ("Intro Cryptography", "Modular arithmetic", "Easy"),
            ("Intro Cryptography", "Toy RSA encryption/decryption", "Easy"),
        ]
        for subject, topic, difficulty in checks:
            with self.subTest(topic=topic):
                problem = app.make_problem(subject, topic, difficulty)
                answer = str(problem["correct_answer"])
                if problem["answer_type"] == "numeric":
                    answer = f"{answer} {problem['units']}"
                is_correct, note, warning = app.grade_answer(problem, answer)
                self.assertTrue(is_correct, note)
                self.assertIsNone(warning)

    def test_numeric_answer_warns_for_wrong_unit_without_failing(self):
        problem = app.make_problem("Physics II", "Ohm's Law", "Easy")
        answer = f"{problem['correct_answer']} kg"
        is_correct, note, warning = app.grade_answer(problem, answer)
        self.assertTrue(is_correct, note)
        self.assertIsNotNone(warning)
        self.assertIn("expected", warning)


if __name__ == "__main__":
    unittest.main()
