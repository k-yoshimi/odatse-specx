"""
AkaiKKR入力ファイル生成モジュール

位置（atmicx）は同じまま、粒子の種類（atmtyp）を変更して
新しい入力ファイルを生成する機能を提供する。
"""

from pathlib import Path
from typing import Dict, List, Tuple, Union, Optional


def parse_atomic_positions(
    input_lines: List[str],
) -> Tuple[List[str], List[Tuple[str, str, str, str]]]:
    """
    AkaiKKR入力ファイルから原子位置情報を抽出する。

    Parameters
    ----------
    input_lines : List[str]
        入力ファイルの行リスト。

    Returns
    -------
    Tuple[List[str], List[Tuple[str, str, str, str]]]
        ヘッダー行と原子位置情報のリスト。
        原子位置情報は (x, y, z, atmtyp) のタプル。
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
            # 空行やコメント行をスキップ
            stripped = line.strip()
            if not stripped or stripped.startswith("c") or stripped.startswith("#"):
                if not stripped.startswith("end"):
                    header_lines.append(line)
                continue

            # endが見つかったら終了
            if "end" in stripped.lower():
                break

            # 原子位置行をパース
            # 形式: x y z atmtyp または xa yb zc atmtyp
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
    AkaiKKR入力ファイルから原子タイプ定義情報を抽出する。

    Parameters
    ----------
    input_lines : List[str]
        入力ファイルの行リスト。

    Returns
    -------
    Tuple[int, List[Dict], int]
        ntypの値、原子タイプ定義のリスト、ntypセクションの開始インデックス。
        各原子タイプ定義は以下のキーを持つ辞書：
        - 'type': タイプ名
        - 'ncmp': 原子種数
        - 'rmt': マフィンティン半径
        - 'field': 外部磁場
        - 'mxl': 角運動量最大値
        - 'atoms': [(anclr, conc), ...] のリスト
    """
    ntyp = None
    atom_types = []
    ntyp_start_idx = None
    i = 0

    # ntyp行を見つける（コメント行に含まれている場合も考慮）
    while i < len(input_lines):
        line = input_lines[i]
        stripped = line.strip()

        # ntyp行を見つける（コメント行でも可）
        if "ntyp" in stripped.lower():
            ntyp_start_idx = i
            # 次の行からntypの値を読み取る
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

    # typ行を見つける
    while i < len(input_lines):
        line = input_lines[i]
        stripped = line.strip()

        # typ行を見つける
        if "typ" in stripped.lower() and "ncmp" in stripped.lower():
            i += 1
            break
        i += 1

    # 原子タイプ定義を読み取る
    while i < len(input_lines) and len(atom_types) < (ntyp or float("inf")):
        line = input_lines[i]
        stripped = line.strip()

        # コメント行や空行をスキップ
        if not stripped or stripped.startswith("c") or stripped.startswith("#"):
            # セクション区切り（natmなど）を見つけたら終了
            if "natm" in stripped.lower() or "atmicx" in stripped.lower():
                break
            i += 1
            continue

        # セクション区切りを見つけたら終了
        if "natm" in stripped.lower() or "atmicx" in stripped.lower():
            break

        # 原子タイプ定義行をパース
        # タブや複数の空白を考慮して分割
        parts = stripped.split()
        if len(parts) >= 5:
            # type名 ncmp rmt field mxl
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

            # 次の行からanclrとconcを読み取る
            i += 1
            atom_count = 0
            while atom_count < ncmp and i < len(input_lines):
                atom_line = input_lines[i]
                # タブを空白に置換してから処理
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
            # partsが5つ未満の場合は次の行へ
            i += 1

    # ntypが見つからない場合は、atom_typesの数から推測
    if ntyp is None:
        ntyp = len(atom_types)
    
    return ntyp, atom_types, ntyp_start_idx if ntyp_start_idx else 0


def load_input_file(input_path: Union[str, Path]) -> Dict:
    """
    AkaiKKR入力ファイルを読み込んで構造化データを返す。

    Parameters
    ----------
    input_path : Union[str, Path]
        入力ファイルのパス。

    Returns
    -------
    Dict
        解析された入力ファイルの情報を含む辞書。
        - 'header': ファイルの先頭部分（ntyp以前）
        - 'ntyp': 原子タイプ数
        - 'atom_type_definitions': 原子タイプ定義のリスト
        - 'atomic_header': atmicxセクションのヘッダー
        - 'atomic_positions': 原子位置情報のリスト
        - 'footer': ファイルの末尾部分（end以降）

    Examples
    --------
    >>> input_data = load_input_file('test.in')
    >>> print(f"Found {len(input_data['atomic_positions'])} atoms")
    >>> print(f"Found {input_data['ntyp']} atom types")
    """
    input_path = Path(input_path)
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 原子タイプ定義を解析
    ntyp, atom_type_definitions, ntyp_start_idx = parse_atom_type_definitions(lines)
    
    # ntypがNoneの場合は、atom_type_definitionsの数から推測
    if ntyp is None:
        ntyp = len(atom_type_definitions)

    # atmicxセクションを見つける
    atomic_start_idx = None
    for i, line in enumerate(lines):
        if "atmicx" in line.lower() or "atmtyp" in line.lower():
            atomic_start_idx = i
            break

    if atomic_start_idx is None:
        raise ValueError("atmicx atmtyp section not found in input file")

    # ヘッダー部分（ntyp以前）
    header = lines[:ntyp_start_idx]

    # 原子位置セクション
    atomic_header, atomic_positions = parse_atomic_positions(lines[atomic_start_idx:])

    # フッター部分（end以降）
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
    構造化データに対して、インデックス指定で原子の種類を置き換える。

    Parameters
    ----------
    input_data : Dict
        load_input_file()で読み込んだ構造化データ。
    atom_type_mapping : Dict[int, str]
        原子インデックス（0始まり）から新しいatmtypへのマッピング。
        例: {2: 'Ba_2t_0', 5: 'Cu_1a_5'}

    Returns
    -------
    Dict
        原子置換後の構造化データ（新しいコピー）。

    Examples
    --------
    >>> input_data = load_input_file('test.in')
    >>> modified_data = replace_atom_types(
    ...     input_data,
    ...     {2: 'Ba_2t_0', 5: 'Cu_1a_5'}
    ... )
    """
    # 新しいコピーを作成
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

    # 原子位置を更新
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
    構造化データに対して、座標指定で原子の種類を置き換える。

    Parameters
    ----------
    input_data : Dict
        load_input_file()で読み込んだ構造化データ。
    coordinate_mapping : Dict[Tuple[str, str, str], str]
        座標 (x, y, z) から新しいatmtypへのマッピング。
        例: {('0.5a', '0.5b', '0.5c'): 'Ba_2t_0'}

    Returns
    -------
    Dict
        原子置換後の構造化データ（新しいコピー）。

    Examples
    --------
    >>> input_data = load_input_file('test.in')
    >>> modified_data = replace_atom_types_by_coordinates(
    ...     input_data,
    ...     {('0.50000000a', '0.50000000b', '0.50000000c'): 'Ba_2t_0'}
    ... )
    """
    # 新しいコピーを作成
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

    # 原子位置を更新
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
    構造化データに対して、ラベル（atmtyp）を指定して
    同じラベルを持つすべての原子を一括で置き換える。

    Parameters
    ----------
    input_data : Dict
        load_input_file()で読み込んだ構造化データ。
    label_mapping : Dict[str, str]
        元のラベルから新しいラベルへのマッピング。
        例: {'Ba_2t_0': 'Y_1h_2', 'Cu_2q_3': 'Cu_1a_5'}

    Returns
    -------
    Dict
        原子置換後の構造化データ（新しいコピー）。

    Examples
    --------
    >>> input_data = load_input_file('test.in')
    >>> # Ba_2t_0というラベルを持つすべての原子をY_1h_2に置き換え
    >>> modified_data = replace_atom_types_by_label(
    ...     input_data,
    ...     {'Ba_2t_0': 'Y_1h_2'}
    ... )
    >>> # 複数のラベルを同時に置き換え
    >>> modified_data = replace_atom_types_by_label(
    ...     input_data,
    ...     {'Ba_2t_0': 'Y_1h_2', 'Cu_2q_3': 'Cu_1a_5'}
    ... )
    """
    # 新しいコピーを作成
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

    # 原子位置を更新
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
    新しい原子種の定義を追加する。

    Parameters
    ----------
    input_data : Dict
        load_input_file()で読み込んだ構造化データ。
    type_name : str
        新しい原子タイプの名前（ラベル）。
    ncmp : int
        そのサイトを占める原子種の数。
    rmt : float
        マフィンティン半径（0.0の場合は自動決定）。
    field : float
        外部磁場。
    mxl : int
        角運動量最大値。
    atoms : List[Tuple[int, float]]
        (原子番号, 濃度)のリスト。濃度の合計は100.0になることが推奨。

    Returns
    -------
    Dict
        新しい原子種定義が追加された構造化データ（新しいコピー）。

    Examples
    --------
    >>> input_data = load_input_file('test.in')
    >>> # 新しい原子種を追加
    >>> new_data = add_atom_type_definition(
    ...     input_data,
    ...     type_name='New_Type',
    ...     ncmp=1,
    ...     rmt=0.0,
    ...     field=0.0,
    ...     mxl=2,
    ...     atoms=[(26, 100.0)]  # Fe原子100%
    ... )
    """
    # 新しいコピーを作成
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

    # 新しい原子タイプ定義を追加
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


def write_input_file(input_data: Dict, output_path: Union[str, Path]) -> None:
    """
    構造化データをAkaiKKR入力ファイルとして書き出す。

    出力先のディレクトリが存在しない場合は自動的に作成する。

    Parameters
    ----------
    input_data : Dict
        load_input_file()または置換関数で作成した構造化データ。
    output_path : Union[str, Path]
        出力ファイルのパス。

    Examples
    --------
    >>> input_data = load_input_file('test.in')
    >>> modified_data = replace_atom_types(input_data, {2: 'Ba_2t_0'})
    >>> write_input_file(modified_data, 'test_new.in')
    >>> # ディレクトリが存在しない場合も自動的に作成される
    >>> write_input_file(modified_data, 'output/new_dir/test_new.in')
    """
    output_path = Path(output_path)
    
    # 出力先のディレクトリが存在しない場合は作成
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        # ヘッダー部分
        f.writelines(input_data["header"])

        # ntypセクション
        if "ntyp" in input_data and "atom_type_definitions" in input_data:
            # 実際に使用されている原子タイプを収集
            used_types = set()
            for _, _, _, atmtyp in input_data["atomic_positions"]:
                used_types.add(atmtyp)

            # 使用されている原子タイプの定義のみをフィルタリング
            used_definitions = []
            type_def_dict = {
                defn["type"]: defn
                for defn in input_data["atom_type_definitions"]
            }

            # 使用されているタイプの定義を順番に追加
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

            # 各原子タイプ定義
            for type_def in used_definitions:
                f.write(
                    f"    {type_def['type']}  {type_def['ncmp']}  "
                    f"{type_def['rmt']}  {type_def['field']}  {type_def['mxl']}\n"
                )
                for anclr, conc in type_def["atoms"]:
                    f.write(f"                              {anclr}  {conc}\n")

            f.write("c------------------------------------------------------------\n")

        # 原子位置セクションのヘッダー
        f.writelines(input_data["atomic_header"])

        # 原子位置
        for x, y, z, atmtyp in input_data["atomic_positions"]:
            f.write(f"    {x}  {y}  {z}  {atmtyp}\n")

        # フッター部分
        f.writelines(input_data["footer"])


def list_atomic_positions(input_data: Union[Dict, str, Path]) -> None:
    """
    構造化データまたは入力ファイル内の原子位置を一覧表示する。

    Parameters
    ----------
    input_data : Union[Dict, str, Path]
        load_input_file()で読み込んだ構造化データ、または入力ファイルのパス。

    Examples
    --------
    >>> # 構造化データから表示
    >>> input_data = load_input_file('test.in')
    >>> list_atomic_positions(input_data)
    >>> # またはファイルパスから直接表示
    >>> list_atomic_positions('test.in')
    """
    if isinstance(input_data, (str, Path)):
        input_data = load_input_file(input_data)

    print(f"Found {len(input_data['atomic_positions'])} atomic positions:")
    for idx, (x, y, z, atmtyp) in enumerate(input_data["atomic_positions"]):
        print(f"Index {idx}: ({x}, {y}, {z}) -> {atmtyp}")


if __name__ == "__main__":
    # 使用例: 新しい原子種を定義して、ラベル指定での一括置換を行う
    input_file = "refs/REBCO/test-1/test.in"
    output_file = "refs/REBCO/test-1/test_modified.in"

    # 入力ファイルを読み込む
    input_data = load_input_file(input_file)

    # 原子位置を一覧表示
    print("Original atomic positions:")
    list_atomic_positions(input_data)
    print()

    # 新しい原子種を定義（Fe原子100%）
    new_data_with_type = add_atom_type_definition(
        input_data,
        type_name="Fe_new",
        ncmp=1,
        rmt=0.0,
        field=0.0,
        mxl=2,
        atoms=[(26, 100.0)],  # Fe原子（原子番号26）100%
    )

    # ラベル指定での一括置換
    # Ba_2t_0というラベルを持つすべての原子を新しく定義したFe_newに置き換え
    label_mapping = {"Ba_2t_0": "Fe_new"}
    modified_data = replace_atom_types_by_label(new_data_with_type, label_mapping)
    write_input_file(modified_data, output_file)

    print(f"Generated new input file: {output_file}")
    print("  (Added Fe_new atom type and replaced all Ba_2t_0 atoms with it)")
    print()

    # 別の例: 新しい混合原子種を定義して、複数のラベルを一括置換
    output_file_2 = "refs/REBCO/test-1-out/test_modified_2.in"
    # 新しい混合原子種（Y 50%, La 50%）を追加
    new_data_with_mixed = add_atom_type_definition(
        input_data,
        type_name="Y0.5La0.5",
        ncmp=2,
        rmt=0.0,
        field=0.0,
        mxl=2,
        atoms=[(39, 50.0), (57, 50.0)],  # Y 50%, La 50%
    )

    # 複数のラベルを同時に新しい混合原子種に置き換え
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

