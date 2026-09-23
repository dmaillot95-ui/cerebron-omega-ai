import pathlib
import sys
import unittest

PLATFORM = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))

from semantic_tools import semantic_try_solve


class SemanticDispatchTests(unittest.TestCase):
    def test_math_product_paraphrase(self):
        r=semantic_try_solve("Give only the product of 18 and 27.")
        self.assertTrue(r["handled"])
        self.assertEqual(r["answer"], "486")

    def test_python_expression_after_instruction_text(self):
        r=semantic_try_solve("Evaluate this Python expression and answer only with the value: (7+5)*2")
        self.assertTrue(r["handled"])
        self.assertEqual(r["answer"], "24")

    def test_engineering_natural_language(self):
        r=semantic_try_solve("A mass of 12 kg accelerates at 3.5 m/s^2. Using force equals mass times acceleration, give only the force.")
        self.assertTrue(r["handled"])
        self.assertEqual(r["answer"], "42")

    def test_grounded_data_field(self):
        r=semantic_try_solve("FACTS: alpha is 0.250; beta is 0.750; gamma is 1.500. Based only on FACTS, give the value of beta.")
        self.assertTrue(r["handled"])
        self.assertEqual(r["answer"], "0.750")

    def test_planning_arrows_and_pipe_options(self):
        r=semantic_try_solve("Choose only A, B, or C. K must be first; L must occur before M. Candidate orders: A: L > K > M | B: K > M > L | C: K > L > M")
        self.assertTrue(r["handled"])
        self.assertEqual(r["answer"], "C")

    def test_wrong_claim_synonym(self):
        r=semantic_try_solve("Which claim is incorrect? Reply only with its letter. A) 4+4=8; B) 9-3=6; C) 5*5=24")
        self.assertTrue(r["handled"])
        self.assertEqual(r["answer"], "C")

    def test_unknown_creative_request_does_not_force_tool(self):
        r=semantic_try_solve("Write a short story about a rover.")
        self.assertFalse(r["handled"])


if __name__ == "__main__":
    unittest.main()
