import pathlib
import sys
import unittest

PLATFORM = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))

from specialist_tools import (
    ToolWorkerError,
    safe_eval,
    solve_code,
    solve_engineering,
    solve_error_detection,
    solve_math,
    solve_planning,
    solve_research,
    try_solve,
)


class SpecialistToolTests(unittest.TestCase):
    def test_math_arithmetic_and_linear_equation(self):
        self.assertEqual(solve_math("Return only the number. Compute: 17*23")["answer"], "391")
        self.assertEqual(solve_math("Return only x. Solve for x: 3*x+5=29")["answer"], "8")

    def test_code_is_restricted_but_useful(self):
        self.assertEqual(
            solve_code("Return only the Python result: sorted([3,1,2])[1]")["answer"],
            "2",
        )
        with self.assertRaises(ToolWorkerError):
            safe_eval("__import__('os').system('id')")
        with self.assertRaises(ToolWorkerError):
            safe_eval("(1).__class__")

    def test_engineering_formula_worker(self):
        result = solve_engineering("Using P=Fv; F=80; v=2.5. Return only P.")
        self.assertEqual(result["answer"], "200")

    def test_source_extraction_does_not_invent(self):
        result = solve_research(
            "SOURCE: alpha=0.25; beta=0.75; gamma=1.50. "
            "Using only the source, return only beta."
        )
        self.assertEqual(result["answer"], "0.75")
        self.assertIsNone(
            solve_research(
                "SOURCE: alpha=0.25. Using only the source, return only missing."
            )
        )

    def test_planning_constraint_checker(self):
        result = solve_planning(
            "Return only A, B, or C. Constraints: X first; Y before Z. "
            "Options: A=Y,X,Z; B=X,Z,Y; C=X,Y,Z."
        )
        self.assertEqual(result["answer"], "C")

    def test_false_arithmetic_claim_checker(self):
        result = solve_error_detection(
            "Return only the false letter. A: 2+2=4; B: 3*3=9; C: 10/2=6;"
        )
        self.assertEqual(result["answer"], "C")

    def test_unknown_task_fails_to_model_fallback_boundary(self):
        result = try_solve("Écris un court poème sur la Lune.")
        self.assertFalse(result["handled"])
        self.assertEqual(result["status"], "NOT_APPLICABLE")


    def test_semantic_math_transfer_forms(self):
        self.assertEqual(solve_math("Multiply 17 by 23. Reply with the numeric answer and nothing else.")["answer"], "391")
        self.assertEqual(solve_math("Which number x satisfies 3x + 5 = 29? Output x only.")["answer"], "8")
        self.assertEqual(solve_math("Give only the greatest common divisor of 36 and 84.")["answer"], "12")
        self.assertEqual(solve_math("Only the numeric value: 25% of 320.")["answer"], "80")

    def test_semantic_code_transfer_form_stays_sandboxed(self):
        self.assertEqual(
            solve_code("Evaluate this safe Python expression: sorted([4,1,3])[1]. Respond only with its value.")["answer"],
            "3",
        )
        self.assertIsNone(solve_code("Evaluate JavaScript: process.exit()."))

    def test_semantic_engineering_transfer_forms(self):
        self.assertEqual(
            solve_engineering("A mass of 20 kg accelerates at 2.5 m/s^2. What force in newtons? Number only.")["answer"],
            "50",
        )
        self.assertEqual(
            solve_engineering("A force of 80 N acts while moving at 2.5 m/s. Mechanical power in watts? Number only.")["answer"],
            "200",
        )

    def test_semantic_grounded_lookup_transfer_form(self):
        r = solve_research(
            "Reference data — alpha: 0.25 | beta: 0.75 | gamma: 1.50. "
            "Based solely on that reference, provide the value for beta; output only the value."
        )
        self.assertEqual(r["answer"], "0.75")

    def test_semantic_planning_transfer_form(self):
        r = solve_planning(
            "Scheduling rules — J must be first; K must come before L; M must be last. "
            "Candidate orders — X: J > K > L > M / Y: K > J > L > M / Z: J > L > K > M."
        )
        self.assertEqual(r["answer"], "X")

    def test_semantic_error_detection_transfer_form(self):
        r = solve_error_detection(
            "Exactly one statement is wrong. X) 2+2=4; Y) 3*3=8; Z) 10/2=5. Reply only X, Y, or Z."
        )
        self.assertEqual(r["answer"], "Y")

    def test_semantic_contract_unknown_text_still_falls_back(self):
        r = try_solve("Compare two philosophical interpretations of scientific realism.")
        self.assertFalse(r["handled"])
        self.assertEqual(r["status"], "NOT_APPLICABLE")


if __name__ == "__main__":
    unittest.main()
