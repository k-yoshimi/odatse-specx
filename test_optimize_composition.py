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

from optimize_composition import HEAObjective, MetricExtractor


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
                    "dimension": 2,  # 2 species, no simplex_mode
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

    def test_parse_band_energy_case_insensitive(self):
        tmpdir = tempfile.TemporaryDirectory()
        try:
            output_file = Path(tmpdir.name) / "test.out"
            # Uppercase field name to verify ignore_case works
            output_file.write_text("BAND ENERGY= 12.34\n")

            metric = MetricExtractor({"name": "band_energy"})
            value = metric.extract(output_file)
            self.assertAlmostEqual(value, 12.34)
        finally:
            tmpdir.cleanup()

    def test_custom_metric_group_and_scale(self):
        tmpdir = tempfile.TemporaryDirectory()
        try:
            output_file = Path(tmpdir.name) / "test.out"
            output_file.write_text("val=1 foo=42\n")

            metric = MetricExtractor(
                {
                    "name": "custom",
                    "pattern": r"val=(\d+)\s+foo=(\d+)",
                    "group": 2,
                    "scale": 0.1,
                }
            )
            value = metric.extract(output_file)
            self.assertAlmostEqual(value, 4.2)
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
                    "dimension": 2,  # 2 species, no simplex_mode
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


class TestHEAObjectiveErrorHandling(unittest.TestCase):
    """Test error handling in HEAObjective when output file handling fails."""

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
                "dimension": 2,
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
            "simplex_mode": False,
            "species": [
                {"label": "Y", "atomic_number": 39},
                {"label": "La", "atomic_number": 57},
            ],
        }

    def tearDown(self):
        self.tmpdir.cleanup()

    def _instantiate_objective(self, config_overrides=None):
        config = self.config.copy()
        if config_overrides:
            config.update(config_overrides)

        with patch("optimize_composition.load_input_file", return_value=self.base_input), patch(
            "optimize_composition.add_atom_type_definition",
            side_effect=lambda *args, **kwargs: self.base_input,
        ), patch(
            "optimize_composition.replace_atom_types_by_label",
            side_effect=lambda data, mapping: data,
        ), patch("optimize_composition.write_input_file"):
            return HEAObjective(config, self.info)

    def test_file_not_found_error_returns_penalty(self):
        """Test that FileNotFoundError returns error_penalty."""
        # Create objective without mock_output and with a command that doesn't create output
        objective = self._instantiate_objective(
            {
                "error_penalty": 999.0,
                "mock_output": None,
                "akai_command": ["echo", "test"],  # Command that doesn't create output_file
            }
        )

        params = np.array([0.5, 0.5], dtype=float)
        result = objective(params)

        self.assertEqual(result, 999.0)
        self.assertIsInstance(result, float)

    def test_custom_error_penalty(self):
        """Test that custom error_penalty is used."""
        custom_penalty = 5555.0
        objective = self._instantiate_objective(
            {"error_penalty": custom_penalty, "mock_output": None}
        )

        params = np.array([0.5, 0.5], dtype=float)
        result = objective(params)

        self.assertEqual(result, custom_penalty)

    def test_metric_not_found_returns_penalty(self):
        """Test that RuntimeError when metric not found returns penalty."""
        # Create output file without the metric
        output_without_metric = self.root / "no_metric.out"
        output_without_metric.write_text("some content\nbut no total energy\n")

        objective = self._instantiate_objective(
            {
                "mock_output": str(output_without_metric.relative_to(self.root)),
                "error_penalty": 777.0,
            }
        )

        params = np.array([0.5, 0.5], dtype=float)
        result = objective(params)

        self.assertEqual(result, 777.0)

    def test_error_log_written_on_error(self):
        """Test that error log is written when error occurs."""
        error_log_path = self.root / "error_log.txt"

        objective = self._instantiate_objective(
            {
                "error_log": str(error_log_path.relative_to(self.root)),
                "error_penalty": 888.0,
                "mock_output": None,  # Trigger FileNotFoundError
            }
        )

        params = np.array([0.5, 0.5], dtype=float)
        result = objective(params)

        self.assertEqual(result, 888.0)
        self.assertTrue(error_log_path.exists())

        log_content = error_log_path.read_text()
        self.assertIn("ERROR", log_content)
        self.assertIn("FileNotFoundError", log_content)
        self.assertIn("Input file", log_content)
        self.assertIn("Output file", log_content)
        self.assertIn("Trial directory", log_content)

    def test_error_log_not_written_when_no_error(self):
        """Test that error log is not written when no error occurs."""
        error_log_path = self.root / "error_log.txt"

        objective = self._instantiate_objective(
            {"error_log": str(error_log_path.relative_to(self.root))}
        )

        params = np.array([0.5, 0.5], dtype=float)
        result = objective(params)

        # Should succeed and return energy value
        self.assertAlmostEqual(result, -1.23)
        # Error log should not exist or be empty
        if error_log_path.exists():
            self.assertEqual(error_log_path.read_text(), "")

    def test_keep_intermediate_on_error(self):
        """Test that intermediate files are kept when keep_intermediate=true on error."""
        objective = self._instantiate_objective(
            {
                "keep_intermediate": True,
                "error_penalty": 999.0,
                "mock_output": None,  # Trigger error
            }
        )

        params = np.array([0.5, 0.5], dtype=float)
        result = objective(params)

        self.assertEqual(result, 999.0)

        # Check that trial directory still exists
        work_dir = self.root / "runs"
        trial_dirs = list(work_dir.glob("trial_*"))
        self.assertGreater(len(trial_dirs), 0)
        # At least one trial directory should exist
        self.assertTrue(any(trial_dir.exists() for trial_dir in trial_dirs))

    def test_remove_intermediate_on_error(self):
        """Test that intermediate files are removed when keep_intermediate=false on error."""
        objective = self._instantiate_objective(
            {
                "keep_intermediate": False,
                "error_penalty": 111.0,
                "mock_output": None,  # Trigger error
            }
        )

        params = np.array([0.5, 0.5], dtype=float)
        result = objective(params)

        self.assertEqual(result, 111.0)

        # Check that trial directories are removed
        work_dir = self.root / "runs"
        if work_dir.exists():
            trial_dirs = list(work_dir.glob("trial_*"))
            # All trial directories should be removed
            self.assertEqual(len([d for d in trial_dirs if d.exists()]), 0)

    def test_akai_kkr_execution_failure(self):
        """Test that AkaiKKR execution failure returns penalty."""
        objective = self._instantiate_objective(
            {
                "mock_output": None,  # Use real command
                "akai_command": ["false"],  # Command that always fails
                "error_penalty": 222.0,
            }
        )

        params = np.array([0.5, 0.5], dtype=float)
        result = objective(params)

        self.assertEqual(result, 222.0)

    def test_multiple_errors_logged(self):
        """Test that multiple errors are logged correctly."""
        error_log_path = self.root / "error_log.txt"

        objective = self._instantiate_objective(
            {
                "error_log": str(error_log_path.relative_to(self.root)),
                "error_penalty": 333.0,
                "mock_output": None,
            }
        )

        # Trigger multiple errors
        params1 = np.array([0.5, 0.5], dtype=float)
        result1 = objective(params1)

        params2 = np.array([0.3, 0.7], dtype=float)
        result2 = objective(params2)

        self.assertEqual(result1, 333.0)
        self.assertEqual(result2, 333.0)

        # Check that both errors are logged
        log_content = error_log_path.read_text()
        error_count = log_content.count("ERROR")
        self.assertGreaterEqual(error_count, 2)

    def test_unexpected_exception_handling(self):
        """Test that unexpected exceptions are caught and return penalty."""
        # Create an objective that will raise an unexpected error
        objective = self._instantiate_objective({"error_penalty": 444.0})

        # Patch extract to raise an unexpected exception
        with patch.object(
            objective.metric, "extract", side_effect=KeyError("unexpected")
        ):
            params = np.array([0.5, 0.5], dtype=float)
            result = objective(params)

            self.assertEqual(result, 444.0)


if __name__ == "__main__":
    unittest.main()
