import math
import tempfile
import unittest
from pathlib import Path

from history import (
    create_operation,
    delete_operation,
    get_operations,
    initialize_database,
    update_description,
)
from numerical_methods import evaluate_expression, solve


class NumericalMethodsTests(unittest.TestCase):
    def test_bisection_finds_root(self) -> None:
        result = solve(
            "bisection",
            "x**2 - 2",
            {"a": 0, "b": 2, "tolerance": 1e-8, "max_iterations": 100},
        )
        self.assertAlmostEqual(result["value"], math.sqrt(2), places=7)

    def test_newton_finds_root(self) -> None:
        result = solve(
            "newton",
            "x**2 - 2",
            {"x0": 1, "tolerance": 1e-8, "max_iterations": 100},
        )
        self.assertAlmostEqual(result["value"], math.sqrt(2), places=7)

    def test_integral_methods_evaluate_polynomials(self) -> None:
        trapezoid = solve(
            "trapezoid", "x", {"a": 0, "b": 1, "intervals": 1000}
        )
        simpson = solve("simpson", "x**3", {"a": 0, "b": 1, "intervals": 10})
        self.assertAlmostEqual(trapezoid["value"], 0.5, places=6)
        self.assertAlmostEqual(simpson["value"], 0.25, places=12)

    def test_rejects_unsupported_expression_syntax(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_expression("__import__('os').system('echo unsafe')", 1)

    def test_simpson_requires_an_even_interval_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "número par"):
            solve("simpson", "x", {"a": 0, "b": 1, "intervals": 3})


class HistoryTests(unittest.TestCase):
    def test_create_read_update_and_delete(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "history.db"
            initialize_database(database_path)
            operation_id = create_operation(
                method="Bisección",
                expression="x**2 - 2",
                parameters={"a": 0, "b": 2},
                result={"value": math.sqrt(2), "iterations": 20, "residual": 1e-8},
                description="Raíz de 2",
                database_path=database_path,
            )

            self.assertEqual(len(get_operations(database_path)), 1)
            update_description(operation_id, "Prueba editada", database_path)
            self.assertEqual(
                get_operations(database_path)[0]["description"], "Prueba editada"
            )
            delete_operation(operation_id, database_path)
            self.assertEqual(get_operations(database_path), [])


if __name__ == "__main__":
    unittest.main()
