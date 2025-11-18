"""
AkaiKKR入力ファイル生成モジュールのテストスイート

テスト対象:
- load_input_file()
- replace_atom_types()
- replace_atom_types_by_coordinates()
- replace_atom_types_by_label()
- add_atom_type_definition()
- write_input_file()
- 統合テスト
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
    """load_input_file()のテスト"""

    def setUp(self):
        """テストのセットアップ"""
        self.test_input_file = "refs/odatse-specx/test-1/test.in"
        self.sample_input_data = load_input_file(self.test_input_file)

    def test_load_input_file_basic(self):
        """基本的な読み込みテスト"""
        data = load_input_file(self.test_input_file)

        assert "ntyp" in data
        assert "atom_type_definitions" in data
        assert "atomic_positions" in data
        assert "header" in data
        assert "footer" in data

    def test_load_input_file_ntyp(self):
        """ntypの値が正しく読み込まれているか"""
        self.assertEqual(self.sample_input_data["ntyp"], 8)

    def test_load_input_file_atom_type_definitions(self):
        """原子タイプ定義が正しく読み込まれているか"""
        self.assertEqual(len(self.sample_input_data["atom_type_definitions"]), 8)

        # 最初の原子タイプを確認
        first_type = self.sample_input_data["atom_type_definitions"][0]
        self.assertEqual(first_type["type"], "Ba_2t_0")
        self.assertEqual(first_type["ncmp"], 1)
        self.assertEqual(len(first_type["atoms"]), 1)
        self.assertEqual(first_type["atoms"][0], (56, 100.0))

    def test_load_input_file_atomic_positions(self):
        """原子位置が正しく読み込まれているか"""
        self.assertEqual(len(self.sample_input_data["atomic_positions"]), 13)

        # 最初の原子位置を確認
        first_pos = self.sample_input_data["atomic_positions"][0]
        self.assertEqual(len(first_pos), 4)
        self.assertEqual(first_pos[3], "Ba_2t_0")  # atmtyp

    def test_load_input_file_immutability(self):
        """複数回読み込んでも同じ結果が得られるか"""
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
    """replace_atom_types()のテスト"""

    def setUp(self):
        """テストのセットアップ"""
        self.test_input_file = "refs/odatse-specx/test-1/test.in"
        self.sample_input_data = load_input_file(self.test_input_file)

    def test_replace_atom_types_basic(self):
        """基本的な置換テスト"""
        modified = replace_atom_types(self.sample_input_data, {0: "Y_1h_2"})

        # 元のデータは変更されていない
        self.assertEqual(self.sample_input_data["atomic_positions"][0][3], "Ba_2t_0")

        # 新しいデータは変更されている
        self.assertEqual(modified["atomic_positions"][0][3], "Y_1h_2")

    def test_replace_atom_types_multiple(self):
        """複数の原子を置換"""
        modified = replace_atom_types(
            self.sample_input_data, {0: "Y_1h_2", 5: "Cu_2q_3"}
        )

        self.assertEqual(modified["atomic_positions"][0][3], "Y_1h_2")
        self.assertEqual(modified["atomic_positions"][5][3], "Cu_2q_3")
        # 置換されていない原子は元のまま
        self.assertEqual(modified["atomic_positions"][1][3], "Ba_2t_0")

    def test_replace_atom_types_immutability(self):
        """元のデータが保持されるか"""
        original_first = self.sample_input_data["atomic_positions"][0]

        modified = replace_atom_types(self.sample_input_data, {0: "Y_1h_2"})

        # 元のデータは変更されていない
        self.assertEqual(self.sample_input_data["atomic_positions"][0], original_first)
        # 新しいデータは変更されている
        self.assertEqual(modified["atomic_positions"][0][3], "Y_1h_2")


class TestReplaceAtomTypesByCoordinates(unittest.TestCase):
    """replace_atom_types_by_coordinates()のテスト"""

    def setUp(self):
        """テストのセットアップ"""
        self.test_input_file = "refs/odatse-specx/test-1/test.in"
        self.sample_input_data = load_input_file(self.test_input_file)

    def test_replace_atom_types_by_coordinates_basic(self):
        """座標指定での置換テスト"""
        coord = (
            "0.50000000a",
            "0.50000000b",
            "0.50000000c",
        )
        modified = replace_atom_types_by_coordinates(
            self.sample_input_data, {coord: "Cu_1a_5"}
        )

        # 指定した座標の原子が置換されている
        found = False
        for x, y, z, atmtyp in modified["atomic_positions"]:
            if (x, y, z) == coord:
                self.assertEqual(atmtyp, "Cu_1a_5")
                found = True
                break
        self.assertTrue(found, "指定した座標の原子が見つかりません")

    def test_replace_atom_types_by_coordinates_immutability(self):
        """元のデータが保持されるか"""
        original_positions = self.sample_input_data["atomic_positions"][:]

        coord = (
            "0.50000000a",
            "0.50000000b",
            "0.50000000c",
        )
        modified = replace_atom_types_by_coordinates(
            self.sample_input_data, {coord: "Cu_1a_5"}
        )

        # 元のデータは変更されていない
        self.assertEqual(
            self.sample_input_data["atomic_positions"], original_positions
        )


class TestReplaceAtomTypesByLabel(unittest.TestCase):
    """replace_atom_types_by_label()のテスト"""

    def setUp(self):
        """テストのセットアップ"""
        self.test_input_file = "refs/odatse-specx/test-1/test.in"
        self.sample_input_data = load_input_file(self.test_input_file)

    def test_replace_atom_types_by_label_basic(self):
        """基本的なラベル置換テスト"""
        modified = replace_atom_types_by_label(
            self.sample_input_data, {"Ba_2t_0": "Y_1h_2"}
        )

        # Ba_2t_0を持つすべての原子が置換されていることを確認
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
        """同じラベルのすべての原子が置換されるか"""
        # Ba_2t_0は2つある
        ba_count = sum(
            1
            for _, _, _, atmtyp in self.sample_input_data["atomic_positions"]
            if atmtyp == "Ba_2t_0"
        )
        self.assertEqual(ba_count, 2)

        modified = replace_atom_types_by_label(
            self.sample_input_data, {"Ba_2t_0": "Y_1h_2"}
        )

        # すべてのBa_2t_0が置換されている
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
        )  # 元のY_1h_2 + 置換されたBa_2t_0

    def test_replace_atom_types_by_label_multiple(self):
        """複数のラベルを同時に置換"""
        modified = replace_atom_types_by_label(
            self.sample_input_data, {"Ba_2t_0": "Y_1h_2", "Cu_2q_3": "Cu_1a_5"}
        )

        # 両方のラベルが置換されている
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
        """元のデータが保持されるか"""
        original_positions = self.sample_input_data["atomic_positions"][:]

        modified = replace_atom_types_by_label(
            self.sample_input_data, {"Ba_2t_0": "Y_1h_2"}
        )

        # 元のデータは変更されていない
        self.assertEqual(
            self.sample_input_data["atomic_positions"], original_positions
        )


class TestAddAtomTypeDefinition(unittest.TestCase):
    """add_atom_type_definition()のテスト"""

    def setUp(self):
        """テストのセットアップ"""
        self.test_input_file = "refs/odatse-specx/test-1/test.in"
        self.sample_input_data = load_input_file(self.test_input_file)

    def test_add_atom_type_definition_basic(self):
        """基本的な原子タイプ追加テスト"""
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

        # 新しい原子タイプが追加されている
        self.assertEqual(
            len(new_data["atom_type_definitions"]), original_count + 1
        )
        self.assertEqual(new_data["ntyp"], original_count + 1)

        # 追加された原子タイプを確認
        fe_type = None
        for type_def in new_data["atom_type_definitions"]:
            if type_def["type"] == "Fe_new":
                fe_type = type_def
                break

        self.assertIsNotNone(fe_type)
        self.assertEqual(fe_type["ncmp"], 1)
        self.assertEqual(fe_type["atoms"], [(26, 100.0)])

    def test_add_atom_type_definition_mixed(self):
        """混合原子タイプの追加テスト"""
        new_data = add_atom_type_definition(
            self.sample_input_data,
            type_name="Y0.5La0.5",
            ncmp=2,
            rmt=0.0,
            field=0.0,
            mxl=2,
            atoms=[(39, 50.0), (57, 50.0)],
        )

        # 混合原子タイプが追加されている
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
        """元のデータが保持されるか"""
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

        # 元のデータは変更されていない
        self.assertEqual(
            len(self.sample_input_data["atom_type_definitions"]), original_count
        )


class TestWriteInputFile(unittest.TestCase):
    """write_input_file()のテスト"""

    def setUp(self):
        """テストのセットアップ"""
        self.test_input_file = "refs/odatse-specx/test-1/test.in"
        self.sample_input_data = load_input_file(self.test_input_file)

    def test_write_input_file_basic(self):
        """基本的な書き込みテスト"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".in", delete=False
        ) as f:
            temp_path = f.name

        try:
            write_input_file(self.sample_input_data, temp_path)

            # ファイルが作成されている
            self.assertTrue(Path(temp_path).exists())

            # ファイルを再度読み込んで確認
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
        """使用されている原子タイプのみが書き出されるか"""
        # 新しい原子タイプを追加
        new_data = add_atom_type_definition(
            self.sample_input_data,
            type_name="Unused_Type",
            ncmp=1,
            rmt=0.0,
            field=0.0,
            mxl=2,
            atoms=[(1, 100.0)],
        )

        # 使用されていない原子タイプで置換（実際には使用されない）
        # 実際に使用されているタイプのみを確認
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".in", delete=False
        ) as f:
            temp_path = f.name

        try:
            write_input_file(new_data, temp_path)

            # ファイルを再度読み込んで確認
            reloaded = load_input_file(temp_path)

            # 使用されている原子タイプの数を確認
            used_types = set()
            for _, _, _, atmtyp in new_data["atomic_positions"]:
                used_types.add(atmtyp)

            # 書き出された原子タイプ定義の数が使用されているタイプの数と一致する
            self.assertEqual(
                len(reloaded["atom_type_definitions"]), len(used_types)
            )
            self.assertEqual(reloaded["ntyp"], len(used_types))

            # Unused_Typeは使用されていないので書き出されていない
            type_names = {d["type"] for d in reloaded["atom_type_definitions"]}
            self.assertNotIn("Unused_Type", type_names)
        finally:
            Path(temp_path).unlink()

    def test_write_input_file_create_directory(self):
        """存在しないディレクトリが自動的に作成されるか"""
        import tempfile
        import shutil

        # 一時ディレクトリを作成
        temp_dir = tempfile.mkdtemp()
        try:
            # 存在しないサブディレクトリを含むパス
            output_path = Path(temp_dir) / "new_dir" / "sub_dir" / "test.in"

            # ディレクトリが存在しないことを確認
            self.assertFalse(output_path.parent.exists())

            # ファイルを書き出す
            write_input_file(self.sample_input_data, output_path)

            # ディレクトリが作成されている
            self.assertTrue(output_path.parent.exists())
            # ファイルが作成されている
            self.assertTrue(output_path.exists())

            # ファイルを再度読み込んで確認
            reloaded = load_input_file(output_path)
            self.assertEqual(reloaded["ntyp"], self.sample_input_data["ntyp"])
        finally:
            # 一時ディレクトリを削除
            shutil.rmtree(temp_dir)


class TestIntegration(unittest.TestCase):
    """統合テスト"""

    def setUp(self):
        """テストのセットアップ"""
        self.test_input_file = "refs/odatse-specx/test-1/test.in"
        self.sample_input_data = load_input_file(self.test_input_file)

    def test_full_workflow(self):
        """完全なワークフローのテスト"""
        # 1. 新しい原子タイプを追加
        new_data = add_atom_type_definition(
            self.sample_input_data,
            type_name="Fe_new",
            ncmp=1,
            rmt=0.0,
            field=0.0,
            mxl=2,
            atoms=[(26, 100.0)],
        )

        # 2. ラベルで置換
        modified = replace_atom_types_by_label(
            new_data, {"Ba_2t_0": "Fe_new"}
        )

        # 3. ファイルに書き出し
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".in", delete=False
        ) as f:
            temp_path = f.name

        try:
            write_input_file(modified, temp_path)

            # 4. 再度読み込んで確認
            reloaded = load_input_file(temp_path)

            # 検証
            type_names = {d["type"] for d in reloaded["atom_type_definitions"]}
            self.assertIn("Fe_new", type_names)

            # Ba_2t_0がFe_newに置換されている
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
            )  # 元のBa_2t_0が置換された
        finally:
            Path(temp_path).unlink()

    def test_multiple_variations_from_same_data(self):
        """同じデータから複数のバリエーションを生成"""
        # パターン1
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

        # パターン2（元のデータから）
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

        # 元のデータは変更されていない
        self.assertEqual(
            len(self.sample_input_data["atom_type_definitions"]), 8
        )

        # 各パターンが正しく生成されている
        self.assertEqual(len(modified1["atom_type_definitions"]), 9)
        self.assertEqual(len(modified2["atom_type_definitions"]), 9)

        # パターン1ではFe_newが使用されている
        fe_in_1 = any(
            d["type"] == "Fe_new"
            for d in modified1["atom_type_definitions"]
        )
        self.assertTrue(fe_in_1)

        # パターン2ではY0.5La0.5が使用されている
        yla_in_2 = any(
            d["type"] == "Y0.5La0.5"
            for d in modified2["atom_type_definitions"]
        )
        self.assertTrue(yla_in_2)


if __name__ == "__main__":
    unittest.main(verbosity=2)

