# TOML Configuration Examples

This directory contains example TOML configuration files for `optimize_composition.py`.
Each example is organized in its own directory with the configuration file and template input file.

## Directory Structure

Each example directory contains:
- `config.toml`: Configuration file for `optimize_composition.py`
- `template.in`: AkaiKKR input template file

## Metric Examples

### `hea_total_energy/`
Minimizes total energy (default metric). This is the most common use case for HEA
composition optimization.

**Usage:**
```bash
cd examples/hea_total_energy
python ../../optimize_composition.py config.toml
```

### `hea_band_energy/`
Minimizes band energy. Useful for band structure optimization.

**Usage:**
```bash
cd examples/hea_band_energy
python ../../optimize_composition.py config.toml
```

### `hea_magnetization/`
Minimizes magnetization. Extracts magnetization value from AkaiKKR output using
a custom regular expression pattern.

**Usage:**
```bash
cd examples/hea_magnetization
python ../../optimize_composition.py config.toml
```

## Element Count Examples

### `hea_3element/`
3-element alloy configuration. Note that `dimension = 2` (number of species - 1)
when using `simplex_mode = true`.

### `hea_5element/`
5-element alloy configuration. `dimension = 4` (number of species - 1).

## Execution Environment Examples

### `hea_with_env/`
Example with environment variables for parallel computation. Useful for HPC
environments where you need to set `OMP_NUM_THREADS` or `MKL_NUM_THREADS`.

### `hea_debug/`
Debug mode configuration with intermediate files kept. Useful for troubleshooting
and development. Features:
- Smaller grid for faster testing
- `keep_intermediate = true` to inspect trial directories
- Detailed error logging

### `hea_mock_test/`
Mock test mode that uses a pre-existing output file instead of running AkaiKKR.
Useful for testing the workflow without actual calculations. You can also use
the `--mock-output` command-line flag.

**Usage:**
```bash
cd examples/hea_mock_test
python ../../optimize_composition.py config.toml
# or with CLI override:
python ../../optimize_composition.py config.toml --mock-output ../../test/refs/test.out
```

### `hea_fine_grid/`
Fine grid search configuration with higher resolution (`num_list = [10, 10, 10]`).
Useful for detailed exploration after initial coarse searches.

## Common Parameters

### Dimension Settings
When `simplex_mode = true`:
- `dimension = number of species - 1`
- Example: 4-element alloy → `dimension = 3`

### Algorithm Parameters
- `min_list`: Lower bounds for each dimension (must match `dimension`)
- `max_list`: Upper bounds for each dimension (must match `dimension`)
- `num_list`: Number of grid points per dimension (must match `dimension`)

### HEA Settings
- `template_input`: Path to the base AkaiKKR input file (relative to config file location)
- `target_label`: Atom label to replace with mixed composition
- `new_label`: Name for the new mixed atom species
- `simplex_mode`: When `true`, uses stick-breaking transformation to ensure
  concentrations sum to 1.0

### Metric Settings
- `name`: Metric name (`"total_energy"`, `"band_energy"`, or custom)
- `pattern`: Regular expression pattern for custom metrics (optional)
- `scale`: Scaling factor for the extracted value (default: 1.0)
- `transform`: Transformation function (`"abs"`, `"log1p"`, etc.)

## Customization

To create your own configuration:

1. Copy one of the example directories as a starting point
2. Modify `config.toml` to adjust parameters
3. Update `template.in` if you need a different base structure
4. Adjust `[base]` section for your output directories
5. Set `[algorithm.param]` to match your desired search grid
6. Configure `[hea]` section with your target label
7. Define `[[hea.species]]` entries for your alloy elements
8. Select appropriate metric in `[hea.metric]` section

## See Also

- `README_optimize_composition.md`: Detailed parameter manual
- `hea_mapper.toml`: Main configuration file in project root

