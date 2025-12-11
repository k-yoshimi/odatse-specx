"""
AkaiKKR input file generation module

Provides functionality to generate new input files by changing particle types
(atmtyp) while keeping positions (atmicx) the same.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Optional


def parse_atomic_positions(
    input_lines: List[str],
) -> Tuple[List[str], List[Tuple[str, str, str, str]]]:
    """
    Extract atomic position information from an AkaiKKR input file.

    Parameters
    ----------
    input_lines : List[str]
        List of lines from the input file.

    Returns
    -------
    Tuple[List[str], List[Tuple[str, str, str, str]]]
        Header lines and list of atomic position information.
        Atomic position information is a tuple of (x, y, z, atmtyp).
    """
    header_lines = []
    atomic_positions = []
    in_atomic_section = False

    for line in input_lines:
        if "atmicx" in line.lower() or "atmtyp" in line.lower():
            in_atomic_section = True
            header_lines.append(line)
            continue

        if in_atomic_section:
            # Skip empty lines and comment lines
            stripped = line.strip()
            if not stripped or stripped.startswith("c") or stripped.startswith("#"):
                if not stripped.startswith("end"):
                    header_lines.append(line)
                continue

            # Exit when end is found
            if "end" in stripped.lower():
                break

            # Parse atomic position line
            # Format: x y z atmtyp or xa yb zc atmtyp
            parts = stripped.split()
            if len(parts) >= 4:
                x = parts[0]
                y = parts[1]
                z = parts[2]
                atmtyp = parts[3]
                atomic_positions.append((x, y, z, atmtyp))

    return header_lines, atomic_positions


def parse_atom_type_definitions(input_lines: List[str]) -> Tuple[int, List[Dict], int]:
    """
    Extract atom type definition information from an AkaiKKR input file.

    Parameters
    ----------
    input_lines : List[str]
        List of lines from the input file.

    Returns
    -------
    Tuple[int, List[Dict], int]
        ntyp value, list of atom type definitions, and starting index of ntyp section.
        Each atom type definition is a dictionary with the following keys:
        - 'type': Type name
        - 'ncmp': Number of atom species
        - 'rmt': Muffin-tin radius
        - 'field': External magnetic field
        - 'mxl': Maximum angular momentum
        - 'atoms': List of [(anclr, conc), ...]
    """
    ntyp = None
    atom_types = []
    ntyp_start_idx = None
    i = 0

    # Find ntyp line (also consider if it's in a comment line)
    while i < len(input_lines):
        line = input_lines[i]
        stripped = line.strip()

        # Find ntyp line (can be in comment line)
        if "ntyp" in stripped.lower():
            ntyp_start_idx = i
            # Read ntyp value from next line
            i += 1
            while i < len(input_lines):
                next_line = input_lines[i].strip()
                if next_line and not next_line.startswith("c"):
                    try:
                        ntyp = int(next_line.split()[0])
                    except (ValueError, IndexError):
                        pass
                    i += 1
                    break
                i += 1
            break
        i += 1

    if ntyp_start_idx is None:
        return 0, [], 0

    # Find typ line
    while i < len(input_lines):
        line = input_lines[i]
        stripped = line.strip()

        # Find typ line
        if "typ" in stripped.lower() and "ncmp" in stripped.lower():
            i += 1
            break
        i += 1

    # Read atom type definitions
    while i < len(input_lines) and len(atom_types) < (ntyp or float("inf")):
        line = input_lines[i]
        stripped = line.strip()

        # Skip comment lines and empty lines
        if not stripped or stripped.startswith("c") or stripped.startswith("#"):
            # Exit when section delimiter (natm, etc.) is found
            if "natm" in stripped.lower() or "atmicx" in stripped.lower():
                break
            i += 1
            continue

        # Exit when section delimiter is found
        if "natm" in stripped.lower() or "atmicx" in stripped.lower():
            break

        # Parse atom type definition line
        # Split considering tabs and multiple spaces
        parts = stripped.split()
        if len(parts) >= 5:
            # type name ncmp rmt field mxl
            type_name = parts[0]
            try:
                ncmp = int(parts[1])
                rmt = float(parts[2])
                field = float(parts[3])
                mxl = int(parts[4])
            except (ValueError, IndexError):
                i += 1
                continue

            current_type = {
                "type": type_name,
                "ncmp": ncmp,
                "rmt": rmt,
                "field": field,
                "mxl": mxl,
                "atoms": [],
            }

            # Read anclr and conc from next lines
            i += 1
            atom_count = 0
            while atom_count < ncmp and i < len(input_lines):
                atom_line = input_lines[i]
                # Replace tabs with spaces before processing
                atom_line_clean = atom_line.replace("\t", " ").strip()
                if atom_line_clean and not atom_line_clean.startswith("c"):
                    atom_parts = atom_line_clean.split()
                    if len(atom_parts) >= 2:
                        try:
                            anclr = int(atom_parts[0])
                            conc = float(atom_parts[1])
                            current_type["atoms"].append((anclr, conc))
                            atom_count += 1
                        except (ValueError, IndexError):
                            pass
                i += 1

            if current_type and len(current_type["atoms"]) == ncmp:
                atom_types.append(current_type)
        else:
            # Move to next line if parts is less than 5
            i += 1

    # If ntyp is not found, infer from number of atom_types
    if ntyp is None:
        ntyp = len(atom_types)
    
    return ntyp, atom_types, ntyp_start_idx if ntyp_start_idx else 0


def load_input_file(input_path: Union[str, Path]) -> Dict:
    """
    Load AkaiKKR input file and return structured data.

    Parameters
    ----------
    input_path : Union[str, Path]
        Path to the input file.

    Returns
    -------
    Dict
        Dictionary containing information about the parsed input file.
        - 'header': Header part before ntyp
        - 'ntyp': Number of atom types
        - 'atom_type_definitions': List of atom type definitions
        - 'atomic_header': Header of atmicx section
        - 'atomic_positions': List of atomic position information
        - 'footer': Footer part after end

    Examples
    --------
    >>> input_data = load_input_file('test.in')
    >>> print(f"Found {len(input_data['atomic_positions'])} atoms")
    >>> print(f"Found {input_data['ntyp']} atom types")
    """
    input_path = Path(input_path)
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Parse atom type definitions
    ntyp, atom_type_definitions, ntyp_start_idx = parse_atom_type_definitions(lines)
    
    # If ntyp is None, infer from number of atom_type_definitions
    if ntyp is None:
        ntyp = len(atom_type_definitions)

    # Find atmicx section
    atomic_start_idx = None
    for i, line in enumerate(lines):
        if "atmicx" in line.lower() or "atmtyp" in line.lower():
            atomic_start_idx = i
            break

    if atomic_start_idx is None:
        raise ValueError("atmicx atmtyp section not found in input file")

    # Header part (before ntyp)
    header = lines[:ntyp_start_idx]

    # Atomic position section
    atomic_header, atomic_positions = parse_atomic_positions(lines[atomic_start_idx:])

    # Footer part (after end)
    footer = []
    end_found = False
    for i in range(atomic_start_idx + len(atomic_header), len(lines)):
        line = lines[i]
        if "end" in line.lower() and not line.strip().startswith("c"):
            footer.append(line)
            end_found = True
            break
        if end_found or i >= atomic_start_idx + len(atomic_header) + len(
            atomic_positions
        ):
            footer.append(line)

    return {
        "header": header,
        "ntyp": ntyp,
        "atom_type_definitions": atom_type_definitions,
        "atomic_header": atomic_header,
        "atomic_positions": atomic_positions,
        "footer": footer,
    }


def replace_atom_types(
    input_data: Dict,
    atom_type_mapping: Dict[int, str],
) -> Dict:
    """
    Replace atom types in structured data by index specification.

    Parameters
    ----------
    input_data : Dict
        Structured data loaded by load_input_file().
    atom_type_mapping : Dict[int, str]
        Mapping from atom index (0-based) to new atmtyp.
        Example: {2: 'Ba_2t_0', 5: 'Cu_1a_5'}

    Returns
    -------
    Dict
        Structured data with replaced atoms (new copy).

    Examples
    --------
    >>> input_data = load_input_file('test.in')
    >>> modified_data = replace_atom_types(
    ...     input_data,
    ...     {2: 'Ba_2t_0', 5: 'Cu_1a_5'}
    ... )
    """
    # Create new copy
    new_data = {
        "header": input_data["header"][:],
        "ntyp": input_data.get("ntyp", 0),
        "atom_type_definitions": [
            defn.copy() for defn in input_data.get("atom_type_definitions", [])
        ],
        "atomic_header": input_data["atomic_header"][:],
        "atomic_positions": [],
        "footer": input_data["footer"][:],
    }

    # Update atomic positions
    for idx, (x, y, z, atmtyp) in enumerate(input_data["atomic_positions"]):
        if idx in atom_type_mapping:
            new_atmtyp = atom_type_mapping[idx]
            new_data["atomic_positions"].append((x, y, z, new_atmtyp))
        else:
            new_data["atomic_positions"].append((x, y, z, atmtyp))

    return new_data


def replace_atom_types_by_coordinates(
    input_data: Dict,
    coordinate_mapping: Dict[Tuple[str, str, str], str],
) -> Dict:
    """
    Replace atom types in structured data by coordinate specification.

    Parameters
    ----------
    input_data : Dict
        Structured data loaded by load_input_file().
    coordinate_mapping : Dict[Tuple[str, str, str], str]
        Mapping from coordinates (x, y, z) to new atmtyp.
        Example: {('0.5a', '0.5b', '0.5c'): 'Ba_2t_0'}

    Returns
    -------
    Dict
        Structured data with replaced atoms (new copy).

    Examples
    --------
    >>> input_data = load_input_file('test.in')
    >>> modified_data = replace_atom_types_by_coordinates(
    ...     input_data,
    ...     {('0.50000000a', '0.50000000b', '0.50000000c'): 'Ba_2t_0'}
    ... )
    """
    # Create new copy
    new_data = {
        "header": input_data["header"][:],
        "ntyp": input_data.get("ntyp", 0),
        "atom_type_definitions": [
            defn.copy() for defn in input_data.get("atom_type_definitions", [])
        ],
        "atomic_header": input_data["atomic_header"][:],
        "atomic_positions": [],
        "footer": input_data["footer"][:],
    }

    # Update atomic positions
    for x, y, z, atmtyp in input_data["atomic_positions"]:
        coord_key = (x, y, z)
        if coord_key in coordinate_mapping:
            new_atmtyp = coordinate_mapping[coord_key]
            new_data["atomic_positions"].append((x, y, z, new_atmtyp))
        else:
            new_data["atomic_positions"].append((x, y, z, atmtyp))

    return new_data


def replace_atom_types_by_label(
    input_data: Dict,
    label_mapping: Dict[str, str],
) -> Dict:
    """
    Replace all atoms with the same label (atmtyp) in structured data by label specification.

    Parameters
    ----------
    input_data : Dict
        Structured data loaded by load_input_file().
    label_mapping : Dict[str, str]
        Mapping from original label to new label.
        Example: {'Ba_2t_0': 'Y_1h_2', 'Cu_2q_3': 'Cu_1a_5'}

    Returns
    -------
    Dict
        Structured data with replaced atoms (new copy).

    Examples
    --------
    >>> input_data = load_input_file('test.in')
    >>> # Replace all atoms with label 'Ba_2t_0' with 'Y_1h_2'
    >>> modified_data = replace_atom_types_by_label(
    ...     input_data,
    ...     {'Ba_2t_0': 'Y_1h_2'}
    ... )
    >>> # Replace multiple labels simultaneously
    >>> modified_data = replace_atom_types_by_label(
    ...     input_data,
    ...     {'Ba_2t_0': 'Y_1h_2', 'Cu_2q_3': 'Cu_1a_5'}
    ... )
    """
    # Create new copy
    new_data = {
        "header": input_data["header"][:],
        "ntyp": input_data.get("ntyp", 0),
        "atom_type_definitions": [
            defn.copy() for defn in input_data.get("atom_type_definitions", [])
        ],
        "atomic_header": input_data["atomic_header"][:],
        "atomic_positions": [],
        "footer": input_data["footer"][:],
    }

    # Update atomic positions
    for x, y, z, atmtyp in input_data["atomic_positions"]:
        if atmtyp in label_mapping:
            new_atmtyp = label_mapping[atmtyp]
            new_data["atomic_positions"].append((x, y, z, new_atmtyp))
        else:
            new_data["atomic_positions"].append((x, y, z, atmtyp))

    return new_data


def add_atom_type_definition(
    input_data: Dict,
    type_name: str,
    ncmp: int,
    rmt: float,
    field: float,
    mxl: int,
    atoms: List[Tuple[int, float]],
) -> Dict:
    """
    Add a new atom species definition.

    Parameters
    ----------
    input_data : Dict
        Structured data loaded by load_input_file().
    type_name : str
        Name of the new atom type (label).
    ncmp : int
        Number of atom species occupying the site.
    rmt : float
        Muffin-tin radius (0.0 for automatic determination).
    field : float
        External magnetic field.
    mxl : int
        Maximum angular momentum.
    atoms : List[Tuple[int, float]]
        List of (atomic number, concentration). The sum of concentrations should be 100.0.

    Returns
    -------
    Dict
        Structured data with new atom species definition added (new copy).

    Examples
    --------
    >>> input_data = load_input_file('test.in')
    >>> # Add new atom species
    >>> new_data = add_atom_type_definition(
    ...     input_data,
    ...     type_name='New_Type',
    ...     ncmp=1,
    ...     rmt=0.0,
    ...     field=0.0,
    ...     mxl=2,
    ...     atoms=[(26, 100.0)]  # 100% Fe atoms
    ... )
    """
    # Create new copy
    ntyp_value = input_data.get("ntyp")
    if ntyp_value is None:
        ntyp_value = len(input_data.get("atom_type_definitions", []))
    
    new_data = {
        "header": input_data["header"][:],
        "ntyp": ntyp_value + 1,
        "atom_type_definitions": [
            defn.copy() for defn in input_data.get("atom_type_definitions", [])
        ],
        "atomic_header": input_data["atomic_header"][:],
        "atomic_positions": input_data["atomic_positions"][:],
        "footer": input_data["footer"][:],
    }

    # Add new atom type definition
    new_type_def = {
        "type": type_name,
        "ncmp": ncmp,
        "rmt": rmt,
        "field": field,
        "mxl": mxl,
        "atoms": atoms[:],
    }

    new_data["atom_type_definitions"].append(new_type_def)

    return new_data


def modify_atom_type_definition(
    input_data: Dict,
    type_name: str,
    atoms: Optional[List[Tuple[int, float]]] = None,
    ncmp: Optional[int] = None,
    rmt: Optional[float] = None,
    field: Optional[float] = None,
    mxl: Optional[int] = None,
) -> Dict:
    """
    Modify an existing atom type definition.

    Parameters
    ----------
    input_data : Dict
        Structured data loaded by load_input_file().
    type_name : str
        Name of the atom type to modify.
    atoms : Optional[List[Tuple[int, float]]]
        New list of (atomic number, concentration). If None, keep original.
    ncmp : Optional[int]
        New number of atom species. If None, infer from atoms or keep original.
    rmt : Optional[float]
        New muffin-tin radius. If None, keep original.
    field : Optional[float]
        New external magnetic field. If None, keep original.
    mxl : Optional[int]
        New maximum angular momentum. If None, keep original.

    Returns
    -------
    Dict
        Structured data with modified atom type definition (new copy).

    Raises
    ------
    ValueError
        If the specified type_name is not found.

    Examples
    --------
    >>> input_data = load_input_file('test.in')
    >>> # Add vacancy to O2_1e_6 site (93% O + 7% vacancy)
    >>> modified = modify_atom_type_definition(
    ...     input_data,
    ...     type_name='O2_1e_6',
    ...     atoms=[(8, 93.0), (0, 7.0)]  # O 93%, vacancy 7%
    ... )
    """
    # Create new copy with deep copy of atom_type_definitions
    new_data = {
        "header": input_data["header"][:],
        "ntyp": input_data.get("ntyp", 0),
        "atom_type_definitions": [],
        "atomic_header": input_data["atomic_header"][:],
        "atomic_positions": input_data["atomic_positions"][:],
        "footer": input_data["footer"][:],
    }

    found = False
    for defn in input_data.get("atom_type_definitions", []):
        new_defn = {
            "type": defn["type"],
            "ncmp": defn["ncmp"],
            "rmt": defn["rmt"],
            "field": defn["field"],
            "mxl": defn["mxl"],
            "atoms": list(defn["atoms"]),
        }

        if defn["type"] == type_name:
            found = True
            if atoms is not None:
                new_defn["atoms"] = list(atoms)
                # Update ncmp if atoms are provided and ncmp is not specified
                if ncmp is None:
                    new_defn["ncmp"] = len(atoms)
            if ncmp is not None:
                new_defn["ncmp"] = ncmp
            if rmt is not None:
                new_defn["rmt"] = rmt
            if field is not None:
                new_defn["field"] = field
            if mxl is not None:
                new_defn["mxl"] = mxl

        new_data["atom_type_definitions"].append(new_defn)

    if not found:
        raise ValueError(f"Atom type '{type_name}' not found in input data.")

    return new_data


def count_atoms_by_type(input_data: Dict, type_name: str) -> int:
    """
    Count the number of atoms with the specified type in atomic positions.

    Parameters
    ----------
    input_data : Dict
        Structured data loaded by load_input_file().
    type_name : str
        Name of the atom type to count.

    Returns
    -------
    int
        Number of atoms with the specified type.

    Examples
    --------
    >>> input_data = load_input_file('test.in')
    >>> count = count_atoms_by_type(input_data, 'O2_1e_6')
    >>> print(f"Found {count} O2_1e_6 atoms")
    """
    count = 0
    for _, _, _, atmtyp in input_data["atomic_positions"]:
        if atmtyp == type_name:
            count += 1
    return count


def write_input_file(input_data: Dict, output_path: Union[str, Path]) -> None:
    """
    Write structured data as an AkaiKKR input file.

    Creates the output directory if it does not exist.

    Parameters
    ----------
    input_data : Dict
        Structured data created by load_input_file() or replacement functions.
    output_path : Union[str, Path]
        Path to the output file.

    Examples
    --------
    >>> input_data = load_input_file('test.in')
    >>> modified_data = replace_atom_types(input_data, {2: 'Ba_2t_0'})
    >>> write_input_file(modified_data, 'test_new.in')
    >>> # Directory is created automatically if it doesn't exist
    >>> write_input_file(modified_data, 'output/new_dir/test_new.in')
    """
    output_path = Path(output_path)
    
    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        # Header part
        f.writelines(input_data["header"])

        # ntyp section
        if "ntyp" in input_data and "atom_type_definitions" in input_data:
            # Collect actually used atom types
            used_types = set()
            for _, _, _, atmtyp in input_data["atomic_positions"]:
                used_types.add(atmtyp)

            # Filter only definitions of used atom types
            used_definitions = []
            type_def_dict = {
                defn["type"]: defn
                for defn in input_data["atom_type_definitions"]
            }

            # Add definitions of used types in order
            for _, _, _, atmtyp in input_data["atomic_positions"]:
                if atmtyp in type_def_dict and atmtyp not in [
                    d["type"] for d in used_definitions
                ]:
                    used_definitions.append(type_def_dict[atmtyp])

            f.write("c------------------------------------------------------------\n")
            f.write("c   ntyp\n")
            f.write(f"    {len(used_definitions)}\n")
            f.write("c------------------------------------------------------------\n")
            f.write("c   typ ncmp rmt field mxl [anclr conc]\n")

            # Each atom type definition
            for type_def in used_definitions:
                f.write(
                    f"    {type_def['type']}  {type_def['ncmp']}  "
                    f"{type_def['rmt']}  {type_def['field']}  {type_def['mxl']}\n"
                )
                for anclr, conc in type_def["atoms"]:
                    f.write(f"                              {anclr}  {conc}\n")

        # natm section (number of atoms)
        natm = len(input_data["atomic_positions"])
        f.write("c------------------------------------------------------------\n")
        f.write("c   natm\n")
        f.write(f"    {natm}\n")
        f.write("c------------------------------------------------------------\n")

        # Header of atomic position section
        # Remove separator lines (lines starting with c---) from atomic_header (to avoid duplication)
        header_lines = [
            line for line in input_data["atomic_header"]
            if not line.strip().startswith("c---")
        ]
        f.writelines(header_lines)

        # Atomic positions
        for x, y, z, atmtyp in input_data["atomic_positions"]:
            f.write(f"    {x}  {y}  {z}  {atmtyp}\n")

        # Footer part
        f.writelines(input_data["footer"])


def list_atomic_positions(input_data: Union[Dict, str, Path]) -> None:
    """
    List atomic positions in structured data or input file.

    Parameters
    ----------
    input_data : Union[Dict, str, Path]
        Structured data loaded by load_input_file(), or input file path.

    Examples
    --------
    >>> # Display from structured data
    >>> input_data = load_input_file('test.in')
    >>> list_atomic_positions(input_data)
    >>> # Or display directly from file path
    >>> list_atomic_positions('test.in')
    """
    if isinstance(input_data, (str, Path)):
        input_data = load_input_file(input_data)

    print(f"Found {len(input_data['atomic_positions'])} atomic positions:")
    for idx, (x, y, z, atmtyp) in enumerate(input_data["atomic_positions"]):
        print(f"Index {idx}: ({x}, {y}, {z}) -> {atmtyp}")


if __name__ == "__main__":
    # Usage example: Define new atom species and perform batch replacement by label
    input_file = "test/refs/test.in"
    output_file = "test/refs/test_modified.in"

    # Load input file
    input_data = load_input_file(input_file)

    # List atomic positions
    print("Original atomic positions:")
    list_atomic_positions(input_data)
    print()

    # Define new atom species (100% Fe atoms)
    new_data_with_type = add_atom_type_definition(
        input_data,
        type_name="Fe_new",
        ncmp=1,
        rmt=0.0,
        field=0.0,
        mxl=2,
        atoms=[(26, 100.0)],  # 100% Fe atoms (atomic number 26)
    )

    # Batch replacement by label
    # Replace all atoms with label 'Ba_2t_0' with newly defined Fe_new
    label_mapping = {"Ba_2t_0": "Fe_new"}
    modified_data = replace_atom_types_by_label(new_data_with_type, label_mapping)
    write_input_file(modified_data, output_file)

    print(f"Generated new input file: {output_file}")
    print("  (Added Fe_new atom type and replaced all Ba_2t_0 atoms with it)")
    print()

    # Another example: Define new mixed atom species and replace multiple labels
    output_file_2 = "test/refs/test_modified_2.in"
    # Add new mixed atom species (Y 50%, La 50%)
    new_data_with_mixed = add_atom_type_definition(
        input_data,
        type_name="Y0.5La0.5",
        ncmp=2,
        rmt=0.0,
        field=0.0,
        mxl=2,
        atoms=[(39, 50.0), (57, 50.0)],  # Y 50%, La 50%
    )

    # Replace multiple labels simultaneously with new mixed atom species
    label_mapping_2 = {
        "Ba_2t_0": "Y0.5La0.5",
        "Y_1h_2": "Y0.5La0.5",
    }
    modified_data_2 = replace_atom_types_by_label(
        new_data_with_mixed, label_mapping_2
    )
    write_input_file(modified_data_2, output_file_2)

    print(f"Generated another input file: {output_file_2}")
    print(
        "  (Added Y0.5La0.5 mixed atom type and replaced "
        "Ba_2t_0 and Y_1h_2 atoms with it)"
    )

