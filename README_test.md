# テストスイートの説明

`test_generate_input.py`は、`generate_input.py`モジュールの機能をテストするための包括的なテストスイートです。

## テストの実行方法

### 基本的な実行

```bash
python3 test_generate_input.py
```

### 詳細な出力で実行

```bash
python3 test_generate_input.py -v
```

または

```bash
python3 -m unittest test_generate_input.py -v
```

## テスト構成

テストスイートは以下の7つのテストクラスで構成されています：

### 1. TestLoadInputFile (5テスト)

`load_input_file()`関数のテスト

- `test_load_input_file_basic`: 基本的な読み込みテスト
- `test_load_input_file_ntyp`: ntypの値が正しく読み込まれているか
- `test_load_input_file_atom_type_definitions`: 原子タイプ定義が正しく読み込まれているか
- `test_load_input_file_atomic_positions`: 原子位置が正しく読み込まれているか
- `test_load_input_file_immutability`: 複数回読み込んでも同じ結果が得られるか

### 2. TestReplaceAtomTypes (3テスト)

`replace_atom_types()`関数のテスト

- `test_replace_atom_types_basic`: 基本的な置換テスト
- `test_replace_atom_types_multiple`: 複数の原子を置換
- `test_replace_atom_types_immutability`: 元のデータが保持されるか

### 3. TestReplaceAtomTypesByCoordinates (2テスト)

`replace_atom_types_by_coordinates()`関数のテスト

- `test_replace_atom_types_by_coordinates_basic`: 座標指定での置換テスト
- `test_replace_atom_types_by_coordinates_immutability`: 元のデータが保持されるか

### 4. TestReplaceAtomTypesByLabel (4テスト)

`replace_atom_types_by_label()`関数のテスト

- `test_replace_atom_types_by_label_basic`: 基本的なラベル置換テスト
- `test_replace_atom_types_by_label_all_instances`: 同じラベルのすべての原子が置換されるか
- `test_replace_atom_types_by_label_multiple`: 複数のラベルを同時に置換
- `test_replace_atom_types_by_label_immutability`: 元のデータが保持されるか

### 5. TestAddAtomTypeDefinition (3テスト)

`add_atom_type_definition()`関数のテスト

- `test_add_atom_type_definition_basic`: 基本的な原子タイプ追加テスト
- `test_add_atom_type_definition_mixed`: 混合原子タイプの追加テスト
- `test_add_atom_type_definition_immutability`: 元のデータが保持されるか

### 6. TestWriteInputFile (3テスト)

`write_input_file()`関数のテスト

- `test_write_input_file_basic`: 基本的な書き込みテスト
- `test_write_input_file_only_used_types`: 使用されている原子タイプのみが書き出されるか
- `test_write_input_file_create_directory`: 存在しないディレクトリが自動的に作成されるか

### 7. TestIntegration (2テスト)

統合テスト

- `test_full_workflow`: 完全なワークフローのテスト（新しい原子タイプ追加→置換→書き出し→読み込み）
- `test_multiple_variations_from_same_data`: 同じデータから複数のバリエーションを生成

## テストのカバレッジ

テストスイートは以下の機能をカバーしています：

- ✅ 入力ファイルの読み込み
- ✅ インデックス指定での原子置換
- ✅ 座標指定での原子置換
- ✅ ラベル指定での一括置換
- ✅ 新しい原子種の定義（単一・混合）
- ✅ ファイルへの書き出し
- ✅ ディレクトリの自動作成
- ✅ データの不変性（元のデータが保持されること）
- ✅ 統合ワークフロー

## テストの前提条件

テストは以下のファイルを前提としています：

- `refs/REBCO/test-4/test.in`: テスト用の入力ファイル

このファイルが存在しない場合、テストは失敗します。

## テストの実行結果の例

正常に実行された場合、以下のような出力が表示されます：

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

## トラブルシューティング

### テストが失敗する場合

1. **ファイルが見つからないエラー**
   - `refs/REBCO/test-4/test.in`が存在することを確認してください

2. **インポートエラー**
   - `generate_input.py`が同じディレクトリにあることを確認してください

3. **権限エラー**
   - 一時ファイルの作成に必要な権限があることを確認してください

## テストの拡張

新しい機能を追加した場合は、対応するテストも追加してください。テストの構造は以下の通りです：

```python
class TestNewFeature(unittest.TestCase):
    """新しい機能のテスト"""

    def setUp(self):
        """テストのセットアップ"""
        self.test_input_file = "refs/REBCO/test-4/test.in"
        self.sample_input_data = load_input_file(self.test_input_file)

    def test_new_feature_basic(self):
        """基本的な機能テスト"""
        # テストコード
        pass

    def test_new_feature_immutability(self):
        """不変性のテスト"""
        # テストコード
        pass
```

## 参考資料

- [Python unittest ドキュメント](https://docs.python.org/3/library/unittest.html)

