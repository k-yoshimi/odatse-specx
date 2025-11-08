import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np


def _install_odatse_stub():
    """Install a lightweight odatse stub so that optimize_composition can be imported during tests."""

    class DummyInfo:
        def __init__(self, data):
            base = data.get("base", {})
            algorithm = data.get("algorithm", {})
            solver = data.get("solver", {})

            self.base = {
                "root_dir": Path(base.get("root_dir", ".")).absolute(),
                "output_dir": base.get("output_dir", "."),
                "dimension": base.get("dimension"),
            }
            self.algorithm = algorithm
            self.solver = solver

    class DummyRunner:
        def __init__(self, solver, info):
            self.solver = solver
            self.info = info

        def submit(self, x, args):
            return self.solver.evaluate(x)

    class DummyAlgorithmModule:
        class Algorithm:
            def __init__(self, info, runner, *args, **kwargs):
                self.info = info
                self.runner = runner

            def main(self):
                return None

    class DummySolver:
        def __init__(self, info):
            self.info = info
            self.func = None

        def set_function(self, func):
            self.func = func

        def evaluate(self, x):
            return self.func(x)

    class DummyTomlModule:
        @staticmethod
        def load(path):
            return {}

    odatse_stub = types.ModuleType("odatse")
    odatse_stub.Info = DummyInfo
    odatse_stub.Runner = DummyRunner
    odatse_stub.algorithm = DummyAlgorithmModule
    odatse_stub.__version__ = "stub"

    solver_module = types.ModuleType("odatse.solver")
    solver_function_module = types.ModuleType("odatse.solver.function")
    solver_function_module.Solver = DummySolver
    solver_module.function = solver_function_module

    util_module = types.ModuleType("odatse.util")
    util_toml_module = types.ModuleType("odatse.util.toml")
    util_toml_module.load = DummyTomlModule.load
    util_module.toml = util_toml_module

    sys.modules["odatse"] = odatse_stub
    sys.modules["odatse.algorithm"] = DummyAlgorithmModule
    sys.modules["odatse.solver"] = solver_module
    sys.modules["odatse.solver.function"] = solver_function_module
    sys.modules["odatse.util"] = util_module
    sys.modules["odatse.util.toml"] = util_toml_module


_install_odatse_stub()

from optimize_composition import HEAObjective


class TestHEAObjectiveSimplexMode(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name)
        self.template_file = self.root / "template.in"
        self.template_file.write_text("dummy")
        self.mock_output = self.root / "mock.out"
        self.mock_output.write_text("total energy= -1.23\n")

        raw_info = {
            "base": {
                "root_dir": str(self.root),
                "output_dir": "out",
                "dimension": 3,
            },
            "algorithm": {"name": "mapper"},
            "solver": {"name": "function"},
        }

        self.info = sys.modules["odatse"].Info(raw_info)

        self.base_input = {
            "header": [],
            "ntyp": 1,
            "atom_type_definitions": [
                {
                    "type": "Y_1h_2",
                    "ncmp": 1,
                    "rmt": 0.0,
                    "field": 0.0,
                    "mxl": 2,
                    "atoms": [(39, 100.0)],
                }
            ],
            "atomic_header": [],
            "atomic_positions": [
                ("0.0", "0.0", "0.0", "Y_1h_2"),
            ],
            "footer": [],
        }

        self.config = {
            "template_input": str(self.template_file.name),
            "target_label": "Y_1h_2",
            "new_label": "Ln_HEA",
            "work_dir": "runs",
            "output_file": "test.out",
            "akai_command": ["echo", "{input}"],
            "mock_output": str(self.mock_output.relative_to(self.root)),
            "simplex_mode": True,
            "species": [
                {"label": "Y", "atomic_number": 39},
                {"label": "La", "atomic_number": 57},
                {"label": "Nd", "atomic_number": 60},
                {"label": "Sm", "atomic_number": 62},
            ],
        }

    def tearDown(self):
        self.tmpdir.cleanup()

    def _instantiate_objective(self):
        with patch("optimize_composition.load_input_file", return_value=self.base_input), patch(
            "optimize_composition.add_atom_type_definition",
            side_effect=lambda *args, **kwargs: self.base_input,
        ), patch(
            "optimize_composition.replace_atom_types_by_label",
            side_effect=lambda data, mapping: data,
        ), patch("optimize_composition.write_input_file"):
            return HEAObjective(self.config, self.info)

    def test_simplex_mode_fractions_sum_to_one(self):
        objective = self._instantiate_objective()

        params = np.array([0.2, 0.4, 0.6], dtype=float)
        fractions = objective._to_fractions(params)

        self.assertEqual(len(fractions), 4)
        self.assertTrue(np.all(fractions > 0.0))
        self.assertAlmostEqual(fractions.sum(), 1.0, places=6)

        different_params = np.array([0.1, 0.1, 0.1], dtype=float)
        different_fractions = objective._to_fractions(different_params)

        self.assertFalse(np.allclose(fractions, different_fractions))

    def test_simplex_mode_all_ones_behavior(self):
        """全てが1の場合の挙動を確認"""
        objective = self._instantiate_objective()

        # 全てが1.0の場合
        params_all_one = np.array([1.0, 1.0, 1.0], dtype=float)
        fractions = objective._to_fractions(params_all_one)

        self.assertEqual(len(fractions), 4)
        self.assertAlmostEqual(fractions.sum(), 1.0, places=6)
        # 全てが1の場合、最初の成分が大部分を占める
        self.assertGreater(fractions[0], 0.99)
        # 残りの成分は非常に小さい
        self.assertLess(fractions[1], 0.01)
        self.assertLess(fractions[2], 0.01)
        self.assertLess(fractions[3], 0.01)


class TestHEAObjectiveParseEnergy(unittest.TestCase):
    def test_parse_total_energy(self):
        tmpdir = tempfile.TemporaryDirectory()
        try:
            output_file = Path(tmpdir.name) / "test.out"
            output_file.write_text(
                "some header\n"
                "band energy=   60.888109696   total energy= -59275.587686117\n"
                "footer\n"
            )

            raw_info = {
                "base": {
                    "root_dir": tmpdir.name,
                    "output_dir": "out",
                    "dimension": 1,
                },
                "algorithm": {"name": "mapper"},
                "solver": {"name": "function"},
            }
            info = sys.modules["odatse"].Info(raw_info)

            config = {
                "template_input": "dummy.in",
                "target_label": "Y_1h_2",
                "work_dir": "runs",
                "output_file": "test.out",
                "akai_command": ["echo", "{input}"],
                "mock_output": "test.out",
                "species": [
                    {"label": "Y", "atomic_number": 39},
                    {"label": "La", "atomic_number": 57},
                ],
            }

            base_input = {
                "header": [],
                "ntyp": 1,
                "atom_type_definitions": [
                    {
                        "type": "Y_1h_2",
                        "ncmp": 1,
                        "rmt": 0.0,
                        "field": 0.0,
                        "mxl": 2,
                        "atoms": [(39, 100.0)],
                    }
                ],
                "atomic_header": [],
                "atomic_positions": [
                    ("0.0", "0.0", "0.0", "Y_1h_2"),
                ],
                "footer": [],
            }

            with patch("optimize_composition.load_input_file", return_value=base_input), patch(
                "optimize_composition.add_atom_type_definition",
                side_effect=lambda *args, **kwargs: base_input,
            ), patch(
                "optimize_composition.replace_atom_types_by_label",
                side_effect=lambda data, mapping: data,
            ), patch("optimize_composition.write_input_file"):
                objective = HEAObjective(config, info)

            energy = objective.metric.extract(output_file)
            self.assertAlmostEqual(energy, -59275.587686117)
        finally:
            tmpdir.cleanup()

    def test_custom_metric_pattern(self):
        tmpdir = tempfile.TemporaryDirectory()
        try:
            output_file = Path(tmpdir.name) / "test.out"
            output_file.write_text(
                "sigma= 1.2345e+02 mOhm^-1 cm^-1\n"
            )

            raw_info = {
                "base": {
                    "root_dir": tmpdir.name,
                    "output_dir": "out",
                    "dimension": 1,
                },
                "algorithm": {"name": "mapper"},
                "solver": {"name": "function"},
            }
            info = sys.modules["odatse"].Info(raw_info)

            config = {
                "template_input": "dummy.in",
                "target_label": "Y_1h_2",
                "work_dir": "runs",
                "output_file": "test.out",
                "akai_command": ["echo", "{input}"],
                "mock_output": "test.out",
                "metric": {
                    "name": "conductivity",
                    "pattern": r"sigma=\s*([-\d.+Ee]+)",
                },
                "species": [
                    {"label": "Y", "atomic_number": 39},
                    {"label": "La", "atomic_number": 57},
                ],
            }

            base_input = {
                "header": [],
                "ntyp": 1,
                "atom_type_definitions": [
                    {
                        "type": "Y_1h_2",
                        "ncmp": 1,
                        "rmt": 0.0,
                        "field": 0.0,
                        "mxl": 2,
                        "atoms": [(39, 100.0)],
                    }
                ],
                "atomic_header": [],
                "atomic_positions": [
                    ("0.0", "0.0", "0.0", "Y_1h_2"),
                ],
                "footer": [],
            }

            with patch("optimize_composition.load_input_file", return_value=base_input), patch(
                "optimize_composition.add_atom_type_definition",
                side_effect=lambda *args, **kwargs: base_input,
            ), patch(
                "optimize_composition.replace_atom_types_by_label",
                side_effect=lambda data, mapping: data,
            ), patch("optimize_composition.write_input_file"):
                objective = HEAObjective(config, info)

            value = objective.metric.extract(output_file)
            self.assertAlmostEqual(value, 123.45)
        finally:
            tmpdir.cleanup()


if __name__ == "__main__":
    unittest.main()
