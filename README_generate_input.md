# generate_input.py ドキュメント

AkaiKKR入力ファイルを生成・編集するためのモジュールです。

## 概要

このモジュールは、AkaiKKRの入力ファイルを読み込み、原子の種類を置き換えたり、新しい原子種を定義したりして、複数のバリエーションの入力ファイルを効率的に生成する機能を提供します。

## 主な関数

### ファイルの読み込み

#### `load_input_file(input_path: Union[str, Path]) -> Dict`

AkaiKKR入力ファイルを読み込んで構造化データを返します。

**Parameters**
- `input_path`: 入力ファイルのパス

**Returns**
- 構造化データの辞書:
  - `header`: ファイルの先頭部分（ntyp以前）
  - `ntyp`: 原子タイプ数
  - `atom_type_definitions`: 原子タイプ定義のリスト
  - `atomic_header`: atmicxセクションのヘッダー
  - `atomic_positions`: 原子位置情報のリスト
  - `footer`: ファイルの末尾部分（end以降）

**Examples**
```python
input_data = load_input_file("test.in")
print(f"Found {input_data['ntyp']} atom types")
print(f"Found {len(input_data['atomic_positions'])} atoms")
```

### 原子の種類の置換

#### `replace_atom_types(input_data: Dict, atom_type_mapping: Dict[int, str]) -> Dict`

インデックス指定で原子の種類を置き換えます。

**Parameters**
- `input_data`: `load_input_file()`で読み込んだ構造化データ
- `atom_type_mapping`: 原子インデックス（0始まり）から新しいatmtypへのマッピング

**Returns**
- 原子置換後の構造化データ（新しいコピー）

**Examples**
```python
# インデックス0と5の原子を置き換え
modified = replace_atom_types(
    input_data,
    {0: "Y_1h_2", 5: "Cu_2q_3"}
)
```

#### `replace_atom_types_by_coordinates(input_data: Dict, coordinate_mapping: Dict[Tuple[str, str, str], str]) -> Dict`

座標指定で原子の種類を置き換えます。

**Parameters**
- `input_data`: `load_input_file()`で読み込んだ構造化データ
- `coordinate_mapping`: 座標 (x, y, z) から新しいatmtypへのマッピング

**Returns**
- 原子置換後の構造化データ（新しいコピー）

**Examples**
```python
# 特定の座標の原子を置き換え
modified = replace_atom_types_by_coordinates(
    input_data,
    {("0.50000000a", "0.50000000b", "0.50000000c"): "Ba_2t_0"}
)
```

#### `replace_atom_types_by_label(input_data: Dict, label_mapping: Dict[str, str]) -> Dict`

ラベル（atmtyp）を指定して、同じラベルを持つすべての原子を一括で置き換えます。

**Parameters**
- `input_data`: `load_input_file()`で読み込んだ構造化データ
- `label_mapping`: 元のラベルから新しいラベルへのマッピング

**Returns**
- 原子置換後の構造化データ（新しいコピー）

**Examples**
```python
# Ba_2t_0というラベルを持つすべての原子をY_1h_2に置き換え
modified = replace_atom_types_by_label(
    input_data,
    {"Ba_2t_0": "Y_1h_2"}
)

# 複数のラベルを同時に置き換え
modified = replace_atom_types_by_label(
    input_data,
    {"Ba_2t_0": "Y_1h_2", "Cu_2q_3": "Cu_1a_5"}
)
```

### 新しい原子種の定義

#### `add_atom_type_definition(input_data: Dict, type_name: str, ncmp: int, rmt: float, field: float, mxl: int, atoms: List[Tuple[int, float]]) -> Dict`

新しい原子種の定義を追加します。

**Parameters**
- `input_data`: `load_input_file()`で読み込んだ構造化データ
- `type_name`: 新しい原子タイプの名前（ラベル）
- `ncmp`: そのサイトを占める原子種の数
- `rmt`: マフィンティン半径（0.0の場合は自動決定）
- `field`: 外部磁場
- `mxl`: 角運動量最大値
- `atoms`: (原子番号, 濃度)のリスト。濃度の合計は100.0になることが推奨

**Returns**
- 新しい原子種定義が追加された構造化データ（新しいコピー）

**Examples**
```python
# 単一原子種（Fe原子100%）を追加
new_data = add_atom_type_definition(
    input_data,
    type_name="Fe_new",
    ncmp=1,
    rmt=0.0,
    field=0.0,
    mxl=2,
    atoms=[(26, 100.0)]  # Fe原子（原子番号26）100%
)

# 混合原子種（Y 50%, La 50%）を追加
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

### ファイルの書き出し

#### `write_input_file(input_data: Dict, output_path: Union[str, Path]) -> None`

構造化データをAkaiKKR入力ファイルとして書き出します。

出力先のディレクトリが存在しない場合は自動的に作成されます。

**Parameters**
- `input_data`: `load_input_file()`または置換関数で作成した構造化データ
- `output_path`: 出力ファイルのパス

**Examples**
```python
# 基本的な書き出し
write_input_file(modified_data, "test_new.in")

# ディレクトリが存在しない場合も自動的に作成される
write_input_file(modified_data, "output/new_dir/test_new.in")
```

### ユーティリティ関数

#### `list_atomic_positions(input_data: Union[Dict, str, Path]) -> None`

構造化データまたは入力ファイル内の原子位置を一覧表示します。

**Parameters**
- `input_data`: `load_input_file()`で読み込んだ構造化データ、または入力ファイルのパス

**Examples**
```python
# 構造化データから表示
input_data = load_input_file("test.in")
list_atomic_positions(input_data)

# またはファイルパスから直接表示
list_atomic_positions("test.in")
```

## 使用例

### 例1: 新しい原子種を定義してラベル指定で一括置換

```python
from generate_input import (
    load_input_file,
    add_atom_type_definition,
    replace_atom_types_by_label,
    write_input_file,
)

# 入力ファイルを読み込む
input_data = load_input_file("refs/REBCO/test-4/test.in")

# 新しい原子種（Fe原子100%）を追加
new_data = add_atom_type_definition(
    input_data,
    type_name="Fe_new",
    ncmp=1,
    rmt=0.0,
    field=0.0,
    mxl=2,
    atoms=[(26, 100.0)],
)

# Ba_2t_0というラベルを持つすべての原子をFe_newに置き換え
modified = replace_atom_types_by_label(
    new_data,
    {"Ba_2t_0": "Fe_new"}
)

# ファイルに書き出し
write_input_file(modified, "output/test_modified.in")
```

### 例2: 同じデータから複数のバリエーションを生成

```python
from generate_input import (
    load_input_file,
    add_atom_type_definition,
    replace_atom_types_by_label,
    write_input_file,
)

# 入力ファイルを一度だけ読み込む
input_data = load_input_file("refs/REBCO/test-4/test.in")

# パターン1: Fe_newを追加してBa_2t_0を置き換え
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

# パターン2: 元のデータから別のパターンを生成
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

## 重要な注意事項

### データの不変性

すべての置換関数と`add_atom_type_definition()`は、元のデータを変更せずに新しいコピーを返します。これにより、同じ`input_data`から複数の異なるバリエーションを生成できます。

```python
input_data = load_input_file("test.in")

# パターン1
modified1 = replace_atom_types_by_label(input_data, {"Ba_2t_0": "Y_1h_2"})

# パターン2（元のinput_dataから）
modified2 = replace_atom_types_by_label(input_data, {"Cu_2q_3": "Cu_1a_5"})

# input_dataは変更されていない
```

### 使用されている原子タイプのみが書き出される

`write_input_file()`は、実際に原子位置で使用されている原子タイプの定義のみを書き出します。定義されているが使用されていない原子タイプは出力ファイルに含まれません。

### ディレクトリの自動作成

`write_input_file()`は、出力先のディレクトリが存在しない場合、自動的に作成します。

```python
# ディレクトリが存在しない場合でも自動的に作成される
write_input_file(modified_data, "output/new_dir/test.in")
```

## 原子番号の参考

主要な原子の原子番号：

- H: 1, He: 2
- Li: 3, Be: 4, B: 5, C: 6, N: 7, O: 8, F: 9, Ne: 10
- Na: 11, Mg: 12, Al: 13, Si: 14, P: 15, S: 16, Cl: 17, Ar: 18
- K: 19, Ca: 20, Sc: 21, Ti: 22, V: 23, Cr: 24, Mn: 25, Fe: 26, Co: 27, Ni: 28, Cu: 29, Zn: 30
- Y: 39, Zr: 40, Nb: 41, Mo: 42, Tc: 43, Ru: 44, Rh: 45, Pd: 46, Ag: 47, Cd: 48
- La: 57, Ce: 58, Pr: 59, Nd: 60, Pm: 61, Sm: 62, Eu: 63, Gd: 64
- Ba: 56

## 参考資料

- [AkaiKKR入力ファイルの解説](https://academeia.github.io/AkaiKKR_Documents/input)

