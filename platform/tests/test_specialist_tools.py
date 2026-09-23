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


if __name__ == "__main__":
    unittest.main()
