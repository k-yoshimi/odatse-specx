#!/usr/bin/env python3
"""
High-entropy alloy (HEA) composition optimizer for AkaiKKR.

This script couples ODAT-SE's search algorithms with the helper utilities
provided in generate_input.py so that alloy compositions can be scanned
automatically.  Each candidate composition is converted into an AkaiKKR
input file, the solver is executed (or a mock output is copied), and the
total energy reported by AkaiKKR is fed back to ODAT-SE as the objective
value to minimize.

Usage
-----
    python optimize_composition.py hea_mapper.toml

See ``hea_mapper.toml`` for a minimal configuration that sweeps the rare-earth
composition on the ``Y_1h_2`` site and parses the ``total energy`` field from
``refs/REBCO/test-1/test.out``.
"""

from __future__ import annotations

import argparse
import math
import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import numpy as np
import odatse
import odatse.algorithm
import odatse.solver.function
import odatse.util.toml

from generate_input import (
    add_atom_type_definition,
    load_input_file,
    replace_atom_types_by_label,
    write_input_file,
)

DEFAULT_METRIC_PATTERNS = {
    "total_energy": r"total energy=?\s+([-\d.+Ee]+)",
    "band_energy": r"band energy=?\s+([-\d.+Ee]+)",
}


def _as_command_list(command: Any) -> List[str]:
    """Convert a TOML value into a command list."""
    if isinstance(command, str):
        return shlex.split(command)
    if isinstance(command, Sequence):
        return [str(token) for token in command]
    raise ValueError("akai_command must be a list or a string")


class MetricExtractor:
    """Utility to parse scalar metrics from AkaiKKR output."""

    _TRANSFORMS = {
        "identity": lambda x: x,
        "abs": lambda x: abs(x),
        "log": lambda x: math.log(x),
        "log1p": lambda x: math.log1p(x),
        "sqrt": lambda x: math.sqrt(x),
        "square": lambda x: x * x,
    }

    def __init__(self, metric_cfg: Dict[str, Any]):
        name = metric_cfg.get("name", "total_energy")
        pattern = metric_cfg.get("pattern") or DEFAULT_METRIC_PATTERNS.get(name)
        if not pattern:
            raise ValueError(
                f"Unsupported metric '{name}'. Provide a custom regex via metric.pattern."
            )

        ignore_case = metric_cfg.get("ignore_case", True)
        flags = re.IGNORECASE if ignore_case else 0
        self.pattern = re.compile(pattern, flags)
        self.group = int(metric_cfg.get("group", 1))
        self.scale = float(metric_cfg.get("scale", 1.0))
        self.name = name

        transform_name = metric_cfg.get("transform", "identity")
        transform = self._TRANSFORMS.get(transform_name)
        if transform is None:
            supported = ", ".join(sorted(self._TRANSFORMS))
            raise ValueError(
                f"Unsupported metric.transform '{transform_name}'. "
                f"Choose from: {supported}"
            )
        self.transform = transform

    def extract(self, output_path: Path) -> float:
        if not output_path.exists():
            raise FileNotFoundError(f"{output_path} was not created by AkaiKKR.")

        with output_path.open("r", encoding="utf-8", errors="ignore") as fp:
            for line in fp:
                match = self.pattern.search(line)
                if match:
                    value = float(match.group(self.group))
                    scaled = value * self.scale
                    return self.transform(scaled)

        raise RuntimeError(
            f"Metric '{self.name}' not found in {output_path}. "
            "Adjust [hea.metric] settings if the output format differs."
        )


class HEAObjective:
    """
    Callable wrapper that maps ODAT-SE parameters to AkaiKKR total energy.
    """

    def __init__(self, config: Dict[str, Any], info: odatse.Info):
        if not config:
            raise ValueError("Missing [hea] section in the TOML config.")

        self.info = info
        self.root_dir = Path(info.base.get("root_dir", ".")).expanduser().absolute()
        self.template_input = self.root_dir / config["template_input"]
        self.target_label = config["target_label"]
        self.new_label = config.get("new_label", f"{self.target_label}_mix")
        self.work_dir = (self.root_dir / config.get("work_dir", "runs")).absolute()
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.output_filename = config.get("output_file", "test.out")
        self.keep_intermediate = bool(config.get("keep_intermediate", False))
        # akai_command examples:
        #   ["specx", "<", "{input}", ">", "{output}"]  -> specx < test.in > test.out
        #   ["specx", "<", "{input}"]                    -> specx < test.in (stdin redirection)
        #   ["specx", "{input}"]                         -> specx test.in (command argument)
        #   ["specx", "{input_path}"]                    -> specx /full/path/to/test.in
        # Placeholders:
        #   {input} = filename only (e.g., "test.in")
        #   {input_path} = full path (e.g., "/full/path/to/test.in")
        #   {output} = output filename (e.g., "test.out")
        self.command_template = _as_command_list(config.get("akai_command", []))
        if not self.command_template:
            raise ValueError("akai_command must be provided inside [hea].")
        self.command_timeout = config.get("timeout_sec")
        self.command_env = os.environ.copy()
        self.command_env.update(config.get("env", {}))
        self.mock_output = config.get("mock_output")
        if self.mock_output:
            self.mock_output = (self.root_dir / self.mock_output).absolute()
        self.trial_counter = 0
        self.metric = MetricExtractor(config.get("metric", {}))

        # Error handling configuration
        self.error_penalty = float(config.get("error_penalty", 1.0e10))
        self.error_log_file = config.get("error_log")
        if self.error_log_file:
            self.error_log_file = (self.root_dir / self.error_log_file).absolute()
            self.error_log_file.parent.mkdir(parents=True, exist_ok=True)

        self.base_input_data = load_input_file(self.template_input)
        self.reference_type = self._get_reference_type()
        self.mix_rmt = float(config.get("rmt", self.reference_type["rmt"]))
        self.mix_field = float(config.get("field", self.reference_type["field"]))
        self.mix_mxl = int(config.get("mxl", self.reference_type["mxl"]))
        self.simplex_mode = bool(config.get("simplex_mode", False))

        species_cfg = config.get("species", [])
        if not species_cfg:
            raise ValueError("Define at least one [[hea.species]] entry.")
        self.species = [
            {
                "label": entry.get("label") or entry.get("symbol"),
                "atomic_number": int(entry["atomic_number"]),
            }
            for entry in species_cfg
        ]

        if self.simplex_mode and len(self.species) < 2:
            raise ValueError("Define at least two species to enable simplex_mode.")

        expected_dim = len(self.species) - 1 if self.simplex_mode else len(self.species)
        base_dim = self.info.base.get("dimension")
        if base_dim and base_dim != expected_dim:
            raise ValueError(
                "base.dimension ({}) must equal {} (len(species)={}{}).".format(
                    base_dim,
                    expected_dim,
                    len(self.species),
                    " - 1 for simplex_mode" if self.simplex_mode else "",
                )
            )

    def __call__(self, params: np.ndarray) -> float:
        """
        Evaluate a candidate composition and return the objective value.

        Parameters
        ----------
        params : np.ndarray
            ODAT-SE parameters (converted to fractions).

        Returns
        -------
        float
            Objective value (total energy or error penalty).
        """
        fractions = self._to_fractions(params)
        trial_dir = self._prepare_trial_dir()
        input_path = trial_dir / self.template_input.name
        output_path = trial_dir / self.output_filename

        try:
            modified = self._build_input_data(fractions)
            write_input_file(modified, input_path)

            if self.mock_output:
                shutil.copy(self.mock_output, output_path)
            else:
                self._run_akai_kkr(input_path, trial_dir)

            energy = self.metric.extract(output_path)
            print(
                f"[Trial {self.trial_counter:05d}] fractions={fractions} -> {self.metric.name}={energy}"
            )

            if not self.keep_intermediate:
                shutil.rmtree(trial_dir, ignore_errors=True)

            return energy

        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            error_msg = (
                f"[Trial {self.trial_counter:05d}] ERROR: fractions={fractions} -> "
                f"{type(exc).__name__}: {exc}"
            )
            print(error_msg)

            if self.error_log_file:
                with self.error_log_file.open("a", encoding="utf-8") as f:
                    f.write(f"{error_msg}\n")
                    f.write(f"  Input file: {input_path}\n")
                    f.write(f"  Output file: {output_path}\n")
                    f.write(f"  Trial directory: {trial_dir}\n")
                    f.write("\n")

            # Keep intermediate files on error if configured
            if not self.keep_intermediate:
                shutil.rmtree(trial_dir, ignore_errors=True)

            return self.error_penalty

        except Exception as exc:
            error_msg = (
                f"[Trial {self.trial_counter:05d}] UNEXPECTED ERROR: "
                f"fractions={fractions} -> {type(exc).__name__}: {exc}"
            )
            print(error_msg)

            if self.error_log_file:
                with self.error_log_file.open("a", encoding="utf-8") as f:
                    f.write(f"{error_msg}\n")
                    f.write(f"  Input file: {input_path}\n")
                    f.write(f"  Output file: {output_path}\n")
                    f.write(f"  Trial directory: {trial_dir}\n")
                    f.write("\n")

            if not self.keep_intermediate:
                shutil.rmtree(trial_dir, ignore_errors=True)

            return self.error_penalty

    def _prepare_trial_dir(self) -> Path:
        self.trial_counter += 1
        trial_dir = self.work_dir / f"trial_{self.trial_counter:05d}"
        trial_dir.mkdir(parents=True, exist_ok=True)
        return trial_dir

    def _get_reference_type(self) -> Dict[str, Any]:
        for entry in self.base_input_data.get("atom_type_definitions", []):
            if entry["type"] == self.target_label:
                return entry
        raise ValueError(f"Atom type '{self.target_label}' not found in template.")

    def _build_input_data(self, fractions: np.ndarray) -> Dict[str, Any]:
        atoms = [
            (spec["atomic_number"], round(float(frac) * 100.0, 6))
            for spec, frac in zip(self.species, fractions)
        ]
        mixed = add_atom_type_definition(
            self.base_input_data,
            type_name=self.new_label,
            ncmp=len(self.species),
            rmt=self.mix_rmt,
            field=self.mix_field,
            mxl=self.mix_mxl,
            atoms=atoms,
        )
        return replace_atom_types_by_label(
            mixed,
            {self.target_label: self.new_label},
        )

    def _run_akai_kkr(self, input_path: Path, trial_dir: Path) -> None:
        """
        Execute AkaiKKR command with input file handling.
        
        Supports stdin/stdout redirection (<, >) and placeholder substitution:
        - {input} -> input_path.name (e.g., "test.in")
        - {input_path} -> str(input_path) (e.g., "/full/path/to/test.in")
        - {output} -> output_filename (e.g., "test.out")
        """
        cmd = []
        stdin_file = None
        stdout_file = None
        skip_next = False
        
        for i, token in enumerate(self.command_template):
            if skip_next:
                skip_next = False
                continue
            
            # Replace placeholders: {input} = filename, {input_path} = full path, {output} = output filename
            replaced = token.replace("{input}", input_path.name).replace(
                "{input_path}", str(input_path)
            ).replace("{output}", self.output_filename)
            
            if replaced == "<":
                # Handle stdin redirection: < filename
                # Next token should be the input file (may contain {input} or {input_path})
                if i + 1 < len(self.command_template):
                    next_token = self.command_template[i + 1].replace(
                        "{input}", input_path.name
                    ).replace("{input_path}", str(input_path))
                    # Open file relative to trial_dir
                    stdin_file = (trial_dir / next_token).open("r")
                    skip_next = True
                else:
                    # If < is at the end, use input_path directly
                    stdin_file = input_path.open("r")
            elif replaced == ">":
                # Handle stdout redirection: > filename
                # Next token should be the output file (may contain {output})
                if i + 1 < len(self.command_template):
                    next_token = self.command_template[i + 1].replace(
                        "{output}", self.output_filename
                    )
                    # Open file relative to trial_dir for writing
                    stdout_file = (trial_dir / next_token).open("w")
                    skip_next = True
                else:
                    # If > is at the end, use output_filename
                    stdout_file = (trial_dir / self.output_filename).open("w")
            else:
                # Regular command argument
                cmd.append(replaced)
        
        try:
            subprocess.run(
                cmd,
                cwd=trial_dir,
                check=True,
                env=self.command_env,
                timeout=self.command_timeout,
                stdin=stdin_file,
                stdout=stdout_file,
            )
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"AkaiKKR failed for {input_path}") from exc
        finally:
            if stdin_file is not None:
                stdin_file.close()
            if stdout_file is not None:
                stdout_file.close()

    def _to_fractions(self, params: np.ndarray) -> np.ndarray:
        if self.simplex_mode:
            return self._stick_breaking(params)
        return self._normalize(params)

    @staticmethod
    def _normalize(values: np.ndarray) -> np.ndarray:
        clipped = np.clip(np.asarray(values, dtype=float), 0.0, None)
        total = clipped.sum()
        if total <= 0.0:
            return np.ones_like(clipped) / len(clipped)
        return clipped / total

    def _stick_breaking(self, params: np.ndarray) -> np.ndarray:
        values = np.clip(np.asarray(params, dtype=float), 1e-6, 1 - 1e-6)
        remainder = 1.0
        fractions: List[float] = []
        for stick in values:
            portion = remainder * stick
            fractions.append(portion)
            remainder -= portion
        fractions.append(max(remainder, 0.0))
        return np.asarray(fractions)


def build_runner(
    config_path: Path, mock_output_override: str | None = None
) -> Tuple[odatse.Runner, odatse.Info]:
    raw_config = odatse.util.toml.load(str(config_path))
    if mock_output_override is not None:
        raw_config.setdefault("hea", {})
        raw_config["hea"]["mock_output"] = mock_output_override

    info = odatse.Info(raw_config)
    objective = HEAObjective(raw_config.get("hea"), info)

    solver = odatse.solver.function.Solver(info)
    solver.set_function(objective)
    runner = odatse.Runner(solver, info)
    return runner, info


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Optimize HEA compositions with ODAT-SE + AkaiKKR."
    )
    parser.add_argument(
        "config",
        help="Path to the ODAT-SE TOML configuration (e.g. hea_mapper.toml).",
    )
    parser.add_argument(
        "--mock-output",
        metavar="PATH",
        help=(
            "Use a mock AkaiKKR output file instead of running AkaiKKR. "
            "Overrides [hea].mock_output in the TOML."
        ),
    )
    args = parser.parse_args()

    config_path = Path(args.config).expanduser().absolute()
    runner, info = build_runner(config_path, mock_output_override=args.mock_output)

    alg_module = odatse.algorithm.choose_algorithm(info.algorithm.get("name", "mapper"))
    algorithm = alg_module.Algorithm(info, runner)
    algorithm.main()


if __name__ == "__main__":
    main()
