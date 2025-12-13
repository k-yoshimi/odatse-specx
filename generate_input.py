"""
Compatibility shim that re-exports AkaiKKR input helpers from odatse-kkr.

This file remains so that existing scripts importing ``generate_input``
continue to work.  The actual implementations now live in
``odatse_kkr.generate_input`` so that multiple ODAT-SE frontends can reuse the
same code without depending on the full odatse-specx package.
"""

from __future__ import annotations

from odatse_kkr.generate_input import *  # noqa: F401,F403
from odatse_kkr.generate_input import (
    add_atom_type_definition,
    count_atoms_by_type,
    list_atomic_positions,
    load_input_file,
    modify_atom_type_definition,
    replace_atom_types,
    replace_atom_types_by_coordinates,
    replace_atom_types_by_label,
    write_input_file,
)

__all__ = [
    "add_atom_type_definition",
    "count_atoms_by_type",
    "list_atomic_positions",
    "load_input_file",
    "modify_atom_type_definition",
    "replace_atom_types",
    "replace_atom_types_by_coordinates",
    "replace_atom_types_by_label",
    "write_input_file",
]


if __name__ == "__main__":
    input_file = "test/refs/test.in"
    output_file = "test/refs/test_modified.in"

    input_data = load_input_file(input_file)
    print("Original atomic positions:")
    list_atomic_positions(input_data)
    print()

    new_data_with_type = add_atom_type_definition(
        input_data,
        type_name="Fe_new",
        ncmp=1,
        rmt=0.0,
        field=0.0,
        mxl=2,
        atoms=[(26, 100.0)],
    )

    label_mapping = {"Ba_2t_0": "Fe_new"}
    modified_data = replace_atom_types_by_label(new_data_with_type, label_mapping)
    write_input_file(modified_data, output_file)

    print(f"Generated new input file: {output_file}")
    print("  (Added Fe_new atom type and replaced all Ba_2t_0 atoms with it)")
    print()

    output_file_2 = "test/refs/test_modified_2.in"
    new_data_with_mixed = add_atom_type_definition(
        input_data,
        type_name="Y0.5La0.5",
        ncmp=2,
        rmt=0.0,
        field=0.0,
        mxl=2,
        atoms=[(39, 50.0), (57, 50.0)],
    )

    mapping = {
        "Ba_2t_0": "Y0.5La0.5",
        "Cu_2q_3": "Cu_1a_5",
    }
    modified_data = replace_atom_types_by_label(new_data_with_mixed, mapping)
    write_input_file(modified_data, output_file_2)

    print(f"Generated new input file: {output_file_2}")
    print("  (Added Y0.5La0.5 atom type and replaced multiple labels)")
