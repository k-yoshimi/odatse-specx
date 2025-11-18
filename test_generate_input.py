"""
Test suite for AkaiKKR input file generation module

Test targets:
- load_input_file()
- replace_atom_types()
- replace_atom_types_by_coordinates()
- replace_atom_types_by_label()
- add_atom_type_definition()
- write_input_file()
- Integration tests
"""

import tempfile
import unittest
from pathlib import Path

from generate_input import (
    add_atom_type_definition,
    load_input_file,
    replace_atom_types,
    replace_atom_types_by_coordinates,
    replace_atom_types_by_label,
    write_input_file,
)


class TestLoadInputFile(unittest.TestCase):
    """Tests for load_input_file()"""

    def setUp(self):
        """Test setup"""
        self.test_input_file = "refs/odatse-specx/test-1/test.in"
        self.sample_input_data = load_input_file(self.test_input_file)

    def test_load_input_file_basic(self):
        """Basic loading test"""
        data = load_input_file(self.test_input_file)

        assert "ntyp" in data
        assert "atom_type_definitions" in data
        assert "atomic_positions" in data
        assert "header" in data
        assert "footer" in data

    def test_load_input_file_ntyp(self):
        """Test that ntyp value is correctly loaded"""
        self.assertEqual(self.sample_input_data["ntyp"], 8)

    def test_load_input_file_atom_type_definitions(self):
        """Test that atom type definitions are correctly loaded"""
        self.assertEqual(len(self.sample_input_data["atom_type_definitions"]), 8)

        # Check first atom type
        first_type = self.sample_input_data["atom_type_definitions"][0]
        self.assertEqual(first_type["type"], "Ba_2t_0")
        self.assertEqual(first_type["ncmp"], 1)
        self.assertEqual(len(first_type["atoms"]), 1)
        self.assertEqual(first_type["atoms"][0], (56, 100.0))

    def test_load_input_file_atomic_positions(self):
        """Test that atomic positions are correctly loaded"""
        self.assertEqual(len(self.sample_input_data["atomic_positions"]), 13)

        # Check first atomic position
        first_pos = self.sample_input_data["atomic_positions"][0]
        self.assertEqual(len(first_pos), 4)
        self.assertEqual(first_pos[3], "Ba_2t_0")  # atmtyp

    def test_load_input_file_immutability(self):
        """Test that the same result is obtained when loading multiple times"""
        data1 = load_input_file(self.test_input_file)
        data2 = load_input_file(self.test_input_file)

        self.assertEqual(data1["ntyp"], data2["ntyp"])
        self.assertEqual(
            len(data1["atom_type_definitions"]),
            len(data2["atom_type_definitions"]),
        )
        self.assertEqual(
            len(data1["atomic_positions"]), len(data2["atomic_positions"])
        )


class TestReplaceAtomTypes(unittest.TestCase):
    """Tests for replace_atom_types()"""

    def setUp(self):
        """Test setup"""
        self.test_input_file = "refs/odatse-specx/test-1/test.in"
        self.sample_input_data = load_input_file(self.test_input_file)

    def test_replace_atom_types_basic(self):
        """Basic replacement test"""
        modified = replace_atom_types(self.sample_input_data, {0: "Y_1h_2"})

        # Original data is unchanged
        self.assertEqual(self.sample_input_data["atomic_positions"][0][3], "Ba_2t_0")

        # New data is changed
        self.assertEqual(modified["atomic_positions"][0][3], "Y_1h_2")

    def test_replace_atom_types_multiple(self):
        """Replace multiple atoms"""
        modified = replace_atom_types(
            self.sample_input_data, {0: "Y_1h_2", 5: "Cu_2q_3"}
        )

        self.assertEqual(modified["atomic_positions"][0][3], "Y_1h_2")
        self.assertEqual(modified["atomic_positions"][5][3], "Cu_2q_3")
        # Atoms not replaced remain unchanged
        self.assertEqual(modified["atomic_positions"][1][3], "Ba_2t_0")

    def test_replace_atom_types_immutability(self):
        """Test that original data is preserved"""
        original_first = self.sample_input_data["atomic_positions"][0]

        modified = replace_atom_types(self.sample_input_data, {0: "Y_1h_2"})

        # Original data is unchanged
        self.assertEqual(self.sample_input_data["atomic_positions"][0], original_first)
        # New data is changed
        self.assertEqual(modified["atomic_positions"][0][3], "Y_1h_2")


class TestReplaceAtomTypesByCoordinates(unittest.TestCase):
    """Tests for replace_atom_types_by_coordinates()"""

    def setUp(self):
        """Test setup"""
        self.test_input_file = "refs/odatse-specx/test-1/test.in"
        self.sample_input_data = load_input_file(self.test_input_file)

    def test_replace_atom_types_by_coordinates_basic(self):
        """Replacement test by coordinate specification"""
        coord = (
            "0.50000000a",
            "0.50000000b",
            "0.50000000c",
        )
        modified = replace_atom_types_by_coordinates(
            self.sample_input_data, {coord: "Cu_1a_5"}
        )

        # Atom at specified coordinates is replaced
        found = False
        for x, y, z, atmtyp in modified["atomic_positions"]:
            if (x, y, z) == coord:
                self.assertEqual(atmtyp, "Cu_1a_5")
                found = True
                break
        self.assertTrue(found, "Atom at specified coordinates not found")

    def test_replace_atom_types_by_coordinates_immutability(self):
        """Test that original data is preserved"""
        original_positions = self.sample_input_data["atomic_positions"][:]

        coord = (
            "0.50000000a",
            "0.50000000b",
            "0.50000000c",
        )
        modified = replace_atom_types_by_coordinates(
            self.sample_input_data, {coord: "Cu_1a_5"}
        )

        # Original data is unchanged
        self.assertEqual(
            self.sample_input_data["atomic_positions"], original_positions
        )


class TestReplaceAtomTypesByLabel(unittest.TestCase):
    """Tests for replace_atom_types_by_label()"""

    def setUp(self):
        """Test setup"""
        self.test_input_file = "refs/odatse-specx/test-1/test.in"
        self.sample_input_data = load_input_file(self.test_input_file)

    def test_replace_atom_types_by_label_basic(self):
        """Basic label replacement test"""
        modified = replace_atom_types_by_label(
            self.sample_input_data, {"Ba_2t_0": "Y_1h_2"}
        )

        # Verify that all atoms with Ba_2t_0 are replaced
        ba_indices = [
            i
            for i, (_, _, _, atmtyp) in enumerate(
                self.sample_input_data["atomic_positions"]
            )
            if atmtyp == "Ba_2t_0"
        ]

        for idx in ba_indices:
            self.assertEqual(modified["atomic_positions"][idx][3], "Y_1h_2")

    def test_replace_atom_types_by_label_all_instances(self):
        """Test that all atoms with the same label are replaced"""
        # There are 2 Ba_2t_0 atoms
        ba_count = sum(
            1
            for _, _, _, atmtyp in self.sample_input_data["atomic_positions"]
            if atmtyp == "Ba_2t_0"
        )
        self.assertEqual(ba_count, 2)

        modified = replace_atom_types_by_label(
            self.sample_input_data, {"Ba_2t_0": "Y_1h_2"}
        )

        # All Ba_2t_0 are replaced
        ba_count_after = sum(
            1
            for _, _, _, atmtyp in modified["atomic_positions"]
            if atmtyp == "Ba_2t_0"
        )
        self.assertEqual(ba_count_after, 0)

        y_count_after = sum(
            1
            for _, _, _, atmtyp in modified["atomic_positions"]
            if atmtyp == "Y_1h_2"
        )
        self.assertGreaterEqual(
            y_count_after, 3
        )  # Original Y_1h_2 + replaced Ba_2t_0

    def test_replace_atom_types_by_label_multiple(self):
        """Replace multiple labels simultaneously"""
        modified = replace_atom_types_by_label(
            self.sample_input_data, {"Ba_2t_0": "Y_1h_2", "Cu_2q_3": "Cu_1a_5"}
        )

        # Both labels are replaced
        ba_count = sum(
            1
            for _, _, _, atmtyp in modified["atomic_positions"]
            if atmtyp == "Ba_2t_0"
        )
        self.assertEqual(ba_count, 0)

        cu2q3_count = sum(
            1
            for _, _, _, atmtyp in modified["atomic_positions"]
            if atmtyp == "Cu_2q_3"
        )
        self.assertEqual(cu2q3_count, 0)

    def test_replace_atom_types_by_label_immutability(self):
        """Test that original data is preserved"""
        original_positions = self.sample_input_data["atomic_positions"][:]

        modified = replace_atom_types_by_label(
            self.sample_input_data, {"Ba_2t_0": "Y_1h_2"}
        )

        # Original data is unchanged
        self.assertEqual(
            self.sample_input_data["atomic_positions"], original_positions
        )


class TestAddAtomTypeDefinition(unittest.TestCase):
    """Tests for add_atom_type_definition()"""

    def setUp(self):
        """Test setup"""
        self.test_input_file = "refs/odatse-specx/test-1/test.in"
        self.sample_input_data = load_input_file(self.test_input_file)

    def test_add_atom_type_definition_basic(self):
        """Basic atom type addition test"""
        original_count = len(self.sample_input_data["atom_type_definitions"])

        new_data = add_atom_type_definition(
            self.sample_input_data,
            type_name="Fe_new",
            ncmp=1,
            rmt=0.0,
            field=0.0,
            mxl=2,
            atoms=[(26, 100.0)],
        )

        # New atom type is added
        self.assertEqual(
            len(new_data["atom_type_definitions"]), original_count + 1
        )
        self.assertEqual(new_data["ntyp"], original_count + 1)

        # Check added atom type
        fe_type = None
        for type_def in new_data["atom_type_definitions"]:
            if type_def["type"] == "Fe_new":
                fe_type = type_def
                break

        self.assertIsNotNone(fe_type)
        self.assertEqual(fe_type["ncmp"], 1)
        self.assertEqual(fe_type["atoms"], [(26, 100.0)])

    def test_add_atom_type_definition_mixed(self):
        """Mixed atom type addition test"""
        new_data = add_atom_type_definition(
            self.sample_input_data,
            type_name="Y0.5La0.5",
            ncmp=2,
            rmt=0.0,
            field=0.0,
            mxl=2,
            atoms=[(39, 50.0), (57, 50.0)],
        )

        # Mixed atom type is added
        yla_type = None
        for type_def in new_data["atom_type_definitions"]:
            if type_def["type"] == "Y0.5La0.5":
                yla_type = type_def
                break

        self.assertIsNotNone(yla_type)
        self.assertEqual(yla_type["ncmp"], 2)
        self.assertEqual(len(yla_type["atoms"]), 2)
        self.assertIn((39, 50.0), yla_type["atoms"])
        self.assertIn((57, 50.0), yla_type["atoms"])

    def test_add_atom_type_definition_immutability(self):
        """Test that original data is preserved"""
        original_count = len(self.sample_input_data["atom_type_definitions"])

        new_data = add_atom_type_definition(
            self.sample_input_data,
            type_name="Fe_new",
            ncmp=1,
            rmt=0.0,
            field=0.0,
            mxl=2,
            atoms=[(26, 100.0)],
        )

        # Original data is unchanged
        self.assertEqual(
            len(self.sample_input_data["atom_type_definitions"]), original_count
        )


class TestWriteInputFile(unittest.TestCase):
    """Tests for write_input_file()"""

    def setUp(self):
        """Test setup"""
        self.test_input_file = "refs/odatse-specx/test-1/test.in"
        self.sample_input_data = load_input_file(self.test_input_file)

    def test_write_input_file_basic(self):
        """Basic write test"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".in", delete=False
        ) as f:
            temp_path = f.name

        try:
            write_input_file(self.sample_input_data, temp_path)

            # File is created
            self.assertTrue(Path(temp_path).exists())

            # Reload file and verify
            reloaded = load_input_file(temp_path)
            self.assertEqual(reloaded["ntyp"], self.sample_input_data["ntyp"])
            self.assertEqual(
                len(reloaded["atom_type_definitions"]),
                len(self.sample_input_data["atom_type_definitions"]),
            )
            self.assertEqual(
                len(reloaded["atomic_positions"]),
                len(self.sample_input_data["atomic_positions"]),
            )
        finally:
            Path(temp_path).unlink()

    def test_write_input_file_only_used_types(self):
        """Test that only used atom types are written"""
        # Add new atom type
        new_data = add_atom_type_definition(
            self.sample_input_data,
            type_name="Unused_Type",
            ncmp=1,
            rmt=0.0,
            field=0.0,
            mxl=2,
            atoms=[(1, 100.0)],
        )

        # Replace with unused atom type (actually not used)
        # Check only actually used types
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".in", delete=False
        ) as f:
            temp_path = f.name

        try:
            write_input_file(new_data, temp_path)

            # Reload file and verify
            reloaded = load_input_file(temp_path)

            # Check number of used atom types
            used_types = set()
            for _, _, _, atmtyp in new_data["atomic_positions"]:
                used_types.add(atmtyp)

            # Number of written atom type definitions matches number of used types
            self.assertEqual(
                len(reloaded["atom_type_definitions"]), len(used_types)
            )
            self.assertEqual(reloaded["ntyp"], len(used_types))

            # Unused_Type is not written because it's not used
            type_names = {d["type"] for d in reloaded["atom_type_definitions"]}
            self.assertNotIn("Unused_Type", type_names)
        finally:
            Path(temp_path).unlink()

    def test_write_input_file_create_directory(self):
        """Test that non-existent directories are automatically created"""
        import tempfile
        import shutil

        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        try:
            # Path containing non-existent subdirectories
            output_path = Path(temp_dir) / "new_dir" / "sub_dir" / "test.in"

            # Verify directory doesn't exist
            self.assertFalse(output_path.parent.exists())

            # Write file
            write_input_file(self.sample_input_data, output_path)

            # Directory is created
            self.assertTrue(output_path.parent.exists())
            # File is created
            self.assertTrue(output_path.exists())

            # Reload file and verify
            reloaded = load_input_file(output_path)
            self.assertEqual(reloaded["ntyp"], self.sample_input_data["ntyp"])
        finally:
            # Remove temporary directory
            shutil.rmtree(temp_dir)


class TestIntegration(unittest.TestCase):
    """Integration tests"""

    def setUp(self):
        """Test setup"""
        self.test_input_file = "refs/odatse-specx/test-1/test.in"
        self.sample_input_data = load_input_file(self.test_input_file)

    def test_full_workflow(self):
        """Complete workflow test"""
        # 1. Add new atom type
        new_data = add_atom_type_definition(
            self.sample_input_data,
            type_name="Fe_new",
            ncmp=1,
            rmt=0.0,
            field=0.0,
            mxl=2,
            atoms=[(26, 100.0)],
        )

        # 2. Replace by label
        modified = replace_atom_types_by_label(
            new_data, {"Ba_2t_0": "Fe_new"}
        )

        # 3. Write to file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".in", delete=False
        ) as f:
            temp_path = f.name

        try:
            write_input_file(modified, temp_path)

            # 4. Reload and verify
            reloaded = load_input_file(temp_path)

            # Verification
            type_names = {d["type"] for d in reloaded["atom_type_definitions"]}
            self.assertIn("Fe_new", type_names)

            # Ba_2t_0 is replaced with Fe_new
            ba_count = sum(
                1
                for _, _, _, atmtyp in reloaded["atomic_positions"]
                if atmtyp == "Ba_2t_0"
            )
            self.assertEqual(ba_count, 0)

            fe_count = sum(
                1
                for _, _, _, atmtyp in reloaded["atomic_positions"]
                if atmtyp == "Fe_new"
            )
            self.assertGreaterEqual(
                fe_count, 2
            )  # Original Ba_2t_0 was replaced
        finally:
            Path(temp_path).unlink()

    def test_multiple_variations_from_same_data(self):
        """Generate multiple variations from the same data"""
        # Pattern 1
        data1 = add_atom_type_definition(
            self.sample_input_data,
            type_name="Fe_new",
            ncmp=1,
            rmt=0.0,
            field=0.0,
            mxl=2,
            atoms=[(26, 100.0)],
        )
        modified1 = replace_atom_types_by_label(data1, {"Ba_2t_0": "Fe_new"})

        # Pattern 2 (from original data)
        data2 = add_atom_type_definition(
            self.sample_input_data,
            type_name="Y0.5La0.5",
            ncmp=2,
            rmt=0.0,
            field=0.0,
            mxl=2,
            atoms=[(39, 50.0), (57, 50.0)],
        )
        modified2 = replace_atom_types_by_label(
            data2, {"Ba_2t_0": "Y0.5La0.5", "Y_1h_2": "Y0.5La0.5"}
        )

        # Original data is unchanged
        self.assertEqual(
            len(self.sample_input_data["atom_type_definitions"]), 8
        )

        # Each pattern is correctly generated
        self.assertEqual(len(modified1["atom_type_definitions"]), 9)
        self.assertEqual(len(modified2["atom_type_definitions"]), 9)

        # Fe_new is used in pattern 1
        fe_in_1 = any(
            d["type"] == "Fe_new"
            for d in modified1["atom_type_definitions"]
        )
        self.assertTrue(fe_in_1)

        # Y0.5La0.5 is used in pattern 2
        yla_in_2 = any(
            d["type"] == "Y0.5La0.5"
            for d in modified2["atom_type_definitions"]
        )
        self.assertTrue(yla_in_2)


if __name__ == "__main__":
    unittest.main(verbosity=2)

