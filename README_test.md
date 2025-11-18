# Test Suite Documentation

`test_generate_input.py` is a comprehensive test suite for testing the functionality of the `generate_input.py` module.

## How to Run Tests

### Run All Tests at Once (Recommended)

```bash
# Using pytest (recommended)
python -m pytest test_*.py -v

# Or run all tests in the current directory
python -m pytest -v

# More detailed output
python -m pytest test_*.py -vv
```

### Using unittest

```bash
# Run all test files at once
python -m unittest discover -v

# Or search for tests with a specific pattern
python -m unittest discover -p "test_*.py" -v
```

### Run Individual Test Files

```bash
# test_generate_input.py only
python -m pytest test_generate_input.py -v

# test_optimize_composition.py only
python -m pytest test_optimize_composition.py -v

# Or using unittest
python3 test_generate_input.py -v
python3 -m unittest test_generate_input.py -v
```

## Test Structure

The test suite consists of the following 7 test classes:

### 1. TestLoadInputFile (5 tests)

Tests for `load_input_file()` function

- `test_load_input_file_basic`: Basic loading test
- `test_load_input_file_ntyp`: Test that ntyp value is correctly loaded
- `test_load_input_file_atom_type_definitions`: Test that atom type definitions are correctly loaded
- `test_load_input_file_atomic_positions`: Test that atomic positions are correctly loaded
- `test_load_input_file_immutability`: Test that the same result is obtained when loading multiple times

### 2. TestReplaceAtomTypes (3 tests)

Tests for `replace_atom_types()` function

- `test_replace_atom_types_basic`: Basic replacement test
- `test_replace_atom_types_multiple`: Replace multiple atoms
- `test_replace_atom_types_immutability`: Test that original data is preserved

### 3. TestReplaceAtomTypesByCoordinates (2 tests)

Tests for `replace_atom_types_by_coordinates()` function

- `test_replace_atom_types_by_coordinates_basic`: Replacement test by coordinate specification
- `test_replace_atom_types_by_coordinates_immutability`: Test that original data is preserved

### 4. TestReplaceAtomTypesByLabel (4 tests)

Tests for `replace_atom_types_by_label()` function

- `test_replace_atom_types_by_label_basic`: Basic label replacement test
- `test_replace_atom_types_by_label_all_instances`: Test that all atoms with the same label are replaced
- `test_replace_atom_types_by_label_multiple`: Replace multiple labels simultaneously
- `test_replace_atom_types_by_label_immutability`: Test that original data is preserved

### 5. TestAddAtomTypeDefinition (3 tests)

Tests for `add_atom_type_definition()` function

- `test_add_atom_type_definition_basic`: Basic atom type addition test
- `test_add_atom_type_definition_mixed`: Mixed atom type addition test
- `test_add_atom_type_definition_immutability`: Test that original data is preserved

### 6. TestWriteInputFile (3 tests)

Tests for `write_input_file()` function

- `test_write_input_file_basic`: Basic write test
- `test_write_input_file_only_used_types`: Test that only used atom types are written
- `test_write_input_file_create_directory`: Test that non-existent directories are automatically created

### 7. TestIntegration (2 tests)

Integration tests

- `test_full_workflow`: Complete workflow test (add new atom type → replace → write → read)
- `test_multiple_variations_from_same_data`: Generate multiple variations from the same data

## Test Coverage

The test suite covers the following functionality:

- ✅ Input file loading
- ✅ Atom replacement by index
- ✅ Atom replacement by coordinates
- ✅ Batch replacement by label
- ✅ New atom species definition (single and mixed)
- ✅ File writing
- ✅ Automatic directory creation
- ✅ Data immutability (original data is preserved)
- ✅ Integrated workflow

## Test Prerequisites

Tests assume the following file exists:

- `refs/odatse-specx/test-1/test.in`: Input file for testing

If this file does not exist, tests will fail.

## Example Test Execution Results

When executed successfully, the following output is displayed:

```
test_add_atom_type_definition_basic ... ok
test_add_atom_type_definition_immutability ... ok
test_add_atom_type_definition_mixed ... ok
test_full_workflow ... ok
test_multiple_variations_from_same_data ... ok
test_load_input_file_atom_type_definitions ... ok
test_load_input_file_atomic_positions ... ok
test_load_input_file_basic ... ok
test_load_input_file_immutability ... ok
test_load_input_file_ntyp ... ok
test_replace_atom_types_basic ... ok
test_replace_atom_types_immutability ... ok
test_replace_atom_types_multiple ... ok
test_replace_atom_types_by_coordinates_basic ... ok
test_replace_atom_types_by_coordinates_immutability ... ok
test_replace_atom_types_by_label_all_instances ... ok
test_replace_atom_types_by_label_basic ... ok
test_replace_atom_types_by_label_immutability ... ok
test_replace_atom_types_by_label_multiple ... ok
test_write_input_file_basic ... ok
test_write_input_file_create_directory ... ok
test_write_input_file_only_used_types ... ok

----------------------------------------------------------------------
Ran 22 tests in 0.011s

OK
```

## Troubleshooting

### When Tests Fail

1. **File not found error**
   - Ensure that `refs/odatse-specx/test-4/test.in` exists

2. **Import error**
   - Ensure that `generate_input.py` is in the same directory

3. **Permission error**
   - Ensure that you have the necessary permissions to create temporary files

## Extending Tests

When adding new functionality, also add corresponding tests. The test structure is as follows:

```python
class TestNewFeature(unittest.TestCase):
    """Tests for new feature"""

    def setUp(self):
        """Test setup"""
        self.test_input_file = "refs/odatse-specx/test-4/test.in"
        self.sample_input_data = load_input_file(self.test_input_file)

    def test_new_feature_basic(self):
        """Basic functionality test"""
        # Test code
        pass

    def test_new_feature_immutability(self):
        """Immutability test"""
        # Test code
        pass
```

## References

- [Python unittest Documentation](https://docs.python.org/3/library/unittest.html)
