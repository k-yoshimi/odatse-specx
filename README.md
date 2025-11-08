# REBCO - AkaiKKR入力ファイル生成ツール

AkaiKKRの入力ファイルを生成・編集するためのPythonツールです。

## 概要

このプロジェクトは、AkaiKKR（第一原理計算コード）の入力ファイルを読み込み、原子の種類を置き換えたり、新しい原子種を定義したりして、複数のバリエーションの入力ファイルを効率的に生成するためのツールです。

## 主な機能

- **入力ファイルの読み込み**: AkaiKKRの入力ファイルを構造化データとして読み込む
- **原子の種類の置換**: 
  - インデックス指定での置換
  - 座標指定での置換
  - ラベル指定での一括置換
- **新しい原子種の定義**: 単一原子種や混合原子種を定義して追加
- **入力ファイルの書き出し**: 構造化データをAkaiKKR入力ファイル形式で書き出し

## ファイル構成

```
REBCO/
├── README.md                 # このファイル（プロジェクト全体の説明）
├── generate_input.py         # メインのモジュール
├── README_generate_input.md  # generate_input.pyの詳細ドキュメント
├── test_generate_input.py    # テストスイート
├── README_test.md            # テストの説明
├── LICENSE                   # ライセンスファイル
└── refs/                     # 参照用の入力ファイル
    └── REBCO/
        └── test-1/
```

## クイックスタート

### 基本的な使用例

```python
from generate_input import (
    load_input_file,
    replace_atom_types_by_label,
    add_atom_type_definition,
    write_input_file,
)

# 入力ファイルを読み込む
input_data = load_input_file("refs/REBCO/test-4/test.in")

# 新しい原子種を定義
new_data = add_atom_type_definition(
    input_data,
    type_name="Fe_new",
    ncmp=1,
    rmt=0.0,
    field=0.0,
    mxl=2,
    atoms=[(26, 100.0)],  # Fe原子100%
)

# ラベル指定で一括置換
modified = replace_atom_types_by_label(
    new_data,
    {"Ba_2t_0": "Fe_new"}
)

# ファイルに書き出し（ディレクトリが存在しない場合は自動作成）
write_input_file(modified, "output/test_modified.in")
```

## 詳細ドキュメント

- **`generate_input.py`の詳細**: [README_generate_input.md](README_generate_input.md)
- **テストの説明**: [README_test.md](README_test.md)

## テスト

テストスイートを実行するには：

```bash
python3 test_generate_input.py
```

詳細は [README_test.md](README_test.md) を参照してください。

## ライセンス

MIT License

## 参考資料

- [AkaiKKR公式ドキュメント](https://academeia.github.io/AkaiKKR_Documents/input)

