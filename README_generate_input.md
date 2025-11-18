# generate_input.py Documentation

A module for generating and editing AkaiKKR input files.

## Overview

This module provides functionality to read AkaiKKR input files, replace atom types, define new atom species, and efficiently generate multiple variations of input files.

## Main Functions

### File Loading

#### `load_input_file(input_path: Union[str, Path]) -> Dict`

Loads an AkaiKKR input file and returns structured data.

**Parameters**
- `input_path`: Path to the input file

**Returns**
- Dictionary containing structured data:
  - `header`: Header section before ntyp
  - `ntyp`: Number of atom types
  - `atom_type_definitions`: List of atom type definitions
  - `atomic_header`: Header of the atmicx section
  - `atomic_positions`: List of atomic position information
  - `footer`: Footer section after end

**Examples**
```python
input_data = load_input_file("test.in")
print(f"Found {input_data['ntyp']} atom types")
print(f"Found {len(input_data['atomic_positions'])} atoms")
```

### Atom Type Replacement

#### `replace_atom_types(input_data: Dict, atom_type_mapping: Dict[int, str]) -> Dict`

Replaces atom types by index specification.

**Parameters**
- `input_data`: Structured data loaded by `load_input_file()`
- `atom_type_mapping`: Mapping from atom index (0-based) to new atmtyp

**Returns**
- Structured data with replaced atoms (new copy)

**Examples**
```python
# Replace atoms at indices 0 and 5
modified = replace_atom_types(
    input_data,
    {0: "Y_1h_2", 5: "Cu_2q_3"}
)
```

#### `replace_atom_types_by_coordinates(input_data: Dict, coordinate_mapping: Dict[Tuple[str, str, str], str]) -> Dict`

Replaces atom types by coordinate specification.

**Parameters**
- `input_data`: Structured data loaded by `load_input_file()`
- `coordinate_mapping`: Mapping from coordinates (x, y, z) to new atmtyp

**Returns**
- Structured data with replaced atoms (new copy)

**Examples**
```python
# Replace atom at specific coordinates
modified = replace_atom_types_by_coordinates(
    input_data,
    {("0.50000000a", "0.50000000b", "0.50000000c"): "Ba_2t_0"}
)
```

#### `replace_atom_types_by_label(input_data: Dict, label_mapping: Dict[str, str]) -> Dict`

Replaces all atoms with the same label (atmtyp) in batch.

**Parameters**
- `input_data`: Structured data loaded by `load_input_file()`
- `label_mapping`: Mapping from original label to new label

**Returns**
- Structured data with replaced atoms (new copy)

**Examples**
```python
# Replace all atoms with label 'Ba_2t_0' with 'Y_1h_2'
modified = replace_atom_types_by_label(
    input_data,
    {"Ba_2t_0": "Y_1h_2"}
)

# Replace multiple labels simultaneously
modified = replace_atom_types_by_label(
    input_data,
    {"Ba_2t_0": "Y_1h_2", "Cu_2q_3": "Cu_1a_5"}
)
```

### New Atom Species Definition

#### `add_atom_type_definition(input_data: Dict, type_name: str, ncmp: int, rmt: float, field: float, mxl: int, atoms: List[Tuple[int, float]]) -> Dict`

Adds a new atom species definition.

**Parameters**
- `input_data`: Structured data loaded by `load_input_file()`
- `type_name`: Name of the new atom type (label)
- `ncmp`: Number of atom species occupying the site
- `rmt`: Muffin-tin radius (0.0 for automatic determination)
- `field`: External magnetic field
- `mxl`: Maximum angular momentum
- `atoms`: List of (atomic number, concentration). The sum of concentrations should be 100.0

**Returns**
- Structured data with new atom species definition added (new copy)

**Examples**
```python
# Add single atom species (100% Fe atoms)
new_data = add_atom_type_definition(
    input_data,
    type_name="Fe_new",
    ncmp=1,
    rmt=0.0,
    field=0.0,
    mxl=2,
    atoms=[(26, 100.0)]  # 100% Fe atoms (atomic number 26)
)

# Add mixed atom species (Y 50%, La 50%)
new_data = add_atom_type_definition(
    input_data,
    type_name="Y0.5La0.5",
    ncmp=2,
    rmt=0.0,
    field=0.0,
    mxl=2,
    atoms=[(39, 50.0), (57, 50.0)]  # Y 50%, La 50%
)
```

### File Export

#### `write_input_file(input_data: Dict, output_path: Union[str, Path]) -> None`

Writes structured data as an AkaiKKR input file.

The output directory is created automatically if it does not exist.

**Parameters**
- `input_data`: Structured data created by `load_input_file()` or replacement functions
- `output_path`: Path to the output file

**Examples**
```python
# Basic export
write_input_file(modified_data, "test_new.in")

# Directory is created automatically if it doesn't exist
write_input_file(modified_data, "output/new_dir/test_new.in")
```

### Utility Functions

#### `list_atomic_positions(input_data: Union[Dict, str, Path]) -> None`

Lists atomic positions in structured data or input file.

**Parameters**
- `input_data`: Structured data loaded by `load_input_file()`, or input file path

**Examples**
```python
# Display from structured data
input_data = load_input_file("test.in")
list_atomic_positions(input_data)

# Or display directly from file path
list_atomic_positions("test.in")
```

## Usage Examples

### Example 1: Define New Atom Species and Replace by Label

```python
from generate_input import (
    load_input_file,
    add_atom_type_definition,
    replace_atom_types_by_label,
    write_input_file,
)

# Load input file
input_data = load_input_file("refs/odatse-specx/test-4/test.in")

# Add new atom species (100% Fe atoms)
new_data = add_atom_type_definition(
    input_data,
    type_name="Fe_new",
    ncmp=1,
    rmt=0.0,
    field=0.0,
    mxl=2,
    atoms=[(26, 100.0)],
)

# Replace all atoms with label 'Ba_2t_0' with 'Fe_new'
modified = replace_atom_types_by_label(
    new_data,
    {"Ba_2t_0": "Fe_new"}
)

# Write to file
write_input_file(modified, "output/test_modified.in")
```

### Example 2: Generate Multiple Variations from Same Data

```python
from generate_input import (
    load_input_file,
    add_atom_type_definition,
    replace_atom_types_by_label,
    write_input_file,
)

# Load input file once
input_data = load_input_file("refs/odatse-specx/test-4/test.in")

# Pattern 1: Add Fe_new and replace Ba_2t_0
data1 = add_atom_type_definition(
    input_data,
    type_name="Fe_new",
    ncmp=1,
    rmt=0.0,
    field=0.0,
    mxl=2,
    atoms=[(26, 100.0)],
)
modified1 = replace_atom_types_by_label(data1, {"Ba_2t_0": "Fe_new"})
write_input_file(modified1, "output/pattern1.in")

# Pattern 2: Generate different pattern from original data
data2 = add_atom_type_definition(
    input_data,
    type_name="Y0.5La0.5",
    ncmp=2,
    rmt=0.0,
    field=0.0,
    mxl=2,
    atoms=[(39, 50.0), (57, 50.0)],
)
modified2 = replace_atom_types_by_label(
    data2,
    {"Ba_2t_0": "Y0.5La0.5", "Y_1h_2": "Y0.5La0.5"}
)
write_input_file(modified2, "output/pattern2.in")
```

## Important Notes

### Data Immutability

All replacement functions and `add_atom_type_definition()` return new copies without modifying the original data. This allows you to generate multiple different variations from the same `input_data`.

```python
input_data = load_input_file("test.in")

# Pattern 1
modified1 = replace_atom_types_by_label(input_data, {"Ba_2t_0": "Y_1h_2"})

# Pattern 2 (from original input_data)
modified2 = replace_atom_types_by_label(input_data, {"Cu_2q_3": "Cu_1a_5"})

# input_data is unchanged
```

### Only Used Atom Types Are Written

`write_input_file()` only writes definitions for atom types that are actually used in atomic positions. Atom types that are defined but not used are not included in the output file.

### Automatic Directory Creation

`write_input_file()` automatically creates the output directory if it does not exist.

```python
# Directory is created automatically even if it doesn't exist
write_input_file(modified_data, "output/new_dir/test.in")
```

## Atomic Number Reference

Atomic numbers of major elements:

- H: 1, He: 2
- Li: 3, Be: 4, B: 5, C: 6, N: 7, O: 8, F: 9, Ne: 10
- Na: 11, Mg: 12, Al: 13, Si: 14, P: 15, S: 16, Cl: 17, Ar: 18
- K: 19, Ca: 20, Sc: 21, Ti: 22, V: 23, Cr: 24, Mn: 25, Fe: 26, Co: 27, Ni: 28, Cu: 29, Zn: 30
- Y: 39, Zr: 40, Nb: 41, Mo: 42, Tc: 43, Ru: 44, Rh: 45, Pd: 46, Ag: 47, Cd: 48
- La: 57, Ce: 58, Pr: 59, Nd: 60, Pm: 61, Sm: 62, Eu: 63, Gd: 64
- Ba: 56

## References

- [AkaiKKR Input File Documentation](https://academeia.github.io/AkaiKKR_Documents/input)
