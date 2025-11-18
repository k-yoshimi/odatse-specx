# odatse-specx - AkaiKKR Input File Generation Tool

A Python tool for generating and editing AkaiKKR input files.

## Overview

This project provides tools to read AkaiKKR (first-principles calculation code) input files, replace atom types, define new atom species, and efficiently generate multiple variations of input files.

## Main Features

- **Input file loading**: Load AkaiKKR input files as structured data
- **Atom type replacement**:
  - Replacement by index
  - Replacement by coordinates
  - Batch replacement by label
- **New atom species definition**: Define and add single or mixed atom species
- **Input file export**: Write structured data in AkaiKKR input file format

## File Structure

```
odatse-specx/
├── README.md                 # This file (project overview)
├── generate_input.py         # Main module
├── README_generate_input.md  # Detailed documentation for generate_input.py
├── test_generate_input.py    # Test suite
├── README_test.md            # Test documentation
├── LICENSE                   # License file
└── refs/                     # Reference input files
    └── odatse-specx/
        └── test-1/
```

## Quick Start

### Basic Usage Example

```python
from generate_input import (
    load_input_file,
    replace_atom_types_by_label,
    add_atom_type_definition,
    write_input_file,
)

# Load input file
input_data = load_input_file("refs/odatse-specx/test-4/test.in")

# Define new atom species
new_data = add_atom_type_definition(
    input_data,
    type_name="Fe_new",
    ncmp=1,
    rmt=0.0,
    field=0.0,
    mxl=2,
    atoms=[(26, 100.0)],  # 100% Fe atoms
)

# Batch replacement by label
modified = replace_atom_types_by_label(
    new_data,
    {"Ba_2t_0": "Fe_new"}
)

# Write to file (directory is created automatically if it doesn't exist)
write_input_file(modified, "output/test_modified.in")
```

## Composition Exploration with ODAT-SE

A sample workflow for exploring high-entropy alloy (HEA) compositions by connecting AkaiKKR calculations to ODAT-SE's search algorithms has been added in `optimize_composition.py` / `hea_mapper.toml`.

1. Edit `hea_mapper.toml` and list the atom species (atomic numbers) you want to mix in `[[hea.species]]`. In `akai_command`, specify the command sequence to launch AkaiKKR. Available placeholders:
   - `{input}`: Input filename (e.g., `"test.in"`)
   - `{input_path}`: Full path to the input file
   - `{output}`: Output filename (specified by `output_file` setting, default: `"test.out"`)
   
   Standard input/output redirection is also supported. Recommended setting:
   ```toml
   akai_command = ["specx", "<", "{input}", ">", "{output}"]
   ```
   This is equivalent to `specx < test.in > test.out`. If `{output}` is omitted, standard output is not saved to a file.
2. For testing only, keep `mock_output = "test/refs/test.out"` to read `total energy= -59275.587686117` from `test/refs/test.out:523` and trace the entire process without running AkaiKKR. For actual calculations, both `total energy=` and `total energy` (without `=`) formats are supported.
3. For actual calculations, remove the `mock_output` line, specify the filename that AkaiKKR outputs (e.g., `test.out`) in `output_file`, and run `python optimize_composition.py hea_mapper.toml`. A new mixed label is applied to the site corresponding to `target_label` (e.g., `Y_1h_2`), and the obtained `total energy` is minimized as ODAT-SE's objective function.
4. To strictly normalize each HEA concentration to 1, specify `[hea] simplex_mode = true`. In this case, ODAT-SE's `base.dimension` and `algorithm.param.*` should match the dimension count of `len([[hea.species]]) - 1` (e.g., 3 dimensions for a 4-element alloy). The stick-breaking parameterization always generates compositions that are non-negative and sum to 1.
5. The metric to optimize can be selected in `[hea.metric]`. The default is `total_energy`, but you can extend to other observables such as conductivity by specifying custom regular expressions like `name = "band_energy"` or `pattern = "sigma=..."`. You can also apply metric transformations to the extracted value using `transform` (e.g., `log1p` or `abs`).

## Appendix: simplex_mode Algorithm

`simplex_mode` maps free variables passed from ODAT-SE to concentration vectors that are always non-negative and sum to 1 using a "stick-breaking" transformation (`optimize_composition.py:243-252`).

1. Input dimension: If the number of atom species to mix is `N`, ODAT-SE explores only `N-1` continuous variables (`base.dimension = N-1`).
2. Variable clipping: Each parameter is clipped to `[1e-6, 1-1e-6]` to prevent numerical instability when values stick to 0 or 1.
3. Stick-breaking: Start with an initial remainder `remainder = 1.0`, and each parameter `x_i` is interpreted as "the proportion of the current remainder". Assign `portion_i = remainder * x_i`, then update `remainder -= portion_i`. In other words, each parameter represents "how much of the remaining amount to allocate to this component".
4. Last component: After processing all sticks, add the remaining `remainder` as the `N`-th concentration, ensuring that `Σ portion_i + remainder = 1` always holds.
5. AkaiKKR input generation: Pass the resulting concentration vector to `generate_input.py`'s `add_atom_type_definition()` / `replace_atom_types_by_label()`, and return AkaiKKR's `total energy` as the objective function.

**Note**: Since each parameter represents "the proportion of the remainder", when all parameters are close to 1 (e.g., `[1.0, 1.0, 1.0]`), the first component occupies almost 100% of the remainder, and the remaining components become very small (e.g., `[0.999999, 0.000001, 0.0, 0.0]`). This is a natural result of the "allocate 100% of the remainder" behavior. To obtain an even composition (e.g., `[0.25, 0.25, 0.25, 0.25]`), adjust the parameters appropriately (e.g., approximately `[0.25, 0.33, 0.5]` for a 4-element alloy).

This transformation allows ODAT-SE to explore a simple rectangular region while actually evaluating composition points on a simplex. Proportional candidates (e.g., `[0.1,...]` and `[0.2,...]`) will not be treated as identical.

## Appendix: Metric Extraction via hea.metric

`optimize_composition.py` implements a `MetricExtractor` that parses the metric to minimize (energy, conductivity, etc.) from AkaiKKR output files (`optimize_composition.py:60-93`).

1. The `name` in `[hea.metric]` has two meanings: (a) an identifier to switch built-in patterns, and (b) a label reported in logs and error messages. If `pattern` is omitted, a default regular expression is selected based on `name = "total_energy"` / `"band_energy"`, and on successful extraction, it is recorded as `[Trial ...] ... -> total_energy=...`. The default `total_energy` pattern supports both `total energy=` and `total energy` (without `=`) formats (e.g., `total energy= -59275.587686117` or `total energy        -64162.390074716`).
2. To minimize an arbitrary metric, specify a regular expression in `pattern`. The first matching group's numeric value is extracted and multiplied by `scale` (useful for sign inversion or unit conversion).
3. `ignore_case` (default: true) can be set to false for case-sensitive search. You can specify the capture group number to extract using `group`.
4. Extraction results are obtained through `HEAObjective`'s `metric.extract()` and returned as ODAT-SE's objective function value. If the corresponding line is not found, an error occurs prompting a review of the settings.

## Appendix: Error Handling

`optimize_composition.py` performs appropriate error handling when AkaiKKR calculations fail or numeric values cannot be obtained (`optimize_composition.py:165-242`).

1. **Penalty value on error**: When a calculation fails, a large penalty value of `1.0e10` is returned by default. This causes the optimization algorithm to avoid failed composition points. You can customize this value by specifying `error_penalty` in the `[hea]` section.

2. **Error log**: If you specify a file path in `error_log` in the `[hea]` section, detailed information about failed trials is recorded. The log includes:
   - Error type and message
   - Trial number and composition parameters
   - Paths to input file, output file, and trial directory

3. **Preserving intermediate files**: Even when an error occurs, if `keep_intermediate = true` is set, files from failed trials are preserved. This allows you to investigate the cause of errors later.

4. **Error types**: The following errors are caught and return a penalty value:
   - `FileNotFoundError`: When the output file was not generated
   - `RuntimeError`: When AkaiKKR execution failed, or when the metric was not found
   - `ValueError`: When there is a problem with the configuration or data format
   - Other unexpected errors

### TOML Example (hea.metric)

```toml
[hea.metric]
name = "total_energy"      # Use default pattern
# name = "band_energy"     # To minimize band energy
transform = "identity"     # Post-processing of extracted value: identity / abs / log / log1p / sqrt / square

# Example: Minimize conductivity assuming AkaiKKR output has "sigma = ..."
# name = "conductivity"
# pattern = "sigma=\\s*([-.0-9Ee]+)"
# scale = 1.0              # Change as needed for unit conversion
# ignore_case = true
# group = 1

# Example: Smooth total_energy with log1p
# name = "total_energy"
# transform = "log1p"

# Example: To add transform presets (requires code changes)
# - File: Add to MetricExtractor._TRANSFORMS in optimize_composition.py
# - Format: "cube": lambda x: x ** 3   (add one line like this)
# After adding, you can use it in TOML with `transform = "cube"`.

# Example: Minimize spin moment
# name = "spin_moment"
# pattern = "spin moment= ?\\s+([-\\d.+Ee]+)"
# scale = 1.0
# ignore_case = true
# group = 1
```

### TOML Configuration Example

```toml
[base]
dimension = 3  # For exploring 4-element alloy (= number of species - 1)

[algorithm]
name = "mapper"

[algorithm.param]
min_list = [0.0, 0.0, 0.0]
max_list = [1.0, 1.0, 1.0]
num_list = [5, 5, 5]

[solver]
name = "function"

[hea]
template_input = "test/refs/test.in"
target_label = "Y_1h_2"
new_label = "Ln_HEA"
simplex_mode = true  # ← Enable this to use stick-breaking transformation
error_penalty = 1.0e10  # Penalty value on calculation failure (optional, default: 1.0e10)
error_log = "runs/error_log.txt"  # Error log file (optional)

[hea.metric]
name = "total_energy"  # band_energy / custom pattern
# pattern = "sigma=\\s*([-.0-9Ee]+)"  # Can override if metric has different notation in file

[[hea.species]]
label = "Y"
atomic_number = 39

[[hea.species]]
label = "La"
atomic_number = 57

[[hea.species]]
label = "Nd"
atomic_number = 60

[[hea.species]]
label = "Sm"
atomic_number = 62
```

When `simplex_mode = true` is set, the dimension to explore on the ODAT-SE side should match `base.dimension = len([[hea.species]]) - 1`. Be careful that `algorithm.param`'s `min_list` / `max_list` / `num_list` have the same length. Also, the `[hea.metric]` block allows switching the minimization target, and in addition to default values like `name = "total_energy"` / `"band_energy"`, you can extract arbitrary scalars such as conductivity by specifying regular expressions like `pattern = "sigma=\\s*([-.0-9Ee]+)"`.

## Detailed Documentation

- **Details on `generate_input.py`**: [README_generate_input.md](README_generate_input.md)
- **Test documentation**: [README_test.md](README_test.md)

## Testing

To run the test suite:

```bash
python3 test_generate_input.py
```

For details, see [README_test.md](README_test.md).

## License

MIT License

## References

- [AkaiKKR Official Documentation](https://academeia.github.io/AkaiKKR_Documents/input)
